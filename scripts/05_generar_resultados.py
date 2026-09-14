"""
scripts/05_generar_resultados.py
Calculo de estadisticas comparativas, factores asociados al acuerdo y generacion del reporte HTML.
"""
import sys
import logging
from pathlib import Path
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.reporting import generar_reporte_html, calcular_comparativa

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("05_generar_resultados")

def main():
    ruta_dataset = ROOT_DIR / "data" / "processed" / "dataset_final.csv"
    logger.info(f"Cargando datos analiticos desde {ruta_dataset}...")
    df = pd.read_csv(ruta_dataset, encoding="utf-8")
    
    resumen = calcular_comparativa(df)
    logger.info("Resumen comparativo Humano vs IA:")
    logger.info(f"  Contactabilidad: Humano {resumen['contactabilidad_h']:.1f}% | IA {resumen['contactabilidad_ia']:.1f}%")
    logger.info(f"  Oferta de Pago:  Humano {resumen['oferta_h']:.1f}% | IA {resumen['oferta_ia']:.1f}%")
    logger.info(f"  Acuerdo de Pago: Humano {resumen['acuerdo_h']:.1f}% | IA {resumen['acuerdo_ia']:.1f}%")
    logger.info(f"  Duracion Media:  Humano {resumen['duracion_media_h']:.1f}s | IA {resumen['duracion_media_ia']:.1f}s")
    
    ruta_html = ROOT_DIR / "reports" / "informe.html"
    ruta_html.parent.mkdir(parents=True, exist_ok=True)
    generar_reporte_html(df, str(ruta_html))
    logger.info(f"Reporte ejecutivo HTML generado en: {ruta_html}")

if __name__ == "__main__":
    main()
