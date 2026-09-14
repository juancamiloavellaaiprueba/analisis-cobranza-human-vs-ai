"""
src/cleaning.py
Normalizacion de texto y deteccion de anomalias en transcripciones de cobranza.
"""
import re
import unicodedata
from typing import Optional
import pandas as pd

PATRONES_BUZON = [
    r"buzon de voz", r"deje su mensaje", r"despues del tono",
    r"la llamada sera cobrada", r"casilla de mensajes",
    r"el numero que marco", r"no se encuentra disponible",
    r"por favor intente mas tarde", r"deja tu mensaje",
    r"grave su mensaje", r"grabacion llego al tiempo limite"
]

PATRONES_WHISPER_ERROR = [
    r"thank you for watching", r"subtitles by", r"amara\.org",
    r"suscribete al canal", r"specimen", r"scholarship", r"recommendations"
]

def normalizar_texto(texto: Optional[str]) -> str:
    """Normaliza texto a minusculas, sin tildes y con espacios unificados."""
    if texto is None or pd.isna(texto):
        return ""
    s = str(texto).strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"\s+", " ", s)
    return s

def es_texto_vacio(texto: Optional[str]) -> bool:
    """Determina si un texto carece de contenido alfabetico o numerico."""
    if texto is None or pd.isna(texto):
        return True
    return len(str(texto).strip()) == 0

def es_texto_muy_corto(texto: Optional[str], umbral: int = 10) -> bool:
    """Indica si el texto posee menos tokens que el umbral minimo."""
    if es_texto_vacio(texto):
        return True
    return len(str(texto).strip().split()) < umbral

def es_buzon_voz(texto: Optional[str]) -> bool:
    """Detecta si la grabacion corresponde a contestador o buzon telefonico."""
    t = normalizar_texto(texto)
    for p in PATRONES_BUZON:
        if re.search(p, t):
            return True
    return False

def tiene_error_whisper(texto: Optional[str]) -> bool:
    """Detecta alucinaciones o palabras en ingles generadas por Whisper."""
    t = normalizar_texto(texto)
    for p in PATRONES_WHISPER_ERROR:
        if re.search(p, t):
            return True
    return False

def contar_palabras(texto: Optional[str]) -> int:
    """Calcula la cantidad de palabras del texto."""
    if es_texto_vacio(texto):
        return 0
    return len(str(texto).strip().split())

def limpiar_dataset_transcripciones(df: pd.DataFrame) -> pd.DataFrame:
    """Limpia y agrega variables de calidad tecnica al dataset."""
    df_clean = df.copy()
    col_texto = "transcripcion_limpia" if "transcripcion_limpia" in df_clean.columns else "texto"
    if col_texto not in df_clean.columns and "transcripcion" in df_clean.columns:
        col_texto = "transcripcion"
        
    df_clean["texto"] = df_clean[col_texto].fillna("")
    df_clean["texto_normalizado"] = df_clean["texto"].apply(normalizar_texto)
    df_clean["num_palabras"] = df_clean["texto"].apply(contar_palabras)
    df_clean["texto_vacio"] = df_clean["texto"].apply(es_texto_vacio)
    df_clean["texto_muy_corto"] = df_clean["texto"].apply(es_texto_muy_corto)
    df_clean["es_buzon_voz"] = df_clean["texto"].apply(es_buzon_voz)
    df_clean["posible_error_whisper"] = df_clean["texto"].apply(tiene_error_whisper)
    
    return df_clean
