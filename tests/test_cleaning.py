"""
tests/test_cleaning.py
Pruebas de normalizacion, espacios, textos vacios y deteccion de anomalias.
"""
from src.cleaning import (
    normalizar_texto,
    es_texto_vacio,
    es_texto_muy_corto,
    es_buzon_voz,
    tiene_error_whisper
)

def test_normalizacion():
    assert normalizar_texto("HOLA MUNDO") == "hola mundo"
    assert normalizar_texto("¿Cómo estás?") == "¿como estas?"
    assert normalizar_texto("Estará cancelado") == "estara cancelado"
    assert normalizar_texto("   espacios    multiples   ") == "espacios multiples"
    assert normalizar_texto("") == ""
    assert normalizar_texto(None) == ""

def test_textos_vacios_y_cortos():
    assert es_texto_vacio("") is True
    assert es_texto_vacio("    ") is True
    assert es_texto_vacio(None) is True
    assert es_texto_vacio("hola") is False
    assert es_texto_muy_corto("dos palabras") is True
    assert es_texto_muy_corto("uno dos tres cuatro cinco seis siete ocho nueve diez once") is False

def test_deteccion_buzon_y_alucinaciones():
    assert es_buzon_voz("deje su mensaje despues del tono") is True
    assert es_buzon_voz("buenos dias me comunico con el titular") is False
    assert tiene_error_whisper("thank you for watching specimen scholarship") is True
    assert tiene_error_whisper("muchas gracias por atender la llamada") is False
