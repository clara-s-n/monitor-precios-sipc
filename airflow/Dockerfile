FROM apache/airflow:2.9.2

# Instalar dependencias de Python como usuario airflow
USER airflow

RUN pip install --no-cache-dir \
  pyspark \
  pandas
