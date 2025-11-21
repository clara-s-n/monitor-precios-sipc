"""DAG principal para el pipeline ETL de Monitor de Precios SIPC.

Orquesta la ingesta, transformación y cálculo de métricas.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

# Las funciones de procesamiento se importarán desde src/
# from src.ingestion.ingest_landing import ingest_landing_data
# from src.transform.build_raw import transform_to_raw
# from src.transform.build_dimensions import build_dimensions
# from src.transform.build_facts import build_facts


# Configuración por defecto del DAG
default_args = {
    'owner': 'monitor-precios-team',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}


with DAG(
    dag_id='monitor_precios_sipc_etl',
    default_args=default_args,
    description='Pipeline ETL completo para análisis de precios SIPC',
    schedule_interval='@daily',  # Ejecutar diariamente
    start_date=datetime(2024, 1, 1),
    catchup=False,  # No ejecutar fechas pasadas
    tags=['sipc', 'etl', 'precios'],
) as dag:
    
    # TODO: Descomentar cuando se implementen las funciones
    
    # Tarea 1: Ingestar datos a landing zone
    # ingest_task = PythonOperator(
    #     task_id='ingest_landing_data',
    #     python_callable=ingest_landing_data,
    # )
    
    # Tarea 2: Limpiar y transformar a raw zone
    # build_raw_task = PythonOperator(
    #     task_id='build_raw_zone',
    #     python_callable=transform_to_raw,
    # )
    
    # Tarea 3: Construir dimensiones
    # build_dims_task = PythonOperator(
    #     task_id='build_dimensions',
    #     python_callable=build_dimensions,
    # )
    
    # Tarea 4: Construir tabla de hechos
    # build_facts_task = PythonOperator(
    #     task_id='build_facts',
    #     python_callable=build_facts,
    # )
    
    # Definir dependencias
    # ingest_task >> build_raw_task >> build_dims_task >> build_facts_task
    
    pass  # Placeholder hasta implementar tareas
