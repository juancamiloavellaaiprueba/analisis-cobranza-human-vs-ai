"""
scripts/02_limpiar.py
Limpieza, normalizacion y control de calidad de transcripciones.
"""
import sys
import logging
from pathlib import Path
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.cleaning import limpiar_dataset_transcripciones

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("02_limpiar")

def main():
    ruta_input = ROOT_DIR / "data" / "raw" / "dataset_limpio.csv"
    if not ruta_input.exists():
        logger.error(f"No se encontro {ruta_input}")
        sys.exit(1)
        
    logger.info(f"Cargando {ruta_input}...")
    df = pd.read_csv(ruta_input, encoding="utf-8")
    df_limpio = limpiar_dataset_transcripciones(df)
    
    salida = ROOT_DIR / "data" / "processed" / "dataset_limpio_procesado.csv"
    salida.parent.mkdir(parents=True, exist_ok=True)
    try:
        df_limpio.to_csv(salida, index=False, encoding="utf-8")
        logger.info(f"Limpieza completada exitosamente. Registros guardados en {salida}: {len(df_limpio)}")
    except PermissionError:
        logger.warning(f"El archivo {salida} esta abierto en otra aplicacion. Se preserva el archivo existente.")

if __name__ == "__main__":
    main()
