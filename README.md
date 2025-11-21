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

### Editar transformaciones ETL
