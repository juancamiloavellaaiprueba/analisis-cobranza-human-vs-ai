"""
tests/test_fase2_casos.py
Pruebas unitarias obligatorias de la Fase 2 para validación de lógica NLP,
acuerdos, ofertas, fechas, montos e intenciones (Casos 1 al 7).
"""
import pytest
import numpy as np
from src.nlp_rules import (
    detectar_aceptacion,
    detectar_compromiso_pago,
    clasificar_intencion_y_dificultad
)
from src.payment_extraction import (
    extraer_fecha_compromiso,
    extraer_condiciones_economicas
)
import importlib
extraer_mod = importlib.import_module("scripts.03_extraer_variables")
procesar_llamada = extraer_mod.procesar_llamada

def test_caso_1_pregunta_agente_con_rechazo_cliente():
    """
    CASO 1:
    Agente: '¿Está de acuerdo con pagar $300.000?'
    Cliente: 'No puedo pagar.'
    Esperado: aceptacion_pago = 0, acuerdo_pago = 0
    """
    texto = "¿Esta de acuerdo con pagar 300000 pesos? No puedo pagar."
    fila = {
        "id": 101,
        "archivo": "audio_101.wav",
        "tipo_agente": "Humano",
        "duracion_segundos": 45,
        "transcripcion_limpia": texto,
        "transcripcion_original": texto,
        "contactabilidad": 1,
        "es_buzon_voz": 0,
        "es_equivocado": 0,
        "titular_confirmado": 1
    }
    res = procesar_llamada(fila)
    assert res["aceptacion_pago"] == 0
    assert res["acuerdo_pago"] == 0

def test_caso_2_propuesta_agente_con_aceptacion_cliente():
    """
    CASO 2:
    Agente: 'Le propongo pagar $300.000 el 15 de agosto.'
    Cliente: 'Sí, acepto.'
    Esperado: oferta_pago = 1, aceptacion_pago = 1, acuerdo_pago = 1
    """
    texto = "Le propongo pagar 300.000 el 15 de agosto. Si, acepto."
    fila = {
        "id": 102,
        "archivo": "audio_102.wav",
        "tipo_agente": "IA",
        "duracion_segundos": 50,
        "transcripcion_limpia": texto,
        "transcripcion_original": texto,
        "contactabilidad": 1,
        "es_buzon_voz": 0,
        "es_equivocado": 0,
        "titular_confirmado": 1
    }
    res = procesar_llamada(fila)
    assert res["oferta_pago"] == 1
    assert res["aceptacion_pago"] == 1
    assert res["acuerdo_pago"] == 1

def test_caso_3_muletilla_agente_no_es_aceptacion():
    """
    CASO 3:
    Agente: 'De acuerdo señor, voy a revisar la información.'
    Cliente: 'No puedo comprometerme.'
    Esperado: aceptacion_pago = 0, acuerdo_pago = 0
    """
    texto = "De acuerdo senor, voy a revisar la informacion. No puedo comprometerme."
    fila = {
        "id": 103,
        "archivo": "audio_103.wav",
        "tipo_agente": "Humano",
        "duracion_segundos": 40,
        "transcripcion_limpia": texto,
        "transcripcion_original": texto,
        "contactabilidad": 1,
        "es_buzon_voz": 0,
        "es_equivocado": 0,
        "titular_confirmado": 1
    }
    res = procesar_llamada(fila)
    assert res["aceptacion_pago"] == 0
    assert res["acuerdo_pago"] == 0

def test_caso_4_diferenciacion_monto_propuesto_vs_acordado():
    """
    CASO 4:
    Agente: 'Le propongo $500.000.'
    Cliente: 'Solo puedo pagar $300.000.'
    Agente: 'Está bien.'
    Cliente: 'Sí, acepto.'
    Esperado: monto_propuesto = 500000, monto_acordado = 300000
    """
    texto = "Le propongo $500.000. Solo puedo pagar $300.000. Esta bien. Si, acepto."
    cond = extraer_condiciones_economicas(texto)
    assert cond["monto_propuesto"] == 500000.0
    assert cond["monto_acordado"] == 300000.0

def test_caso_5_fecha_historica_vs_fecha_compromiso():
    """
    CASO 5:
    Agente: 'La deuda se originó el 27 de diciembre de 2017.'
    Cliente: 'Sí, pagaré el 15 de agosto.'
    Esperado: fecha_compromiso = '15 de agosto', NO '27 de diciembre de 2017'
    """
    texto = "La deuda se origino el 27 de diciembre de 2017. Si, pagare el 15 de agosto."
    fecha = extraer_fecha_compromiso(texto)
    assert fecha == "15 de agosto"
    assert "2017" not in (fecha or "")

def test_caso_6_pregunta_agente_no_es_intencion_positiva_cliente():
    """
    CASO 6:
    Agente: '¿Puede pagar el viernes?'
    Cliente: 'No puedo.'
    Esperado: intencion_pago != 1 (debe ser 0)
    """
    texto = "¿Puede pagar el viernes? No puedo."
    intencion, dificultad = clasificar_intencion_y_dificultad(texto)
    assert intencion == 0

def test_caso_7_negacion_inicial_con_compromiso_posterior():
    """
    CASO 7:
    Cliente: 'No puedo pagar hoy, pero sí puedo pagar el 15.'
    Esperado: Detectar señal positiva posterior y no clasificarlo como rechazo absoluto.
    """
    texto = "No puedo pagar hoy, pero si puedo pagar el 15."
    compromiso = detectar_compromiso_pago(texto)
    intencion, dificultad = clasificar_intencion_y_dificultad(texto)
    assert compromiso is True
    assert intencion == 1
