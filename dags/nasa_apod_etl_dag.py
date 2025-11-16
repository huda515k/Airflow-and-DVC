"""
NASA APOD ETL Pipeline DAG
This DAG implements a complete ETL pipeline with 5 sequential steps:
1. Extract data from NASA APOD API
2. Transform JSON data into structured format
3. Load data to PostgreSQL and CSV
4. Version data with DVC
5. Commit DVC metadata to Git
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import requests
import pandas as pd
import json
import os
import subprocess
import logging

# Default arguments for the DAG
default_args = {
    'owner': 'mlops',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# DAG definition
dag = DAG(
    'nasa_apod_etl_pipeline',
    default_args=default_args,
    description='ETL pipeline for NASA APOD data with DVC versioning',
    schedule_interval=timedelta(days=1),  # Run daily
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['etl', 'nasa', 'dvc', 'mlops'],
)

# Configuration
NASA_API_URL = "https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY"
CSV_FILE_PATH = "/opt/airflow/data/apod_data.csv"
DVC_REPO_PATH = "/opt/airflow/dvc_repo"
GIT_REPO_PATH = "/opt/airflow/dvc_repo"


def extract_nasa_data(**context):
    """
    Step 1: Extract data from NASA APOD API
    """
    logging.info("Step 1: Extracting data from NASA APOD API...")
    
    try:
        response = requests.get(NASA_API_URL, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        logging.info(f"Successfully extracted data: {data.get('title', 'Unknown')}")
        
        # Store in XCom for next task
        context['ti'].xcom_push(key='raw_data', value=data)
        
        return data
    except Exception as e:
        logging.error(f"Error extracting data: {str(e)}")
        raise


def transform_data(**context):
    """
    Step 2: Transform JSON data into structured format using Pandas
    """
    logging.info("Step 2: Transforming data...")
    
    try:
        # Retrieve data from previous task
        raw_data = context['ti'].xcom_pull(key='raw_data', task_ids='extract_nasa_data')
        
        if not raw_data:
            raise ValueError("No data received from extraction step")
        
        # Select specific fields of interest
        fields_of_interest = {
            'date': raw_data.get('date', ''),
            'title': raw_data.get('title', ''),
            'url': raw_data.get('url', ''),
            'explanation': raw_data.get('explanation', ''),
            'media_type': raw_data.get('media_type', ''),
            'copyright': raw_data.get('copyright', ''),
        }
        
        # Create DataFrame
        df = pd.DataFrame([fields_of_interest])
        
        # Add timestamp for tracking
        df['ingestion_timestamp'] = datetime.now().isoformat()
        
        logging.info(f"Transformed data shape: {df.shape}")
        logging.info(f"Columns: {df.columns.tolist()}")
        
        # Store DataFrame as JSON in XCom (for passing to next task)
        df_json = df.to_json(orient='records')
        context['ti'].xcom_push(key='transformed_data', value=df_json)
        
        return df_json
    except Exception as e:
        logging.error(f"Error transforming data: {str(e)}")
        raise


def load_data(**context):
    """
    Step 3: Load data to PostgreSQL and CSV file simultaneously
    """
    logging.info("Step 3: Loading data to PostgreSQL and CSV...")
    
    try:
        # Retrieve transformed data
        df_json = context['ti'].xcom_pull(key='transformed_data', task_ids='transform_data')
        df = pd.read_json(df_json, orient='records')
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(CSV_FILE_PATH), exist_ok=True)
        
        # Load to CSV (append mode if file exists)
        if os.path.exists(CSV_FILE_PATH):
            existing_df = pd.read_csv(CSV_FILE_PATH)
            combined_df = pd.concat([existing_df, df], ignore_index=True)
            # Remove duplicates based on date
            combined_df = combined_df.drop_duplicates(subset=['date'], keep='last')
            combined_df.to_csv(CSV_FILE_PATH, index=False)
            logging.info(f"Appended to existing CSV. Total rows: {len(combined_df)}")
        else:
            df.to_csv(CSV_FILE_PATH, index=False)
            logging.info(f"Created new CSV file with {len(df)} rows")
        
        # Load to PostgreSQL
        postgres_hook = PostgresHook(postgres_conn_id='postgres_default')
        
        # Create table if it doesn't exist
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS nasa_apod_data (
            id SERIAL PRIMARY KEY,
            date VARCHAR(50),
            title TEXT,
            url TEXT,
            explanation TEXT,
            media_type VARCHAR(50),
            copyright VARCHAR(255),
            ingestion_timestamp TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        postgres_hook.run(create_table_sql)
        
        # Insert data (avoid duplicates)
        for _, row in df.iterrows():
            check_sql = "SELECT COUNT(*) FROM nasa_apod_data WHERE date = %s"
            exists = postgres_hook.get_first(check_sql, parameters=(row['date'],))[0]
            
            if exists == 0:
                insert_sql = """
                INSERT INTO nasa_apod_data (date, title, url, explanation, media_type, copyright, ingestion_timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                postgres_hook.run(
                    insert_sql,
                    parameters=(
                        row['date'],
                        row['title'],
                        row['url'],
                        row['explanation'],
                        row.get('media_type', ''),
                        row.get('copyright', ''),
                        row['ingestion_timestamp']
                    )
                )
                logging.info(f"Inserted record for date: {row['date']}")
            else:
                logging.info(f"Record for date {row['date']} already exists, skipping")
        
        logging.info("Step 3 completed: Data loaded to both PostgreSQL and CSV")
        
    except Exception as e:
        logging.error(f"Error loading data: {str(e)}")
        raise


def version_data_with_dvc(**context):
    """
    Step 4: Version the CSV file using DVC
    """
    logging.info("Step 4: Versioning data with DVC...")
    
    try:
        # Ensure DVC repository is initialized
        if not os.path.exists(os.path.join(DVC_REPO_PATH, '.dvc')):
            logging.info("Initializing DVC repository...")
            subprocess.run(['dvc', 'init', '--no-scm'], cwd=DVC_REPO_PATH, check=True)
        
        # Add CSV file to DVC
        logging.info(f"Adding {CSV_FILE_PATH} to DVC...")
        
        # Copy CSV to DVC repo if needed (or use absolute path)
        dvc_csv_path = os.path.join(DVC_REPO_PATH, 'apod_data.csv')
        if CSV_FILE_PATH != dvc_csv_path:
            import shutil
            shutil.copy2(CSV_FILE_PATH, dvc_csv_path)
        
        # Add file to DVC tracking
        result = subprocess.run(
            ['dvc', 'add', 'apod_data.csv'],
            cwd=DVC_REPO_PATH,
            capture_output=True,
            text=True,
            check=True
        )
        
        logging.info(f"DVC add output: {result.stdout}")
        logging.info("Step 4 completed: Data versioned with DVC")
        
        # Store DVC metadata path in XCom
        dvc_metadata_path = os.path.join(DVC_REPO_PATH, 'apod_data.csv.dvc')
        context['ti'].xcom_push(key='dvc_metadata_path', value=dvc_metadata_path)
        
    except subprocess.CalledProcessError as e:
        logging.error(f"DVC command failed: {e.stderr}")
        raise
    except Exception as e:
        logging.error(f"Error versioning data with DVC: {str(e)}")
        raise


def commit_to_git(**context):
    """
    Step 5: Commit DVC metadata file to Git
    """
    logging.info("Step 5: Committing DVC metadata to Git...")
    
    try:
        # Check if Git repository is initialized
        if not os.path.exists(os.path.join(GIT_REPO_PATH, '.git')):
            logging.info("Initializing Git repository...")
            subprocess.run(['git', 'init'], cwd=GIT_REPO_PATH, check=True)
            # Configure git user (required for commits)
            subprocess.run(
                ['git', 'config', 'user.name', 'Airflow DAG'],
                cwd=GIT_REPO_PATH,
                check=True
            )
            subprocess.run(
                ['git', 'config', 'user.email', 'airflow@mlops.local'],
                cwd=GIT_REPO_PATH,
                check=True
            )
        
        # Add DVC metadata file
        dvc_metadata_path = context['ti'].xcom_pull(key='dvc_metadata_path', task_ids='version_data_with_dvc')
        
        if dvc_metadata_path and os.path.exists(dvc_metadata_path):
            # Add .dvc file and .gitignore
            subprocess.run(
                ['git', 'add', 'apod_data.csv.dvc', '.gitignore'],
                cwd=GIT_REPO_PATH,
                check=True
            )
            
            # Commit
            commit_message = f"Add DVC metadata for APOD data - {datetime.now().isoformat()}"
            result = subprocess.run(
                ['git', 'commit', '-m', commit_message],
                cwd=GIT_REPO_PATH,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logging.info(f"Git commit successful: {result.stdout}")
            else:
                # If nothing to commit, that's okay
                if "nothing to commit" in result.stdout or "nothing to commit" in result.stderr:
                    logging.info("No changes to commit (data already versioned)")
                else:
                    logging.warning(f"Git commit warning: {result.stderr}")
            
            logging.info("Step 5 completed: DVC metadata committed to Git")
        else:
            logging.warning("DVC metadata file not found, skipping Git commit")
        
    except subprocess.CalledProcessError as e:
        logging.error(f"Git command failed: {e.stderr}")
        # Don't fail the DAG if Git commit fails (might be expected in some environments)
        logging.warning("Continuing despite Git commit failure")
    except Exception as e:
        logging.error(f"Error committing to Git: {str(e)}")
        logging.warning("Continuing despite Git commit error")


# Define tasks
extract_task = PythonOperator(
    task_id='extract_nasa_data',
    python_callable=extract_nasa_data,
    dag=dag,
)

transform_task = PythonOperator(
    task_id='transform_data',
    python_callable=transform_data,
    dag=dag,
)

load_task = PythonOperator(
    task_id='load_data',
    python_callable=load_data,
    dag=dag,
)

dvc_task = PythonOperator(
    task_id='version_data_with_dvc',
    python_callable=version_data_with_dvc,
    dag=dag,
)

git_task = PythonOperator(
    task_id='commit_to_git',
    python_callable=commit_to_git,
    dag=dag,
)

# Define task dependencies
extract_task >> transform_task >> load_task >> dvc_task >> git_task

