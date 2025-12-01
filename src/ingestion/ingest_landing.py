"""Módulo de ingesta de datos del SIPC a la landing zone.

Responsable de:
- Validar archivos CSV de origen
- Copiar a landing/ manteniendo estructura
- Registrar metadata de ingesta
- Validar estructura de columnas esperadas
"""

import shutil
import csv
from pathlib import Path
from datetime import datetime
import logging

from utils.paths import DataLakePaths

logger = logging.getLogger(__name__)


class SIPCDataIngestor:
    """Gestor de ingesta de datos SIPC a landing zone."""
    
    EXPECTED_FILES = {
        "precios.csv": ["fecha", "producto_id", "establecimiento_id", "precio", "unidad"],
        "productos.csv": ["id.producto", "producto", "marca", "especificacion", "nombre"],
        "establecimientos.csv": ["id.establecimientos", "razon.social", "nombre.sucursal", 
                                  "direccion", "ciudad", "depto", "cadena"],
    }
    
    def __init__(self, source_dir: str = None):
        """Inicializa el ingestor.
        
        Args:
            source_dir: Directorio con CSVs descargados del SIPC.
                       Si es None, asume que ya están en landing/
        """
        self.paths = DataLakePaths()
        self.source_dir = Path(source_dir) if source_dir else None
        
    def validate_source_files(self) -> bool:
        """Verifica que existan los archivos CSV esperados y valida columnas.
        
        Returns:
            True si todos los archivos existen con columnas correctas, False en caso contrario
        """
        if not self.source_dir:
            logger.warning("No se especificó directorio de origen")
            return False
            
        missing_files = []
        invalid_files = []
        
        for filename, expected_cols in self.EXPECTED_FILES.items():
            file_path = self.source_dir / filename
            
            if not file_path.exists():
                missing_files.append(filename)
                continue
                
            # Validar columnas del CSV
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    reader = csv.reader(f, delimiter=';')
                    header = next(reader)
                    
                    # Verificar que las columnas esperadas estén presentes
                    missing_cols = [col for col in expected_cols if col not in header]
                    if missing_cols:
                        invalid_files.append(f"{filename} (columnas faltantes: {missing_cols})")
                        logger.error(f"{filename} - Columnas faltantes: {missing_cols}")
                    else:
                        logger.info(f"✓ {filename} validado correctamente")
            except Exception as e:
                invalid_files.append(f"{filename} (error: {str(e)})")
                logger.error(f"Error validando {filename}: {e}")
                
        if missing_files:
            logger.error(f"Archivos faltantes: {missing_files}")
            return False
            
        if invalid_files:
            logger.error(f"Archivos inválidos: {invalid_files}")
            return False
            
        logger.info(f"Todos los archivos fuente validados: {list(self.EXPECTED_FILES.keys())}")
        return True
    
    def ingest_to_landing(self) -> None:
        """Copia archivos CSV del directorio de origen a landing zone."""
        if not self.source_dir:
            logger.info("Sin directorio de origen, asumiendo datos ya en landing/")
            return
            
        self.paths.ensure_directories()
        
        for filename in self.EXPECTED_FILES.keys():
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
            f.write(f"Archivos procesados: {', '.join(self.EXPECTED_FILES.keys())}\n")
            
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
