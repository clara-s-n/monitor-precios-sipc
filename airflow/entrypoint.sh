#!/bin/bash
set -e

# Asegurar que las carpetas necesarias existen con permisos correctos
mkdir -p /opt/airflow/logs /opt/airflow/dags /opt/airflow/plugins /opt/airflow/data
chown -R airflow:root /opt/airflow/logs /opt/airflow/dags /opt/airflow/plugins /opt/airflow/data
chmod -R 775 /opt/airflow/logs /opt/airflow/data

# Asegurar permisos completos en data_sipc para evitar errores de Spark con directorios temporales
if [ -d "/opt/airflow/data_sipc" ]; then
  chmod -R 777 /opt/airflow/data_sipc
  echo "Permisos configurados en /opt/airflow/data_sipc"
fi

# Ejecutar como usuario airflow usando runuser
cd /opt/airflow
runuser -u airflow -- bash -c "
  export AIRFLOW_HOME=/opt/airflow
  export PYTHONPATH=/opt/airflow/src
  airflow db init
  airflow users create --username admin --firstname Airflow --lastname Admin --email airflowadmin@example.com --role Admin --password admin || true
  airflow webserver &
  exec airflow scheduler
"
