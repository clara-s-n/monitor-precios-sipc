"""Versión simplificada de métricas para garantizar funcionamiento.

Calcula las 6 métricas principales de forma robusta evitando ambigüedades.
"""

import logging
from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F

from src.utils.spark_session import get_spark_session, stop_spark_session
from src.utils.paths import DataLakePaths

logger = logging.getLogger(__name__)


# Definición de canasta básica basada en CBAEN 2024 (Tabla 2)
# Productos esenciales para calcular el costo de vida
CANASTA_BASICA = [
    # Carnes
    "Carne picada vacuna",
    "Aguja vacuna",
    "Pollo entero fresco con menudos",
    
    # Pescados y huevos
    "Pescado fresco",
    "Huevos colorados",
    
    # Frutas
    "Naranja Navel", "Naranja Valencia",
    "Mandarina Avana", "Mandarina Común", "Mandarina Ellendale", "Mandarina Zazuma",
    "Pera Francesa", "Pera Packams", "Pera Williams",
    "Manzana Fuji", "Manzana Granny Smith", "Manzana Red Chieff",
    "Manzana Red Deliciosa", "Manzana Roja", "Manzana Royal Gala",
    "Banana Brasil", "Banana Ecuador",
    "Durazno Pavía", "Durazno Rey del Monte",
    "Frutilla",
    "Limón",
    
    # Verduras
    "Zanahoria",
    "Lechuga Crespa", "Lechuga Mantecosa",
    "Tomate Americano", "Tomate Perita",
    "Cebolla Seca", "Cebolla de Verdeo",
    "Zapallo Criollo", "Zapallo Kabutiá", "Zapallo Calabacín",
    "Morrón Amarillo", "Morrón Rojo", "Morrón Verde",
    "Zapallito Redondo", "Zapallito Zuchini",
    
    # Tubérculos
    "Papa Blanca", "Papa Rosada",
    "Boniato Arapery", "Boniato Morado",
    
    # Cereales
    "Harina trigo común 0000", "Harina trigo común 000",
    "Arroz blanco",
    "Fideos secos al huevo", "Fideos secos semolados",
    "Pan flauta",
    "Pan de molde lacteado",  # Aproximación a Pan Porteño
    
    # Leguminosas
    "Arvejas", "Arvejas en conserva",
    
    # Azúcares y dulces
    "Azúcar blanco",
    "Dulce de leche",
    "Dulce de membrillo",
    
    # Aceites y grasas
    "Aceite de soja",
    "Aceite de girasol",
    "Manteca",
    
    # Otros (infusiones / varios)
    "Sal fina yodada fluorada",
    "Yerba mate común",
    "Agua de mesa con gas", "Agua de mesa sin gas",
]


def calculate_simple_metrics() -> None:
    """Calcula las 6 métricas principales de forma simplificada."""
    spark = get_spark_session("SimpleMetrics")
    paths = DataLakePaths()
    
    try:
        logger.info("Iniciando cálculo de métricas...")
        
        # Cargar datos
        fact = spark.read.parquet(str(paths.get_refined_table("fact_precios")))
        dim_producto = spark.read.parquet(str(paths.get_refined_table("dim_producto")))
        dim_tiempo = spark.read.parquet(str(paths.get_refined_table("dim_tiempo")))
        dim_establecimiento = spark.read.parquet(str(paths.get_refined_table("dim_establecimiento")))
        
        # 1. Precio promedio por producto
        logger.info("1. Calculando precio promedio...")
        precio_prom = (
            fact.alias("f")
            .join(dim_producto.select("producto_id", F.col("nombre").alias("producto")).alias("p"), 
                  F.col("f.producto_id") == F.col("p.producto_id"))
            .join(dim_tiempo.select("fecha_id", "anio", "mes").alias("t"),
                  F.col("f.fecha_id") == F.col("t.fecha_id"))
            .groupBy("p.producto", "t.anio", "t.mes")
            .agg(F.avg("f.precio").alias("precio_promedio"))
            .orderBy("t.anio", "t.mes", "p.producto")
        )
        precio_prom.write.mode("overwrite").parquet(str(paths.get_export_file("precio_promedio.parquet")))
        logger.info(f"   ✅ {precio_prom.count()} registros")
        
        # 2. Min/Max por producto
        logger.info("2. Calculando min/max...")
        min_max = (
            fact.alias("f")
            .join(dim_producto.select("producto_id", F.col("nombre").alias("producto")).alias("p"),
                  F.col("f.producto_id") == F.col("p.producto_id"))
            .join(dim_tiempo.select("fecha_id", "anio", "mes").alias("t"),
                  F.col("f.fecha_id") == F.col("t.fecha_id"))
            .groupBy("p.producto", "t.anio", "t.mes")
            .agg(
                F.min("f.precio").alias("precio_minimo"),
                F.max("f.precio").alias("precio_maximo"),
                F.avg("f.precio").alias("precio_promedio")
            )
            .orderBy("t.anio", "t.mes")
        )
        min_max.write.mode("overwrite").parquet(str(paths.get_export_file("min_max_precios.parquet")))
        logger.info(f"   ✅ {min_max.count()} registros")
        
        # 3. Índice de dispersión
        logger.info("3. Calculando dispersión...")
        dispersion = (
            min_max
            .withColumn("indice_dispersion",
                       (F.col("precio_maximo") - F.col("precio_minimo")) / F.col("precio_promedio"))
            .orderBy(F.desc("indice_dispersion"))
        )
        dispersion.write.mode("overwrite").parquet(str(paths.get_export_file("dispersion_precios.parquet")))
        logger.info(f"   ✅ {dispersion.count()} registros")
        
        # 4. Canasta básica
        logger.info("4. Calculando canasta básica...")
        canasta = (
            fact.alias("f")
            .join(dim_producto.select("producto_id", F.col("nombre").alias("producto_nombre")).alias("p"),
                  F.col("f.producto_id") == F.col("p.producto_id"))
            .join(dim_tiempo.select("fecha_id", "anio", "mes").alias("t"),
                  F.col("f.fecha_id") == F.col("t.fecha_id"))
            .join(dim_establecimiento.select("establecimiento_id", F.col("nombre").alias("supermercado")).alias("e"),
                  F.col("f.establecimiento_id") == F.col("e.establecimiento_id"))
            .filter(F.col("p.producto_nombre").isin(CANASTA_BASICA))
            .groupBy("e.supermercado", "t.anio", "t.mes")
            .agg(F.sum("f.precio").alias("costo_canasta"))
            .orderBy("t.anio", "t.mes", "costo_canasta")
        )
        canasta.write.mode("overwrite").parquet(str(paths.get_export_file("canasta_basica.parquet")))
        logger.info(f"   ✅ {canasta.count()} registros")
        
        # 5. Ranking supermercados
        logger.info("5. Calculando ranking...")
        window = Window.partitionBy("anio", "mes").orderBy("costo_canasta")
        ranking = (
            canasta
            .withColumn("ranking", F.row_number().over(window))
            .orderBy("anio", "mes", "ranking")
        )
        ranking.write.mode("overwrite").parquet(str(paths.get_export_file("ranking_supermercados.parquet")))
        logger.info(f"   ✅ {ranking.count()} registros")
        
        # 6. Variación mensual simplificada
        logger.info("6. Calculando variación mensual...")
        mensual = (
            fact.alias("f")
            .join(dim_producto.select("producto_id", F.col("nombre").alias("producto")).alias("p"),
                  F.col("f.producto_id") == F.col("p.producto_id"))
            .join(dim_tiempo.select("fecha_id", "anio", "mes").alias("t"),
                  F.col("f.fecha_id") == F.col("t.fecha_id"))
            .groupBy("p.producto", "t.anio", "t.mes")
            .agg(F.avg("f.precio").alias("precio_mes"))
        )
        
        window_var = Window.partitionBy("producto").orderBy("anio", "mes")
        variacion = (
            mensual
            .withColumn("precio_anterior", F.lag("precio_mes").over(window_var))
            .withColumn("variacion_pct",
                       F.when(F.col("precio_anterior").isNotNull(),
                             (F.col("precio_mes") - F.col("precio_anterior")) / F.col("precio_anterior") * 100)
                       .otherwise(None))
            .filter(F.col("variacion_pct").isNotNull())
        )
        variacion.write.mode("overwrite").parquet(str(paths.get_export_file("variacion_mensual.parquet")))
        logger.info(f"   ✅ {variacion.count()} registros")
        
        logger.info("✅ Todas las métricas calculadas exitosamente")
        
    finally:
        stop_spark_session(spark)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    calculate_simple_metrics()
