# AI Coding Agent Instructions – Monitor de Precios SIPC

## Project Overview

**Academic Big Data Project** - Universidad Católica del Uruguay (Campus Salto)  
**Course:** Big Data  
**Status:** ✅ COMPLETED (December 2024)

Pipeline ETL con Apache Airflow para analizar datos del SIPC (Sistema de Información de Precios al Consumidor) de Uruguay. Implementa un Data Lake con modelo estrella y calcula 6 indicadores económicos.

## Architecture

### Data Lake Zones (`data_sipc/`)

| Zone | Format | Description |
|------|--------|-------------|
| `landing/` | CSV | Raw files from SIPC (not versioned) |
| `raw/` | Parquet | Cleaned and typed data |
| `refined/` | Parquet | Star schema (dimensions + facts) |
| `exports_dashboard/` | Parquet | Pre-calculated metrics |

### Tech Stack

- **PySpark** (local mode `local[*]`)
- **Apache Airflow 2.9.2** (SequentialExecutor + SQLite)
- **Docker Compose** (services: `airflow`, `jupyter`)
- **Parquet** (columnar storage)

## Project Structure

```
monitor-precios-sipc/
├── README.md                    # Main documentation
├── docker-compose.yaml
├── requirements.txt
├── build_model_quick.sh         # Quick build script
│
├── airflow/dags/
│   └── monitor_precios_dag.py   # Main DAG
│
├── src/
│   ├── ingestion/ingest_landing.py
│   ├── transform/
│   │   ├── build_raw.py
│   │   ├── build_dimensions.py
│   │   └── build_facts.py
│   ├── metrics/simple_metrics.py
│   └── utils/{spark_session,paths}.py
│
├── notebooks/
│   ├── README.md                # Notebooks documentation
│   ├── 01_exploracion.ipynb
│   ├── 02_modelo_datos.ipynb
│   └── 03_dashboard.ipynb
│
├── docs/
│   ├── canasta_basica_cbaen_2024.md
│   ├── NOTEBOOKS_IMPLEMENTATION_SUMMARY.md
│   ├── STATUS_DEC_1_2024.md
│   └── metadata/
│
└── data_sipc/                   # Data Lake (gitignored)
```

## Star Schema Model

**Dimensions:**
- `dim_tiempo`: fecha_id (PK), fecha, anio, mes, dia, trimestre
- `dim_producto`: producto_id (PK), nombre, categoria, subcategoria, marca
- `dim_establecimiento`: establecimiento_id (PK), nombre, cadena
- `dim_ubicacion`: ubicacion_id (PK), departamento, ciudad, direccion

**Fact Table:**
- `fact_precios`: fecha_id (FK), producto_id (FK), establecimiento_id (FK), ubicacion_id (FK), precio, oferta

## 6 Business Metrics

1. **Precio promedio por producto** → `precio_promedio.parquet`
2. **Variación porcentual mensual** → `variacion_mensual.parquet`
3. **Precio mínimo y máximo** → `min_max_precios.parquet`
4. **Costo de canasta básica** → `canasta_basica.parquet` (62 productos CBAEN 2024)
5. **Índice de dispersión** → `dispersion_precios.parquet`
6. **Ranking de supermercados** → `ranking_supermercados.parquet`

## Quick Commands

```bash
# Start environment
docker-compose up -d

# Access points
# - Airflow: http://localhost:8080
# - Jupyter: http://localhost:8888

# Trigger ETL pipeline
docker exec airflow airflow dags trigger monitor_precios_sipc_etl

# Check DAG status
docker exec airflow airflow dags list-runs -d monitor_precios_sipc_etl

# Stop environment
docker-compose down
```

## Development Guidelines

### Module Organization

- `src/ingestion/`: Data acquisition
- `src/transform/`: PySpark ETL jobs
- `src/metrics/`: Business logic for KPIs
- `src/utils/`: Shared utilities

### Naming Conventions

- DAG file: `monitor_precios_dag.py`
- Transform scripts: `build_*.py`
- Dimension tables: `dim_*`
- Fact tables: `fact_*`

### Path Management

- **Airflow container**: `/opt/airflow/data_sipc/`
- **Notebooks**: `../data_sipc/` (relative)
- Use `src/utils/paths.py` for centralized paths

### Known Solutions

**Permission issues in Docker volumes:**
- Use `_clean_output_dir()` function before Spark writes
- Pattern: `shutil.rmtree()` + write without `mode("overwrite")`

**CSV encoding:**
- Files use ISO-8859-1 encoding and `;` delimiter

## Documentation Structure

| File | Location | Purpose |
|------|----------|---------|
| `README.md` | Root | Main documentation with usage guide |
| `notebooks/README.md` | notebooks/ | Detailed notebook execution guide |
| `canasta_basica_cbaen_2024.md` | docs/ | CBAEN 2024 basket definition |
| `NOTEBOOKS_IMPLEMENTATION_SUMMARY.md` | docs/ | Implementation details |
| `STATUS_DEC_1_2024.md` | docs/ | Project status snapshot |
