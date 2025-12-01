FROM apache/airflow:2.9.2

# Usamos root para instalar paquetes del sistema
USER root

# Instalar Java (17 en este ejemplo)
RUN apt-get update && \
  apt-get install -y --no-install-recommends openjdk-17-jre-headless && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*

# Configurar JAVA_HOME y PATH
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:${PATH}"

# Tu código Python
ENV PYTHONPATH=/opt/airflow/src

# Copiar el script de entrada personalizado
COPY entrypoint.sh /opt/airflow/entrypoint.sh
RUN chmod +x /opt/airflow/entrypoint.sh

# Cambiar a usuario airflow para instalar dependencias de Python
USER airflow

# Dependencias Python
RUN pip install --no-cache-dir \
  pandas==2.1.4 \
  pyarrow==14.0.1 \
  pyspark==3.4.1 \
  psycopg2-binary==2.9.9

# Volver a root para ejecutar el entrypoint
USER root

# Configurar el entrypoint
ENTRYPOINT ["/opt/airflow/entrypoint.sh"]