"""
tests/test_consistency_statistical.py
Test automático de consistencia metodológica y numérica de la base analítica
data/processed/dataset_final.csv y de los cálculos inferenciales del reporte.
"""
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

ROOT_DIR = Path(__file__).resolve().parent.parent
from src.reporting import calcular_comparativa, prueba_fisher_exacta_2x2, prueba_chi_cuadrado_2x2

def test_dataset_final_counts():
    """Verifica conteos exactos de la muestra en dataset_final.csv."""
    ruta_csv = ROOT_DIR / "data" / "processed" / "dataset_final.csv"
    assert ruta_csv.exists(), f"No se encontró {ruta_csv}"
    
    df = pd.read_csv(ruta_csv)
    assert len(df) == 100, f"Se esperaban 100 filas, se encontraron {len(df)}"
    
    h = df[df["tipo_agente"] == "humano"]
    ia = df[df["tipo_agente"] == "ia"]
    assert len(h) == 50, f"Se esperaban 50 humanos, se encontraron {len(h)}"
    assert len(ia) == 50, f"Se esperaban 50 IA, se encontraron {len(ia)}"
    
    # 1. Acuerdos de pago
    assert int(h["acuerdo_pago"].sum()) == 7, f"Acuerdos H != 7 ({h['acuerdo_pago'].sum()})"
    assert int(ia["acuerdo_pago"].sum()) == 2, f"Acuerdos IA != 2 ({ia['acuerdo_pago'].sum()})"
    
    # 2. Intención de pago
    assert int(h["intencion_pago"].sum()) == 12, f"Intención H != 12 ({h['intencion_pago'].sum()})"
    assert int(ia["intencion_pago"].sum()) == 1, f"Intención IA != 1 ({ia['intencion_pago'].sum()})"
    
    # 3. Oferta de pago
    assert int(h["oferta_pago"].sum()) == 26, f"Oferta H != 26 ({h['oferta_pago'].sum()})"
    assert int(ia["oferta_pago"].sum()) == 37, f"Oferta IA != 37 ({ia['oferta_pago'].sum()})"
    
    # 4. Descuento
    assert int(h["tiene_descuento"].sum()) == 22, f"Descuentos H != 22 ({h['tiene_descuento'].sum()})"
    assert int(ia["tiene_descuento"].sum()) == 35, f"Descuentos IA != 35 ({ia['tiene_descuento'].sum()})"
    
    # 5. Negociación
    assert int(h["negociacion"].sum()) == 24, f"Negociación H != 24 ({h['negociacion'].sum()})"
    assert int(ia["negociacion"].sum()) == 35, f"Negociación IA != 35 ({ia['negociacion'].sum()})"
    
    # 6. Duración mediana
    mdn_dur_h = float(h["duracion_segundos"].median())
    mdn_dur_ia = float(ia["duracion_segundos"].median())
    assert abs(mdn_dur_h - 168.0) < 0.1, f"Mediana duración H != 168.0 ({mdn_dur_h})"
    assert abs(mdn_dur_ia - 148.5) < 0.2, f"Mediana duración IA != 148.5 ({mdn_dur_ia})"

def test_statistical_calculations():
    """Verifica que los p-valores y cálculos inferenciales coincidan con la auditoría aprobada."""
    ruta_csv = ROOT_DIR / "data" / "processed" / "dataset_final.csv"
    df = pd.read_csv(ruta_csv)
    res = calcular_comparativa(df)
    
    # Acuerdo: Fisher p = 0.1595
    p_acu = res["acuerdo"]["p_fisher"]
    assert abs(p_acu - 0.1595) < 0.005, f"p-valor acuerdo != 0.1595 ({p_acu})"
    assert res["acuerdo"]["dif_pp"] == pytest.approx(10.0, abs=0.1)
    
    # Intención: Chi2 p = 0.0029, FDR sobrevive
    p_int = res["intencion"]["p_raw"]
    assert abs(p_int - 0.0029) < 0.001, f"p-valor intención != 0.0029 ({p_int})"
    assert res["intencion"]["sobrevive_fdr"] is True
    assert res["intencion"]["p_adj"] == pytest.approx(0.0147, abs=0.002)
    
    # Oferta: Chi2 p = 0.0383, FDR no sobrevive (p_adj = 0.0639)
    p_ofe = res["oferta"]["p_raw"]
    assert abs(p_ofe - 0.0383) < 0.002, f"p-valor oferta != 0.0383 ({p_ofe})"
    assert res["oferta"]["sobrevive_fdr"] is False
    assert res["oferta"]["p_adj"] == pytest.approx(0.0639, abs=0.005)
    
    # Conversión condicional oferta -> acuerdo: 7/26 (26.9%) vs 2/37 (5.4%), p = 0.0263
    p_conv = res["conv_oferta"]["p_fisher"]
    assert abs(p_conv - 0.0263) < 0.005, f"p-valor conversión != 0.0263 ({p_conv})"
    assert res["conv_oferta"]["h_pct"] == pytest.approx(26.92, abs=0.1)
    assert res["conv_oferta"]["ia_pct"] == pytest.approx(5.41, abs=0.1)

def test_html_reports_exist():
    """Verifica que los archivos de reporte existan y no estén vacíos."""
    rep_dir = ROOT_DIR / "reports"
    inf = rep_dir / "informe.html"
    anx = rep_dir / "anexo_tecnico.html"
    
    assert inf.exists(), f"Falta {inf}"
    assert anx.exists(), f"Falta {anx}"
    
    inf_text = inf.read_text(encoding="utf-8")
    assert "Comparación de Gestión de Cobranza: Humanos vs. IA" in inf_text
    assert "14.0%" in inf_text and "4.0%" in inf_text
    assert "p = 0.1595" in inf_text
    # Auditoría de lenguaje en HTML ejecutivo: asegurar que no haya términos causales prohibidos
    prohibidos = [
        "los humanos causan", "superioridad persuasiva", "la IA domina",
        "la IA quema el descuento", "la máquina no olvida", "negociación estéril",
        "5 veces más efectivo"
    ]
    for p in prohibidos:
        assert p.lower() not in inf_text.lower(), f"Término prohibido encontrado en informe.html: '{p}'"
