"""
tests/test_negation.py
Pruebas obligatorias de negacion contextual, intencion y aceptacion.
"""
import pytest
from src.nlp_rules import detectar_compromiso_pago, detectar_aceptacion, clasificar_intencion_y_dificultad

@pytest.mark.parametrize("frase,esperado", [
    ("voy a pagar", True),
    ("no voy a pagar", False),
    ("puedo pagar", True),
    ("no puedo pagar", False),
    ("no puedo pagar este mes", False),
    ("no quiero pagar", False),
    ("no puedo comprometerme", False),
    ("me comprometo a pagar el viernes", True)
])
def test_compromiso_pago_obligatorios(frase, esperado):
    assert detectar_compromiso_pago(frase) is esperado

@pytest.mark.parametrize("frase,esperado", [
    ("acepto", True),
    ("no acepto", False),
    ("estoy de acuerdo", True),
    ("no estoy de acuerdo", False),
    ("de acuerdo", False),  # Fase 2: 'de acuerdo' aislado ya NO es regla autónoma de aceptación
    ("si, de acuerdo", True),
    ("si, estoy de acuerdo con la cuota", True),
    ("de acuerdo senor, voy a revisar la informacion", False),
    ("no me sirve", False)
])
def test_aceptacion_obligatorios(frase, esperado):
    assert detectar_aceptacion(frase) is esperado

def test_diferenciacion_intencion_vs_dificultad():
    # 'no puedo pagar' debe ser dificultad=1, pero intencion=0
    intencion, dificultad = clasificar_intencion_y_dificultad("en este momento no puedo pagar estoy sin trabajo")
    assert intencion == 0
    assert dificultad == 1
    
    # 'voy a pagar' es intencion=1, dificultad=0
    intencion_pos, dificultad_pos = clasificar_intencion_y_dificultad("si claro voy a pagar el viernes")
    assert intencion_pos == 1
    assert dificultad_pos == 0
