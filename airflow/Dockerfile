FROM apache/airflow:2.9.2

# Pasar a root para instalar paquetes
USER root

# Instalar dependencias de Python que necesitan los DAGs
RUN pip install --no-cache-dir \
  pyspark \
  pandas

# Volver al usuario por defecto de Airflow
USER airflow
