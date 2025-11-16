#!/bin/bash

# Setup script for MLOps A3 NASA APOD ETL Pipeline

echo "🚀 Setting up MLOps A3 Project..."

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p dags logs plugins data dvc_repo

# Set Airflow UID
echo "🔧 Setting Airflow UID..."
echo -e "AIRFLOW_UID=$(id -u)\nAIRFLOW_PROJ_DIR=.\n_AIRFLOW_WWW_USER_USERNAME=airflow\n_AIRFLOW_WWW_USER_PASSWORD=airflow" > .env

# Make script executable
chmod +x setup.sh

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Review the configuration in docker-compose.yml"
echo "2. Run: docker-compose up -d"
echo "3. Access Airflow UI at http://localhost:8080 (airflow/airflow)"
echo "4. Trigger the 'nasa_apod_etl_pipeline' DAG"

