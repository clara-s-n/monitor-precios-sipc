"""
Módulo de validación y calidad de datos para el pipeline SIPC.

Implementa checks de calidad sobre las tablas del modelo dimensional:
- Completitud (valores nulos)
- Integridad referencial (FKs)
- Consistencia de datos
- Duplicados
- Rangos válidos
"""

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pathlib import Path
import sys

# Agregar src al path para imports
sys.path.append(str(Path(__file__).parent.parent))

from utils.spark_session import get_spark_session
from utils.paths import REFINED_PATH, EXPORTS_DASHBOARD_PATH


class DataQualityChecker:
    """Clase para ejecutar validaciones de calidad de datos."""
    
    def __init__(self, spark: SparkSession):
        self.spark = spark
        self.results = []
    
    def check_nulls(self, df: DataFrame, table_name: str, critical_columns: list) -> dict:
        """
        Verifica valores nulos en columnas críticas.
        
        Args:
            df: DataFrame a validar
            table_name: Nombre de la tabla
            critical_columns: Lista de columnas que no deben tener nulos
        
        Returns:
            dict con resultados de la validación
        """
        total_rows = df.count()
        null_counts = {}
        
        for col in critical_columns:
            if col in df.columns:
                null_count = df.filter(F.col(col).isNull()).count()
                null_pct = (null_count / total_rows * 100) if total_rows > 0 else 0
                null_counts[col] = {
                    'count': null_count,
                    'percentage': null_pct,
                    'passed': null_count == 0
                }
        
        all_passed = all(v['passed'] for v in null_counts.values())
        
        result = {
            'table': table_name,
            'check': 'null_values',
            'total_rows': total_rows,
            'details': null_counts,
            'passed': all_passed,
            'message': f"{'✅' if all_passed else '⚠️'} Null check for {table_name}"
        }
        
        self.results.append(result)
        return result
    
    def check_referential_integrity(self, fact_df: DataFrame, dim_df: DataFrame, 
                                   fk_column: str, pk_column: str, 
                                   fact_name: str, dim_name: str) -> dict:
        """
        Verifica integridad referencial entre tabla de hechos y dimensión.
        
        Args:
            fact_df: DataFrame de tabla de hechos
            dim_df: DataFrame de dimensión
            fk_column: Columna de FK en tabla de hechos
            pk_column: Columna de PK en dimensión
            fact_name: Nombre de tabla de hechos
            dim_name: Nombre de dimensión
        
        Returns:
            dict con resultados de la validación
        """
        orphan_records = fact_df.join(
            dim_df.select(pk_column), 
            fact_df[fk_column] == dim_df[pk_column], 
            'left_anti'
        ).count()
        
        total_fact_rows = fact_df.count()
        orphan_pct = (orphan_records / total_fact_rows * 100) if total_fact_rows > 0 else 0
        passed = orphan_records == 0
        
        result = {
            'table': f"{fact_name} -> {dim_name}",
            'check': 'referential_integrity',
            'fk_column': fk_column,
            'pk_column': pk_column,
            'orphan_records': orphan_records,
            'orphan_percentage': orphan_pct,
            'total_fact_rows': total_fact_rows,
            'passed': passed,
            'message': f"{'✅' if passed else '❌'} FK {fk_column} -> {dim_name}.{pk_column}: {orphan_records} orphans"
        }
        
        self.results.append(result)
        return result
    
    def check_duplicates(self, df: DataFrame, table_name: str, key_columns: list) -> dict:
        """
        Verifica duplicados en columnas clave.
        
        Args:
            df: DataFrame a validar
            table_name: Nombre de la tabla
            key_columns: Lista de columnas que definen unicidad
        
        Returns:
            dict con resultados de la validación
        """
        total_rows = df.count()
        
        if key_columns:
            unique_rows = df.select(key_columns).distinct().count()
            duplicates = total_rows - unique_rows
            duplicate_pct = (duplicates / total_rows * 100) if total_rows > 0 else 0
        else:
            # Si no hay key_columns, compara filas completas
            unique_rows = df.distinct().count()
            duplicates = total_rows - unique_rows
            duplicate_pct = (duplicates / total_rows * 100) if total_rows > 0 else 0
        
        passed = duplicates == 0
        
        result = {
            'table': table_name,
            'check': 'duplicates',
            'key_columns': key_columns,
            'total_rows': total_rows,
            'unique_rows': unique_rows,
            'duplicate_rows': duplicates,
            'duplicate_percentage': duplicate_pct,
            'passed': passed,
            'message': f"{'✅' if passed else '⚠️'} Duplicate check for {table_name}: {duplicates} duplicates"
        }
        
        self.results.append(result)
        return result
    
    def check_range(self, df: DataFrame, table_name: str, column: str, 
                   min_value=None, max_value=None) -> dict:
        """
        Verifica que valores estén dentro de un rango válido.
        
        Args:
            df: DataFrame a validar
            table_name: Nombre de la tabla
            column: Columna a validar
            min_value: Valor mínimo permitido (opcional)
            max_value: Valor máximo permitido (opcional)
        
        Returns:
            dict con resultados de la validación
        """
        total_rows = df.count()
        out_of_range = 0
        
        # Filtrar valores fuera de rango
        filtered_df = df
        if min_value is not None:
            filtered_df = filtered_df.filter(F.col(column) >= min_value)
        if max_value is not None:
            filtered_df = filtered_df.filter(F.col(column) <= max_value)
        
        valid_rows = filtered_df.count()
        out_of_range = total_rows - valid_rows
        out_of_range_pct = (out_of_range / total_rows * 100) if total_rows > 0 else 0
        
        passed = out_of_range == 0
        
        result = {
            'table': table_name,
            'check': 'range_validation',
            'column': column,
            'min_value': min_value,
            'max_value': max_value,
            'total_rows': total_rows,
            'valid_rows': valid_rows,
            'out_of_range': out_of_range,
            'out_of_range_percentage': out_of_range_pct,
            'passed': passed,
            'message': f"{'✅' if passed else '❌'} Range check for {table_name}.{column}: {out_of_range} out of range"
        }
        
        self.results.append(result)
        return result
    
    def check_consistency(self, df: DataFrame, table_name: str, 
                         column: str, allowed_values: list) -> dict:
        """
        Verifica que valores estén dentro de un conjunto permitido.
        
        Args:
            df: DataFrame a validar
            table_name: Nombre de la tabla
            column: Columna a validar
            allowed_values: Lista de valores permitidos
        
        Returns:
            dict con resultados de la validación
        """
        total_rows = df.count()
        valid_rows = df.filter(F.col(column).isin(allowed_values)).count()
        invalid_rows = total_rows - valid_rows
        invalid_pct = (invalid_rows / total_rows * 100) if total_rows > 0 else 0
        
        passed = invalid_rows == 0
        
        result = {
            'table': table_name,
            'check': 'consistency',
            'column': column,
            'allowed_values': allowed_values,
            'total_rows': total_rows,
            'valid_rows': valid_rows,
            'invalid_rows': invalid_rows,
            'invalid_percentage': invalid_pct,
            'passed': passed,
            'message': f"{'✅' if passed else '❌'} Consistency check for {table_name}.{column}: {invalid_rows} invalid values"
        }
        
        self.results.append(result)
        return result
    
    def get_summary(self) -> dict:
        """
        Retorna resumen de todos los checks ejecutados.
        
        Returns:
            dict con estadísticas generales
        """
        total_checks = len(self.results)
        passed_checks = sum(1 for r in self.results if r['passed'])
        failed_checks = total_checks - passed_checks
        pass_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        
        return {
            'total_checks': total_checks,
            'passed': passed_checks,
            'failed': failed_checks,
            'pass_rate': pass_rate,
            'all_passed': failed_checks == 0
        }
    
    def print_report(self):
        """Imprime reporte detallado de calidad de datos."""
        print("\n" + "=" * 80)
        print("📊 REPORTE DE CALIDAD DE DATOS - SIPC")
        print("=" * 80)
        
        for result in self.results:
            print(f"\n{result['message']}")
            if not result['passed']:
                print(f"  ⚠️ DETALLES:")
                for key, value in result.items():
                    if key not in ['message', 'passed', 'check', 'table']:
                        print(f"    {key}: {value}")
        
        summary = self.get_summary()
        print("\n" + "=" * 80)
        print("📈 RESUMEN:")
        print(f"  Total de checks: {summary['total_checks']}")
        print(f"  ✅ Pasados: {summary['passed']}")
        print(f"  ❌ Fallados: {summary['failed']}")
        print(f"  📊 Tasa de éxito: {summary['pass_rate']:.2f}%")
        print("=" * 80)
        
        if summary['all_passed']:
            print("✅ TODOS LOS CHECKS DE CALIDAD PASARON")
        else:
            print("⚠️ ALGUNOS CHECKS FALLARON - REVISAR DETALLES")
        print("=" * 80 + "\n")


def run_quality_checks():
    """
    Ejecuta todos los checks de calidad sobre el modelo dimensional.
    """
    print("🔍 Iniciando validación de calidad de datos...")
    
    # Obtener Spark session
    spark = get_spark_session("SIPC Data Quality Checks")
    
    # Crear checker
    checker = DataQualityChecker(spark)
    
    # Cargar tablas desde refined zone
    print("📁 Cargando tablas del modelo dimensional...")
    
    fact_precios = spark.read.parquet(str(REFINED_PATH / "fact_precios.parquet"))
    dim_tiempo = spark.read.parquet(str(REFINED_PATH / "dim_tiempo.parquet"))
    dim_producto = spark.read.parquet(str(REFINED_PATH / "dim_producto.parquet"))
    dim_establecimiento = spark.read.parquet(str(REFINED_PATH / "dim_establecimiento.parquet"))
    dim_ubicacion = spark.read.parquet(str(REFINED_PATH / "dim_ubicacion.parquet"))
    
    print("✅ Tablas cargadas correctamente\n")
    
    # ===== CHECKS DE VALORES NULOS =====
    print("🔍 Ejecutando checks de valores nulos...")
    
    checker.check_nulls(fact_precios, "fact_precios", 
                       ['fecha_id', 'producto_id', 'establecimiento_id', 'ubicacion_id', 'precio'])
    
    checker.check_nulls(dim_tiempo, "dim_tiempo", 
                       ['fecha_id', 'fecha', 'anio', 'mes', 'dia'])
    
    checker.check_nulls(dim_producto, "dim_producto", 
                       ['producto_id', 'nombre'])
    
    checker.check_nulls(dim_establecimiento, "dim_establecimiento", 
                       ['establecimiento_id', 'nombre'])
    
    checker.check_nulls(dim_ubicacion, "dim_ubicacion", 
                       ['ubicacion_id', 'establecimiento_id'])
    
    # ===== CHECKS DE INTEGRIDAD REFERENCIAL =====
    print("🔗 Ejecutando checks de integridad referencial...")
    
    checker.check_referential_integrity(fact_precios, dim_tiempo, 
                                       'fecha_id', 'fecha_id',
                                       'fact_precios', 'dim_tiempo')
    
    checker.check_referential_integrity(fact_precios, dim_producto,
                                       'producto_id', 'producto_id',
                                       'fact_precios', 'dim_producto')
    
    checker.check_referential_integrity(fact_precios, dim_establecimiento,
                                       'establecimiento_id', 'establecimiento_id',
                                       'fact_precios', 'dim_establecimiento')
    
    checker.check_referential_integrity(fact_precios, dim_ubicacion,
                                       'ubicacion_id', 'ubicacion_id',
                                       'fact_precios', 'dim_ubicacion')
    
    # ===== CHECKS DE DUPLICADOS =====
    print("🔎 Ejecutando checks de duplicados...")
    
    checker.check_duplicates(dim_tiempo, "dim_tiempo", ['fecha_id'])
    checker.check_duplicates(dim_producto, "dim_producto", ['producto_id'])
    checker.check_duplicates(dim_establecimiento, "dim_establecimiento", ['establecimiento_id'])
    checker.check_duplicates(dim_ubicacion, "dim_ubicacion", ['ubicacion_id'])
    
    # ===== CHECKS DE RANGOS =====
    print("📏 Ejecutando checks de rangos válidos...")
    
    # Precios deben ser positivos
    checker.check_range(fact_precios, "fact_precios", "precio", min_value=0.01)
    
    # Años razonables
    checker.check_range(dim_tiempo, "dim_tiempo", "anio", min_value=2020, max_value=2030)
    
    # Meses válidos
    checker.check_range(dim_tiempo, "dim_tiempo", "mes", min_value=1, max_value=12)
    
    # Días válidos
    checker.check_range(dim_tiempo, "dim_tiempo", "dia", min_value=1, max_value=31)
    
    # ===== CHECKS DE CONSISTENCIA =====
    print("✓ Ejecutando checks de consistencia...")
    
    # Valores de oferta deben ser 0 o 1
    checker.check_consistency(fact_precios, "fact_precios", "oferta", [0, 1])
    
    # Días de semana válidos
    checker.check_consistency(dim_tiempo, "dim_tiempo", "dia_semana", [1, 2, 3, 4, 5, 6, 7])
    
    # Trimestres válidos
    checker.check_consistency(dim_tiempo, "dim_tiempo", "trimestre", [1, 2, 3, 4])
    
    # ===== GENERAR REPORTE =====
    checker.print_report()
    
    # ===== EXPORTAR RESULTADOS =====
    print("💾 Exportando resultados de calidad...")
    
    # Convertir resultados a DataFrame y guardar
    results_data = []
    for r in checker.results:
        results_data.append({
            'table': r['table'],
            'check_type': r['check'],
            'passed': r['passed'],
            'message': r['message']
        })
    
    df_results = spark.createDataFrame(results_data)
    output_path = EXPORTS_DASHBOARD_PATH / "data_quality_report.parquet"
    
    # Limpiar directorio de salida
    from utils.spark_session import _clean_output_dir
    _clean_output_dir(str(output_path))
    
    df_results.write.parquet(str(output_path))
    print(f"✅ Reporte guardado en: {output_path}")
    
    # Guardar summary como JSON
    summary = checker.get_summary()
    summary_path = EXPORTS_DASHBOARD_PATH / "quality_summary.json"
    
    import json
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"✅ Resumen guardado en: {summary_path}")
    
    spark.stop()
    
    return summary['all_passed']


if __name__ == "__main__":
    success = run_quality_checks()
    sys.exit(0 if success else 1)
