"""
scripts/04_validar.py
Segunda pasada automática de control de calidad y generación del Excel de validación humana.
"""
import sys
import logging
from pathlib import Path
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.validation import ejecutar_segunda_verificacion, generar_excel_validacion

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("04_validar")

def main():
    ruta_dataset = ROOT_DIR / "data" / "processed" / "dataset_final.csv"
    logger.info(f"Cargando {ruta_dataset} para segunda verificacion...")
    df = pd.read_csv(ruta_dataset, encoding="utf-8")
    
    df_auditado = ejecutar_segunda_verificacion(df)
    df_auditado.to_csv(ruta_dataset, index=False, encoding="utf-8")
    
    logger.info(f"Segunda verificacion completada. Distribucion control_calidad:")
    logger.info(df_auditado["control_calidad"].value_counts().to_dict())
    logger.info(f"Total registros que requieren revision: {df_auditado['requiere_revision'].sum()}")
    
    ruta_excel = ROOT_DIR / "data" / "validation" / "dataset_validacion.xlsx"
    try:
        generar_excel_validacion(df_auditado, str(ruta_excel))
        logger.info(f"Archivo de validacion humana generado en: {ruta_excel}")
    except PermissionError:
        logger.warning(f"El archivo {ruta_excel} esta abierto en Excel. Se preserva el archivo existente.")

if __name__ == "__main__":
    main()
