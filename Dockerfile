# Custom Airflow image with DVC and required dependencies
FROM apache/airflow:2.8.0

USER root

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Switch to airflow user
USER airflow

# Install Python dependencies using system pip
# This ensures packages are installed in the same environment as Airflow
RUN /usr/local/bin/pip install --no-cache-dir --user \
    apache-airflow-providers-postgres==5.10.0 \
    pandas==2.0.3 \
    requests==2.31.0 \
    psycopg2-binary==2.9.9 \
    dvc==3.41.0 \
    python-dotenv==1.0.0

# Create necessary directories
RUN mkdir -p /opt/airflow/data /opt/airflow/dvc_repo

# Set working directory
WORKDIR /opt/airflow

