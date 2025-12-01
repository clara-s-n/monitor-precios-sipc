"""Transformación de landing a raw zone con PySpark.

Procesa CSVs y los convierte a Parquet con tipos correctos.
"""

import logging
import shutil
from pathlib import Path
from pyspark.sql import DataFrame
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, 
    IntegerType, DateType, TimestampType
)
from pyspark.sql import functions as F

from src.utils.spark_session import get_spark_session, stop_spark_session
from src.utils.paths import DataLakePaths

logger = logging.getLogger(__name__)


# Schemas esperados para cada archivo SIPC
SCHEMA_PRECIOS = StructType([
    StructField("fecha", DateType(), True),
    StructField("producto_id", StringType(), True),
    StructField("establecimiento_id", StringType(), True),
    StructField("precio", DoubleType(), True),
    StructField("unidad", StringType(), True),
])

SCHEMA_PRODUCTOS = StructType([
    StructField("producto_id", StringType(), False),
    StructField("nombre", StringType(), True),
    StructField("categoria", StringType(), True),
    StructField("subcategoria", StringType(), True),
    StructField("marca", StringType(), True),
])

SCHEMA_ESTABLECIMIENTOS = StructType([
    StructField("establecimiento_id", StringType(), False),
    StructField("nombre", StringType(), True),
    StructField("cadena", StringType(), True),
    StructField("departamento", StringType(), True),
    StructField("ciudad", StringType(), True),
    StructField("direccion", StringType(), True),
])


class RawZoneBuilder:
    """Constructor de la zona raw a partir de datos en landing."""
    
    def __init__(self):
        self.spark = get_spark_session("BuildRawZone")
        self.paths = DataLakePaths()
        self.paths.ensure_directories()
    
    def _clean_output_dir(self, output_path: str) -> None:
        """Limpia directorio de salida si existe para evitar conflictos de permisos."""
        path = Path(output_path)
        if path.exists():
            logger.info(f"Limpiando directorio existente: {output_path}")
            try:
                # Intentar con shutil primero
                shutil.rmtree(output_path, ignore_errors=True)
            except Exception as e:
                logger.warning(f"No se pudo limpiar con shutil: {e}")
            
            # También intentar con Hadoop FileSystem de Spark
            try:
                hadoop_conf = self.spark._jsc.hadoopConfiguration()
                fs = self.spark._jvm.org.apache.hadoop.fs.FileSystem.get(hadoop_conf)
                fs.delete(self.spark._jvm.org.apache.hadoop.fs.Path(output_path), True)
                logger.info(f"Directorio limpiado exitosamente: {output_path}")
            except Exception as e:
                logger.warning(f"No se pudo limpiar con Hadoop FS: {e}")
    
    def process_precios(self) -> None:
        """Procesa archivo de precios a formato Parquet."""
        logger.info("Procesando precios...")
        
        landing_file = str(self.paths.get_landing_file("precios.csv"))
        raw_table = str(self.paths.get_raw_table("precios"))
        
        df = (
            self.spark.read
            .option("header", "true")
            .option("inferSchema", "false")
            .option("delimiter", ",")
            .option("quote", '"')
            .option("escape", '"')
            .option("encoding", "UTF-8")
            .csv(landing_file)
        )
        
        # Limpiar y tipear datos
        df_clean = (
            df
            # Fecha del CSV -> columna fecha (DATE)
            .withColumn("fecha", F.to_date(F.col("Fecha"), "yyyy-MM-dd"))
            # Precio numérico
            .withColumn("precio", F.col("Precio").cast(DoubleType()))
            # IDs lógicos
            .withColumn("producto_id", F.col("Presentacion_Producto").cast(StringType()))
            .withColumn("establecimiento_id", F.col("Establecimiento").cast(StringType()))
            # Columnas adicionales útiles
            .withColumn("oferta", F.col("Oferta").cast(IntegerType()))
            # Seleccionar solo las columnas necesarias
            .select("fecha", "producto_id", "establecimiento_id", "precio", "oferta")
            # Filtros básicos
            .filter(F.col("precio").isNotNull())
            .filter(F.col("precio") > 0)
            .filter(F.col("producto_id").isNotNull())
            .filter(F.col("establecimiento_id").isNotNull())
        )
        
        # Contar registros antes de escribir
        count = df_clean.count()
        logger.info(f"Escribiendo {count} registros de precios...")
        
        # Limpiar directorio de salida antes de escribir
        self._clean_output_dir(raw_table)
        
        # Guardar como Parquet (ya limpiamos manualmente, no usar overwrite)
        (
            df_clean
            .write
            .parquet(raw_table)
        )
        
        logger.info(f"✅ Precios procesados: {count} registros -> {raw_table}")
    
    def process_productos(self) -> None:
        """Procesa archivo de productos a formato Parquet."""
        logger.info("Procesando productos...")
        
        landing_file = str(self.paths.get_landing_file("productos.csv"))
        raw_table = str(self.paths.get_raw_table("productos"))
        
        df = (
            self.spark.read
            .option("header", "true")
            .option("delimiter", ";")
            .option("encoding", "ISO-8859-1")
            .csv(landing_file)
        )
        
        # Normalizar nombres de columnas
        df_normalized = (
            df
            .withColumnRenamed("id.producto", "producto_id")
            .withColumn("categoria", F.col("producto"))  # Usar producto como categoría base
            .withColumn("subcategoria", F.col("especificacion"))
        )
        
        # Deduplicar por producto_id
        df_clean = df_normalized.dropDuplicates(["producto_id"])
        
        # Limpiar directorio de salida antes de escribir
        self._clean_output_dir(raw_table)
        
        (
            df_clean
            .write
            .mode("overwrite")
            .parquet(raw_table)
        )
        
        logger.info(f"✅ Productos procesados: {df_clean.count()} registros -> {raw_table}")
    
    def process_establecimientos(self) -> None:
        """Procesa archivo de establecimientos a formato Parquet."""
        logger.info("Procesando establecimientos...")
        
        landing_file = str(self.paths.get_landing_file("establecimientos.csv"))
        raw_table = str(self.paths.get_raw_table("establecimientos"))
        
        df = (
            self.spark.read
            .option("header", "true")
            .option("delimiter", ";")
            .option("encoding", "ISO-8859-1")
            .csv(landing_file)
        )
        
        # Normalizar nombres de columnas
        df_normalized = (
            df
            .withColumnRenamed("id.establecimientos", "establecimiento_id")
            .withColumnRenamed("razon.social", "razon_social")
            .withColumnRenamed("nombre.sucursal", "nombre")
        )
        
        # Deduplicar por establecimiento_id
        df_clean = df_normalized.dropDuplicates(["establecimiento_id"])
        
        # Limpiar directorio de salida antes de escribir
        self._clean_output_dir(raw_table)
        
        (
            df_clean
            .write
            .mode("overwrite")
            .parquet(raw_table)
        )
        
        logger.info(f"✅ Establecimientos procesados: {df_clean.count()} registros -> {raw_table}")
    
    def build_all(self) -> None:
        """Procesa todos los archivos de landing a raw."""
        try:
            self.process_precios()
            self.process_productos()
            self.process_establecimientos()
            logger.info("✅ Raw zone construida exitosamente")
        finally:
            stop_spark_session(self.spark)


def transform_to_raw() -> None:
    """Función principal para ser llamada desde Airflow DAG."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    builder = RawZoneBuilder()
    builder.build_all()
