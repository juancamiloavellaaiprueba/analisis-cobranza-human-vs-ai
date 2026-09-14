"""
tests/test_fase3_5_correcciones.py
Pruebas unitarias obligatorias de la Fase 3.5:
1. Aceptación administrativa -> 0
2. Aceptación de pago -> 1
3. 'de acuerdo' aislado sin contexto -> 0
4. 'dos' sin contexto monetario -> NaN
5. 'dos mil pesos' -> 2000
6. '$2.000' -> 2000
7. Número de cuotas sin monto ('15 cuotas') -> no interpretado como dinero
8. 'dos cuotas de 300 mil' -> monto = 300000 y cuotas = 2
9. Inconsistencia matemática (15 cuotas de 60 mil vs 830 mil) -> bandera = 1
10. Preservación de negación de pago
"""
import pytest
import numpy as np
from src.nlp_rules import (
    detectar_aceptacion,
    detectar_compromiso_pago,
    clasificar_intencion_y_dificultad
)
from src.payment_extraction import (
    parsear_monto,
    extraer_cuotas,
    extraer_condiciones_economicas
)
import importlib
extraer_mod = importlib.import_module("scripts.03_extraer_variables")
procesar_llamada = extraer_mod.procesar_llamada

# ---------------------------------------------------------
# CORRECCIÓN 1: ACEPTACIÓN CONTEXTUAL VS ADMINISTRATIVA
# ---------------------------------------------------------

def test_aceptacion_administrativa():
    """1. Frases con aceptación administrativa (callback/llamada) no deben contar como aceptación de pago."""
    frase_1 = "sí, de acuerdo, llámeme mañana"
    frase_2 = "entonces yo me comunico con usted mañana a las cuatro. sí, de acuerdo."
    frase_3 = "de acuerdo, envíeme la información al correo"
    assert detectar_aceptacion(frase_1) is False
    assert detectar_aceptacion(frase_2) is False
    assert detectar_aceptacion(frase_3) is False

def test_aceptacion_de_pago():
    """2. Aceptación vinculada explícitamente a condiciones económicas o propuesta de pago."""
    assert detectar_aceptacion("sí, estoy de acuerdo con pagar $300.000 el 15") is True
    assert detectar_aceptacion("de acuerdo con las cuotas") is True
    assert detectar_aceptacion("sí señora, acepto ese plan") is True
    assert detectar_aceptacion("acepto pagar los 200 mil pesos") is True

def test_de_acuerdo_aislado_sin_contexto():
    """3. 'de acuerdo' aislado sin contexto no debe considerarse aceptación de pago."""
    assert detectar_aceptacion("de acuerdo") is False
    assert detectar_aceptacion("de acuerdo señor, permítame un momento") is False

# ---------------------------------------------------------
# CORRECCIÓN 2: EXTRACCIÓN MONETARIA Y NÚMEROS CARDINALES
# ---------------------------------------------------------

def test_numero_cardinal_aislado_sin_dinero():
    """4. Palabras cardinales o números aislados sin evidencia monetaria no deben parsearse como dinero."""
    for caso in ["dos", "tres", "cuatro", "uno", "a dos", "por dos", "dos y eso", "tengo dos problemas"]:
        assert np.isnan(parsear_monto(caso)), f"Falló para: {caso}"

def test_dos_mil_pesos():
    """5. 'dos mil pesos' con evidencia monetaria clara debe retornar 2000.0."""
    assert parsear_monto("dos mil pesos") == 2000.0
    assert parsear_monto("2.000 pesos") == 2000.0

def test_signo_pesos_dos_mil():
    """6. '$2.000' con símbolo monetario debe retornar 2000.0."""
    assert parsear_monto("$2.000") == 2000.0
    assert parsear_monto("$ 2000") == 2000.0

def test_cuotas_sin_monto():
    """7. '15 cuotas' no debe interpretarse como monto monetario ($15.000)."""
    assert np.isnan(parsear_monto("15 cuotas"))
    c = extraer_cuotas("el cliente pagará en 15 cuotas")
    assert c["numero_cuotas"] == 15.0
    assert np.isnan(c["monto_cuota"])

def test_dos_cuotas_de_trescientos_mil():
    """8. 'dos cuotas de 300 mil' -> cuotas = 2, monto = 300000."""
    c = extraer_cuotas("le ofrezco pagar dos cuotas de 300 mil pesos")
    assert c["numero_cuotas"] == 2.0
    assert c["monto_cuota"] == 300000.0

# ---------------------------------------------------------
# CORRECCIÓN 3: INCONSISTENCIA MATEMÁTICA
# ---------------------------------------------------------

def test_inconsistencia_matematica_acuerdo():
    """
    9. Inconsistencia matemática entre monto total pactado ($830.000) y producto de cuotas
    (15 cuotas de $60.000 = $900.000). El NLP debe extraer fielmente y levantar bandera = 1.
    """
    texto = (
        "El acuerdo es por 830 mil pesos en total. "
        "Que pagará en 15 cuotas mensuales de 60 mil pesos cada una. "
        "¿Estamos de acuerdo? De acuerdo."
    )
    fila = {
        "id": 185,
        "archivo": "audio_185.wav",
        "tipo_agente": "IA",
        "duracion_segundos": 60,
        "transcripcion_limpia": texto,
        "transcripcion_original": texto,
        "contactabilidad": 1,
        "es_buzon_voz": 0,
        "es_equivocado": 0,
        "titular_confirmado": 1
    }
    res = procesar_llamada(fila)
    assert res["acuerdo_pago"] == 1
    assert res["monto_acordado"] == 830000.0
    assert res["numero_cuotas"] == 15.0
    assert res["monto_cuota"] == 60000.0
    assert res["inconsistencia_matematica_acuerdo"] == 1

def test_consistencia_matematica_acuerdo():
    """Caso consistente: 2 cuotas de 400 mil con acuerdo de 800 mil -> bandera = 0."""
    texto = (
        "El acuerdo es por 800 mil pesos en total. "
        "Que pagará en 2 cuotas mensuales de 400 mil pesos cada una. "
        "¿Estamos de acuerdo? De acuerdo."
    )
    fila = {
        "id": 186,
        "archivo": "audio_186.wav",
        "tipo_agente": "Humano",
        "duracion_segundos": 60,
        "transcripcion_limpia": texto,
        "transcripcion_original": texto,
        "contactabilidad": 1,
        "es_buzon_voz": 0,
        "es_equivocado": 0,
        "titular_confirmado": 1
    }
    res = procesar_llamada(fila)
    assert res["acuerdo_pago"] == 1
    assert res["monto_acordado"] == 800000.0
    assert res["inconsistencia_matematica_acuerdo"] == 0

# ---------------------------------------------------------
# CORRECCIÓN 5: PRESERVACIÓN DE NEGACIÓN
# ---------------------------------------------------------

@pytest.mark.parametrize("frase_negada", [
    "no puedo pagar",
    "no tengo dinero",
    "no acepto",
    "no puedo comprometerme"
])
def test_preservacion_negaciones(frase_negada):
    """10. Las negaciones explícitas no deben convertirse en aceptación ni intención positiva."""
    assert detectar_aceptacion(frase_negada) is False
    assert detectar_compromiso_pago(frase_negada) is False
    intencion, _ = clasificar_intencion_y_dificultad(frase_negada)
    assert intencion == 0
