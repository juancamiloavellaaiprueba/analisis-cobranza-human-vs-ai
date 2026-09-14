"""
scripts/01_transcribir.py
Pipeline de audio a texto mediante Whisper para llamadas de cobranza bancaria.

Convierte archivos de audio (.wav, .mp3, etc.) o paquetes comprimidos (.zip)
en transcripciones .txt y un CSV de resumen, preservando la inmutabilidad
de los datos ya existentes por defecto.
"""
import os
import sys
import zipfile
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("01_transcribir")

EXTENSIONES_AUDIO_COMPATIBLES = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".aac", ".wma"}

def descomprimir_zip(ruta_zip: Path, dir_destino: Path) -> Path:
    """
    Descomprime un archivo ZIP con grabaciones de audio en el directorio de destino.
    """
    if not ruta_zip.exists():
        raise FileNotFoundError(f"El archivo ZIP especificado no existe: {ruta_zip}")
    if not zipfile.is_zipfile(ruta_zip):
        raise zipfile.BadZipFile(f"El archivo especificado no es un ZIP válido: {ruta_zip}")
        
    dir_destino.mkdir(parents=True, exist_ok=True)
    logger.info(f"Descomprimiendo audios desde: {ruta_zip}")
    with zipfile.ZipFile(ruta_zip, "r") as zip_ref:
        zip_ref.extractall(dir_destino)
    logger.info(f"Descompresión terminada en: {dir_destino}")
    return dir_destino

def encontrar_audios(dir_audios: Path) -> List[Path]:
    """
    Busca recursivamente archivos de audio compatibles (.wav, .mp3, etc.) y los ordena.
    """
    if not dir_audios.exists() or not dir_audios.is_dir():
        logger.warning(f"El directorio de audios no existe o no es carpeta: {dir_audios}")
        return []
    
    archivos = [
        p for p in dir_audios.rglob("*")
        if p.is_file() and p.suffix.lower() in EXTENSIONES_AUDIO_COMPATIBLES
    ]
    return sorted(archivos)

def cargar_modelo(nombre_modelo: str = "small", device: Optional[str] = None):
    """
    Carga el modelo Whisper indicado (por defecto 'small').
    Prioriza CPU si device es None y no hay GPU disponible.
    """
    import whisper
    import torch
    
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
    logger.info(f"Cargando modelo Whisper '{nombre_modelo}' en dispositivo '{device}'...")
    modelo = whisper.load_model(nombre_modelo, device=device)
    logger.info("Modelo cargado correctamente.")
    return modelo

def calcular_duracion(resultado_whisper: dict) -> float:
    """
    Calcula la duración en segundos a partir de los segmentos generados por Whisper.
    """
    if not isinstance(resultado_whisper, dict):
        return 0.0
    segmentos = resultado_whisper.get("segments", [])
    if segmentos and isinstance(segmentos, list) and len(segmentos) > 0:
        ultimo_segmento = segmentos[-1]
        if isinstance(ultimo_segmento, dict) and "end" in ultimo_segmento:
            return float(ultimo_segmento["end"])
    return 0.0

def transcribir_audio(ruta_audio: Path, modelo: Any, idioma: str = "es") -> Tuple[str, float]:
    """
    Ejecuta la transcripción de un archivo de audio mediante Whisper en idioma español.
    Retorna (texto_transcrito, duracion_segundos).
    """
    resultado = modelo.transcribe(
        str(ruta_audio),
        language=idioma,
        task="transcribe",
        fp16=False
    )
    texto = resultado.get("text", "").strip()
    duracion = calcular_duracion(resultado)
    return texto, duracion

def guardar_transcripcion(texto: str, ruta_txt: Path):
    """
    Guarda el texto transcribido en un archivo .txt con codificación UTF-8.
    """
    ruta_txt.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta_txt, "w", encoding="utf-8") as f:
        f.write(texto)

def procesar_audio(
    ruta_audio: Path,
    modelo: Any,
    dir_salida: Path,
    tipo_agente: str = "humano",
    idioma: str = "es",
    overwrite: bool = False,
    dir_base_entrada: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Procesa un único archivo de audio:
    - Determina ruta de salida .txt preservando subdirectorios si existen.
    - Si el .txt ya existe y overwrite=False, se preserva inmutable.
    - Si procede, ejecuta transcripción Whisper y guarda el archivo .txt.
    """
    nombre_archivo = ruta_audio.name
    
    # Calcular ruta de salida preservando subcarpeta relativa si aplica (ej. Humanos/ o IA/)
    if dir_base_entrada and dir_base_entrada in ruta_audio.parents:
        rel_path = ruta_audio.relative_to(dir_base_entrada)
        ruta_txt = dir_salida / rel_path.with_suffix(".txt")
    else:
        ruta_txt = dir_salida / f"{ruta_audio.stem}.txt"
        
    # Determinar tipo de agente si no está fijado explícitamente
    if tipo_agente == "auto":
        tipo_determinado = "ia" if "ia" in str(ruta_audio).lower() else "humano"
    else:
        tipo_determinado = tipo_agente

    # 1. Comprobación de inmutabilidad
    if ruta_txt.exists() and not overwrite:
        logger.info(f"Transcripción existente: se conserva sin modificar: {ruta_txt.name}")
        texto_existente = ruta_txt.read_text(encoding="utf-8", errors="replace").strip()
        return {
            "archivo": nombre_archivo,
            "tipo_agente": tipo_determinado,
            "duracion_segundos": None,
            "transcripcion": texto_existente,
            "estado": "omitido_existente",
            "ruta_txt": str(ruta_txt)
        }

    # 2. Transcripción
    try:
        texto, duracion = transcribir_audio(ruta_audio, modelo, idioma=idioma)
        guardar_transcripcion(texto, ruta_txt)
        logger.info(f"✓ Transcripción terminada: {nombre_archivo} ({duracion:.1f}s)")
        return {
            "archivo": nombre_archivo,
            "tipo_agente": tipo_determinado,
            "duracion_segundos": duracion,
            "transcripcion": texto,
            "estado": "procesado",
            "ruta_txt": str(ruta_txt)
        }
    except Exception as e:
        logger.error(f"✗ ERROR al transcribir {nombre_archivo}: {e}")
        return {
            "archivo": nombre_archivo,
            "tipo_agente": tipo_determinado,
            "duracion_segundos": None,
            "transcripcion": "",
            "estado": f"error: {str(e)}",
            "ruta_txt": str(ruta_txt)
        }

def guardar_resumen(resultados: List[Dict[str, Any]], ruta_csv: Path) -> Optional[Path]:
    """
    Crea un archivo CSV resumen con los metadatos y transcripciones procesadas.
    Artefacto secundario independiente que no reemplaza dataset_final.csv.
    """
    if not resultados:
        logger.info("No hay resultados para exportar en CSV resumen.")
        return None
        
    ruta_csv.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(resultados)
    df.to_csv(ruta_csv, index=False, encoding="utf-8-sig")
    logger.info(f"Archivo CSV de resumen generado en: {ruta_csv}")
    return ruta_csv

def parsear_argumentos(args_list: Optional[List[str]] = None) -> argparse.Namespace:
    """
    Configura y parsea los argumentos de línea de comandos.
    """
    parser = argparse.ArgumentParser(
        description="Pipeline reproducible de transcripción de audio a texto mediante Whisper"
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        default=ROOT_DIR / "data" / "raw" / "audios",
        help="Directorio con archivos de audio para transcribir"
    )
    parser.add_argument(
        "--zip", "-z",
        type=Path,
        default=None,
        help="Ruta opcional a un archivo .zip con audios para descomprimir antes de procesar"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=ROOT_DIR / "data" / "raw" / "transcripciones",
        help="Directorio donde se guardarán los archivos .txt y el CSV resumen"
    )
    parser.add_argument(
        "--tipo-agente",
        type=str,
        default="humano",
        choices=["humano", "ia", "auto"],
        help="Tipo de agente para etiquetar en el CSV de resumen (humano, ia, auto). Default: humano"
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        default="small",
        help="Nombre del modelo Whisper (tiny, base, small, medium, large). Default: small"
    )
    parser.add_argument(
        "--language", "-l",
        type=str,
        default="es",
        help="Idioma de las grabaciones de audio. Default: es"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Sobrescribe transcripciones .txt existentes. Por defecto False (inmutables)"
    )
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        help="Dispositivo de cómputo ('cpu', 'cuda'). Si es None, autodetecta."
    )
    parser.add_argument(
        "--csv-nombre",
        type=str,
        default="transcripciones_resumen.csv",
        help="Nombre del archivo CSV resumen a generar en el directorio de salida"
    )
    return parser.parse_args(args_list)

def ejecutar_pipeline_transcripcion(
    dir_entrada: Path,
    dir_salida: Path,
    ruta_zip: Optional[Path] = None,
    nombre_modelo: str = "small",
    tipo_agente: str = "humano",
    idioma: str = "es",
    overwrite: bool = False,
    device: Optional[str] = None,
    nombre_csv: str = "transcripciones_resumen.csv",
    modelo_precargado: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Ejecuta el flujo completo de transcripción con manejo de ZIP, detección,
    inmutabilidad y generación de CSV de resumen.
    """
    # 1. Descomprimir ZIP si fue provisto
    if ruta_zip:
        dir_extraccion = dir_entrada if dir_entrada != (ROOT_DIR / "data" / "raw" / "audios") else (dir_salida.parent / "audios_extraidos")
        descomprimir_zip(ruta_zip, dir_extraccion)
        dir_audios = dir_extraccion
    else:
        dir_audios = dir_entrada

    # 2. Buscar archivos de audio
    archivos_audio = encontrar_audios(dir_audios)
    total = len(archivos_audio)
    logger.info(f"Audios compatibles encontrados: {total}")

    if total == 0:
        logger.info("No se encontraron grabaciones de audio compatibles para procesar.")
        return {
            "total": 0,
            "procesados": 0,
            "omitidos": 0,
            "errores": 0,
            "resultados": [],
            "ruta_csv": None
        }

    # 3. Filtrar pendientes antes de cargar el modelo (optimización de recursos)
    audios_a_procesar = []
    for audio_path in archivos_audio:
        if dir_audios in audio_path.parents:
            rel = audio_path.relative_to(dir_audios)
            salida_txt = dir_salida / rel.with_suffix(".txt")
        else:
            salida_txt = dir_salida / f"{audio_path.stem}.txt"
            
        if not salida_txt.exists() or overwrite:
            audios_a_procesar.append(audio_path)

    # 4. Cargar modelo únicamente si hay audios pendientes de transcripción
    modelo = modelo_precargado
    if len(audios_a_procesar) > 0 and modelo is None:
        modelo = cargar_modelo(nombre_modelo, device=device)

    # 5. Iterar y procesar cada audio
    resultados = []
    conteo_procesados = 0
    conteo_omitidos = 0
    conteo_errores = 0

    for i, ruta_audio in enumerate(archivos_audio, start=1):
        logger.info(f"[{i}/{total}] Procesando: {ruta_audio.name}")
        res = procesar_audio(
            ruta_audio=ruta_audio,
            modelo=modelo,
            dir_salida=dir_salida,
            tipo_agente=tipo_agente,
            idioma=idioma,
            overwrite=overwrite,
            dir_base_entrada=dir_audios
        )
        resultados.append(res)
        if res["estado"] == "procesado":
            conteo_procesados += 1
        elif res["estado"] == "omitido_existente":
            conteo_omitidos += 1
        else:
            conteo_errores += 1

    # 6. Guardar CSV resumen
    ruta_csv = dir_salida / nombre_csv
    guardar_resumen(resultados, ruta_csv)

    logger.info("========================================")
    logger.info(" PROCESO DE TRANSCRIPCIÓN TERMINADO")
    logger.info(f" Total audios: {total} | Procesados: {conteo_procesados} | Omitidos: {conteo_omitidos} | Errores: {conteo_errores}")
    logger.info("========================================")

    return {
        "total": total,
        "procesados": conteo_procesados,
        "omitidos": conteo_omitidos,
        "errores": conteo_errores,
        "resultados": resultados,
        "ruta_csv": ruta_csv
    }

def main(args_list: Optional[List[str]] = None) -> int:
    args = parsear_argumentos(args_list)
    res = ejecutar_pipeline_transcripcion(
        dir_entrada=args.input,
        dir_salida=args.output,
        ruta_zip=args.zip,
        nombre_modelo=args.model,
        tipo_agente=args.tipo_agente,
        idioma=args.language,
        overwrite=args.overwrite,
        device=args.device,
        nombre_csv=args.csv_nombre
    )
    return 0 if res["errores"] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())