# Monitor de Precios SIPC

**Proyecto del curso Big Data** – Universidad Católica del Uruguay (Campus Salto)

Pipeline ETL orquestado con **Apache Airflow** para analizar datos de precios del **SIPC** (Sistema de Información de Precios al Consumidor) de Uruguay. Construye un Data Lake con modelo dimensional (Star Schema) y calcula indicadores económicos clave.

---

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Arquitectura](#-arquitectura)
- [Requisitos](#-requisitos)
- [Instalación y Uso](#-instalación-y-uso)
- [Pipeline ETL](#-pipeline-etl)
- [Modelo de Datos](#-modelo-de-datos)
- [Métricas de Negocio](#-métricas-de-negocio)
- [Notebooks](#-notebooks)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Desarrollo](#-desarrollo)
- [Solución de Problemas](#-solución-de-problemas)
- [Referencias](#-referencias)

---

## ✨ Características

- **Data Lake** con 4 zonas: Landing → Raw → Refined → Exports
- **Star Schema** con 4 dimensiones y 1 tabla de hechos (20M+ registros)
- **6 métricas de negocio** pre-calculadas para análisis
- **Orquestación** automatizada con Apache Airflow
- **Visualizaciones** interactivas en Jupyter Notebooks
- **Dockerizado** para reproducibilidad

---

## 🏗 Arquitectura

### Data Lake (filesystem local)

```
data_sipc/
├── landing/           # CSV originales del SIPC
├── raw/               # Parquet limpio y tipado
├── refined/           # Modelo estrella (dimensiones + hechos)
└── exports_dashboard/ # Métricas para visualización
```

### Stack Tecnológico

| Componente | Tecnología | Descripción |
|------------|------------|-------------|
| ETL | PySpark | Transformaciones en modo `local[*]` |
| Orquestación | Airflow 2.9.2 | SequentialExecutor + SQLite |
| Contenedores | Docker Compose | Servicios `airflow` y `jupyter` |
| Almacenamiento | Parquet | Formato columnar optimizado |

---

## 📦 Requisitos

### Sistema

- **Docker** 20.10+
- **Docker Compose** 2.0+
- **RAM** 4GB mínimo (6GB recomendado)
- **Disco** 5GB disponible

### Datos

Archivos CSV del SIPC (descargar de [Catálogo de Datos Abiertos](https://catalogodatos.gub.uy/)):
- `precios.csv` (~20M+ registros)
- `productos.csv` (~379 productos)
- `establecimientos.csv` (~852 establecimientos)

---

## 🚀 Instalación y Uso

### 1. Clonar el repositorio

```bash
git clone https://github.com/clara-s-n/monitor-precios-sipc.git
cd monitor-precios-sipc
```

### 2. Preparar datos de entrada

Colocar los archivos CSV del SIPC en la carpeta `data_sipc/landing/`:

```
data_sipc/landing/
├── precios.csv
├── productos.csv
└── establecimientos.csv
```

### 3. Iniciar los servicios

```bash
docker-compose up -d
```

### 4. Verificar estado

```bash
docker-compose ps
```

Servicios disponibles:

| Servicio | URL | Descripción |
|----------|-----|-------------|
| Airflow UI | http://localhost:8080 | Interfaz de orquestación |
| Jupyter Lab | http://localhost:8888 | Notebooks de análisis |

### 5. Ejecutar el pipeline ETL

1. Abrir **Airflow UI** en http://localhost:8080
2. Localizar el DAG `monitor_precios_sipc_etl`
3. Activar el toggle (ON)
4. Hacer clic en ▶️ **Trigger DAG**

⏱️ **Tiempo de ejecución:** ~6 minutos

### 6. Verificar resultados

```bash
# Verificar datos generados
ls -la data_sipc/raw/
ls -la data_sipc/refined/
ls -la data_sipc/exports_dashboard/
```

### 7. Explorar notebooks

1. Obtener token de Jupyter:
   ```bash
   docker logs jupyter-spark 2>&1 | grep "token="
   ```
2. Abrir http://localhost:8888 con el token
3. Navegar a `notebooks/` y ejecutar en orden

### 8. Detener servicios

```bash
docker-compose down
```

---

## 🔄 Pipeline ETL

### Flujo de datos

```
📥 Landing Zone (CSV)
    ↓ ingest_landing.py

🧹 Raw Zone (Parquet)
    ↓ build_raw.py

📐 Refined Zone (Star Schema)
    ↓ build_dimensions.py → dim_tiempo, dim_producto, 
    │                       dim_establecimiento, dim_ubicacion
    ↓ build_facts.py → fact_precios

📊 Exports Dashboard
    ↓ simple_metrics.py → 6 métricas pre-calculadas
```

### Tareas del DAG

| Tarea | Descripción | Duración aprox. |
|-------|-------------|-----------------|
| `ingest_landing` | Validar y copiar CSVs | 30s |
| `build_raw` | Limpiar y tipar datos | 2min |
| `build_dimensions` | Crear 4 dimensiones | 1min |
| `build_facts` | Crear tabla de hechos | 2min |
| `calculate_metrics` | Calcular 6 métricas | 30s |

---

## 📐 Modelo de Datos

### Star Schema

```
                    ┌─────────────────┐
                    │   dim_tiempo    │
                    │─────────────────│
                    │ fecha_id (PK)   │
                    │ fecha, anio     │
                    │ mes, dia        │
                    │ trimestre       │
                    └────────┬────────┘
                             │
┌─────────────────┐          │          ┌─────────────────────┐
│  dim_producto   │          │          │ dim_establecimiento │
│─────────────────│          │          │─────────────────────│
│ producto_id(PK) │          │          │ establec_id (PK)    │
│ nombre, marca   │          │          │ nombre, cadena      │
│ categoria       │          │          │ razon_social        │
└────────┬────────┘          │          └──────────┬──────────┘
         │                   │                     │
         │         ┌─────────┴─────────┐           │
         │         │   fact_precios    │           │
         └─────────┤───────────────────├───────────┘
                   │ fecha_id (FK)     │
                   │ producto_id (FK)  │
                   │ establec_id (FK)  │
                   │ ubicacion_id (FK) │
                   │ precio, oferta    │
                   └─────────┬─────────┘
                             │
                    ┌────────┴────────┐
                    │  dim_ubicacion  │
                    │─────────────────│
                    │ ubicacion_id(PK)│
                    │ departamento    │
                    │ ciudad, barrio  │
                    └─────────────────┘
```

### Estadísticas del modelo

| Tabla | Registros | Descripción |
|-------|-----------|-------------|
| `dim_tiempo` | ~365 | Atributos temporales |
| `dim_producto` | 379 | Catálogo de productos |
| `dim_establecimiento` | 852 | Puntos de venta |
| `dim_ubicacion` | 852 | Información geográfica |
| `fact_precios` | 20M+ | Observaciones de precios |

---

## 📊 Métricas de Negocio

El proyecto calcula **6 métricas principales**:

### 1. Precio Promedio por Producto
Promedio del precio agrupado por producto, año y mes.

### 2. Variación Porcentual Mensual
Cambio porcentual del precio respecto al mes anterior:

```
Variación = (Precio actual - Precio anterior) / Precio anterior × 100
```

### 3. Precio Mínimo y Máximo
Rango de precios por producto y período.

### 4. Costo de Canasta Básica
Suma del costo de 62 productos de la canasta CBAEN 2024 por supermercado.

### 5. Índice de Dispersión
Variabilidad de precios entre establecimientos:

```
Dispersión = (Precio máx - Precio mín) / Precio promedio
```

### 6. Ranking de Supermercados
Ordenamiento por costo total de canasta básica.

### Archivos de salida

```
data_sipc/exports_dashboard/
├── precio_promedio.parquet
├── variacion_mensual.parquet
├── min_max_precios.parquet
├── canasta_basica.parquet
├── dispersion_precios.parquet
└── ranking_supermercados.parquet
```

---

## 📓 Notebooks

El proyecto incluye 3 notebooks interactivos:

| Notebook | Descripción | Duración |
|----------|-------------|----------|
| `01_exploracion.ipynb` | Análisis exploratorio de datos raw | 10-15 min |
| `02_modelo_datos.ipynb` | Documentación del Star Schema | 15-20 min |
| `03_dashboard.ipynb` | Dashboard con 6 métricas y visualizaciones | 20-30 min |

### Orden de ejecución

```
01_exploracion → 02_modelo_datos → 03_dashboard
```

### Prerequisito

Los notebooks requieren que el pipeline ETL haya sido ejecutado previamente.

Ver documentación detallada en [`notebooks/README.md`](notebooks/README.md).

---

## 📂 Estructura del Proyecto

```
monitor-precios-sipc/
├── README.md                 # Este archivo
├── docker-compose.yaml       # Configuración de servicios
├── requirements.txt          # Dependencias Python
│
├── airflow/
│   ├── Dockerfile            # Imagen custom con PySpark
│   ├── entrypoint.sh
│   ├── dags/
│   │   └── monitor_precios_dag.py  # DAG principal
│   └── logs/
│
├── src/                      # Código fuente
│   ├── ingestion/
│   │   └── ingest_landing.py
│   ├── transform/
│   │   ├── build_raw.py
│   │   ├── build_dimensions.py
│   │   └── build_facts.py
│   ├── metrics/
│   │   └── simple_metrics.py
│   └── utils/
│       ├── spark_session.py
│       └── paths.py
│
├── notebooks/
│   ├── README.md
│   ├── 01_exploracion.ipynb
│   ├── 02_modelo_datos.ipynb
│   └── 03_dashboard.ipynb
│
├── docs/
│   ├── canasta_basica_cbaen_2024.md
│   └── metadata/
│
└── data_sipc/                # Data Lake (no versionado)
    ├── landing/
    ├── raw/
    ├── refined/
    └── exports_dashboard/
```

---

## 🔧 Desarrollo

### Modificar transformaciones

Los módulos en `src/` están montados como volumen, los cambios se reflejan inmediatamente:

```bash
# Editar transformación
vim src/transform/build_dimensions.py

# Ejecutar DAG para probar cambios
# (desde Airflow UI o línea de comandos)
```

### Comandos útiles

```bash
# Ver logs de Airflow
docker logs airflow --tail 100

# Acceder al contenedor
docker exec -it airflow bash

# Ejecutar DAG manualmente
docker exec airflow airflow dags trigger monitor_precios_sipc_etl

# Ver estado de ejecuciones
docker exec airflow airflow dags list-runs -d monitor_precios_sipc_etl

# Limpiar datos (reiniciar pipeline)
docker exec airflow rm -rf /opt/airflow/data_sipc/raw/* \
    /opt/airflow/data_sipc/refined/* \
    /opt/airflow/data_sipc/exports_dashboard/*
```

---

## 🔍 Solución de Problemas

### Pipeline falla con "Permission denied"

```bash
# Corregir permisos del volumen
docker exec airflow chmod -R 777 /opt/airflow/data_sipc/
```

### Notebook muestra "FileNotFoundError"

**Causa:** Pipeline ETL no ejecutado.

```bash
# Ejecutar pipeline
docker exec airflow airflow dags trigger monitor_precios_sipc_etl

# Esperar ~6 minutos y verificar
ls -la data_sipc/exports_dashboard/
```

### Kernel de Jupyter muere

**Causa:** Memoria insuficiente.

**Solución:** Aumentar memoria en `docker-compose.yaml`:

```yaml
jupyter:
  deploy:
    resources:
      limits:
        memory: 6G
```

### Token de Jupyter no funciona

```bash
# Obtener nuevo token
docker logs jupyter-spark 2>&1 | grep "token="
```

---

## 📚 Referencias

- **Datos:** [SIPC - Catálogo de Datos Abiertos Uruguay](https://catalogodatos.gub.uy/)
- **Canasta básica:** Informe CBAEN 2024 - Instituto Nacional de Estadística (INE)
- **Metodología:** [Kimball Dimensional Modeling](https://www.kimballgroup.com/)
- **PySpark:** [Apache Spark SQL Guide](https://spark.apache.org/docs/latest/sql-programming-guide.html)

---

## 👥 Autores

Proyecto desarrollado por **Ana Clara Sena**, **Francisco Lima** y **Mateo Rodriguez** para el curso **Big Data** – UCU Campus Salto, Diciembre 2025.

---

## 📄 Licencia

Este proyecto es de uso académico.
