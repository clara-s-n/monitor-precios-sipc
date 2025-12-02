#!/bin/bash
# Script rápido para construir el modelo dimensional

echo "🚀 Construyendo modelo dimensional..."

# Asegurar que Docker está corriendo
docker compose up -d

# Esperar a que Airflow esté listo
echo "⏳ Esperando a que Airflow esté listo..."
sleep 10

# Construir dimensiones
echo "📐 Construyendo dimensiones..."
docker compose exec airflow bash -c "cd /opt/airflow && PYTHONPATH=/opt/airflow python3 -c 'from src.transform.build_dimensions import build_dimensions; build_dimensions()'"

# Construir tabla de hechos
echo "📊 Construyendo tabla de hechos..."
docker compose exec airflow bash -c "cd /opt/airflow && PYTHONPATH=/opt/airflow python3 -c 'from src.transform.build_facts import build_facts; build_facts()'"

echo "✅ Modelo dimensional construido!"
echo "📁 Verifica los datos en data_sipc/refined/"
