# MLOps A3: NASA APOD ETL Pipeline with Airflow, DVC, and Postgres

This project implements a comprehensive ETL pipeline that extracts data from NASA's Astronomy Picture of the Day (APOD) API, transforms it, loads it into PostgreSQL and CSV files, and versions it using DVC and Git.

## 🎯 Project Overview

The pipeline consists of 5 sequential steps:

1. **Extract (E)**: Retrieves daily data from NASA APOD API
2. **Transform (T)**: Processes JSON data into structured format using Pandas
3. **Load (L)**: Persists data to both PostgreSQL database and CSV file
4. **Data Versioning (DVC)**: Versions the CSV file using DVC
5. **Code Versioning (Git)**: Commits DVC metadata to Git repository

## 📋 Prerequisites

- Docker and Docker Compose installed
- Git installed
- At least 4GB RAM and 2 CPUs available for Docker
- 10GB free disk space

## 🚀 Quick Start

### 1. Clone and Setup

```bash
cd "MLOps A3"
```

### 2. Initialize Airflow

Set the Airflow user ID (Linux/Mac):

```bash
echo -e "AIRFLOW_UID=$(id -u)" > .env
```

### 3. Start the Services

```bash
docker-compose up -d
```

This will:
- Build the custom Airflow image with DVC and dependencies
- Start PostgreSQL database
- Start Airflow webserver (port 8080)
- Start Airflow scheduler

### 4. Access Airflow UI

Open your browser and navigate to:
- **URL**: http://localhost:8080
- **Username**: `airflow`
- **Password**: `airflow`

### 5. Trigger the DAG

1. In the Airflow UI, find the `nasa_apod_etl_pipeline` DAG
2. Toggle it ON (if paused)
3. Click the play button to trigger a manual run

## 📁 Project Structure

```
MLOps A3/
├── dags/
│   └── nasa_apod_etl_dag.py    # Main Airflow DAG
├── data/                        # CSV files (created by pipeline)
├── dvc_repo/                    # DVC repository (created by pipeline)
├── logs/                        # Airflow logs
├── plugins/                     # Airflow plugins (optional)
├── Dockerfile                   # Custom Airflow image
├── docker-compose.yml           # Docker Compose configuration
├── requirements.txt             # Python dependencies
├── .env                         # Environment variables
├── .gitignore                   # Git ignore rules
└── README.md                    # This file
```

## 🔧 Configuration

### PostgreSQL Connection

The pipeline uses the default PostgreSQL connection (`postgres_default`) configured in docker-compose.yml:
- **Host**: postgres
- **Database**: airflow
- **User**: airflow
- **Password**: airflow

### NASA API

The pipeline uses the NASA APOD API with the DEMO_KEY:
- **URL**: https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY
- **Rate Limit**: 50 requests per hour (DEMO_KEY)

### File Paths

- **CSV File**: `/opt/airflow/data/apod_data.csv`
- **DVC Repo**: `/opt/airflow/dvc_repo/`
- **DVC Metadata**: `/opt/airflow/dvc_repo/apod_data.csv.dvc`

## 📊 Database Schema

The pipeline creates the following table in PostgreSQL:

```sql
CREATE TABLE nasa_apod_data (
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
```

## 🔄 Pipeline Workflow

### Step 1: Extract
- Connects to NASA APOD API
- Retrieves JSON response
- Stores raw data in XCom

### Step 2: Transform
- Extracts fields: date, title, url, explanation, media_type, copyright
- Creates Pandas DataFrame
- Adds ingestion timestamp
- Stores transformed data in XCom

### Step 3: Load
- **PostgreSQL**: Inserts data into `nasa_apod_data` table (skips duplicates)
- **CSV**: Appends to `apod_data.csv` (removes duplicates by date)

### Step 4: DVC Versioning
- Initializes DVC repository if needed
- Adds CSV file to DVC tracking
- Creates `.dvc` metadata file

### Step 5: Git Commit
- Initializes Git repository if needed
- Commits DVC metadata file (`.dvc`) and `.gitignore`
- Links pipeline code to data version

## 🐳 Docker Image Details

The custom Docker image extends `apache/airflow:2.8.0` and includes:
- Git (for version control)
- DVC (for data versioning)
- All Python dependencies from `requirements.txt`
- Required directories for data and DVC repo

## 🚢 Deployment to Astronomer

### Option 1: Using Astronomer CLI

1. Install Astronomer CLI:
```bash
curl -sSL install.astronomer.io | sudo bash
```

2. Initialize Astronomer project:
```bash
astro dev init
```

3. Build and push to Astronomer:
```bash
astro deploy
```

### Option 2: Using Docker Image

1. Build the image:
```bash
docker build -t your-registry/nasa-apod-etl:latest .
```

2. Push to your container registry:
```bash
docker push your-registry/nasa-apod-etl:latest
```

3. Deploy to Astronomer using the image in your `Dockerfile`

## 🧪 Testing

### Manual Testing

1. Check Airflow logs for each task
2. Verify PostgreSQL data:
```bash
docker-compose exec postgres psql -U airflow -d airflow -c "SELECT * FROM nasa_apod_data LIMIT 5;"
```

3. Check CSV file:
```bash
docker-compose exec airflow-webserver cat /opt/airflow/data/apod_data.csv
```

4. Check DVC status:
```bash
docker-compose exec airflow-webserver dvc status -R /opt/airflow/dvc_repo
```

## 📝 Key Learnings

### Orchestration Mastery
- Complex workflow dependencies using Airflow DAGs
- Task sequencing and data passing via XCom
- Error handling and retries

### Data Integrity
- Concurrent loading to multiple storage systems
- Duplicate detection and prevention
- Transaction management

### Data Lineage
- DVC for data versioning
- Git integration for metadata tracking
- Reproducible data pipelines

### Containerized Deployment
- Custom Docker images with dependencies
- Docker Compose for local development
- Astronomer deployment compatibility

## 🐛 Troubleshooting

### Issue: DAG not appearing
- Check logs: `docker-compose logs airflow-scheduler`
- Verify DAG file is in `dags/` directory
- Check for syntax errors in DAG file

### Issue: PostgreSQL connection failed
- Verify PostgreSQL is running: `docker-compose ps`
- Check connection string in docker-compose.yml
- Verify network connectivity between services

### Issue: DVC/Git commands failing
- Check file permissions in mounted volumes
- Verify Git is installed in container
- Check DVC repository initialization

### Issue: API rate limiting
- NASA DEMO_KEY has 50 requests/hour limit
- Wait before retrying
- Consider using a registered API key for production

## 📚 Additional Resources

- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [DVC Documentation](https://dvc.org/doc)
- [NASA APOD API](https://api.nasa.gov/)
- [Astronomer Documentation](https://docs.astronomer.io/)

## 📄 License

This project is for educational purposes as part of the MLOps A3 assignment.

## 👤 Author

MLOps A3 Assignment - Capstone Project

---

**Note**: This pipeline is designed for educational purposes. For production use, consider:
- Using registered NASA API keys
- Implementing proper secret management
- Adding comprehensive error handling
- Setting up monitoring and alerting
- Configuring proper backup strategies

