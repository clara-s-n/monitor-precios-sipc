"""Cálculo de métricas de negocio sobre precios SIPC.

Implementa las 6 métricas principales del proyecto:
1. Precio promedio por producto
2. Variación porcentual diaria/mensual
3. Precio mínimo y máximo
4. Costo de canasta básica por supermercado
5. Índice de dispersión de precios
6. Ranking de supermercados según costo total
"""

import logging
from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F

from src.utils.spark_session import get_spark_session, stop_spark_session
from src.utils.paths import DataLakePaths

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """Calculador de métricas de negocio sobre datos de precios."""
    
    # Definir una canasta básica de productos comunes
    CANASTA_BASICA = [
        "Arroz blanco",
        "Aceite de girasol",
        "Aceite de soja", 
        "Fideos",
        "Harina de trigo",
        "Azúcar",
        "Sal fina",
        "Yerba mate",
        "Leche entera",
        "Pan"
    ]
    
    def __init__(self):
        self.spark = get_spark_session("CalculateMetrics")
        self.paths = DataLakePaths()
        self.paths.ensure_directories()
        
        # Cargar fact y dimensions
        self._load_data()
    
    def _load_data(self) -> None:
        """Carga fact_precios y dimensiones necesarias."""
        logger.info("Cargando datos de refined zone...")
        
        fact_path = str(self.paths.get_refined_table("fact_precios"))
        dim_producto_path = str(self.paths.get_refined_table("dim_producto"))
        dim_establecimiento_path = str(self.paths.get_refined_table("dim_establecimiento"))
        dim_tiempo_path = str(self.paths.get_refined_table("dim_tiempo"))
        dim_ubicacion_path = str(self.paths.get_refined_table("dim_ubicacion"))
        
        self.fact_precios = self.spark.read.parquet(fact_path)
        self.dim_producto = self.spark.read.parquet(dim_producto_path)
        self.dim_establecimiento = self.spark.read.parquet(dim_establecimiento_path)
        self.dim_tiempo = self.spark.read.parquet(dim_tiempo_path)
        self.dim_ubicacion = self.spark.read.parquet(dim_ubicacion_path)
        
        logger.info("Datos cargados exitosamente")
    
    def calculate_precio_promedio(self) -> None:
        """Métrica 1: Precio promedio por producto.
        
        Calcula el precio promedio por producto, mes y establecimiento.
        """
        logger.info("Calculando precio promedio por producto...")
        
        # Join fact con dimensiones
        df = (
            self.fact_precios
            .join(self.dim_producto.select("producto_id", F.col("nombre").alias("producto_nombre")), on="producto_id", how="inner")
            .join(self.dim_tiempo, on="fecha_id", how="inner")
            .join(self.dim_establecimiento.select("establecimiento_id", F.col("nombre").alias("establecimiento_nombre")), on="establecimiento_id", how="inner")
        )
        
        # Calcular promedios a diferentes niveles de agregación
        precio_promedio = (
            df
            .groupBy("producto_id", "producto_nombre", "anio", "mes")
            .agg(
                F.avg("precio").alias("precio_promedio"),
                F.count("*").alias("num_observaciones")
            )
            .orderBy("anio", "mes", "producto_nombre")
        )
        
        # Guardar resultado
        output_path = str(self.paths.get_export_file("precio_promedio_producto.parquet"))
        precio_promedio.write.mode("overwrite").parquet(output_path)
        
        logger.info(f"✅ Precio promedio calculado: {precio_promedio.count()} registros -> {output_path}")
    
    def calculate_variacion_porcentual(self) -> None:
        """Métrica 2: Variación porcentual diaria y mensual.
        
        Calcula variación % del precio respecto al período anterior.
        """
        logger.info("Calculando variación porcentual...")
        
        # Join fact con dimensiones
        df = (
            self.fact_precios
            .join(self.dim_producto.select("producto_id", F.col("nombre").alias("producto_nombre")), on="producto_id", how="inner")
            .join(self.dim_tiempo, on="fecha_id", how="inner")
        )
        
        # Calcular precio promedio por producto y fecha
        precio_por_fecha = (
            df
            .groupBy("producto_id", "producto_nombre", "fecha", "anio", "mes")
            .agg(F.avg("precio").alias("precio_promedio"))
        )
        
        # Calcular variación diaria
        window_dia = Window.partitionBy("producto_id").orderBy("fecha")
        variacion_diaria = (
            precio_por_fecha
            .withColumn("precio_anterior", F.lag("precio_promedio", 1).over(window_dia))
            .withColumn(
                "variacion_diaria_pct",
                F.when(
                    F.col("precio_anterior").isNotNull(),
                    ((F.col("precio_promedio") - F.col("precio_anterior")) / F.col("precio_anterior") * 100)
                ).otherwise(None)
            )
            .filter(F.col("variacion_diaria_pct").isNotNull())
            .select("producto_id", "producto_nombre", "fecha", "precio_promedio", "variacion_diaria_pct")
        )
        
        # Calcular precio promedio mensual
        precio_mensual = (
            df
            .groupBy("producto_id", "producto_nombre", "anio", "mes")
            .agg(F.avg("precio").alias("precio_promedio_mes"))
            .withColumn("anio_mes", F.concat(F.col("anio"), F.lit("-"), F.lpad(F.col("mes"), 2, "0")))
        )
        
        # Calcular variación mensual
        window_mes = Window.partitionBy("producto_id").orderBy("anio", "mes")
        variacion_mensual = (
            precio_mensual
            .withColumn("precio_mes_anterior", F.lag("precio_promedio_mes", 1).over(window_mes))
            .withColumn(
                "variacion_mensual_pct",
                F.when(
                    F.col("precio_mes_anterior").isNotNull(),
                    ((F.col("precio_promedio_mes") - F.col("precio_mes_anterior")) / F.col("precio_mes_anterior") * 100)
                ).otherwise(None)
            )
            .filter(F.col("variacion_mensual_pct").isNotNull())
            .select("producto_id", "producto_nombre", "anio", "mes", "anio_mes", "precio_promedio_mes", "variacion_mensual_pct")
        )
        
        # Guardar resultados
        output_diaria = str(self.paths.get_export_file("variacion_diaria.parquet"))
        output_mensual = str(self.paths.get_export_file("variacion_mensual.parquet"))
        
        variacion_diaria.write.mode("overwrite").parquet(output_diaria)
        variacion_mensual.write.mode("overwrite").parquet(output_mensual)
        
        logger.info(f"✅ Variación diaria: {variacion_diaria.count()} registros -> {output_diaria}")
        logger.info(f"✅ Variación mensual: {variacion_mensual.count()} registros -> {output_mensual}")
    
    def calculate_min_max_precios(self) -> None:
        """Métrica 3: Precio mínimo y máximo por producto.
        
        Identifica precios min/max por producto y período.
        """
        logger.info("Calculando precios mínimos y máximos...")
        
        # Join fact con dimensiones
        df = (
            self.fact_precios
            .join(self.dim_producto.select("producto_id", F.col("nombre").alias("producto_nombre")), on="producto_id", how="inner")
            .join(self.dim_tiempo, on="fecha_id", how="inner")
            .join(self.dim_establecimiento.select("establecimiento_id", F.col("nombre").alias("establecimiento_nombre")), on="establecimiento_id", how="inner")
        )
        
        # Calcular min/max por producto y mes
        min_max = (
            df
            .groupBy("producto_id", "producto_nombre", "anio", "mes")
            .agg(
                F.min("precio").alias("precio_minimo"),
                F.max("precio").alias("precio_maximo"),
                F.avg("precio").alias("precio_promedio")
            )
            .orderBy("anio", "mes", "producto_nombre")
        )
        
        # Encontrar establecimientos con precios mínimos y máximos
        # Primero identificamos el mínimo por producto/mes
        min_por_periodo = (
            df
            .groupBy("producto_id", "anio", "mes")
            .agg(F.min("precio").alias("precio_minimo"))
        )
        
        # Join para encontrar qué establecimientos tienen ese precio mínimo
        establecimientos_min = (
            df
            .join(min_por_periodo, on=["producto_id", "anio", "mes"], how="inner")
            .filter(F.col("precio") == F.col("precio_minimo"))
            .groupBy("producto_id", "producto_nombre", "anio", "mes", "precio_minimo")
            .agg(
                F.first("establecimiento_nombre", ignoreNulls=True).alias("establecimiento_mas_barato")
            )
        )
        
        # Similar para máximo
        max_por_periodo = (
            df
            .groupBy("producto_id", "anio", "mes")
            .agg(F.max("precio").alias("precio_maximo"))
        )
        
        establecimientos_max = (
            df
            .join(max_por_periodo, on=["producto_id", "anio", "mes"], how="inner")
            .filter(F.col("precio") == F.col("precio_maximo"))
            .groupBy("producto_id", "producto_nombre", "anio", "mes", "precio_maximo")
            .agg(
                F.first("establecimiento_nombre", ignoreNulls=True).alias("establecimiento_mas_caro")
            )
        )
        
        # Combinar resultados
        min_max_completo = (
            min_max
            .join(establecimientos_min, on=["producto_id", "producto_nombre", "anio", "mes"], how="left")
            .join(establecimientos_max, on=["producto_id", "producto_nombre", "anio", "mes"], how="left")
            .select(
                "producto_id", "producto_nombre", "anio", "mes",
                "precio_minimo", "establecimiento_mas_barato",
                "precio_maximo", "establecimiento_mas_caro",
                "precio_promedio"
            )
        )
        
        # Guardar resultado
        output_path = str(self.paths.get_export_file("min_max_precios.parquet"))
        min_max_completo.write.mode("overwrite").parquet(output_path)
        
        logger.info(f"✅ Min/Max precios calculado: {min_max_completo.count()} registros -> {output_path}")
    
    def calculate_canasta_basica(self) -> None:
        """Métrica 4: Costo de canasta básica por supermercado.
        
        Suma precios de productos de canasta básica por establecimiento.
        """
        logger.info("Calculando costo de canasta básica...")
        
        # Join fact con dimensiones
        df = (
            self.fact_precios
            .join(self.dim_producto.select("producto_id", "categoria"), on="producto_id", how="inner")
            .join(self.dim_tiempo, on="fecha_id", how="inner")
            .join(self.dim_establecimiento.select("establecimiento_id", F.col("nombre").alias("establecimiento_nombre")), on="establecimiento_id", how="inner")
        )
        
        # Filtrar solo productos de la canasta básica
        df_canasta = df.filter(F.col("categoria").isin(self.CANASTA_BASICA))
        
        # Calcular costo promedio de cada producto por establecimiento y mes
        costo_por_producto = (
            df_canasta
            .groupBy("establecimiento_id", "establecimiento_nombre", "producto_id", "categoria", "anio", "mes")
            .agg(F.avg("precio").alias("precio_promedio"))
        )
        
        # Sumar costos de todos los productos de la canasta por establecimiento
        costo_canasta = (
            costo_por_producto
            .groupBy("establecimiento_id", "establecimiento_nombre", "anio", "mes")
            .agg(
                F.sum("precio_promedio").alias("costo_total_canasta"),
                F.count("producto_id").alias("num_productos_canasta")
            )
            .orderBy("anio", "mes", "costo_total_canasta")
        )
        
        # Guardar resultado
        output_path = str(self.paths.get_export_file("canasta_basica.parquet"))
        costo_canasta.write.mode("overwrite").parquet(output_path)
        
        logger.info(f"✅ Canasta básica calculada: {costo_canasta.count()} registros -> {output_path}")
    
    def calculate_dispersion_precios(self) -> None:
        """Métrica 5: Índice de dispersión de precios.
        
        Fórmula: (precio_max - precio_min) / precio_promedio
        """
        logger.info("Calculando índice de dispersión...")
        
        # Join fact con dimensiones
        df = (
            self.fact_precios
            .join(self.dim_producto.select("producto_id", F.col("nombre").alias("producto_nombre")), on="producto_id", how="inner")
            .join(self.dim_tiempo, on="fecha_id", how="inner")
        )
        
        # Calcular dispersión por producto y período
        dispersion = (
            df
            .groupBy("producto_id", "producto_nombre", "anio", "mes")
            .agg(
                F.min("precio").alias("precio_minimo"),
                F.max("precio").alias("precio_maximo"),
                F.avg("precio").alias("precio_promedio")
            )
            .withColumn(
                "indice_dispersion",
                (F.col("precio_maximo") - F.col("precio_minimo")) / F.col("precio_promedio")
            )
            .orderBy(F.desc("indice_dispersion"))
        )
        
        # Guardar resultado
        output_path = str(self.paths.get_export_file("dispersion_precios.parquet"))
        dispersion.write.mode("overwrite").parquet(output_path)
        
        logger.info(f"✅ Dispersión de precios calculada: {dispersion.count()} registros -> {output_path}")
    
    def calculate_ranking_supermercados(self) -> None:
        """Métrica 6: Ranking de supermercados según costo total.
        
        Ranking basado en el costo de canasta básica.
        """
        logger.info("Calculando ranking de supermercados...")
        
        # Leer canasta básica calculada previamente
        canasta_path = str(self.paths.get_export_file("canasta_basica.parquet"))
        
        # Si no existe, calcularla primero
        try:
            df_canasta = self.spark.read.parquet(canasta_path)
        except:
            logger.warning("Canasta básica no encontrada, calculándola primero...")
            self.calculate_canasta_basica()
            df_canasta = self.spark.read.parquet(canasta_path)
        
        # Crear ranking por mes
        window_ranking = Window.partitionBy("anio", "mes").orderBy("costo_total_canasta")
        
        ranking = (
            df_canasta
            .withColumn("ranking", F.row_number().over(window_ranking))
            .withColumn("anio_mes", F.concat(F.col("anio"), F.lit("-"), F.lpad(F.col("mes"), 2, "0")))
            .select(
                "ranking",
                "establecimiento_id",
                "establecimiento_nombre",
                "anio",
                "mes",
                "anio_mes",
                "costo_total_canasta",
                "num_productos_canasta"
            )
            .orderBy("anio", "mes", "ranking")
        )
        
        # Guardar resultado
        output_path = str(self.paths.get_export_file("ranking_supermercados.parquet"))
        ranking.write.mode("overwrite").parquet(output_path)
        
        logger.info(f"✅ Ranking de supermercados calculado: {ranking.count()} registros -> {output_path}")
    
    def calculate_all(self) -> None:
        """Calcula todas las métricas de negocio."""
        try:
            self.calculate_precio_promedio()
            self.calculate_variacion_porcentual()
            self.calculate_min_max_precios()
            self.calculate_canasta_basica()
            self.calculate_dispersion_precios()
            self.calculate_ranking_supermercados()
            logger.info("✅ Todas las métricas calculadas exitosamente")
        finally:
            stop_spark_session(self.spark)


def calculate_all_metrics() -> None:
    """Función principal para ser llamada desde Airflow DAG."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    calculator = MetricsCalculator()
    calculator.calculate_all()
