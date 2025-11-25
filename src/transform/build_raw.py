"""Transformación de landing a raw zone con PySpark.

Procesa CSVs y los convierte a Parquet con tipos correctos.
"""

import logging
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
    
    def process_precios(self) -> None:
        """Procesa archivos de precios de todos los años a formato Parquet."""
        logger.info("Procesando precios de todos los años...")
        
        raw_table = str(self.paths.get_raw_table("precios"))
        
        # Obtener todos los archivos de precios por año
        precio_files = self.paths.get_landing_files_by_type("precios.csv")
        
        if not precio_files:
            logger.warning("No se encontraron archivos de precios")
            return
        
        logger.info(f"Años encontrados: {[year for year, _ in precio_files]}")
        
        # Leer todos los archivos y combinarlos
        dfs = []
        for year, file_path in precio_files:
            logger.info(f"Leyendo precios_{year}.csv...")
            df_year = (
                self.spark.read
                .option("header", "true")
                .option("inferSchema", "false")
                .option("delimiter", ";")
                .option("encoding", "ISO-8859-1")
                .csv(str(file_path))
            )
            dfs.append(df_year)
        
        # Unir todos los DataFrames
        df = dfs[0]
        for df_next in dfs[1:]:
            df = df.unionByName(df_next, allowMissingColumns=True)
        
        # Limpiar y tipear datos
        df_clean = (
            df
            .withColumn("fecha", F.to_date(F.col("fecha"), "yyyy-MM-dd"))
            .withColumn("precio", F.col("precio").cast(DoubleType()))
            .filter(F.col("precio").isNotNull())
            .filter(F.col("precio") > 0)
            .filter(F.col("producto_id").isNotNull())
            .filter(F.col("establecimiento_id").isNotNull())
        )
        
        # Guardar como Parquet particionado por fecha
        (
            df_clean
            .write
            .mode("overwrite")
            .partitionBy("fecha")
            .parquet(raw_table)
        )
        
        logger.info(f"✅ Precios procesados: {df_clean.count()} registros -> {raw_table}")
    
    def process_productos(self) -> None:
        """Procesa archivos de productos de todos los años a formato Parquet."""
        logger.info("Procesando productos de todos los años...")
        
        raw_table = str(self.paths.get_raw_table("productos"))
        
        # Obtener todos los archivos de productos por año
        producto_files = self.paths.get_landing_files_by_type("productos.csv")
        
        if not producto_files:
            logger.warning("No se encontraron archivos de productos")
            return
        
        logger.info(f"Años encontrados: {[year for year, _ in producto_files]}")
        
        # Leer todos los archivos y combinarlos
        dfs = []
        for year, file_path in producto_files:
            logger.info(f"Leyendo productos_{year}.csv...")
            df_year = (
                self.spark.read
                .option("header", "true")
                .option("delimiter", ";")
                .option("encoding", "ISO-8859-1")
                .csv(str(file_path))
            )
            dfs.append(df_year)
        
        # Unir todos los DataFrames
        df = dfs[0]
        for df_next in dfs[1:]:
            df = df.unionByName(df_next, allowMissingColumns=True)
        
        # Normalizar nombres de columnas
        df_normalized = (
            df
            .withColumnRenamed("id.producto", "producto_id")
            .withColumn("categoria", F.col("producto"))  # Usar producto como categoría base
            .withColumn("subcategoria", F.col("especificacion"))
        )
        
        # Deduplicar por producto_id (puede haber duplicados entre años)
        df_clean = df_normalized.dropDuplicates(["producto_id"])
        
        (
            df_clean
            .write
            .mode("overwrite")
            .parquet(raw_table)
        )
        
        logger.info(f"✅ Productos procesados: {df_clean.count()} registros -> {raw_table}")
    
    def process_establecimientos(self) -> None:
        """Procesa archivos de establecimientos de todos los años a formato Parquet."""
        logger.info("Procesando establecimientos de todos los años...")
        
        raw_table = str(self.paths.get_raw_table("establecimientos"))
        
        # Obtener todos los archivos de establecimientos por año
        establecimiento_files = self.paths.get_landing_files_by_type("establecimientos.csv")
        
        if not establecimiento_files:
            logger.warning("No se encontraron archivos de establecimientos")
            return
        
        logger.info(f"Años encontrados: {[year for year, _ in establecimiento_files]}")
        
        # Leer todos los archivos y combinarlos
        dfs = []
        for year, file_path in establecimiento_files:
            logger.info(f"Leyendo establecimientos_{year}.csv...")
            df_year = (
                self.spark.read
                .option("header", "true")
                .option("delimiter", ";")
                .option("encoding", "ISO-8859-1")
                .csv(str(file_path))
            )
            dfs.append(df_year)
        
        # Unir todos los DataFrames
        df = dfs[0]
        for df_next in dfs[1:]:
            df = df.unionByName(df_next, allowMissingColumns=True)
        
        # Normalizar nombres de columnas
        df_normalized = (
            df
            .withColumnRenamed("id.establecimientos", "establecimiento_id")
            .withColumnRenamed("razon.social", "razon_social")
            .withColumnRenamed("nombre.sucursal", "nombre")
        )
        
        # Deduplicar por establecimiento_id (puede haber duplicados entre años)
        df_clean = df_normalized.dropDuplicates(["establecimiento_id"])
        
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
