"""Gestión centralizada de rutas del Data Lake.

Maneja diferencias entre ejecución en Airflow container vs notebooks.
"""

import os
from pathlib import Path


class DataLakePaths:
    """Rutas del Data Lake configuradas según contexto de ejecución."""
    
    def __init__(self, base_path: str = None):
        """Inicializa rutas del data lake.
        
        Args:
            base_path: Ruta base del data lake. Si es None, detecta automáticamente:
                - En Airflow: /opt/airflow/data_sipc
                - En notebooks: ../data_sipc o ./data_sipc
        """
        if base_path is None:
            # Detectar si estamos en Airflow container
            if os.path.exists("/opt/airflow/data_sipc"):
                base_path = "/opt/airflow/data_sipc"
            # Detectar si estamos en notebooks
            elif os.path.exists("../data_sipc"):
                base_path = "../data_sipc"
            else:
                base_path = "./data_sipc"
        
        self.base = Path(base_path)
        
        # Zonas del Data Lake
        self.landing = self.base / "landing"
        self.raw = self.base / "raw"
        self.refined = self.base / "refined"
        self.exports = self.base / "exports_dashboard"
        
    def ensure_directories(self) -> None:
        """Crea todas las zonas del data lake si no existen."""
        for path in [self.landing, self.raw, self.refined, self.exports]:
            path.mkdir(parents=True, exist_ok=True)
    
    def get_landing_file(self, filename: str) -> Path:
        """Retorna ruta completa a archivo en landing."""
        return self.landing / filename
    
    def get_raw_table(self, table_name: str) -> Path:
        """Retorna ruta a tabla en zona raw."""
        return self.raw / table_name
    
    def get_refined_table(self, table_name: str) -> Path:
        """Retorna ruta a tabla en zona refined."""
        return self.refined / table_name
    
    def get_export_file(self, filename: str) -> Path:
        """Retorna ruta a archivo de exportación para dashboard."""
        return self.exports / filename


# Instancia por defecto para importación rápida
paths = DataLakePaths()
