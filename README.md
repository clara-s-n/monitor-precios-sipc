# Monitor de Precios SIPC – Obligatorio Big Data

Proyecto del curso **Big Data** (UCU – Salto) que construye un **Data Lake** y un **pipeline ETL orquestado con Apache Airflow** para analizar los datos de precios del **SIPC** (Sistema de Información de Precios al Consumidor).

## 🎯 Objetivos

- Limpiar y unificar las tablas de precios, productos y establecimientos del SIPC
- Construir un **modelo tipo estrella** (dimensiones + hechos de precios)
- Calcular 6 métricas clave sobre evolución de precios y canasta básica
- Exponer resultados en **dashboard Jupyter**

## 🧩 Métricas Implementadas

El proyecto calcula las siguientes **6 métricas principales**:

1. **Precio promedio por producto**  
   Promedio del precio de un producto en un período y nivel de agregación determinado (por establecimiento, por cadena, por zona, etc.).  
   Ejemplo: precio promedio mensual del “Arroz 1 kg” por supermercado.

2. **Variación porcentual diaria/mensual**  
   Mide cuánto varió el precio con respecto al período anterior.  
   Fórmula genérica:  
   \[
   \text{VarPct} = \frac{\text{Precio actual} - \text{Precio anterior}}{\text{Precio anterior}}
   \]  
   Se calcula tanto **día a día** como **mes a mes** para productos y/o canasta.

3. **Precio mínimo y máximo**  
   Para cada producto y período, se calcula el **precio mínimo** y **máximo** observado entre todos los establecimientos.  
   Permite identificar supermercados más caros/baratos para cada producto.

4. **Costo de canasta básica por supermercado**  
   Se define una **canasta básica** como conjunto de productos seleccionados.  
   Para cada supermercado y período (por ejemplo, mes), se suma el precio de esos productos → **costo total de la canasta**.  
   Permite comparar el “costo de llenar el carrito” entre supermercados.

5. **Índice de dispersión de precios**  
   Mide cuán dispersos están los precios de un producto entre establecimientos.  
   Fórmula propuesta:  
   \[
   \text{Índice de dispersión} = \frac{\text{Precio máximo} - \text{Precio mínimo}}{\text{Precio promedio}}
   \]  
   Valores altos indican gran diferencia de precios entre comercios.

6. **Ranking de supermercados según costo total**  
   A partir del costo de la canasta básica, se genera un ranking de supermercados (del más barato al más caro) para un período dado.  
   Puede filtrarse por ciudad/zona, cadena, etc.

Estas métricas se calculan sobre la **capa Refined** del Data Lake y se utilizan en el dashboard final.

## 🏗️ Arquitectura

### Data Lake (filesystem local)

```
data_sipc/
├── landing/          # CSV originales del SIPC (no versionados)
├── raw/              # Parquet limpio y tipado (PySpark)
├── refined/          # Modelo estrella (dimensiones + hechos)
└── exports_dashboard/ # Datasets finales para visualización
```

### Stack Tecnológico

- **PySpark** (modo `local[*]`) – Transformaciones ETL sin cluster distribuido
- **Apache Airflow 2.9.2** – Orquestación (SequentialExecutor + SQLite)
- **Docker Compose** – Contenedores `airflow` y `jupyter`
- **Parquet** – Formato de almacenamiento optimizado

## 🚀 Inicio Rápido

### Prerequisitos

- Docker y Docker Compose instalados
- 4GB RAM disponible

### Levantar el entorno

```bash
# Clonar repositorio
git clone https://github.com/clara-s-n/monitor-precios-sipc.git
cd monitor-precios-sipc

# Iniciar servicios
docker-compose up -d

# Verificar estado
docker-compose ps
```

### Acceso a interfaces

| Servicio    | URL                   | Credenciales      |
| ----------- | --------------------- | ----------------- |
| Airflow UI  | http://localhost:8080 | Sin autenticación |
| Jupyter Lab | http://localhost:8888 | Token en logs     |

```bash
# Obtener token de Jupyter
docker logs jupyter-spark | grep "token="
```

### Ejecutar pipeline ETL

1. Colocar archivos CSV del SIPC en `data_sipc/landing/`:

   - `precios.csv`
   - `productos.csv`
   - `establecimientos.csv`

2. En Airflow UI (http://localhost:8080), activar DAG `monitor_precios_sipc_etl`

3. Monitorear ejecución en el panel de tareas

## 📂 Estructura del Proyecto

```
monitor-precios-sipc/
├── airflow/
│   ├── Dockerfile              # Imagen custom con PySpark
│   ├── dags/
│   │   └── monitor_precios_dag.py  # ✅ Orquestación ETL principal
│   └── logs/                   # Logs de ejecución
│
├── src/                        # Lógica de negocio (montado en containers)
│   ├── ingestion/
│   │   └── ingest_landing.py   # ✅ Validación y copia de CSVs
│   ├── transform/
│   │   ├── build_raw.py        # ✅ Landing → Raw (Parquet)
│   │   ├── build_dimensions.py # Construcción de dimensiones
│   │   └── build_facts.py      # Tabla de hechos
│   ├── metrics/                # Cálculo de KPIs
│   └── utils/
│       ├── spark_session.py    # ✅ Factory de sesiones Spark
│       └── paths.py            # ✅ Gestión de rutas del data lake
│
├── notebooks/
│   ├── 01_exploracion.ipynb    # Análisis exploratorio
│   ├── 02_modelo_datos.ipynb   # Diseño star schema
│   └── 03_dashboard.ipynb      # Visualizaciones finales
│
├── data_sipc/                  # Data Lake (gitignored)
└── docker-compose.yaml
```

✅ = Implementado | 🔲 = Pendiente

## 📊 Pipeline ETL

### Flujo de datos

```
📥 Landing Zone (CSV)
    ↓ ingest_landing.py (validación + copia)

🧹 Raw Zone (Parquet limpio)
    ↓ build_raw.py (limpieza + tipado)

📐 Refined Zone (Star Schema)
    ↓ build_dimensions.py
    │   → dim_tiempo, dim_producto, dim_establecimiento, dim_ubicacion
    ↓ build_facts.py
    │   → fact_precios

📈 Exports Dashboard
    ↓ metrics/* (KPIs)
    │   → precio_promedio, dispersion_index, canasta_basica, ranking
```

### Modelo de Datos (Star Schema)

**Dimensiones:**

- `dim_tiempo`: fecha, año, mes, día, trimestre
- `dim_producto`: producto_id, nombre, categoría, subcategoría, marca
- `dim_establecimiento`: establecimiento_id, nombre, cadena
- `dim_ubicacion`: ubicacion_id, departamento, ciudad, dirección

**Hechos:**

- `fact_precios`: precio, fecha_id, producto_id, establecimiento_id, ubicacion_id, unidad

## 🔧 Desarrollo

### Estructura del código ETL

El pipeline ETL está organizado en módulos reutilizables en `src/`:

**Ingesta (`src/ingestion/`):**
- `ingest_landing.py`: Valida y copia archivos CSV a la landing zone
  - Verifica estructura de columnas esperadas
  - Maneja encoding ISO-8859-1 y delimitador `;`
  - Genera metadata de ingesta

**Transformaciones (`src/transform/`):**
- `build_raw.py`: Procesa CSVs a Parquet con limpieza y tipado
  - Convierte fechas, normaliza columnas
  - Filtra registros inválidos
  - Particiona por fecha para optimizar consultas

- `build_dimensions.py`: Construye las 4 dimensiones del modelo estrella
  - `dim_tiempo`: Atributos temporales derivados de fechas
  - `dim_producto`: Catálogo completo de productos
  - `dim_establecimiento`: Información de comercios
  - `dim_ubicacion`: Datos geográficos

- `build_facts.py`: Crea tabla de hechos con claves foráneas
  - Joins con todas las dimensiones
  - Mantiene medidas (precio, unidad)
  - Particionado por fecha

**Métricas (`src/metrics/`):**
- `simple_metrics.py`: Calcula las 6 métricas de negocio
  1. Precio promedio por producto y período
  2. Precios mínimos y máximos
  3. Índice de dispersión de precios
  4. Costo de canasta básica por supermercado
  5. Ranking de supermercados por costo
  6. Variación porcentual mensual

**Utilidades (`src/utils/`):**
- `spark_session.py`: Factory de sesiones Spark (modo local)
- `paths.py`: Gestión centralizada de rutas del Data Lake

### Editar transformaciones ETL

Los módulos en `src/` están montados como volumen en el contenedor de Airflow, por lo que los cambios se reflejan inmediatamente sin necesidad de reconstruir la imagen.

```bash
# Editar archivo
vim src/transform/build_dimensions.py

# Probar localmente con PySpark
cd /ruta/proyecto
python -c "from src.transform.build_dimensions import build_dimensions; build_dimensions()"

# O ejecutar desde Airflow UI
# (activa manualmente el DAG monitor_precios_sipc_etl)
```

### Ejecutar pipeline completo

```bash
# Asegurar que los CSV están en landing/
ls -la data_sipc/landing/*.csv

# Desde Airflow UI:
# 1. Ir a http://localhost:8080
# 2. Buscar DAG 'monitor_precios_sipc_etl'
# 3. Activar toggle a ON
# 4. Trigger DAG manualmente con botón ▶️

# Verificar outputs
ls -la data_sipc/raw/
ls -la data_sipc/refined/
ls -la data_sipc/exports_dashboard/
```

### Estructura de datos generada

**Raw zone** (`data_sipc/raw/`):
- `precios/`: Precios limpios particionados por fecha
- `productos/`: Catálogo de productos
- `establecimientos/`: Información de comercios

**Refined zone** (`data_sipc/refined/`):
- `dim_tiempo/`: Dimensión temporal
- `dim_producto/`: Dimensión de productos
- `dim_establecimiento/`: Dimensión de establecimientos
- `dim_ubicacion/`: Dimensión geográfica
- `fact_precios/`: Tabla de hechos (particionada por fecha)

**Exports** (`data_sipc/exports_dashboard/`):
- `precio_promedio.parquet`
- `min_max_precios.parquet`
- `dispersion_precios.parquet`
- `canasta_basica.parquet`
- `ranking_supermercados.parquet`
- `variacion_mensual.parquet`

### Leer resultados en notebooks

Ver la **guía completa de notebooks** en [`notebooks/README.md`](notebooks/README.md).

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("Dashboard").getOrCreate()

# Leer métricas
precio_prom = spark.read.parquet("../data_sipc/exports_dashboard/precio_promedio.parquet")
precio_prom.show()

# Análisis con Pandas
df_pandas = precio_prom.toPandas()
```

## 📓 Jupyter Notebooks

El proyecto incluye 3 notebooks interactivos para análisis y visualización:

### 1. `01_exploracion.ipynb` - Análisis Exploratorio

**Propósito:** Entender la estructura y calidad de los datos raw

**Contenido:**
- Carga de datos desde zona RAW (Parquet)
- Estadísticas descriptivas (20M+ registros de precios)
- Distribuciones temporales y geográficas
- Análisis de calidad (nulos, duplicados, outliers)
- Verificación de integridad referencial
- Visualizaciones de precios por categoría

**Duración:** ~10-15 minutos

### 2. `02_modelo_datos.ipynb` - Star Schema

**Propósito:** Documentar y validar el modelo dimensional

**Contenido:**
- Explicación del Star Schema implementado
- Descripción de las 4 dimensiones
- Tabla de hechos con 20M+ observaciones
- Validación de integridad referencial (100%)
- Ejemplos de consultas analíticas multidimensionales
- Benchmark de performance

**Duración:** ~15-20 minutos

### 3. `03_dashboard.ipynb` - Dashboard de Métricas

**Propósito:** Visualizar y analizar las 6 métricas principales

**Contenido:**
- **Métrica 1:** Precio promedio - Evolución temporal
- **Métrica 2:** Variación mensual - Histogramas y tendencias
- **Métrica 3:** Min/Max precios - Rangos por producto
- **Métrica 4:** Canasta básica - Comparación por supermercado
- **Métrica 5:** Dispersión - Variabilidad de precios
- **Métrica 6:** Ranking - Supermercados ordenados por costo
- Análisis integrado con correlaciones
- Dashboard consolidado (4 paneles)
- Conclusiones y recomendaciones

**Duración:** ~20-30 minutos

### Cómo Ejecutar los Notebooks

#### Paso 1: Ejecutar el Pipeline ETL

**Prerequisito:** Los notebooks requieren que el pipeline haya generado los datos primero.

```bash
# 1. Asegurar que los CSV están en landing/
ls -la data_sipc/landing/*.csv

# 2. Iniciar servicios
docker-compose up -d

# 3. Ejecutar DAG en Airflow
# Ir a http://localhost:8080
# Activar y ejecutar 'monitor_precios_sipc_etl'

# 4. Verificar que se generaron los datos
ls -la data_sipc/raw/
ls -la data_sipc/refined/
ls -la data_sipc/exports_dashboard/
```

#### Paso 2: Acceder a Jupyter Lab

```bash
# 1. Obtener el token de acceso
docker logs jupyter-spark 2>&1 | grep "token="

# 2. Abrir en navegador
# http://localhost:8888/?token=XXXXXXXXXX
```

#### Paso 3: Ejecutar Notebooks en Orden

```
📓 Orden recomendado:
   01_exploracion.ipynb  →  02_modelo_datos.ipynb  →  03_dashboard.ipynb
```

**Opciones de ejecución:**
- **Celda por celda:** `Shift + Enter`
- **Todo el notebook:** Menu → Run → Run All Cells
- **Hasta una celda:** Menu → Run → Run All Above Selected Cell

#### Verificar Datos Antes de Ejecutar

Los notebooks esperan encontrar datos en estas rutas (relativas desde `notebooks/`):

```python
# Raw zone (para 01_exploracion y 02_modelo_datos)
'../data_sipc/raw/precios.parquet'
'../data_sipc/raw/productos.parquet'
'../data_sipc/raw/establecimientos.parquet'

# Refined zone (para 02_modelo_datos)
'../data_sipc/refined/dim_tiempo.parquet'
'../data_sipc/refined/dim_producto.parquet'
'../data_sipc/refined/dim_establecimiento.parquet'
'../data_sipc/refined/dim_ubicacion.parquet'
'../data_sipc/refined/fact_precios.parquet'

# Exports (para 03_dashboard)
'../data_sipc/exports_dashboard/precio_promedio.parquet'
'../data_sipc/exports_dashboard/variacion_mensual.parquet'
'../data_sipc/exports_dashboard/min_max_precios.parquet'
'../data_sipc/exports_dashboard/canasta_basica.parquet'
'../data_sipc/exports_dashboard/dispersion_precios.parquet'
'../data_sipc/exports_dashboard/ranking_supermercados.parquet'
```

### Solución de Problemas Comunes

#### Error: "FileNotFoundError"

**Causa:** Pipeline ETL no ejecutado o datos incompletos

**Solución:**
```bash
# Ejecutar pipeline completo
docker exec airflow airflow dags trigger monitor_precios_sipc_etl

# Esperar finalización (~6 minutos)
docker exec airflow airflow dags list-runs -d monitor_precios_sipc_etl
```

#### Error: "No module named 'pyspark'"

**Causa:** Ejecutando notebook fuera del contenedor

**Solución:**
- Usar Jupyter Lab dentro del contenedor: http://localhost:8888
- No ejecutar notebooks directamente en el host

#### Kernel muere o se queda sin memoria

**Causa:** Datasets grandes consumiendo mucha RAM

**Solución:**
- Reiniciar kernel: Menu → Kernel → Restart Kernel
- Ejecutar celdas en orden (no todas a la vez)
- Aumentar memoria del contenedor en `docker-compose.yaml`:
  ```yaml
  jupyter:
    deploy:
      resources:
        limits:
          memory: 6G  # Aumentar de 4G a 6G
  ```

#### Visualizaciones no se renderizan

**Causa:** Configuración de matplotlib

**Solución:**
```python
# Añadir al inicio del notebook
%matplotlib inline
import matplotlib.pyplot as plt
plt.rcParams['figure.figsize'] = (14, 6)
```

### Características de los Notebooks

**Visualizaciones incluidas:**
- 📈 Gráficos de líneas (evolución temporal)
- 📊 Histogramas (distribuciones)
- 📦 Boxplots (comparaciones estadísticas)
- 🎯 Scatter plots (correlaciones)
- 🏆 Gráficos de barras (rankings)
- 📉 Dashboards multi-panel (vista consolidada)

**Librerías utilizadas:**
- `pyspark` - Procesamiento de datos
- `pandas` - Manipulación para visualización
- `matplotlib` - Gráficos estáticos
- `seaborn` - Visualizaciones estadísticas mejoradas

**Ventajas del enfoque:**
- ✅ Separación de concerns: ETL en Airflow, análisis en Jupyter
- ✅ Datos pre-procesados para análisis rápido
- ✅ Reproducibilidad: notebooks versionados en git
- ✅ Interactividad: exploración ad-hoc sin reejecutar pipeline
