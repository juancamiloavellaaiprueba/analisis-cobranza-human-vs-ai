"""
tests/test_payment_extraction.py
Pruebas para extraccion de montos, cuotas, fechas, descuentos y valores faltantes.
"""
import numpy as np
from src.payment_extraction import (
    parsear_monto,
    extraer_cuotas,
    extraer_descuento,
    extraer_fecha_compromiso
)

def test_parsear_montos():
    assert parsear_monto("$500.000") == 500000.0
    assert parsear_monto("500 mil") == 500000.0
    assert parsear_monto("quinientos mil") == 500000.0
    assert parsear_monto("300000") == 300000.0
    assert parsear_monto("10 millones") == 10000000.0
    assert parsear_monto("dos mil") == 2000.0

def test_parsear_montos_faltantes():
    assert np.isnan(parsear_monto(None))
    assert np.isnan(parsear_monto(""))
    assert np.isnan(parsear_monto("N/A"))
    assert np.isnan(parsear_monto("-"))
    assert np.isnan(parsear_monto("no aplica"))

def test_cuotas_y_fechas():
    c = extraer_cuotas("le ofrezco pagar dos cuotas cada una por 150 mil")
    assert c["numero_cuotas"] == 2.0
    assert c["monto_cuota"] == 150000.0
    
    assert extraer_fecha_compromiso("cancelo el 15") == "15"
    assert extraer_fecha_compromiso("pago el proximo viernes") == "proximo viernes"
    assert extraer_fecha_compromiso("sin fecha") is None

def test_descuento():
    d1 = extraer_descuento("le mantenemos el descuento del 20%")
    assert d1["tiene_descuento"] is True
    assert d1["porcentaje_descuento"] == 20.0
    
    d2 = extraer_descuento("no hay descuento en este momento")
    assert d2["tiene_descuento"] is False
