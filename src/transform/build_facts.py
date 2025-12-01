"""Construcción de la tabla de hechos fact_precios.

Une los datos de precios con las dimensiones para crear el modelo estrella completo.
"""

import logging
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from src.utils.spark_session import get_spark_session, stop_spark_session
from src.utils.paths import DataLakePaths

logger = logging.getLogger(__name__)


class FactBuilder:
    """Constructor de la tabla de hechos de precios."""
    
    def __init__(self):
        self.spark = get_spark_session("BuildFacts")
        self.paths = DataLakePaths()
        self.paths.ensure_directories()
    
    def build_fact_precios(self) -> None:
        """Construye la tabla de hechos de precios con joins a dimensiones.
        
        Crea fact_precios con claves foráneas a todas las dimensiones.
        """
        logger.info("Construyendo fact_precios...")
        
        # Leer datos de raw zone
        precios_path = str(self.paths.get_raw_table("precios"))
        df_precios = self.spark.read.parquet(precios_path)
        
        # Leer dimensiones
        dim_tiempo_path = str(self.paths.get_refined_table("dim_tiempo"))
        dim_producto_path = str(self.paths.get_refined_table("dim_producto"))
        dim_establecimiento_path = str(self.paths.get_refined_table("dim_establecimiento"))
        dim_ubicacion_path = str(self.paths.get_refined_table("dim_ubicacion"))
        
        dim_tiempo = self.spark.read.parquet(dim_tiempo_path)
        dim_producto = self.spark.read.parquet(dim_producto_path)
        dim_establecimiento = self.spark.read.parquet(dim_establecimiento_path)
        dim_ubicacion = self.spark.read.parquet(dim_ubicacion_path)
        
        # Preparar precios con claves convertidas
        df_precios_prep = (
            df_precios
            .withColumn("producto_id", F.col("producto_id").cast("int"))
            .withColumn("establecimiento_id", F.col("establecimiento_id").cast("int"))
        )
        
        # Join con dim_tiempo para obtener fecha_id
        fact = (
            df_precios_prep
            .join(
                dim_tiempo.select("fecha", "fecha_id"),
                on="fecha",
                how="inner"
            )
        )
        
        # Join con dim_producto
        fact = (
            fact
            .join(
                dim_producto.select("producto_id"),
                on="producto_id",
                how="inner"
            )
        )
        
        # Join con dim_establecimiento
        fact = (
            fact
            .join(
                dim_establecimiento.select("establecimiento_id"),
                on="establecimiento_id",
                how="inner"
            )
        )
        
        # Join con dim_ubicacion para obtener ubicacion_id
        # Nota: ubicacion_id es igual a establecimiento_id en nuestra implementación
        fact = (
            fact
            .join(
                dim_ubicacion.select("establecimiento_id", "ubicacion_id"),
                on="establecimiento_id",
                how="inner"
            )
        )
        
        # Seleccionar columnas finales de la tabla de hechos
        fact_precios = (
            fact
            .select(
                "fecha_id",
                "producto_id",
                "establecimiento_id",
                "ubicacion_id",
                "precio",
                "fecha"  # Mantener fecha para facilitar consultas
            )
        )
        
        # Guardar tabla de hechos particionada por fecha
        output_path = str(self.paths.get_refined_table("fact_precios"))
        (
            fact_precios
            .write
            .mode("overwrite")
            .partitionBy("fecha")
            .parquet(output_path)
        )
        
        logger.info(f"✅ fact_precios creada: {fact_precios.count()} registros -> {output_path}")
    
    def build_all(self) -> None:
        """Construye todas las tablas de hechos."""
        try:
            self.build_fact_precios()
            logger.info("✅ Tabla de hechos construida exitosamente")
        finally:
            stop_spark_session(self.spark)


def build_facts() -> None:
    """Función principal para ser llamada desde Airflow DAG."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    builder = FactBuilder()
    builder.build_all()
