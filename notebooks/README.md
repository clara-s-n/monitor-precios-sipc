# 📓 Jupyter Notebooks - Monitor de Precios SIPC

Este directorio contiene los notebooks Jupyter utilizados para el análisis de datos del proyecto Monitor de Precios SIPC.

## 🗂️ Estructura de Notebooks

### 01_exploracion.ipynb
**Análisis Exploratorio de Datos (EDA)**

- **Objetivo:** Explorar y entender los datos raw del Data Lake
- **Datos utilizados:** `data_sipc/raw/` (precios, productos, establecimientos)
- **Contenido:**
  - Carga y visualización inicial de datos
  - Estadísticas descriptivas
  - Distribuciones temporales y geográficas
  - Análisis de calidad de datos (nulos, duplicados)
  - Verificación de integridad referencial
  - Análisis cruzado de precios por categoría
- **Duración estimada:** 10-15 minutos

### 02_modelo_datos.ipynb
**Documentación del Modelo Dimensional**

- **Objetivo:** Explicar y validar el Star Schema implementado
- **Datos utilizados:** `data_sipc/refined/` (dimensiones y tabla de hechos)
- **Contenido:**
  - Arquitectura del modelo (diagrama conceptual)
  - Descripción detallada de cada dimensión
  - Tabla de hechos y medidas
  - Validación de integridad referencial
  - Ejemplos de consultas analíticas
  - Benchmark de performance
- **Duración estimada:** 15-20 minutos

### 03_dashboard.ipynb
**Dashboard de Métricas de Negocio**

- **Objetivo:** Visualizar y analizar las 6 métricas principales
- **Datos utilizados:** `data_sipc/exports_dashboard/` (métricas pre-calculadas)
- **Contenido:**
  - **Métrica 1:** Precio promedio por producto
  - **Métrica 2:** Variación porcentual mensual
  - **Métrica 3:** Precio mínimo y máximo
  - **Métrica 4:** Costo de canasta básica por supermercado
  - **Métrica 5:** Índice de dispersión de precios
  - **Métrica 6:** Ranking de supermercados
  - Análisis integrado y correlaciones
  - Conclusiones y recomendaciones
- **Duración estimada:** 20-30 minutos

---

## 🚀 Cómo Ejecutar los Notebooks

### Requisitos Previos

1. **Pipeline ETL ejecutado:** Los notebooks requieren que el pipeline de Airflow haya procesado los datos
2. **Jupyter Lab activo:** El contenedor Docker `jupyter` debe estar corriendo

### Paso 1: Iniciar el Entorno

```bash
# Desde el directorio raíz del proyecto
docker-compose up -d
```

Esto inicia:
- Contenedor `airflow` (con el DAG de ETL)
- Contenedor `jupyter` (Jupyter Lab con PySpark)

### Paso 2: Acceder a Jupyter Lab

1. Abrir navegador en: **http://localhost:8888**
2. Navegar a la carpeta `notebooks/`

### Paso 3: Ejecutar los Notebooks

**Orden recomendado:**

```
01_exploracion.ipynb → 02_modelo_datos.ipynb → 03_dashboard.ipynb
```

**Ejecución:**
- Usar `Shift + Enter` para ejecutar celda por celda
- O desde el menú: `Run → Run All Cells`

---

## 📊 Datos Utilizados

### Rutas Relativas en Notebooks

Los notebooks utilizan rutas relativas desde `notebooks/`:

```python
# Ejemplo: cargar datos raw
df = spark.read.parquet('../data_sipc/raw/precios.parquet')

# Ejemplo: cargar datos refined
df = spark.read.parquet('../data_sipc/refined/dim_tiempo.parquet')

# Ejemplo: cargar métricas
df = pd.read_parquet('../data_sipc/exports_dashboard/precio_promedio.parquet')
```

### Verificar Disponibilidad de Datos

Antes de ejecutar, verificar que existen:

```bash
ls -lh data_sipc/raw/
ls -lh data_sipc/refined/
ls -lh data_sipc/exports_dashboard/
```

Si faltan datos, ejecutar el DAG de Airflow:

```bash
# Opción 1: Desde UI de Airflow (http://localhost:8080)
# Trigger manual del DAG "monitor_precios_sipc_etl"

# Opción 2: Desde línea de comandos
docker exec airflow airflow dags trigger monitor_precios_sipc_etl
```

---

## 🎨 Visualizaciones

Los notebooks incluyen múltiples visualizaciones:

- **📈 Gráficos de líneas:** Evolución temporal de precios
- **📊 Histogramas:** Distribución de precios y variaciones
- **📦 Boxplots:** Comparación de dispersión
- **🎯 Scatter plots:** Correlaciones entre métricas
- **🏆 Gráficos de barras:** Rankings y comparaciones

**Librerías utilizadas:**
- `matplotlib` - Gráficos estáticos
- `seaborn` - Visualizaciones estadísticas mejoradas
- `pandas` - Manipulación de datos para gráficos

---

## 🛠️ Solución de Problemas

### Error: "No module named 'pyspark'"

**Causa:** Ejecutando notebook fuera del contenedor Docker

**Solución:**
```bash
# Acceder a Jupyter Lab dentro del contenedor
http://localhost:8888
```

### Error: "FileNotFoundError: [Errno 2] No such file or directory"

**Causa:** Datos no generados por el pipeline

**Solución:**
```bash
# Ejecutar pipeline de Airflow primero
docker exec airflow airflow dags trigger monitor_precios_sipc_etl

# Esperar a que complete (~6 minutos)
docker exec airflow airflow dags list-runs -d monitor_precios_sipc_etl
```

### Kernel muere o se queda sin memoria

**Causa:** Datasets grandes pueden consumir mucha memoria

**Solución:**
- Reiniciar kernel: `Kernel → Restart Kernel`
- Ejecutar celdas en orden (no ejecutar todas a la vez)
- Usar `.sample()` en DataFrames de PySpark para pruebas

---

## 📝 Notas Importantes

### Diferencias entre Notebooks y Pipeline ETL

- **Notebooks:** Usan rutas relativas (`../data_sipc/`)
- **Pipeline Airflow:** Usa rutas absolutas (`/opt/airflow/data_sipc/`)

### Modo de Spark

Los notebooks usan Spark en **modo local**:

```python
spark = SparkSession.builder \
    .appName("MyApp") \
    .master("local[*]") \  # Todos los cores locales
    .getOrCreate()
```

### Persistencia de Resultados

Los notebooks **NO modifican** los datos del Data Lake. Solo leen y visualizan.

Para regenerar métricas, ejecutar el DAG de Airflow.

---

## 📚 Referencias

- **Star Schema Design:** [Kimball Dimensional Modeling](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/)
- **PySpark Documentation:** [Apache Spark SQL Guide](https://spark.apache.org/docs/latest/sql-programming-guide.html)
- **SIPC Data Source:** [Catálogo de Datos Abiertos Uruguay](https://catalogodatos.gub.uy/)

---

## ✅ Checklist de Ejecución

Antes de presentar, verificar:

- [ ] Pipeline ETL ejecutado exitosamente
- [ ] Todos los archivos Parquet generados en `exports_dashboard/`
- [ ] Notebooks ejecutados sin errores
- [ ] Visualizaciones renderizadas correctamente
- [ ] Métricas calculadas con valores coherentes
- [ ] Conclusiones y recomendaciones revisadas

---

**Última actualización:** Diciembre 2024  
**Autor:** Equipo Monitor de Precios SIPC - UCU Campus Salto
