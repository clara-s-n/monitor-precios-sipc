"""Módulo de ingesta de datos del SIPC a la landing zone.

Responsable de:
- Validar archivos CSV de origen
- Copiar a landing/ manteniendo estructura
- Registrar metadata de ingesta
"""

import shutil
from pathlib import Path
from datetime import datetime
import logging

from src.utils.paths import DataLakePaths

logger = logging.getLogger(__name__)


class SIPCDataIngestor:
    """Gestor de ingesta de datos SIPC a landing zone."""
    
    EXPECTED_FILES = [
        "precios.csv",
        "productos.csv",
        "establecimientos.csv",
    ]
    
    def __init__(self, source_dir: str = None):
        """Inicializa el ingestor.
        
        Args:
            source_dir: Directorio con CSVs descargados del SIPC.
                       Si es None, asume que ya están en landing/
        """
        self.paths = DataLakePaths()
        self.source_dir = Path(source_dir) if source_dir else None
        
    def validate_source_files(self) -> bool:
        """Verifica que existan los archivos CSV esperados.
        
        Returns:
            True si todos los archivos existen, False en caso contrario
        """
        if not self.source_dir:
            logger.warning("No se especificó directorio de origen")
            return False
            
        missing_files = []
        for filename in self.EXPECTED_FILES:
            file_path = self.source_dir / filename
            if not file_path.exists():
                missing_files.append(filename)
                
        if missing_files:
            logger.error(f"Archivos faltantes: {missing_files}")
            return False
            
        logger.info(f"Todos los archivos fuente encontrados: {self.EXPECTED_FILES}")
        return True
    
    def ingest_to_landing(self) -> None:
        """Copia archivos CSV del directorio de origen a landing zone."""
        if not self.source_dir:
            logger.info("Sin directorio de origen, asumiendo datos ya en landing/")
            return
            
        self.paths.ensure_directories()
        
        for filename in self.EXPECTED_FILES:
            source_file = self.source_dir / filename
            dest_file = self.paths.get_landing_file(filename)
            
            if source_file.exists():
                shutil.copy2(source_file, dest_file)
                logger.info(f"Copiado: {filename} -> {dest_file}")
            else:
                logger.warning(f"Archivo no encontrado: {source_file}")
        
        # Guardar metadata de ingesta
        self._save_ingestion_metadata()
    
    def _save_ingestion_metadata(self) -> None:
        """Guarda metadata sobre el proceso de ingesta."""
        metadata_file = self.paths.landing / "_ingestion_metadata.txt"
        
        with open(metadata_file, 'w') as f:
            f.write(f"Ingesta realizada: {datetime.now().isoformat()}\n")
            f.write(f"Archivos procesados: {', '.join(self.EXPECTED_FILES)}\n")
            
        logger.info(f"Metadata guardada en {metadata_file}")


def ingest_landing_data(source_dir: str = None) -> None:
    """Función principal para ser llamada desde Airflow DAG.
    
    Args:
        source_dir: Directorio con archivos CSV del SIPC
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    ingestor = SIPCDataIngestor(source_dir)
    
    if source_dir:
        if not ingestor.validate_source_files():
            raise ValueError("Validación de archivos fuente falló")
    
    ingestor.ingest_to_landing()
    logger.info("✅ Ingesta a landing zone completada")
