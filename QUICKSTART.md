# Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Setup Environment

```bash
# Run the setup script
./setup.sh

# Or manually create .env file
echo -e "AIRFLOW_UID=$(id -u)\nAIRFLOW_PROJ_DIR=.\n_AIRFLOW_WWW_USER_USERNAME=airflow\n_AIRFLOW_WWW_USER_PASSWORD=airflow" > .env
```

### Step 2: Start Services

```bash
# Build and start all services
docker-compose up -d

# Check status
docker-compose ps
```

### Step 3: Access and Run

1. **Open Airflow UI**: http://localhost:8080
   - Username: `airflow`
   - Password: `airflow`

2. **Enable the DAG**: Toggle `nasa_apod_etl_pipeline` to ON

3. **Trigger a run**: Click the play button ▶️

## 📋 Pipeline Steps Overview

Once triggered, the `nasa_apod_etl_pipeline` DAG executes 5 sequential steps:

### Step 1: Extract (E)
- Retrieves daily data from NASA APOD API
- Stores raw JSON data in XCom for next task

### Step 2: Transform (T)
- Processes JSON data into structured format using Pandas
- Extracts fields: date, title, url, explanation, media_type, copyright
- Adds ingestion timestamp
- Stores transformed DataFrame in XCom

### Step 3: Data Loading (L)
**Simultaneously persists the cleaned data to two distinct storage locations:**

1. **PostgreSQL Database**: 
   - Inserts data into `nasa_apod_data` table
   - Automatically creates table if it doesn't exist
   - Skips duplicate entries based on date

2. **Local CSV File**: 
   - Saves to `/opt/airflow/data/apod_data.csv`
   - Appends new data to existing file
   - Removes duplicates based on date

### Step 4: Data Versioning (DVC)
- Executes DVC commands within the pipeline
- Adds the CSV file (`apod_data.csv`) to DVC tracking
- Creates corresponding metadata file (`apod_data.csv.dvc`)
- Initializes DVC repository if needed

### Step 5: Code Versioning (Git/GitHub)
- Performs Git operation to commit the updated DVC metadata file (`.dvc`)
- Links the pipeline code to the exact version of the data it produced
- Initializes Git repository if needed
- Commits `.dvc` file and `.gitignore` to track data versions

## ✅ Verify Pipeline Execution

### Check Logs
```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f airflow-scheduler
docker-compose logs -f airflow-webserver
```

### Verify Data in PostgreSQL
```bash
docker-compose exec postgres psql -U airflow -d airflow -c "SELECT * FROM nasa_apod_data ORDER BY created_at DESC LIMIT 5;"
```

### Verify CSV File
```bash
docker-compose exec airflow-webserver cat /opt/airflow/data/apod_data.csv
```

### Verify DVC Status
```bash
docker-compose exec airflow-webserver bash -c "cd /opt/airflow/dvc_repo && dvc status"
```

### Verify Git Commit
```bash
docker-compose exec airflow-webserver bash -c "cd /opt/airflow/dvc_repo && git log --oneline"
```

## 🛑 Stop Services

```bash
docker-compose down

# Remove volumes (clean slate)
docker-compose down -v
```

## 🔧 Troubleshooting

### DAG not appearing?
- Check scheduler logs: `docker-compose logs airflow-scheduler`
- Verify DAG file syntax: `python -m py_compile dags/nasa_apod_etl_dag.py`

### Connection issues?
- Ensure all services are running: `docker-compose ps`
- Check network: `docker network ls`

### Permission issues?
- Verify AIRFLOW_UID in .env matches your user ID
- Check volume permissions

