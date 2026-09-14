"""
tests/test_variables.py
Pruebas de coherencia entre variables, objeciones y jerarquia de acuerdos.
"""
from src.objection_analysis import detectar_objecion
from src.validation import verificar_consistencia_registro

def test_deteccion_objeciones():
    assert detectar_objecion("no tengo dinero estoy sin empleo") == "economica"
    assert detectar_objecion("el salario me llega despues del 15") == "fecha_pago"
    assert detectar_objecion("yo ya pague esa tarjeta ayer") == "desacuerdo_deuda"
    assert detectar_objecion("cuota muy alta cobro excesivo") == "monto"
    assert detectar_objecion("buenos dias si voy a pagar") is None

def test_consistencia_registro():
    # Inconsistencia: acuerdo=1 pero contactabilidad=0
    cat, req_rev, motivos = verificar_consistencia_registro({
        "contactabilidad": 0, "acuerdo_pago": 1, "resultado_final": "acuerdo_pago"
    })
    assert cat == "inconsistente"
    assert req_rev == 1
    
    # Consistente
    cat_ok, req_rev_ok, motivos_ok = verificar_consistencia_registro({
        "contactabilidad": 1, "oferta_pago": 1, "aceptacion_pago": 1,
        "acuerdo_pago": 1, "resultado_final": "acuerdo_pago", "confianza_nlp": 0.9,
        "evidencia_acuerdo": "si me comprometo a pagar el viernes"
    })
    assert cat_ok == "ok"
    assert req_rev_ok == 0
