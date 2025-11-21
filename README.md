# Monitor de Precios SIPC – Obligatorio Big Data

Proyecto del curso **Big Data** (UCU – Salto) que construye un **Data Lake** y un **pipeline ETL orquestado con Apache Airflow** para analizar los datos de precios del **SIPC** (Sistema de Información de Precios al Consumidor).

El objetivo es:

- Limpiar y unificar las tablas de precios, productos y establecimientos.
- Construir un **modelo tipo estrella** con dimensiones (tiempo, producto, establecimiento, ubicación, etc.) y hechos de precios.
- Calcular métricas de negocio sobre la evolución de precios y la canasta básica (ver sección de métricas).
- Exponer los resultados en un **dashboard en Jupyter**.

---

## 🧩 Métricas implementadas

El proyecto implementa las siguientes **6 métricas principales**:

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

---

## Arquitectura y tecnologías

- **Data Lake (local)** con zonas:
  - `landing/` – CSV originales descargados desde el Catálogo de Datos Abiertos de Uruguay.
  - `raw/` – datos limpios y tipados.
  - `refined/` – modelo analítico (dimensiones + hechos).
- **Orquestación:** [Apache Airflow](https://airflow.apache.org/) (modo local, con SQLite).
- **Procesamiento de datos:**
  - **PySpark** (modo `local`) para las transformaciones principales.
  - **Python + Pandas** para exploración y generación de datasets finales para el dashboard.
- **Visualización:** JupyterLab / Notebooks.
- **Contenedores:** Docker + `docker-compose`.

No se levanta un cluster distribuido real; se usa **Spark en modo local**, tal como permite el obligatorio.

---

## Estructura del repositorio

```text
monitor-precios-sipc/
├─ README.md
├─ .gitignore
├─ requirements.txt
├─ docker-compose.yml
│
├─ airflow/
│  ├─ Dockerfile
│  ├─ dags/
│  │  └─ monitor_precios_dag.py
│  ├─ logs/              # se generan en runtime
│  └─ plugins/
│
├─ src/
│  ├─ __init__.py
│  ├─ config.py          # rutas, parámetros generales del proyecto
│  ├─ utils/
│  │  ├─ __init__.py
│  │  ├─ spark_session.py
│  │  └─ paths.py
│  ├─ ingestion/
│  │  ├─ __init__.py
│  │  ├─ ingest_landing.py      # copiado/preparación de datos en landing
│  ├─ transform/
│  │  ├─ __init__.py
│  │  ├─ build_raw.py
│  │  ├─ build_dimensions.py
│  │  └─ build_facts.py
│  └─ metrics/
│     ├─ __init__.py
│     ├─ dispersion_index.py
│     └─ canasta_basica.py
│
├─ notebooks/
│  ├─ 01_exploracion.ipynb
│  ├─ 02_modelo_datos.ipynb
│  └─ 03_dashboard.ipynb
│
├─ data_sipc/
│  ├─ landing/           # CSV originales del SIPC (NO versionados)
│  ├─ raw/               # datos limpios / tipados
│  ├─ refined/           # modelo analítico (dimensiones + hechos)
│  └─ exports_dashboard/ # datasets finales para dashboard
│
└─ docs/
   ├─ informe_obligatorio.md
   ├─ modelo_datos.md
   ├─ arquitectura_datalake.md
   ├─ decisiones_tecnicas.md
   └─ metadata/
      ├─ metadatos-precios.csv
      ├─ metadatos-establecimientos.csv
      └─ metadatos-productos.csv

```

✅ Requisitos previos
Opción A – Con Docker (recomendada para Airflow + Jupyter)

Docker
y docker compose instalados.

Opción B – Sin Docker (entorno local con venv)

Python 3.10+ (ideal 3.11).

pip instalado.

Para usar PySpark local:

Basta con instalar el paquete pyspark (incluye Spark embebido).

No es obligatorio instalar Spark aparte ni configurar un cluster.

🔧 Configuración del entorno local (venv)

Si querés correr partes del proyecto sin Docker (scripts o notebooks en tu máquina), podés usar un entorno virtual.

1. Crear el entorno virtual

Desde la raíz del proyecto:

Windows (PowerShell)
python -m venv .venv

Si python no apunta a 3.10/3.11, podés usar:

py -3.11 -m venv .venv

Linux / macOS
python3 -m venv .venv

2. Activar el entorno virtual
   Windows (PowerShell)
   .\.venv\Scripts\Activate.ps1

Si aparece un error de ejecución de scripts, puede ser necesario ajustar la ExecutionPolicy una vez:

Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

Linux / macOS
source .venv/bin/activate

Vas a ver el prefijo (.venv) en tu terminal.

3. Instalar dependencias

Con el venv activado:

pip install --upgrade pip
pip install -r requirements.txt

requirements.txt debería incluir al menos:

pyspark
pandas
pyarrow
matplotlib
jupyter

(Se pueden agregar más librerías según las vayan usando.)

4. Ejecutar scripts del proyecto (modo local)

Ejemplos (con venv activado):

python -m src.transform.build_raw
python -m src.transform.build_dimensions
python -m src.transform.build_facts
python -m src.metrics.dispersion_index
python -m src.metrics.canasta_basica

Cada script leerá desde data_sipc/landing o data_sipc/raw y escribirá en data_sipc/raw / data_sipc/refined según la configuración en src/config.py.

5. Usar Jupyter con el venv

Con el venv activado:

jupyter lab

Abrir los notebooks en la carpeta notebooks/.

Seleccionar el kernel correspondiente al venv si es necesario.

🚢 Levantar el proyecto con Docker (Airflow + Jupyter)

1. Clonar el repositorio
   git clone https://github.com/<usuario>/monitor-precios-sipc.git
   cd monitor-precios-sipc

2. Copiar los CSV del SIPC a landing/
   data_sipc/landing/precios_2014.csv
   ...
   data_sipc/landing/productos.csv
   data_sipc/landing/establecimientos.csv

3. Levantar los servicios
   docker compose up -d airflow jupyter

4. Acceder a las interfaces

Airflow: http://localhost:8080

JupyterLab: http://localhost:8888
(la URL con token aparece en los logs del contenedor jupyter-spark).

🌀 Ejecución del pipeline (Airflow)

Abrir Airflow en http://localhost:8080.

Verificar que el DAG monitor_precios_sipc_dag aparezca en la lista.

Activar el DAG (toggle ON).

Ejecutar una corrida manual (“Trigger DAG”).

El DAG debería:

Leer los CSV desde data_sipc/landing y generar datos limpios en data_sipc/raw.

Construir dimensiones y hechos en data_sipc/refined.

Calcular las métricas definidas (promedios, variaciones, min/max, canasta, dispersión, ranking).

Exportar datasets listos para el dashboard a data_sipc/exports_dashboard.

📊 Notebooks y dashboard

En JupyterLab (http://localhost:8888):

notebooks/01_exploracion.ipynb
Exploración inicial y verificación de calidad de datos.

notebooks/02_modelo_datos.ipynb
Construcción y validación del modelo de datos (estrella, métricas, dimensiones).

notebooks/03_dashboard.ipynb
Dashboard final:

Evolución de precios.

Comparaciones entre supermercados.

Costo de canasta básica.

Índice de dispersión y ranking de supermercados.

👥 Equipo

Integrantes: (completar nombres del equipo)

Curso: Big Data – Analista en Informática

Universidad Católica del Uruguay – Campus Salto
