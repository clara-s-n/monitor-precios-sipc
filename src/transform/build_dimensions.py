"""Construcción de dimensiones para el modelo estrella.

Crea las 4 dimensiones del modelo:
- dim_tiempo: Basada en las fechas de los precios
- dim_producto: Catálogo de productos con sus atributos
- dim_establecimiento: Catálogo de establecimientos/comercios
- dim_ubicacion: Información geográfica de los establecimientos
"""

import logging
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window

from src.utils.spark_session import get_spark_session, stop_spark_session
from src.utils.paths import DataLakePaths

logger = logging.getLogger(__name__)


class DimensionBuilder:
    """Constructor de dimensiones del modelo estrella."""
    
    def __init__(self):
        self.spark = get_spark_session("BuildDimensions")
        self.paths = DataLakePaths()
        self.paths.ensure_directories()
    
    def build_dim_tiempo(self) -> None:
        """Construye dimensión tiempo a partir de fechas en precios.
        
        Genera una dimensión con atributos temporales útiles para análisis.
        """
        logger.info("Construyendo dim_tiempo...")
        
        # Leer fechas únicas de precios
        precios_path = str(self.paths.get_raw_table("precios"))
        df_precios = self.spark.read.parquet(precios_path)
        
        # Extraer fechas únicas y calcular atributos temporales
        dim_tiempo = (
            df_precios
            .select("fecha")
            .distinct()
            .withColumn("fecha_id", F.date_format("fecha", "yyyyMMdd").cast("int"))
            .withColumn("anio", F.year("fecha"))
            .withColumn("mes", F.month("fecha"))
            .withColumn("dia", F.dayofmonth("fecha"))
            .withColumn("trimestre", F.quarter("fecha"))
            .withColumn("dia_semana", F.dayofweek("fecha"))
            .withColumn("semana_anio", F.weekofyear("fecha"))
            .withColumn("nombre_mes", F.date_format("fecha", "MMMM"))
            .withColumn("nombre_dia", F.date_format("fecha", "EEEE"))
        )
        
        # Ordenar por fecha
        dim_tiempo = dim_tiempo.orderBy("fecha")
        
        # Guardar dimensión
        output_path = str(self.paths.get_refined_table("dim_tiempo"))
        (
            dim_tiempo
            .write
            .mode("overwrite")
            .parquet(output_path)
        )
        
        logger.info(f"✅ dim_tiempo creada: {dim_tiempo.count()} registros -> {output_path}")
    
    def build_dim_producto(self) -> None:
        """Construye dimensión producto con catálogo completo.
        
        Incluye categorización y atributos del producto.
        """
        logger.info("Construyendo dim_producto...")
        
        # Leer productos de raw
        productos_path = str(self.paths.get_raw_table("productos"))
        df_productos = self.spark.read.parquet(productos_path)
        
        # Construir dimensión con claves y atributos
        dim_producto = (
            df_productos
            .select(
                F.col("producto_id").cast("int").alias("producto_id"),
                F.col("nombre").alias("nombre_completo"),
                F.col("producto").alias("nombre"),
                F.col("categoria"),
                F.col("subcategoria"),
                F.col("marca"),
                F.col("especificacion")
            )
            .dropDuplicates(["producto_id"])
        )
        
        # Guardar dimensión
        output_path = str(self.paths.get_refined_table("dim_producto"))
        (
            dim_producto
            .write
            .mode("overwrite")
            .parquet(output_path)
        )
        
        logger.info(f"✅ dim_producto creada: {dim_producto.count()} registros -> {output_path}")
    
    def build_dim_establecimiento(self) -> None:
        """Construye dimensión establecimiento con información del comercio."""
        logger.info("Construyendo dim_establecimiento...")
        
        # Leer establecimientos de raw
        est_path = str(self.paths.get_raw_table("establecimientos"))
        df_establecimientos = self.spark.read.parquet(est_path)
        
        # Construir dimensión
        dim_establecimiento = (
            df_establecimientos
            .select(
                F.col("establecimiento_id").cast("int").alias("establecimiento_id"),
                F.col("nombre"),
                F.col("razon_social"),
                F.col("cadena"),
                F.coalesce(F.col("cadena"), F.lit("Sin Cadena")).alias("cadena_normalizada")
            )
            .dropDuplicates(["establecimiento_id"])
        )
        
        # Guardar dimensión
        output_path = str(self.paths.get_refined_table("dim_establecimiento"))
        (
            dim_establecimiento
            .write
            .mode("overwrite")
            .parquet(output_path)
        )
        
        logger.info(f"✅ dim_establecimiento creada: {dim_establecimiento.count()} registros -> {output_path}")
    
    def build_dim_ubicacion(self) -> None:
        """Construye dimensión ubicación con información geográfica.
        
        Extrae información de ubicación de los establecimientos.
        
        Nota: En esta implementación, ubicacion_id = establecimiento_id para simplicidad,
        asumiendo una relación 1:1 entre establecimientos y ubicaciones. Si en el futuro
        múltiples establecimientos comparten ubicación (ej: varios comercios en un mall),
        será necesario rediseñar esta dimensión para deduplicar por atributos geográficos.
        """
        logger.info("Construyendo dim_ubicacion...")
        
        # Leer establecimientos de raw
        est_path = str(self.paths.get_raw_table("establecimientos"))
        df_establecimientos = self.spark.read.parquet(est_path)
        
        # Crear una clave de ubicación basada en combinación de atributos geográficos
        # y asociarla con establecimiento_id
        # Las coordenadas no son críticas para el análisis, simplemente las omitimos en caso de error
        dim_ubicacion = (
            df_establecimientos
            .select(
                F.col("establecimiento_id").cast("int").alias("establecimiento_id"),
                F.col("depto").alias("departamento"),
                F.col("ciudad"),
                F.col("direccion"),
                F.coalesce(F.col("barrio"), F.lit("Sin Barrio")).alias("barrio")
            )
            .dropDuplicates(["establecimiento_id"])
            .withColumn("ubicacion_id", F.col("establecimiento_id"))  # Usar mismo ID por simplicidad
        )
        
        # Guardar dimensión
        output_path = str(self.paths.get_refined_table("dim_ubicacion"))
        (
            dim_ubicacion
            .write
            .mode("overwrite")
            .parquet(output_path)
        )
        
        logger.info(f"✅ dim_ubicacion creada: {dim_ubicacion.count()} registros -> {output_path}")
    
    def build_all(self) -> None:
        """Construye todas las dimensiones del modelo estrella."""
        try:
            self.build_dim_tiempo()
            self.build_dim_producto()
            self.build_dim_establecimiento()
            self.build_dim_ubicacion()
            logger.info("✅ Todas las dimensiones construidas exitosamente")
        finally:
            stop_spark_session(self.spark)


def build_dimensions() -> None:
    """Función principal para ser llamada desde Airflow DAG."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    builder = DimensionBuilder()
    builder.build_all()
