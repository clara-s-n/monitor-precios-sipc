# AI Coding Agent Instructions – Monitor de Precios SIPC

## Project Overview

**Academic Big Data Project** - Universidad Católica del Uruguay (Campus Salto)  
**Course:** Big Data

This project builds a **Data Lake + ETL pipeline** orchestrated with **Apache Airflow** to analyze consumer price data from Uruguay's SIPC (Sistema de Información de Precios al Consumidor). The objective is to create a dimensional model (star schema) and calculate key economic indicators including price dispersion indexes, basket costs by retailer, and temporal price variations.

### Project Goals

1. **ETL Pipeline**: Ingest, transform, and model SIPC data using PySpark
2. **Dimensional Model**: Implement star schema with fact and dimension tables
3. **Business Metrics**: Calculate 6 key indicators for price analysis
4. **Orchestration**: Automate workflow with Apache Airflow
5. **Jupyter Notebooks**: Complete exploratory analysis and visualizations for metrics

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
- **Parquet**: Columnar storage format for all processed data
- **No distributed cluster**: Intentional per project requirements (local mode only)

### Data Sources

- **Primary**: SIPC CSV files from https://catalogodatos.gub.uy/
  - `precios.csv`: ~20M+ price observations (fecha, producto_id, establecimiento_id, precio)
  - `productos.csv`: ~379 product catalog entries
  - `establecimientos.csv`: ~852 retail locations
- **Secondary**: CBAEN 2024 basket definition (docs/canasta_basica_cbaen_2024.md)

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

### Current Implementation Status ✅

```
✅ ingestion/ingest_landing.py
  ↓ (validates and copies CSV files to landing/)
✅ transform/build_raw.py
  ↓ (clean data types, handle nulls → raw/ as Parquet)
  ↓ Processes 20M+ price records, 379 products, 852 establishments
✅ transform/build_dimensions.py
  ↓ (creates dim_tiempo, dim_producto, dim_establecimiento, dim_ubicacion)
✅ transform/build_facts.py
  ↓ (creates fact_precios with FK references to dimensions)
✅ metrics/simple_metrics.py
  ↓ (calculates 6 core metrics → exports_dashboard/)
```

**Pipeline Execution Time**: ~6 minutes end-to-end on local machine

### Data Model (Star Schema in `refined/`)

**Implemented Dimensions:**
- ✅ `dim_tiempo`: fecha_id (PK), fecha, anio, mes, dia, trimestre, dia_semana, semana_anio, nombre_mes, nombre_dia
- ✅ `dim_producto`: producto_id (PK), nombre_completo, nombre, categoria, subcategoria, marca, especificacion
- ✅ `dim_establecimiento`: establecimiento_id (PK), nombre, razon_social, cadena, cadena_normalizada
- ✅ `dim_ubicacion`: ubicacion_id (PK), establecimiento_id, departamento, ciudad, direccion, barrio

**Implemented Fact Table:**
- ✅ `fact_precios`: fecha_id (FK), producto_id (FK), establecimiento_id (FK), ubicacion_id (FK), precio, oferta

File format: Parquet (non-partitioned due to permissions issues with massive partitioning)

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

### Implemented Metrics ✅

All 6 required metrics are implemented in `src/metrics/simple_metrics.py` and exported to `exports_dashboard/`:

1. ✅ **Precio promedio por producto**: Average price grouped by product/year/month
   - Output: `precio_promedio.parquet`
2. ✅ **Variación porcentual mensual**: Price change % comparing current vs. previous month
   - Output: `variacion_mensual.parquet`
3. ✅ **Precio mínimo y máximo**: Min/max prices per product/period
   - Output: `min_max_precios.parquet`
4. ✅ **Costo de canasta básica por supermercado**: Based on CBAEN 2024 basket (80+ products)
   - Output: `canasta_basica.parquet`
5. ✅ **Índice de dispersión de precios**: `(precio_max - precio_min) / precio_promedio`
   - Output: `dispersion_precios.parquet`
6. ✅ **Ranking de supermercados**: Stores ranked by total basket cost
   - Output: `ranking_supermercados.parquet`

### Known Technical Solutions

**Permission Handling in Spark Writes:**
- Issue: `mode("overwrite")` fails with "Mkdirs failed" errors due to Docker volume permissions
- Solution: Manual directory cleanup via `_clean_output_dir()` function before writing
- Implementation: Added to `build_raw.py`, `build_dimensions.py`, `build_facts.py`, `simple_metrics.py`
- Pattern: Use `shutil.rmtree()` + Hadoop FileSystem cleanup, then write without `mode("overwrite")`

## References

- SIPC Open Data: https://catalogodatos.gub.uy/
- Star Schema pattern: Kimball methodology (fact table + dimension tables)
- Airflow best practices: Keep DAGs declarative, logic in Python modules

---

## Work Plan and Pending Tasks

### ✅ Completed (as of December 1, 2024)

**Infrastructure & Setup:**
- ✅ Docker Compose environment with Airflow + Jupyter
- ✅ Data Lake directory structure (landing, raw, refined, exports_dashboard)
- ✅ Spark session utilities and path management
- ✅ CSV data ingestion (20M+ records, 379 products, 852 establishments)

**ETL Pipeline:**
- ✅ `build_raw.py`: Clean and type CSV data → Parquet (raw zone)
- ✅ `build_dimensions.py`: Create 4 dimensional tables
- ✅ `build_facts.py`: Build fact table with FK relationships
- ✅ `simple_metrics.py`: Calculate all 6 required business metrics
- ✅ Airflow DAG orchestration (end-to-end pipeline working)

**Jupyter Notebooks:**
- ✅ `01_exploracion.ipynb`: Complete exploratory data analysis
- ✅ `02_modelo_datos.ipynb`: Star schema documentation and validation
- ✅ `03_dashboard.ipynb`: All 6 metrics with visualizations, analysis, and conclusions

**Technical Fixes:**
- ✅ Resolved Spark write permission issues in Docker volumes
- ✅ CSV delimiter and encoding corrections
- ✅ Removed partitioning strategy to avoid filesystem conflicts

### 🔄 Current Focus (December 1-2, 2024)

**DEADLINE: December 2, 2024**

**Priority Tasks:**
- [x] Complete all 3 Jupyter notebooks with 6 metrics
- [x] Ensure pipeline runs successfully end-to-end
- [ ] Test notebooks execution from clean state
- [ ] Final validation of all metrics calculations
- [ ] Code cleanup and commenting

**Optional Enhancements (if time permits):**
- [ ] Add data quality checks to Airflow DAG
- [ ] Improve README with usage examples
- [ ] Add docstrings to key functions
- [ ] Create simple validation tests

**Out of Scope for Current Iteration:**
- Technical report (not required for Dec 2 deadline)
- Presentation slides (not required for Dec 2 deadline)
- Advanced visualizations beyond current notebooks
- Extensive documentation beyond README

### 🎯 Deliverables Checklist

**Required for December 2, 2024:**
- [x] **Source Code**: Complete ETL pipeline + notebooks
- [x] **ETL Pipeline**: Functioning Airflow DAG with all transformations
- [x] **Star Schema**: Dimensional model fully implemented
- [x] **6 Metrics**: All business indicators calculated and exported
- [x] **3 Notebooks**: Exploration, model documentation, and dashboard
- [ ] **Pipeline Testing**: Verify end-to-end execution
- [ ] **README**: Usage instructions for running the project

**Quality Standards (Current Iteration):**
- [x] Pipeline runs successfully end-to-end without manual intervention
- [x] All 6 metrics generate correct outputs
- [x] Notebooks execute without errors
- [ ] Basic code documentation (comments on complex logic)
- [ ] README with clear setup and usage instructions

### 📊 Project Metrics & Success Criteria

**Technical Success Criteria:**
- ✅ ETL pipeline processes 20M+ records in <10 minutes
- ✅ Star schema correctly models dimensional relationships
**Technical Success Criteria:**
- ✅ ETL pipeline processes 20M+ records in <10 minutes
- ✅ Star schema correctly models dimensional relationships
- ✅ All 6 business metrics calculate without errors
- ✅ Airflow orchestration executes all tasks successfully
- ✅ Notebooks generate visualizations without errors
- [ ] Pipeline can be executed from clean state
- [ ] All components documented in README
**Identified Risks:**
1. **Data Quality Issues**: Missing values, inconsistent formats
   - Mitigation: Comprehensive validation in raw zone transformation
2. **Performance Bottlenecks**: Large dataset processing time
   - Mitigation: Already optimized (6-min runtime), use Parquet compression
3. **Technical Complexity**: Airflow/Spark integration challenges
   - Mitigation: Working pipeline achieved, document all solutions
### 📅 Timeline for Dec 2 Deadline

**December 1 (Today):**
- ✅ Complete all 3 notebooks with 6 metrics
- ✅ Verify pipeline execution
- [ ] Test from clean environment
- [ ] Update README with usage instructions

**December 2 (Deadline):**
- [ ] Final testing and validation
- [ ] Code cleanup
- [ ] Submission preparation
# Stop environment
docker-compose down

# Rebuild after code changes (if needed)
docker-compose up -d --build

# View Airflow logs
docker logs airflow --tail 100

# Access Airflow container
docker exec -it airflow bash

# Clean data directories (reset pipeline)
docker exec airflow rm -rf /opt/airflow/data_sipc/raw/* /opt/airflow/data_sipc/refined/* /opt/airflow/data_sipc/exports_dashboard/*

# Fix permissions (if needed)
docker exec airflow chmod -R 777 /opt/airflow/data_sipc/

# Trigger DAG manually
docker exec airflow airflow dags trigger monitor_precios_sipc_etl

# Check DAG status
docker exec airflow airflow dags list-runs -d monitor_precios_sipc_etl
```
