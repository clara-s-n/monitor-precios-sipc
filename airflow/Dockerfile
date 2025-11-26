FROM apache/airflow:2.9.2

# Cambiar a usuario root para configurar el entrypoint
USER root

# Copiar el script de inicio personalizado
COPY entrypoint.sh /opt/airflow/entrypoint.sh
RUN chmod +x /opt/airflow/entrypoint.sh

# Cambiar a usuario airflow para instalar dependencias de Python
USER airflow

# Instalar dependencias de Python
RUN pip install --no-cache-dir \
  pyspark \
  pandas

# Volver a root para ejecutar el entrypoint
USER root

# Configurar el entrypoint
ENTRYPOINT ["/opt/airflow/entrypoint.sh"]
