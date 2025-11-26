#!/bin/bash
set -e

# Asegurar que las carpetas necesarias existen con permisos correctos
mkdir -p /opt/airflow/logs /opt/airflow/dags /opt/airflow/plugins
chown -R airflow:root /opt/airflow/logs /opt/airflow/dags /opt/airflow/plugins
chmod -R 775 /opt/airflow/logs

# Ejecutar como usuario airflow usando runuser
cd /opt/airflow
runuser -u airflow -- bash -c "
  export AIRFLOW_HOME=/opt/airflow
  airflow db init
  airflow webserver &
  exec airflow scheduler
"
