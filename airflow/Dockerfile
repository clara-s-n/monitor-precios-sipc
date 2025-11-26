FROM apache/airflow:2.9.2

# Install Java as root user (required for PySpark)
USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends openjdk-17-jre-headless && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

# Switch back to airflow user
USER airflow

# Install Python dependencies
RUN pip install --no-cache-dir \
  pandas==2.1.4 \
  pyarrow==14.0.1 \
  pyspark==3.4.1
