"""Factory para crear sesiones de Spark configuradas para el proyecto SIPC.

Siempre usa modo local (no cluster) según requisitos del obligatorio.
"""

from pyspark.sql import SparkSession


def get_spark_session(app_name: str = "MonitorPreciosSIPC") -> SparkSession:
    """Crea o retorna sesión Spark existente en modo local.
    
    Args:
        app_name: Nombre de la aplicación Spark
        
    Returns:
        SparkSession configurada para procesamiento local
    """
    spark = (
        SparkSession.builder
        .appName(app_name)
        .master("local[*]")  # Usa todos los cores disponibles
        .config("spark.sql.warehouse.dir", "/tmp/spark-warehouse")
        .config("spark.sql.parquet.compression.codec", "snappy")
        .config("spark.driver.memory", "2g")
        .config("spark.executor.memory", "2g")
        .getOrCreate()
    )
    
    # Configurar nivel de log para reducir verbosidad
    spark.sparkContext.setLogLevel("WARN")
    
    return spark


def stop_spark_session(spark: SparkSession) -> None:
    """Detiene la sesión Spark y libera recursos.
    
    Args:
        spark: Sesión Spark a detener
    """
    if spark:
        spark.stop()
