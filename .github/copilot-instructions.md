# AI Coding Agent Instructions – Monitor de Precios SIPC

## Project Overview

Big Data academic project (UCU Salto) that builds a **Data Lake + ETL pipeline** orchestrated with **Apache Airflow** to analyze consumer price data from Uruguay's SIPC (Sistema de Información de Precios al Consumidor). The goal is to create a star schema model and calculate metrics like price dispersion indexes and "canasta básica" costs by region/store.

## Architecture & Key Concepts

### Data Lake Zones (local filesystem under `data_sipc/`)

- `landing/` – Raw CSV files from Catálogo de Datos Abiertos (NOT versioned in git)
- `raw/` – Cleaned and typed data (PySpark processing)
- `refined/` – Analytical model (star schema: dimensions + fact tables)
- `exports_dashboard/` – Final datasets for Jupyter dashboard

### Tech Stack

- **PySpark (local mode)**: All ETL transformations run on single-node Spark (`spark.master("local[*]")`)
- **Apache Airflow**: Orchestration via Docker container, uses SequentialExecutor + SQLite
- **Docker Compose**: Two services – `airflow` and `jupyter` (pyspark-notebook)
- **No distributed cluster**: This is intentional per project requirements

## Development Workflows

### Starting the Environment

```bash
# Start Airflow + Jupyter
docker-compose up -d

# Access points:
# - Airflow UI: http://localhost:8080 (no auth)
# - Jupyter Lab: http://localhost:8888
```

### DAG Development Pattern

1. Airflow DAGs live in `airflow/dags/monitor_precios_dag.py`
2. DAG imports Python modules from `src/` (mounted as volume in container)
3. Data processing logic goes in `src/transform/` or `src/ingestion/`, NOT in DAG file
4. DAG file should only define task orchestration (PythonOperator calls)

### Spark Session Pattern

- Reusable Spark session factory in `src/utils/spark_session.py`
- Always use `spark.master("local[*]")` – no cluster deployment
- Common config: SQLite support for Airflow metadata, Parquet optimization

### Path Management

- Centralize all data paths in `src/utils/paths.py`
- Use absolute paths when running inside Airflow container (`/opt/airflow/data_sipc`)
- Use relative paths when running notebooks (`./data_sipc` or `../data_sipc`)

## ETL Pipeline Structure

### Expected Flow (to be implemented)

```
ingestion/ingest_landing.py
  ↓ (copy/validate CSV files to landing/)
transform/build_raw.py
  ↓ (clean data types, handle nulls → raw/ as Parquet)
transform/build_dimensions.py
  ↓ (create dim_tiempo, dim_producto, dim_establecimiento, dim_ubicacion)
transform/build_facts.py
  ↓ (create fact_precios with FK references)
metrics/*
  ↓ (calculate dispersion index, canasta básica costs → exports_dashboard/)
```

### Data Model (Star Schema in `refined/`)

- **Dimensions**: `dim_tiempo`, `dim_producto`, `dim_establecimiento`, `dim_ubicacion`
- **Fact**: `fact_precios` (precio, fecha_id, producto_id, establecimiento_id, ubicacion_id)
- File format: Parquet (partitioned by fecha for performance)

## Project-Specific Conventions

### Module Organization

- `src/ingestion/`: Data acquisition and landing zone preparation
- `src/transform/`: PySpark ETL jobs (raw → refined transformations)
- `src/metrics/`: Business logic for KPIs (dispersion index, canasta básica)
- `src/utils/`: Shared utilities (Spark session, path helpers)

### Naming Patterns

- DAG file: `monitor_precios_dag.py` (singular, descriptive)
- Transform scripts: `build_*.py` (verb prefix: build, create, compute)
- Dimension tables: `dim_*` (e.g., `dim_tiempo`, `dim_producto`)
- Fact tables: `fact_*` (e.g., `fact_precios`)

### Airflow Container Mounts

```yaml
volumes:
  - ./airflow/dags:/opt/airflow/dags
  - ./data_sipc:/opt/airflow/data_sipc # ← data lake access
  - ./src:/opt/airflow/src # ← Python modules
```

⚠️ Code changes in `src/` are immediately available to DAGs (no rebuild needed)

### Jupyter Notebooks

- `01_exploracion.ipynb`: Initial data exploration (understand SIPC CSV structure)
- `02_modelo_datos.ipynb`: Design and validate star schema model
- `03_dashboard.ipynb`: Final visualizations and metrics dashboard

Notebooks import from `../src/` and access `../data_sipc/` (parent directory)

## Dependencies & Installation

### Container Images

- Airflow: `apache/airflow:2.9.2` + pyspark, pandas
- Jupyter: `jupyter/pyspark-notebook:latest` (includes Spark pre-configured)

### Python Packages (see `requirements.txt`)

- `pyspark`: DataFrame API and SQL engine
- `pandas`: Data manipulation for dashboard exports
- `pyarrow`: Fast Parquet I/O
- `matplotlib`: Visualization in notebooks

## Important Constraints

1. **No external databases**: All storage is filesystem-based (Parquet files)
2. **No authentication**: Airflow webserver auth disabled for simplicity
3. **Local execution only**: Spark runs in `local[*]` mode, not on YARN/K8s
4. **SQLite for Airflow metadata**: Not PostgreSQL (acceptable for academic project)

## Common Tasks

### Add a new transformation step

1. Create module in `src/transform/my_transform.py`
2. Implement function that takes SparkSession, reads from `raw/`, writes to `refined/`
3. Add PythonOperator task in `monitor_precios_dag.py`
4. Define task dependencies with `>>` operator

### Debug ETL failures

1. Check Airflow logs: `./airflow/logs/<dag_id>/<task_id>/<timestamp>/`
2. Run transformation script directly in Jupyter to test
3. Validate Parquet schema with `spark.read.parquet(...).printSchema()`

### Add new metrics

1. Create module in `src/metrics/` (e.g., `dispersion_index.py`)
2. Read from `refined/` fact and dimension tables
3. Aggregate using PySpark SQL or DataFrame API
4. Export results to `exports_dashboard/` as CSV or Parquet

## Business Metrics (Required for Dashboard)

The project must calculate these 6 key metrics from the SIPC data:

1. **Precio promedio por producto**: Average price grouped by product across all stores/dates
2. **Variación porcentual diaria/mensual**: Price change percentage comparing current vs. previous period
3. **Precio mínimo y máximo**: Min/max prices per product (identify cheapest/most expensive stores)
4. **Costo de canasta básica por supermercado**: Total cost of a defined basket of essential products per store
5. **Índice de dispersión de precios**: Formula: `(precio_max - precio_min) / precio_promedio`
   - Measures price inequality across establishments for same product
6. **Ranking de supermercados según costo total**: Stores ranked by total basket cost (lowest to highest)

All metrics should be implemented in `src/metrics/` and exported to `exports_dashboard/` for visualization.

## References

- SIPC Open Data: https://catalogodatos.gub.uy/
- Star Schema pattern: Kimball methodology (fact table + dimension tables)
- Airflow best practices: Keep DAGs declarative, logic in Python modules
