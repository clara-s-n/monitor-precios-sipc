FROM apache/airflow:2.9.2

# Usamos root para instalar paquetes del sistema
USER root

# Instalar Java (17 en este ejemplo)
RUN apt-get update && \
    apt-get install -y openjdk-17-jre-headless && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Configurar JAVA_HOME y PATH
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:${PATH}"

# Tu código Python
ENV PYTHONPATH=/opt/airflow/src

# Volver al usuario airflow (recomendado por la imagen oficial)
USER airflow

# Dependencias Python
RUN pip install --no-cache-dir \
    pyspark \
    pandas
