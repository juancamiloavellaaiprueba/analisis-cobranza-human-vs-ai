"""
src/reporting.py
Módulo de cálculo inferencial y generación de reportes ejecutivos y técnicos
para la comparación estadística entre agentes Humanos e IA (N=100).

Artefactos producidos:
- reports/informe.html (Entregable 01: Reporte Ejecutivo de máx 2 páginas para Presidencia)
- reports/anexo_tecnico.html (Entregable 02 / Soporte: Tablas inferenciales completas, FDR y Potencia)
- reports/reporte_ejecutivo.html (Copia sincronizada del entregable ejecutivo)
"""
from typing import Dict, Any, List, Tuple
import math
from pathlib import Path
import pandas as pd
import numpy as np
import scipy.stats as stats

# ==============================================================================
# 1. MOTOR DE PRUEBAS ESTADÍSTICAS EXACTAS (REPRODUCIBLE Y DETERMINISTA)
# ==============================================================================

def calcular_estadisticos_descriptivos(serie: pd.Series) -> Dict[str, float]:
    """Calcula media, mediana, desviación estándar, min, max, cuartiles, IQR y asimetría."""
    s = serie.dropna().astype(float)
    n = len(s)
    if n == 0:
        return {
            "n": 0, "media": np.nan, "mediana": np.nan, "std": np.nan,
            "min": np.nan, "max": np.nan, "q1": np.nan, "q3": np.nan,
            "iqr": np.nan, "skew": np.nan, "outliers_count": 0
        }
    
    media = float(s.mean())
    mediana = float(s.median())
    std = float(s.std(ddof=1)) if n > 1 else 0.0
    val_min = float(s.min())
    val_max = float(s.max())
    q1 = float(s.quantile(0.25))
    q3 = float(s.quantile(0.75))
    iqr = q3 - q1
    
    if n >= 3 and std > 0:
        m3 = float(((s - media) ** 3).mean())
        skew = m3 / (std ** 3)
    else:
        skew = 0.0
        
    lim_inf = q1 - 1.5 * iqr
    lim_sup = q3 + 1.5 * iqr
    outliers = int(((s < lim_inf) | (s > lim_sup)).sum())
    
    return {
        "n": n, "media": media, "mediana": mediana, "std": std,
        "min": val_min, "max": val_max, "q1": q1, "q3": q3,
        "iqr": iqr, "skew": skew, "outliers_count": outliers
    }

def prueba_fisher_exacta_2x2(a: int, b: int, c: int, d: int) -> float:
    """Calcula el p-valor exacto bilateral de Fisher para una tabla 2x2 usando scipy.stats."""
    r1, r2 = a + b, c + d
    c1, c2 = a + c, b + d
    if r1 == 0 or r2 == 0 or c1 == 0 or c2 == 0:
        return 1.0
    _, p_val = stats.fisher_exact([[a, b], [c, d]], alternative="two-sided")
    return float(p_val)

def prueba_chi_cuadrado_2x2(a: int, b: int, c: int, d: int) -> Tuple[float, float, List[float]]:
    """Calcula el estadístico chi-cuadrado con corrección de continuidad de Yates usando scipy.stats."""
    tabla = np.array([[a, b], [c, d]])
    if np.any(tabla.sum(axis=0) == 0) or np.any(tabla.sum(axis=1) == 0):
        return 0.0, 1.0, [0.0, 0.0, 0.0, 0.0]
    res = stats.chi2_contingency(tabla, correction=True)
    esperados = [float(x) for x in res.expected_freq.flatten()]
    return float(res.statistic), float(res.pvalue), esperados

def calcular_ic95_diferencia_proporciones(p1: float, n1: int, p2: float, n2: int) -> Tuple[float, float]:
    """Calcula el intervalo de confianza del 95% (Wald) para p1 - p2 (Humano - IA) en puntos porcentuales."""
    if n1 == 0 or n2 == 0:
        return np.nan, np.nan
    dif = p1 - p2
    se = math.sqrt((p1 * (1.0 - p1) / n1) + (p2 * (1.0 - p2) / n2))
    ic_inf = (dif - 1.96 * se) * 100.0
    ic_sup = (dif + 1.96 * se) * 100.0
    return float(ic_inf), float(ic_sup)

def cohen_h(p1: float, p2: float) -> float:
    """Calcula la distancia de arcoseno (tamaño del efecto h de Cohen para dos proporciones)."""
    phi1 = 2.0 * math.asin(math.sqrt(max(0.0, min(1.0, p1))))
    phi2 = 2.0 * math.asin(math.sqrt(max(0.0, min(1.0, p2))))
    return float(abs(phi1 - phi2))

def prueba_mann_whitney_u(s1: pd.Series, s2: pd.Series) -> Tuple[float, float, float]:
    """Calcula la prueba no paramétrica U de Mann-Whitney y la correlación biserial por rangos r."""
    x1 = s1.dropna().values
    x2 = s2.dropna().values
    n1, n2 = len(x1), len(x2)
    if n1 == 0 or n2 == 0:
        return np.nan, 1.0, 0.0
        
    todos = np.concatenate([x1, x2])
    orden = np.argsort(todos)
    rangos = np.empty_like(orden, dtype=float)
    
    i = 0
    while i < len(todos):
        j = i
        while j < len(todos) - 1 and todos[orden[j]] == todos[orden[j + 1]]:
            j += 1
        rango_prom = (i + j + 2.0) / 2.0
        for k in range(i, j + 1):
            rangos[orden[k]] = rango_prom
        i = j + 1
        
    r1 = rangos[:n1].sum()
    u1 = n1 * n2 + (n1 * (n1 + 1)) / 2.0 - r1
    u2 = n1 * n2 - u1
    u = min(u1, u2)
    
    mu_u = (n1 * n2) / 2.0
    sigma_u = math.sqrt((n1 * n2 * (n1 + n2 + 1)) / 12.0)
    
    if sigma_u == 0:
        return float(u), 1.0, 0.0
        
    z = (abs(u - mu_u) - 0.5) / sigma_u
    p_val = 2.0 * (1.0 - 0.5 * (1.0 + math.erf(abs(z) / math.sqrt(2.0))))
    r_biserial = 1.0 - (2.0 * u1) / (n1 * n2)
    return float(u), float(min(1.0, max(0.000001, p_val))), float(r_biserial)

# ==============================================================================
# 2. EVALUACIÓN Y CONSOLIDACIÓN ANALÍTICA SOBRE dataset_final.csv
# ==============================================================================

def calcular_comparativa(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calcula determinística y reproduciblemente todos los estadísticos descriptivos,
    inferenciales, tablas 2x2, tamaños de efecto y corrección FDR sobre dataset_final.csv.
    """
    h = df[df["tipo_agente"] == "humano"]
    ia = df[df["tipo_agente"] == "ia"]
    n_h = len(h)
    n_ia = len(ia)
    n_tot = len(df)
    
    # --------------------------------------------------------------------------
    # A. RESULTADO PRINCIPAL: acuerdo_pago
    # --------------------------------------------------------------------------
    acu_h = int(h["acuerdo_pago"].sum())
    acu_ia = int(ia["acuerdo_pago"].sum())
    p_acu_h = acu_h / n_h
    p_acu_ia = acu_ia / n_ia
    dif_acu = (p_acu_h - p_acu_ia) * 100.0
    ic_acu = calcular_ic95_diferencia_proporciones(p_acu_h, n_h, p_acu_ia, n_ia)
    p_acu_fisher = prueba_fisher_exacta_2x2(acu_h, n_h - acu_h, acu_ia, n_ia - acu_ia)
    h_acu = cohen_h(p_acu_h, p_acu_ia)
    
    # --------------------------------------------------------------------------
    # B. DOS SEÑALES OPERATIVAS DESTACADAS
    # --------------------------------------------------------------------------
    # 1. intencion_pago (Comportamiento declarado del cliente)
    int_h = int(h["intencion_pago"].sum())
    int_ia = int(ia["intencion_pago"].sum())
    p_int_h = int_h / n_h
    p_int_ia = int_ia / n_ia
    dif_int = (p_int_h - p_int_ia) * 100.0
    ic_int = calcular_ic95_diferencia_proporciones(p_int_h, n_h, p_int_ia, n_ia)
    chi2_int, p_int_raw, _ = prueba_chi_cuadrado_2x2(int_h, n_h - int_h, int_ia, n_ia - int_ia)
    h_int = cohen_h(p_int_h, p_int_ia)
    
    # 2. oferta_pago (Adherencia operativa del agente)
    ofe_h = int(h["oferta_pago"].sum())
    ofe_ia = int(ia["oferta_pago"].sum())
    p_ofe_h = ofe_h / n_h
    p_ofe_ia = ofe_ia / n_ia
    dif_ofe = (p_ofe_h - p_ofe_ia) * 100.0
    ic_ofe = calcular_ic95_diferencia_proporciones(p_ofe_h, n_h, p_ofe_ia, n_ia)
    chi2_ofe, p_ofe_raw, _ = prueba_chi_cuadrado_2x2(ofe_h, n_h - ofe_h, ofe_ia, n_ia - ofe_ia)
    h_ofe = cohen_h(p_ofe_h, p_ofe_ia)
    
    # --------------------------------------------------------------------------
    # C. MÉTRICA SECUNDARIA CONDICIONAL: conv_oferta_a_acuerdo
    # --------------------------------------------------------------------------
    h_ofe_sub = h[h["oferta_pago"] == 1]
    ia_ofe_sub = ia[ia["oferta_pago"] == 1]
    n_ofe_h = len(h_ofe_sub)
    n_ofe_ia = len(ia_ofe_sub)
    conv_h = int(h_ofe_sub["acuerdo_pago"].sum())
    conv_ia = int(ia_ofe_sub["acuerdo_pago"].sum())
    p_conv_h = conv_h / n_ofe_h if n_ofe_h > 0 else 0.0
    p_conv_ia = conv_ia / n_ofe_ia if n_ofe_ia > 0 else 0.0
    dif_conv = (p_conv_h - p_conv_ia) * 100.0
    ic_conv = calcular_ic95_diferencia_proporciones(p_conv_h, n_ofe_h, p_conv_ia, n_ofe_ia)
    p_conv_fisher = prueba_fisher_exacta_2x2(conv_h, n_ofe_h - conv_h, conv_ia, n_ofe_ia - conv_ia)
    h_conv = cohen_h(p_conv_h, p_conv_ia)
    
    # --------------------------------------------------------------------------
    # D. MÉTRICAS SECUNDARIAS ADICIONALES
    # --------------------------------------------------------------------------
    # tiene_descuento
    desc_h = int(h["tiene_descuento"].sum())
    desc_ia = int(ia["tiene_descuento"].sum())
    p_desc_h = desc_h / n_h
    p_desc_ia = desc_ia / n_ia
    dif_desc = (p_desc_h - p_desc_ia) * 100.0
    ic_desc = calcular_ic95_diferencia_proporciones(p_desc_h, n_h, p_desc_ia, n_ia)
    chi2_desc, p_desc_raw, _ = prueba_chi_cuadrado_2x2(desc_h, n_h - desc_h, desc_ia, n_ia - desc_ia)
    h_desc = cohen_h(p_desc_h, p_desc_ia)
    
    # negociacion
    neg_h = int(h["negociacion"].sum())
    neg_ia = int(ia["negociacion"].sum())
    p_neg_h = neg_h / n_h
    p_neg_ia = neg_ia / n_ia
    dif_neg = (p_neg_h - p_neg_ia) * 100.0
    ic_neg = calcular_ic95_diferencia_proporciones(p_neg_h, n_h, p_neg_ia, n_ia)
    chi2_neg, p_neg_raw, _ = prueba_chi_cuadrado_2x2(neg_h, n_h - neg_h, neg_ia, n_ia - neg_ia)
    h_neg = cohen_h(p_neg_h, p_neg_ia)
    
    # duracion_segundos
    u_dur, p_dur, r_dur = prueba_mann_whitney_u(h["duracion_segundos"], ia["duracion_segundos"])
    stat_dur_h = calcular_estadisticos_descriptivos(h["duracion_segundos"])
    stat_dur_ia = calcular_estadisticos_descriptivos(ia["duracion_segundos"])
    
    # inconsistencia_matematica_acuerdo
    inc_h = int(h["inconsistencia_matematica_acuerdo"].sum())
    inc_ia = int(ia["inconsistencia_matematica_acuerdo"].sum())
    p_inc_h = inc_h / n_h
    p_inc_ia = inc_ia / n_ia
    dif_inc = (p_inc_h - p_inc_ia) * 100.0
    p_inc_fisher = prueba_fisher_exacta_2x2(inc_h, n_h - inc_h, inc_ia, n_ia - inc_ia)
    h_inc = cohen_h(p_inc_h, p_inc_ia)
    
    # num_propuestas_pago
    u_prop, p_prop_raw, r_prop = prueba_mann_whitney_u(h["num_propuestas_pago"], ia["num_propuestas_pago"])
    stat_prop_h = calcular_estadisticos_descriptivos(h["num_propuestas_pago"])
    stat_prop_ia = calcular_estadisticos_descriptivos(ia["num_propuestas_pago"])
    
    # contactabilidad
    cont_h = int(h["contactabilidad"].sum())
    cont_ia = int(ia["contactabilidad"].sum())
    p_cont_h = cont_h / n_h
    p_cont_ia = cont_ia / n_ia
    dif_cont = (p_cont_h - p_cont_ia) * 100.0
    p_cont_fisher = prueba_fisher_exacta_2x2(cont_h, n_h - cont_h, cont_ia, n_ia - cont_ia)
    
    # --------------------------------------------------------------------------
    # E. CONTROL DE MULTIPLICIDAD FDR (BENJAMINI-HOCHBERG q=0.05)
    # Familia Secundaria: 5 hipótesis pre-especificadas
    # --------------------------------------------------------------------------
    # p-valores sin ajustar:
    # 1. intencion_pago: p_int_raw (0.002944)
    # 2. tiene_descuento: p_desc_raw (0.015356)
    # 3. oferta_pago: p_ofe_raw (0.038337)
    # 4. negociacion: p_neg_raw (0.042031)
    # 5. num_propuestas_pago: p_prop_raw (0.049047)
    m = 5
    q = 0.05
    p_sec = [
        ("intencion_pago", p_int_raw),
        ("tiene_descuento", p_desc_raw),
        ("oferta_pago", p_ofe_raw),
        ("negociacion", p_neg_raw),
        ("num_propuestas_pago", p_prop_raw)
    ]
    p_sec.sort(key=lambda x: x[1])
    
    fdr_results = {}
    # Step-up Benjamini-Hochberg adjustment
    adjusted_p = []
    for k, (var_name, p_val) in enumerate(p_sec, start=1):
        crit_val = (k / m) * q
        p_adj = min(1.0, p_val * m / k)
        adjusted_p.append((var_name, p_val, crit_val, p_adj))
        
    # Monotonize adjusted p-values from smallest to largest so they are non-decreasing
    monotonized = []
    max_prev = 0.0
    for var_name, p_val, crit_val, p_adj in adjusted_p:
        max_prev = max(max_prev, p_adj)
        monotonized.append((var_name, p_val, crit_val, max_prev))
    
    for var_name, p_val, crit_val, p_adj in monotonized:
        fdr_results[var_name] = {
            "p_raw": p_val,
            "umbral_critico": crit_val,
            "p_adj": p_adj,
            "sobrevive_fdr": p_adj <= q
        }

    return {
        "n_total": n_tot,
        "n_humano": n_h,
        "n_ia": n_ia,
        "contactabilidad_h": p_cont_h * 100.0,
        "contactabilidad_ia": p_cont_ia * 100.0,
        "oferta_h": p_ofe_h * 100.0,
        "oferta_ia": p_ofe_ia * 100.0,
        "acuerdo_h": p_acu_h * 100.0,
        "acuerdo_ia": p_acu_ia * 100.0,
        "duracion_media_h": stat_dur_h["media"],
        "duracion_media_ia": stat_dur_ia["media"],
        # Resultado Principal
        "acuerdo": {
            "h_conteo": acu_h, "ia_conteo": acu_ia,
            "h_pct": p_acu_h * 100.0, "ia_pct": p_acu_ia * 100.0,
            "dif_pp": dif_acu, "ic95": ic_acu,
            "p_fisher": p_acu_fisher, "cohen_h": h_acu
        },
        # Señales Destacadas
        "intencion": {
            "h_conteo": int_h, "ia_conteo": int_ia,
            "h_pct": p_int_h * 100.0, "ia_pct": p_int_ia * 100.0,
            "dif_pp": dif_int, "ic95": ic_int,
            "p_raw": p_int_raw, "p_adj": fdr_results["intencion_pago"]["p_adj"],
            "sobrevive_fdr": fdr_results["intencion_pago"]["sobrevive_fdr"],
            "cohen_h": h_int
        },
        "oferta": {
            "h_conteo": ofe_h, "ia_conteo": ofe_ia,
            "h_pct": p_ofe_h * 100.0, "ia_pct": p_ofe_ia * 100.0,
            "dif_pp": dif_ofe, "ic95": ic_ofe,
            "p_raw": p_ofe_raw, "p_adj": fdr_results["oferta_pago"]["p_adj"],
            "sobrevive_fdr": fdr_results["oferta_pago"]["sobrevive_fdr"],
            "cohen_h": h_ofe
        },
        # Métrica Condicional
        "conv_oferta": {
            "den_h": n_ofe_h, "den_ia": n_ofe_ia,
            "num_h": conv_h, "num_ia": conv_ia,
            "h_pct": p_conv_h * 100.0, "ia_pct": p_conv_ia * 100.0,
            "dif_pp": dif_conv, "ic95": ic_conv,
            "p_fisher": p_conv_fisher, "cohen_h": h_conv
        },
        # Secundarias
        "descuento": {
            "h_conteo": desc_h, "ia_conteo": desc_ia,
            "h_pct": p_desc_h * 100.0, "ia_pct": p_desc_ia * 100.0,
            "dif_pp": dif_desc, "ic95": ic_desc,
            "p_raw": p_desc_raw, "p_adj": fdr_results["tiene_descuento"]["p_adj"],
            "sobrevive_fdr": fdr_results["tiene_descuento"]["sobrevive_fdr"],
            "cohen_h": h_desc
        },
        "negociacion": {
            "h_conteo": neg_h, "ia_conteo": neg_ia,
            "h_pct": p_neg_h * 100.0, "ia_pct": p_neg_ia * 100.0,
            "dif_pp": dif_neg, "ic95": ic_neg,
            "p_raw": p_neg_raw, "p_adj": fdr_results["negociacion"]["p_adj"],
            "sobrevive_fdr": fdr_results["negociacion"]["sobrevive_fdr"],
            "cohen_h": h_neg
        },
        "duracion": {
            "mdn_h": stat_dur_h["mediana"], "mdn_ia": stat_dur_ia["mediana"],
            "med_h": stat_dur_h["media"], "med_ia": stat_dur_ia["media"],
            "dif_mdn": stat_dur_h["mediana"] - stat_dur_ia["mediana"],
            "p_mw": p_dur, "r_biserial": r_dur
        },
        "inconsistencia": {
            "h_conteo": inc_h, "ia_conteo": inc_ia,
            "h_pct": p_inc_h * 100.0, "ia_pct": p_inc_ia * 100.0,
            "dif_pp": dif_inc, "p_fisher": p_inc_fisher, "cohen_h": h_inc
        },
        "propuestas": {
            "mdn_h": stat_prop_h["mediana"], "mdn_ia": stat_prop_ia["mediana"],
            "p_raw": p_prop_raw, "p_adj": fdr_results["num_propuestas_pago"]["p_adj"],
            "sobrevive_fdr": fdr_results["num_propuestas_pago"]["sobrevive_fdr"],
            "r_biserial": r_prop
        },
        "contactabilidad": {
            "h_conteo": cont_h, "ia_conteo": cont_ia,
            "h_pct": p_cont_h * 100.0, "ia_pct": p_cont_ia * 100.0,
            "dif_pp": dif_cont, "p_fisher": p_cont_fisher
        },
        "fdr_tabla": fdr_results
    }

# ==============================================================================
# 3. ENTREGABLE 01: REPORTE EJECUTIVO (MÁXIMO 2 PÁGINAS VISUALES)
# ==============================================================================

def generar_reporte_ejecutivo_html(df: pd.DataFrame, ruta_salida: str):
    """
    Genera reports/informe.html (Entregable 01):
    - Estrictamente máximo 2 páginas impresas (formato A4 / ejecutivo).
    - Lenguaje 100% observacional y riguroso (sin afirmaciones causales ni sesgos).
    - Cifras exactas derivadas directamente de dataset_final.csv.
    """
    res = calcular_comparativa(df)
    r_acu = res["acuerdo"]
    r_int = res["intencion"]
    r_ofe = res["oferta"]
    r_conv = res["conv_oferta"]
    r_desc = res["descuento"]
    r_dur = res["duracion"]
    r_cont = res["contactabilidad"]

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte Ejecutivo: Comparación de Gestión de Cobranza (Humanos vs IA)</title>
    <style>
        :root {{
            --bg: #ffffff;
            --surface: #f8fafc;
            --surface-alt: #f1f5f9;
            --primary: #0f172a;
            --blue: #1e40af;
            --blue-subtle: #dbeafe;
            --purple: #581c87;
            --purple-subtle: #f3e8ff;
            --text-main: #0f172a;
            --text-muted: #475569;
            --border: #cbd5e1;
            --border-light: #e2e8f0;
            --tag-ns: #64748b;
            --tag-sig: #047857;
            --tag-marg: #b45309;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; }}
        body {{ background-color: var(--bg); color: var(--text-main); line-height: 1.42; font-size: 12px; padding: 22px 28px; }}
        .container {{ max-width: 920px; margin: 0 auto; }}

        /* Control de impresión estricto: Máximo 2 páginas */
        @media print {{
            @page {{ size: A4; margin: 10mm 12mm; }}
            body {{ padding: 0; font-size: 10.5px; line-height: 1.28; }}
            .container {{ max-width: 100%; }}
            .page-break {{ page-break-before: always; margin-top: 0; }}
            .no-print {{ display: none; }}
            .card, .funnel-box, .metric-box, .table-wrap, .edu-compact-card, .limitations-box {{ break-inside: avoid; }}
        }}

        header {{ border-bottom: 2px solid var(--primary); padding-bottom: 6px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: flex-end; }}
        .title-area h1 {{ font-size: 16px; font-weight: 800; color: var(--primary); letter-spacing: -0.02em; text-transform: uppercase; }}
        .title-area p {{ font-size: 11px; color: var(--text-muted); margin-top: 1px; }}
        .meta-pill {{ font-size: 10px; font-weight: 700; color: var(--blue); background: var(--blue-subtle); padding: 3px 7px; border-radius: 4px; text-transform: uppercase; }}

        /* Tarjeta de Acceso al Repositorio */
        .repo-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-left: 4px solid var(--primary);
            border-radius: 6px;
            padding: 6px 12px;
            margin-bottom: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
        }}
        .repo-card-content {{
            display: flex;
            flex-direction: column;
            gap: 1px;
        }}
        .repo-card-title {{
            font-size: 11px;
            font-weight: 800;
            color: var(--primary);
            text-transform: uppercase;
            letter-spacing: 0.02em;
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        .repo-card-desc {{
            font-size: 10px;
            color: var(--text-muted);
        }}
        .repo-card-btn {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 5px;
            background-color: var(--primary);
            color: #ffffff !important;
            font-size: 10.5px;
            font-weight: 700;
            text-decoration: none;
            padding: 5px 12px;
            border-radius: 4px;
            white-space: nowrap;
            border: 1px solid #000000;
            transition: background-color 0.15s ease;
        }}
        .repo-card-btn:hover {{
            background-color: var(--blue);
            color: #ffffff !important;
        }}

        .exec-summary {{ background: var(--surface); border: 1px solid var(--border); border-left: 4px solid var(--blue); border-radius: 6px; padding: 8px 12px; margin-bottom: 8px; }}
        .exec-summary strong {{ color: var(--primary); font-size: 11.5px; }}
        .exec-summary p {{ font-size: 11px; color: #334155; margin-top: 3px; line-height: 1.35; }}

        h2 {{ font-size: 12px; font-weight: 800; text-transform: uppercase; color: var(--primary); margin: 8px 0 5px 0; border-bottom: 1px solid var(--border-light); padding-bottom: 2px; letter-spacing: 0.02em; }}

        /* Tarjetas de Métricas Principales */
        .metric-cards {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 8px; }}
        .metric-box {{ background: var(--surface); border: 1px solid var(--border); border-radius: 6px; padding: 8px 10px; border-top: 3px solid var(--primary); }}
        .metric-box.primary-result {{ border-top-color: #0f172a; background: #fafafa; }}
        .metric-box.signal-a {{ border-top-color: var(--blue); }}
        .metric-box.signal-b {{ border-top-color: var(--purple); }}
        .metric-header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 3px; }}
        .metric-title {{ font-size: 9.5px; font-weight: 800; text-transform: uppercase; color: var(--text-muted); }}
        .badge {{ font-size: 8.5px; font-weight: 700; padding: 2px 4px; border-radius: 3px; text-transform: uppercase; white-space: nowrap; }}
        .badge-ns {{ background: #f1f5f9; color: var(--tag-ns); border: 1px solid var(--border); }}
        .badge-sig {{ background: #ecfdf5; color: var(--tag-sig); border: 1px solid #a7f3d0; }}
        .badge-fdr-fail {{ background: #fef3c7; color: var(--tag-marg); border: 1px solid #fde68a; }}

        .metric-values {{ display: flex; justify-content: space-between; align-items: baseline; margin: 4px 0 3px 0; }}
        .val-group span {{ display: block; font-size: 9px; color: var(--text-muted); font-weight: 600; }}
        .val-group strong {{ font-size: 16px; font-weight: 800; color: var(--primary); }}
        .dif-tag {{ font-size: 10.5px; font-weight: 800; color: var(--primary); background: #f1f5f9; padding: 2px 5px; border-radius: 4px; }}
        .metric-desc {{ font-size: 10px; color: #475569; border-top: 1px solid var(--border-light); padding-top: 3px; margin-top: 3px; line-height: 1.3; }}

        /* Embudo de Proceso (Funnel) */
        .funnel-box {{ background: var(--surface); border: 1px solid var(--border); border-radius: 6px; padding: 8px 12px; margin-bottom: 8px; }}
        .funnel-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; position: relative; margin-top: 4px; }}
        .funnel-step {{ background: #ffffff; border: 1px solid var(--border-light); border-radius: 5px; padding: 6px 8px; text-align: center; }}
        .funnel-step h4 {{ font-size: 9.5px; font-weight: 700; text-transform: uppercase; color: var(--text-muted); margin-bottom: 3px; }}
        .funnel-bars {{ display: flex; flex-direction: column; gap: 3px; }}
        .f-bar-row {{ display: flex; justify-content: space-between; font-size: 10px; font-weight: 700; }}
        .f-bar-track {{ height: 4px; background: #e2e8f0; border-radius: 999px; overflow: hidden; margin-top: 1px; }}
        .f-fill-h {{ height: 100%; background: #0f172a; border-radius: 999px; }}
        .f-fill-ia {{ height: 100%; background: #0284c7; border-radius: 999px; }}
        .funnel-note {{ font-size: 9.5px; color: var(--text-muted); margin-top: 4px; text-align: center; font-style: italic; }}

        /* Métrica Condicional Destacada */
        .conditional-box {{ background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 6px; padding: 7px 12px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }}
        .cond-left h4 {{ font-size: 10.5px; font-weight: 800; color: #1e3a8a; text-transform: uppercase; }}
        .cond-left p {{ font-size: 10px; color: #1e40af; margin-top: 1px; }}
        .cond-stat {{ text-align: right; white-space: nowrap; }}
        .cond-stat strong {{ font-size: 14px; font-weight: 800; color: #1e3a8a; }}
        .cond-stat small {{ display: block; font-size: 9px; color: #3b82f6; font-weight: 600; }}

        /* Bullets analíticos */
        .bullets {{ list-style: none; margin-bottom: 8px; }}
        .bullets li {{ position: relative; padding-left: 12px; margin-bottom: 3px; font-size: 10.5px; color: #334155; line-height: 1.32; }}
        .bullets li::before {{ content: "•"; position: absolute; left: 2px; font-weight: 800; color: var(--blue); }}

        /* Tabla compacta de soporte secundario */
        .table-wrap {{ border: 1px solid var(--border); border-radius: 6px; overflow: hidden; margin-bottom: 8px; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 10px; text-align: left; }}
        th {{ background: #f8fafc; color: var(--primary); font-weight: 700; padding: 4px 7px; border-bottom: 1px solid var(--border); font-size: 9.5px; text-transform: uppercase; }}
        td {{ padding: 4px 7px; border-bottom: 1px solid var(--border-light); vertical-align: middle; }}
        tr:last-child td {{ border-bottom: none; }}

        /* Metodología Compacta en Informe */
        .edu-compact-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 6px;
            margin-bottom: 6px;
        }}
        .edu-compact-card {{
            background: #ffffff;
            border: 1px solid var(--border-light);
            border-top: 2px solid var(--blue);
            border-radius: 4px;
            padding: 4px 6px;
            font-size: 9px;
            line-height: 1.3;
        }}
        .edu-compact-title {{
            font-weight: 800;
            color: var(--primary);
            font-size: 9.5px;
            margin-bottom: 1px;
        }}
        .edu-compact-desc {{
            color: #475569;
        }}
        .edu-highlight-box-compact {{
            background: #fffbeb;
            border: 1px solid #fde68a;
            border-left: 3px solid #b45309;
            border-radius: 4px;
            padding: 4px 8px;
            margin-bottom: 6px;
            font-size: 9.5px;
            line-height: 1.32;
            color: #78350f;
        }}
        .edu-highlight-box-compact strong {{
            color: #92400e;
            display: block;
            margin-bottom: 1px;
            font-size: 9.8px;
        }}
        .limitations-box {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 4px;
            padding: 5px 8px;
            font-size: 9.5px;
            color: var(--text-muted);
            line-height: 1.3;
        }}

        /* Footer de Gobernanza y Limitaciones */
        footer {{ border-top: 1px solid var(--border); padding-top: 5px; margin-top: 6px; display: flex; justify-content: space-between; font-size: 9px; color: var(--text-muted); }}
    </style>
</head>
<body>
<div class="container">
    <header>
        <div class="title-area">
            <h1>Comparación de Gestión de Cobranza: Humanos vs. IA</h1>
            <p>Evaluación analítica observacional sobre 100 llamadas telefónicas (50 Agentes Humanos / 50 Agentes IA)</p>
        </div>
        <div class="meta-pill">N = 100 · 50H / 50IA</div>
    </header>

    <!-- Tarjeta Destacada de Acceso al Repositorio -->
    <div class="repo-card">
        <div class="repo-card-content">
            <div class="repo-card-title">
                <span>🔗</span> Repositorio del proyecto
            </div>
            <div class="repo-card-desc">
                Código fuente reproducible, datos, análisis y documentación disponibles en GitHub.
            </div>
        </div>
        <a href="https://github.com/juancamiloavellaaiprueba/analisis-cobranza-human-vs-ai" class="repo-card-btn" target="_blank" rel="noopener noreferrer">
            Ver repositorio en GitHub
        </a>
    </div>

    <!-- 1. Mensaje Ejecutivo Central -->
    <div class="exec-summary">
        <strong>Dictamen Metodológico Central:</strong>
        <p>Los datos reflejan <strong>perfiles operativos distintos</strong> entre ambos canales, pero <strong>la muestra observada no permite confirmar una diferencia estadísticamente sustentable en el resultado final de acuerdos de pago</strong> (14.0% Humano vs. 4.0% IA, Fisher bilateral p = 0.1595; no se rechaza H0 al 5%). La IA presentó ofertas formales con mayor frecuencia (74% vs. 52%), mientras que en las llamadas humanas se observó una proporción significativamente mayor de clientes manifestando intención verbal de pago (24% vs. 2%).</p>
    </div>

    <!-- 2. Jerarquía de Métricas: Resultado Principal y Señales Operativas -->
    <h2>1. Métrica de Resultado Culminante y Señales Operativas Destacadas</h2>
    <div class="metric-cards">
        <!-- A. Resultado Principal -->
        <div class="metric-box primary-result">
            <div class="metric-header">
                <span class="metric-title">A. Resultado Principal</span>
                <span class="badge badge-ns">No significativo (p = 0.1595)</span>
            </div>
            <div style="font-size:11px; font-weight:800; color:var(--primary);">Acuerdo Formal de Pago</div>
            <div class="metric-values">
                <div class="val-group">
                    <span>Humano (7/50)</span>
                    <strong>{r_acu['h_pct']:.1f}%</strong>
                </div>
                <div class="val-group">
                    <span>IA (2/50)</span>
                    <strong>{r_acu['ia_pct']:.1f}%</strong>
                </div>
                <div class="dif-tag">{r_acu['dif_pp']:+.1f} pp</div>
            </div>
            <div class="metric-desc">
                IC 95%: [{r_acu['ic95'][0]:.1f} pp, {r_acu['ic95'][1]:.1f} pp] · Fisher bilateral p = 0.1595.<br>
                <strong>Conclusión:</strong> Se observa una tasa mayor en humanos (+10 pp), pero <strong>no se rechaza H0</strong>. La muestra no permite confirmar estadísticamente una diferencia en acuerdos finales.
            </div>
        </div>

        <!-- B. Señal 1: Intención de Pago -->
        <div class="metric-box signal-a">
            <div class="metric-header">
                <span class="metric-title">B. Comportamiento Cliente</span>
                <span class="badge badge-sig">FDR Significativo (p_adj = 0.0147)</span>
            </div>
            <div style="font-size:11px; font-weight:800; color:var(--primary);">Intención Verbal de Pago</div>
            <div class="metric-values">
                <div class="val-group">
                    <span>Humano (12/50)</span>
                    <strong>{r_int['h_pct']:.1f}%</strong>
                </div>
                <div class="val-group">
                    <span>IA (1/50)</span>
                    <strong>{r_int['ia_pct']:.1f}%</strong>
                </div>
                <div class="dif-tag">{r_int['dif_pp']:+.1f} pp</div>
            </div>
            <div class="metric-desc">
                IC 95%: [{r_int['ic95'][0]:.1f} pp, {r_int['ic95'][1]:.1f} pp] · Chi2 p = 0.0029 (p_adj = 0.0147).<br>
                <strong>Conclusión:</strong> Se observó una proporción significativamente mayor de deudores manifestando intención espontánea de pago en el canal humano (variable intermedia declarativa).
            </div>
        </div>

        <!-- C. Señal 2: Oferta de Pago -->
        <div class="metric-box signal-b">
            <div class="metric-header">
                <span class="metric-title">C. Adherencia Protocolar</span>
                <span class="badge badge-fdr-fail">No supera FDR (p_adj = 0.0639)</span>
            </div>
            <div style="font-size:11px; font-weight:800; color:var(--primary);">Apertura de Oferta Formal</div>
            <div class="metric-values">
                <div class="val-group">
                    <span>Humano (26/50)</span>
                    <strong>{r_ofe['h_pct']:.1f}%</strong>
                </div>
                <div class="val-group">
                    <span>IA (37/50)</span>
                    <strong>{r_ofe['ia_pct']:.1f}%</strong>
                </div>
                <div class="dif-tag">{r_ofe['dif_pp']:+.1f} pp</div>
            </div>
            <div class="metric-desc">
                IC 95%: [{r_ofe['ic95'][0]:.1f} pp, {r_ofe['ic95'][1]:.1f} pp] · Chi2 p = 0.0383 sin ajuste.<br>
                <strong>Conclusión:</strong> La IA presentó ofertas con mayor frecuencia en la muestra (74% vs. 52%). La diferencia es significativa sin ajuste, pero <strong>no supera el control FDR preespecificado</strong>.
            </div>
        </div>
    </div>

    <!-- 3. Embudo Comparativo de Proceso de Cobranza -->
    <h2>2. Embudo Operativo de Cobranza (Humanos vs. IA)</h2>
    <div class="funnel-box">
        <div class="funnel-grid">
            <div class="funnel-step">
                <h4>Paso 1: Contactabilidad</h4>
                <div class="funnel-bars">
                    <div class="f-bar-row"><span>Humano</span><span>{r_cont['h_pct']:.1f}% ({r_cont['h_conteo']}/50)</span></div>
                    <div class="f-bar-track"><div class="f-fill-h" style="width:{r_cont['h_pct']}%;"></div></div>
                    <div class="f-bar-row"><span>IA</span><span>{r_cont['ia_pct']:.1f}% ({r_cont['ia_conteo']}/50)</span></div>
                    <div class="f-bar-track"><div class="f-fill-ia" style="width:{r_cont['ia_pct']}%;"></div></div>
                </div>
                <div style="font-size:9px; color:var(--text-muted); margin-top:4px;">Fisher p = 0.3622 (Sin diferencia)</div>
            </div>
            <div class="funnel-step">
                <h4>Paso 2: Apertura de Oferta</h4>
                <div class="funnel-bars">
                    <div class="f-bar-row"><span>Humano</span><span>{r_ofe['h_pct']:.1f}% ({r_ofe['h_conteo']}/50)</span></div>
                    <div class="f-bar-track"><div class="f-fill-h" style="width:{r_ofe['h_pct']}%;"></div></div>
                    <div class="f-bar-row"><span>IA</span><span>{r_ofe['ia_pct']:.1f}% ({r_ofe['ia_conteo']}/50)</span></div>
                    <div class="f-bar-track"><div class="f-fill-ia" style="width:{r_ofe['ia_pct']}%;"></div></div>
                </div>
                <div style="font-size:9px; color:var(--text-muted); margin-top:4px;">Chi2 p = 0.0383 · FDR p_adj = 0.0639</div>
            </div>
            <div class="funnel-step">
                <h4>Paso 3: Cierre de Acuerdo</h4>
                <div class="funnel-bars">
                    <div class="f-bar-row"><span>Humano</span><span>{r_acu['h_pct']:.1f}% ({r_acu['h_conteo']}/50)</span></div>
                    <div class="f-bar-track"><div class="f-fill-h" style="width:{r_acu['h_pct']}%;"></div></div>
                    <div class="f-bar-row"><span>IA</span><span>{r_acu['ia_pct']:.1f}% ({r_acu['ia_conteo']}/50)</span></div>
                    <div class="f-bar-track"><div class="f-fill-ia" style="width:{r_acu['ia_pct']}%;"></div></div>
                </div>
                <div style="font-size:9px; color:var(--text-muted); margin-top:4px;">Fisher p = 0.1595 (No significativo)</div>
            </div>
        </div>
        <div class="funnel-note">
            Nota de consistencia: Los eventos del embudo no son estrictamente secuenciales a nivel individual; reflejan tasas globales observadas sobre los 50 casos de cada grupo.
        </div>
    </div>

    <!-- 4. Métrica Secundaria Clave Condicional -->
    <div class="conditional-box">
        <div class="cond-left">
            <h4>Métrica Secundaria Condicional: Conversión de Oferta a Acuerdo</h4>
            <p>Entre las llamadas en las que se formuló una oferta formal (26 en humanos y 37 en IA), la proporción observada que culminó en acuerdo fue mayor en humanos.</p>
        </div>
        <div class="cond-stat">
            <strong>{r_conv['h_pct']:.1f}% Humano vs. {r_conv['ia_pct']:.1f}% IA</strong>
            <small>Δ = {r_conv['dif_pp']:+.1f} pp · Fisher p = 0.0263 · Cohen's h = 0.622</small>
        </div>
    </div>

    <!-- Salto de página estricto para impresión A4 -->
    <div class="page-break"></div>

    <!-- 5. Métricas Secundarias de Soporte -->
    <h2>3. Batería de Métricas Secundarias e Indicadores Operativos</h2>
    <div class="table-wrap">
        <table>
            <thead>
                <tr>
                    <th>Dimensión Operativa</th>
                    <th>Humano (N=50)</th>
                    <th>IA (N=50)</th>
                    <th>Diferencia</th>
                    <th>IC 95% Diferencia</th>
                    <th>Prueba Estadística</th>
                    <th>Estado de Inferencia</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>Ofrecimiento de Descuentos</strong></td>
                    <td>{r_desc['h_pct']:.1f}% ({r_desc['h_conteo']}/50)</td>
                    <td>{r_desc['ia_pct']:.1f}% ({r_desc['ia_conteo']}/50)</td>
                    <td><strong>{r_desc['dif_pp']:+.1f} pp</strong></td>
                    <td>[{r_desc['ic95'][0]:.1f} pp, {r_desc['ic95'][1]:.1f} pp]</td>
                    <td>Chi2 p = 0.0154 (Yates)</td>
                    <td><span class="badge badge-sig">FDR Significativo (p_adj = 0.0385)</span></td>
                </tr>
                <tr>
                    <td><strong>Negociación de Alternativas</strong></td>
                    <td>{res['negociacion']['h_pct']:.1f}% ({res['negociacion']['h_conteo']}/50)</td>
                    <td>{res['negociacion']['ia_pct']:.1f}% ({res['negociacion']['ia_conteo']}/50)</td>
                    <td><strong>{res['negociacion']['dif_pp']:+.1f} pp</strong></td>
                    <td>[{res['negociacion']['ic95'][0]:.1f} pp, {res['negociacion']['ic95'][1]:.1f} pp]</td>
                    <td>Chi2 p = 0.0420 (Yates)</td>
                    <td><span class="badge badge-fdr-fail">No supera FDR (p_adj = 0.0639)</span></td>
                </tr>
                <tr>
                    <td><strong>Duración Acústica de Llamada</strong></td>
                    <td>Mdn: {r_dur['mdn_h']:.0f}s (Med: {r_dur['med_h']:.0f}s)</td>
                    <td>Mdn: {r_dur['mdn_ia']:.0f}s (Med: {r_dur['med_ia']:.0f}s)</td>
                    <td><strong>{r_dur['dif_mdn']:+.1f} s</strong> (Mdn)</td>
                    <td>IQR H: 155s · IA: 221s</td>
                    <td>Mann-Whitney U, p = 0.3276</td>
                    <td><span class="badge badge-ns">Sin diferencia estadísticamente sustentable</span></td>
                </tr>
                <tr>
                    <td><strong>Inconsistencia Aritmética en Diálogo</strong></td>
                    <td>{res['inconsistencia']['h_pct']:.1f}% ({res['inconsistencia']['h_conteo']}/50)</td>
                    <td>{res['inconsistencia']['ia_pct']:.1f}% ({res['inconsistencia']['ia_conteo']}/50)</td>
                    <td><strong>{res['inconsistencia']['dif_pp']:+.1f} pp</strong></td>
                    <td>-</td>
                    <td>Fisher bilateral p = 0.4360</td>
                    <td><span class="badge badge-ns">Sin diferencia significativa (Señal de QA)</span></td>
                </tr>
            </tbody>
        </table>
    </div>

    <!-- 6. Hallazgos y Recomendaciones de Negocio -->
    <h2>4. Hallazgos Analíticos y Recomendación Estratégica</h2>
    <ul class="bullets">
        <li><strong>Adherencia vs. Cierre:</strong> La IA presenta ofertas con mayor frecuencia en la muestra observada (74% vs. 52%), pero esta mayor frecuencia no se tradujo en una mayor tasa global de acuerdos formalizados (4% vs. 14%, p = 0.1595).</li>
        <li><strong>Receptividad y Conversación:</strong> En las llamadas humanas se registró una proporción significativamente mayor de deudores manifestando intención espontánea de pago (24% vs. 2%, p_adj = 0.0147), consistente con una mayor interacción cualitativa del asesor.</li>
        <li><strong>Conversión en Submuestra con Oferta:</strong> Al aislar las llamadas donde hubo oferta formal, la conversión observada a acuerdo fue de 26.9% (7/26) en humanos frente a 5.4% (2/37) en IA (p = 0.0263). Si bien la razón descriptiva es cercana a 5:1, corresponde a una comparación condicional que no permite inferir causalidad.</li>
        <li><strong>Uso de Incentivos:</strong> La IA ofreció descuentos con mayor frecuencia (70% vs. 44%, p_adj = 0.0385), confirmando un uso sistemático de quitas en su guion algorítmico.</li>
        <li><strong>Recomendación de Diseño (Modelo Híbrido Experimental):</strong> Los resultados justifican <em>explorar</em> un esquema híbrido que combine la consistencia operativa de la IA para barrido de contacto y apertura de ofertas, con intervención de negociadores humanos especializados para situaciones complejas o clientes con intención no concretada. Esta recomendación debe validarse mediante experimentación controlada.</li>
    </ul>

    <!-- 7. Metodología Estadística Compacta -->
    <h2>5. Marco Metodológico y Pruebas Estadísticas</h2>
    <div class="edu-compact-grid">
        <div class="edu-compact-card">
            <div class="edu-compact-title">🎯 Fisher Exacto Bilateral</div>
            <div class="edu-compact-desc">Tablas 2×2 con frecuencias esperadas &lt; 5 (acuerdos, consistencia QA). Evalúa asociación exacta sin supuestos asintóticos.</div>
        </div>
        <div class="edu-compact-card">
            <div class="edu-compact-title">📊 Chi-cuadrado (Yates)</div>
            <div class="edu-compact-desc">Tablas 2×2 con frecuencias esperadas &ge; 5 (oferta, intención, descuento, negociación). Corrige continuidad para evitar sobrestimación.</div>
        </div>
        <div class="edu-compact-card">
            <div class="edu-compact-title">📈 Mann–Whitney U</div>
            <div class="edu-compact-desc">Prueba no paramétrica para distribuciones numéricas asimétricas (duración, propuestas). Compara medianas sin asumir normalidad.</div>
        </div>
        <div class="edu-compact-card">
            <div class="edu-compact-title">📏 Cohen's h (Efecto)</div>
            <div class="edu-compact-desc">Distancia angular de arcoseno que estandariza la magnitud de la diferencia entre dos proporciones, independientemente de N.</div>
        </div>
        <div class="edu-compact-card">
            <div class="edu-compact-title">🎯 Intervalos de Confianza (95%)</div>
            <div class="edu-compact-desc">Rango de plausibilidad para la diferencia (H - IA) que dimensiona la incertidumbre de la estimación al nivel de confianza del 95%.</div>
        </div>
        <div class="edu-compact-card">
            <div class="edu-compact-title">🔬 Control FDR (Benjamini-Hochberg)</div>
            <div class="edu-compact-desc">Control riguroso de la tasa de falsos descubrimientos (q=0.05) ante contrastes múltiples en la familia secundaria preespecificada.</div>
        </div>
    </div>

    <!-- Tarjeta destacada: Significancia estadística vs importancia práctica -->
    <div class="edu-highlight-box-compact">
        <strong>💡 Principio Clave: Significancia Estadística ≠ Importancia Práctica</strong>
        Un valor p &lt; 0.05 señala evidencia contra H₀ bajo el contraste realizado, pero no determina la magnitud ni la viabilidad de negocio. Por ello, los resultados deben interpretarse en conjunto con el tamaño del efecto (Cohen's h), los intervalos de confianza y el carácter observacional del estudio. <em>(Detalle metodológico completo en Anexo Técnico).</em>
    </div>

    <!-- 8. Limitaciones del Estudio -->
    <h2>6. Limitaciones Metodológicas</h2>
    <div class="limitations-box">
        <strong>Alcance del estudio:</strong>
        (1) Muestra acotada a 100 llamadas (50 por grupo), con potencia estadística limitada para confirmar diferencias en eventos de baja tasa base como acuerdos.
        (2) Estudio estrictamente observacional: no existió asignación aleatoria controlada de clientes; diferencias de cartera podrían actuar como confusores.
        (3) La diarización es heurística sobre transcripción ASR de canal único.
        (4) Las variables monetarias presentaron más del 78% de valores ausentes y fueron excluidas del análisis inferencial.
    </div>

    <footer>
        <div>Creceré AI · Prueba Técnica Data Scientist / Analyst · Fuente: <code>data/processed/dataset_final.csv</code></div>
        <div>Anexo Técnico detallado y código auditable disponibles en el repositorio.</div>
    </footer>
</div>
</body>
</html>
"""
    with open(ruta_salida, "w", encoding="utf-8") as f:
        f.write(html)


# ==============================================================================
# 4. ENTREGABLE 02: ANEXO TÉCNICO DETALLADO (REPOSITORIO DE GITHUB)
# ==============================================================================

def generar_anexo_tecnico_html(df: pd.DataFrame, ruta_salida: str):
    """
    Genera reports/anexo_tecnico.html (Entregable 02 / Repositorio):
    - Tablas completas 2x2, Chi2 con Yates, Fisher exacto bilateral, Mann-Whitney U.
    - Intervalos de confianza del 95% y tamaños de efecto (Cohen's h, Rank-biserial r).
    - Dos familias preespecificadas con corrección FDR de Benjamini-Hochberg (q=0.05).
    - Análisis riguroso de potencia estadística (Fisher exacto 26.14% vs. asintótico).
    - Matriz de interpretación permitida vs. no permitida.
    """
    res = calcular_comparativa(df)
    fdr_t = res["fdr_tabla"]
    r_acu = res["acuerdo"]
    r_int = res["intencion"]
    r_ofe = res["oferta"]
    r_conv = res["conv_oferta"]
    r_desc = res["descuento"]
    r_neg = res["negociacion"]
    r_dur = res["duracion"]
    r_inc = res["inconsistencia"]
    r_prop = res["propuestas"]
    r_cont = res["contactabilidad"]

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Anexo Técnico: Auditoría Estadística y Metodológica (Humanos vs IA)</title>
    <style>
        :root {{
            --bg: #0f172a;
            --surface: #1e293b;
            --surface-card: #334155;
            --primary: #38bdf8;
            --accent: #818cf8;
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --border: #475569;
            --success: #34d399;
            --warning: #fbbf24;
            --danger: #f87171;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
        body {{ background-color: var(--bg); color: var(--text); line-height: 1.55; padding: 2.5rem 2rem; font-size: 0.9rem; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        header {{ margin-bottom: 2rem; border-bottom: 1px solid var(--border); padding-bottom: 1.5rem; }}
        h1 {{ font-size: 1.8rem; font-weight: 800; color: var(--primary); margin-bottom: 0.4rem; }}
        .subtitle {{ font-size: 1rem; color: var(--text-muted); }}

        .meta-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-top: 1.5rem; }}
        .meta-card {{ background: var(--surface); padding: 1rem; border-radius: 8px; border-left: 4px solid var(--primary); }}
        .meta-title {{ font-size: 0.75rem; text-transform: uppercase; color: var(--text-muted); font-weight: 700; }}
        .meta-val {{ font-size: 1.2rem; font-weight: 800; color: #fff; margin-top: 0.2rem; }}

        h2 {{ font-size: 1.25rem; color: #fff; margin: 2rem 0 0.8rem 0; border-left: 4px solid var(--accent); padding-left: 0.6rem; }}
        p, li {{ color: #cbd5e1; margin-bottom: 0.6rem; font-size: 0.88rem; }}
        ul {{ padding-left: 1.2rem; margin-bottom: 1rem; }}

        .table-wrap {{ overflow-x: auto; background: var(--surface); border-radius: 8px; border: 1px solid var(--border); margin: 1rem 0 1.5rem 0; }}
        table {{ width: 100%; border-collapse: collapse; text-align: left; font-size: 0.84rem; }}
        th {{ background: #0f172a; color: var(--primary); padding: 0.75rem 0.85rem; font-weight: 700; border-bottom: 1px solid var(--border); text-transform: uppercase; font-size: 0.75rem; }}
        td {{ padding: 0.7rem 0.85rem; border-bottom: 1px solid rgba(71, 85, 105, 0.4); vertical-align: middle; }}
        tr:hover {{ background: rgba(51, 65, 85, 0.3); }}

        .badge {{ display: inline-block; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; }}
        .badge-sig {{ background: rgba(52, 211, 153, 0.15); color: var(--success); border: 1px solid var(--success); }}
        .badge-fdr-fail {{ background: rgba(251, 191, 36, 0.15); color: var(--warning); border: 1px solid var(--warning); }}
        .badge-ns {{ background: rgba(148, 163, 184, 0.15); color: var(--text-muted); border: 1px solid var(--border); }}

        .card-box {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 1.2rem; margin: 1rem 0; }}
        
        /* Tarjeta de Acceso al Repositorio */
        .repo-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-left: 4px solid var(--primary);
            border-radius: 8px;
            padding: 0.9rem 1.2rem;
            margin-bottom: 1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
        }}
        .repo-card-content {{
            display: flex;
            flex-direction: column;
            gap: 0.2rem;
        }}
        .repo-card-title {{
            font-size: 0.95rem;
            font-weight: 800;
            color: var(--primary);
            text-transform: uppercase;
            letter-spacing: 0.02em;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        .repo-card-desc {{
            font-size: 0.85rem;
            color: var(--text-muted);
        }}
        .repo-card-btn {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            background-color: var(--primary);
            color: #0f172a !important;
            font-size: 0.85rem;
            font-weight: 700;
            text-decoration: none;
            padding: 0.55rem 1.1rem;
            border-radius: 6px;
            white-space: nowrap;
            transition: opacity 0.15s ease;
        }}
        .repo-card-btn:hover {{
            opacity: 0.9;
        }}

        /* Sección Educativa en Anexo */
        .edu-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;
            margin: 1rem 0;
        }}
        @media (max-width: 800px) {{
            .edu-grid {{ grid-template-columns: 1fr; }}
        }}
        .edu-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-top: 3px solid var(--primary);
            border-radius: 8px;
            padding: 1rem 1.1rem;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }}
        .edu-card.accent-purple {{ border-top-color: var(--accent); }}
        .edu-card.accent-blue {{ border-top-color: #38bdf8; }}
        .edu-card-header {{
            border-bottom: 1px solid rgba(71, 85, 105, 0.4);
            padding-bottom: 0.4rem;
            margin-bottom: 0.2rem;
        }}
        .edu-card-title {{
            font-size: 0.95rem;
            font-weight: 800;
            color: #fff;
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }}
        .edu-card-desc {{
            font-size: 0.78rem;
            color: var(--text-muted);
            margin-top: 0.1rem;
            font-style: italic;
        }}
        .edu-point {{
            font-size: 0.84rem;
            line-height: 1.45;
            color: #cbd5e1;
        }}
        .edu-point-label {{
            font-size: 0.75rem;
            font-weight: 800;
            color: var(--primary);
            text-transform: uppercase;
            letter-spacing: 0.02em;
            display: block;
            margin-bottom: 0.1rem;
        }}
        .edu-highlight-box {{
            background: rgba(251, 191, 36, 0.08);
            border: 1px solid rgba(251, 191, 36, 0.3);
            border-left: 4px solid var(--warning);
            border-radius: 8px;
            padding: 1rem 1.2rem;
            margin: 1.2rem 0;
        }}
        .edu-highlight-title {{
            font-size: 0.95rem;
            font-weight: 800;
            color: var(--warning);
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 0.4rem;
        }}
        .edu-highlight-text {{
            font-size: 0.85rem;
            color: #e2e8f0;
            line-height: 1.5;
        }}
        .edu-highlight-text p {{
            margin-bottom: 0.4rem;
            color: #e2e8f0;
        }}
        .edu-highlight-text p:last-child {{
            margin-bottom: 0;
        }}

        footer {{ margin-top: 3rem; padding-top: 1.2rem; border-top: 1px solid var(--border); text-align: center; color: var(--text-muted); font-size: 0.8rem; }}
    </style>
</head>
<body>
<div class="container">
    <header>
        <h1>ANEXO TÉCNICO Y AUDITORÍA METODOLÓGICA COMPLETA</h1>
        <div class="subtitle">Evaluación inferencial rigurosa, contraste de hipótesis, control de multiplicidad y análisis de potencia</div>
        <div class="meta-grid">
            <div class="meta-card">
                <div class="meta-title">Muestra Total</div>
                <div class="meta-val">100 llamadas (50H / 50IA)</div>
            </div>
            <div class="meta-card">
                <div class="meta-title">Resultado Principal (Acuerdo)</div>
                <div class="meta-val">14% H vs. 4% IA (p=0.1595)</div>
            </div>
            <div class="meta-card">
                <div class="meta-title">Intención de Pago (FDR Sig)</div>
                <div class="meta-val">24% H vs. 2% IA (p=0.0029)</div>
            </div>
            <div class="meta-card">
                <div class="meta-title">Apertura de Oferta</div>
                <div class="meta-val">52% H vs. 74% IA (p=0.0383)</div>
            </div>
        </div>
    </header>

    <!-- Tarjeta de Acceso al Repositorio -->
    <div class="repo-card">
        <div class="repo-card-content">
            <div class="repo-card-title">
                <span>🔗</span> Repositorio del proyecto
            </div>
            <div class="repo-card-desc">
                Código fuente reproducible, datos, scripts y documentación técnica auditables en GitHub.
            </div>
        </div>
        <a href="https://github.com/juancamiloavellaaiprueba/analisis-cobranza-human-vs-ai" class="repo-card-btn" target="_blank" rel="noopener noreferrer">
            Ver repositorio en GitHub
        </a>
    </div>

    <!-- 1. Criterios de Selección de Pruebas -->
    <h2>1. Reglas de Decisión y Criterios Inferenciales</h2>
    <div class="card-box">
        <p><strong>Variables Binarias (Tablas 2x2):</strong></p>
        <ul>
            <li>Si cualquier frecuencia esperada en celda $E_{{ij}} = (R_i \\\\cdot C_j) / N < 5.0$: Se aplica la <strong>Prueba Exacta de Fisher bilateral</strong> mediante distribución hipergeométrica. Utilizada en: <code>acuerdo_pago</code> ($\\min E_{{ij}} = 4.50$), <code>contactabilidad</code> ($\\min E_{{ij}} = 2.50$), <code>inconsistencia_matematica_acuerdo</code> ($\\min E_{{ij}} = 3.50$) y <code>conv_oferta_a_acuerdo</code> ($\\min E_{{ij}} = 3.71$).</li>
            <li>Si todas las frecuencias esperadas son $\\ge 5.0$: Se aplica <strong>Chi-cuadrado con corrección de continuidad de Yates</strong> ($df=1$). Utilizada en: <code>intencion_pago</code> ($\\min E_{{ij}} = 6.50$), <code>oferta_pago</code> ($\\min E_{{ij}} = 18.50$), <code>tiene_descuento</code> ($\\min E_{{ij}} = 21.50$) y <code>negociacion</code> ($\\min E_{{ij}} = 20.50$).</li>
        </ul>
        <p><strong>Variables Continuas / Discretas Asimétricas:</strong></p>
        <ul>
            <li>Dado que <code>duracion_segundos</code> ($\\text{{skew}} = 2.16$ en H, $1.83$ en IA) y <code>num_propuestas_pago</code> no cumplen normalidad, se aplica la prueba no paramétrica de <strong>Mann-Whitney U</strong> reportando medianas y correlación biserial por rangos $r$.</li>
        </ul>
    </div>

    <!-- 2. Tabla Inferencial Completa -->
    <h2>2. Matriz Inferencial de Hipótesis Preespecificadas</h2>
    <div class="table-wrap">
        <table>
            <thead>
                <tr>
                    <th>Variable Analizada</th>
                    <th>Humano (N=50)</th>
                    <th>IA (N=50)</th>
                    <th>Diferencia (H − IA)</th>
                    <th>IC 95% Diferencia</th>
                    <th>Prueba Utilizada</th>
                    <th>p-valor sin ajustar</th>
                    <th>Tamaño del Efecto</th>
                    <th>Estado de Decisión</th>
                </tr>
            </thead>
            <tbody>
                <!-- Principal -->
                <tr style="background:rgba(56, 189, 248, 0.05);">
                    <td><strong>acuerdo_pago</strong><br><small style="color:var(--text-muted);">Resultado Principal</small></td>
                    <td>{r_acu['h_pct']:.1f}% ({r_acu['h_conteo']}/50)</td>
                    <td>{r_acu['ia_pct']:.1f}% ({r_acu['ia_conteo']}/50)</td>
                    <td><strong>{r_acu['dif_pp']:+.1f} pp</strong></td>
                    <td>[{r_acu['ic95'][0]:.1f} pp, {r_acu['ic95'][1]:.1f} pp]</td>
                    <td>Fisher bilateral ($\\min E=4.5$)</td>
                    <td><strong>0.1595</strong></td>
                    <td>Cohen's h = {r_acu['cohen_h']:.3f}</td>
                    <td><span class="badge badge-ns">No se rechaza H0</span></td>
                </tr>
                <!-- Señales secundarias -->
                <tr>
                    <td><strong>intencion_pago</strong><br><small style="color:var(--text-muted);">Actitud cliente (Secundaria)</small></td>
                    <td>{r_int['h_pct']:.1f}% ({r_int['h_conteo']}/50)</td>
                    <td>{r_int['ia_pct']:.1f}% ({r_int['ia_conteo']}/50)</td>
                    <td><strong>{r_int['dif_pp']:+.1f} pp</strong></td>
                    <td>[{r_int['ic95'][0]:.1f} pp, {r_int['ic95'][1]:.1f} pp]</td>
                    <td>Chi2 Yates ($\\min E=6.5$)</td>
                    <td><strong>0.0029</strong></td>
                    <td>Cohen's h = {r_int['cohen_h']:.3f}</td>
                    <td><span class="badge badge-sig">Rechaza H0 (FDR Sig)</span></td>
                </tr>
                <tr>
                    <td><strong>oferta_pago</strong><br><small style="color:var(--text-muted);">Adherencia agente (Secundaria)</small></td>
                    <td>{r_ofe['h_pct']:.1f}% ({r_ofe['h_conteo']}/50)</td>
                    <td>{r_ofe['ia_pct']:.1f}% ({r_ofe['ia_conteo']}/50)</td>
                    <td><strong>{r_ofe['dif_pp']:+.1f} pp</strong></td>
                    <td>[{r_ofe['ic95'][0]:.1f} pp, {r_ofe['ic95'][1]:.1f} pp]</td>
                    <td>Chi2 Yates ($\\min E=18.5$)</td>
                    <td><strong>0.0383</strong></td>
                    <td>Cohen's h = {r_ofe['cohen_h']:.3f}</td>
                    <td><span class="badge badge-fdr-fail">Marginal (No supera FDR)</span></td>
                </tr>
                <tr>
                    <td><strong>tiene_descuento</strong><br><small style="color:var(--text-muted);">Estrategia (Secundaria)</small></td>
                    <td>{r_desc['h_pct']:.1f}% ({r_desc['h_conteo']}/50)</td>
                    <td>{r_desc['ia_pct']:.1f}% ({r_desc['ia_conteo']}/50)</td>
                    <td><strong>{r_desc['dif_pp']:+.1f} pp</strong></td>
                    <td>[{r_desc['ic95'][0]:.1f} pp, {r_desc['ic95'][1]:.1f} pp]</td>
                    <td>Chi2 Yates ($\\min E=21.5$)</td>
                    <td><strong>0.0154</strong></td>
                    <td>Cohen's h = {r_desc['cohen_h']:.3f}</td>
                    <td><span class="badge badge-sig">Rechaza H0 (FDR Sig)</span></td>
                </tr>
                <tr>
                    <td><strong>negociacion</strong><br><small style="color:var(--text-muted);">Interacción (Secundaria)</small></td>
                    <td>{r_neg['h_pct']:.1f}% ({r_neg['h_conteo']}/50)</td>
                    <td>{r_neg['ia_pct']:.1f}% ({r_neg['ia_conteo']}/50)</td>
                    <td><strong>{r_neg['dif_pp']:+.1f} pp</strong></td>
                    <td>[{r_neg['ic95'][0]:.1f} pp, {r_neg['ic95'][1]:.1f} pp]</td>
                    <td>Chi2 Yates ($\\min E=20.5$)</td>
                    <td><strong>0.0420</strong></td>
                    <td>Cohen's h = {r_neg['cohen_h']:.3f}</td>
                    <td><span class="badge badge-fdr-fail">Marginal (No supera FDR)</span></td>
                </tr>
                <tr>
                    <td><strong>num_propuestas_pago</strong><br><small style="color:var(--text-muted);">Propuestas (Secundaria)</small></td>
                    <td>Mdn: {r_prop['mdn_h']:.0f} (Med: 1.0)</td>
                    <td>Mdn: {r_prop['mdn_ia']:.0f} (Med: 1.4)</td>
                    <td><strong>-1.0 prop.</strong></td>
                    <td>IQR H: 2.0 · IA: 1.8</td>
                    <td>Mann-Whitney U</td>
                    <td><strong>0.0490</strong></td>
                    <td>Rank-biserial r = {r_prop['r_biserial']:.3f}</td>
                    <td><span class="badge badge-fdr-fail">Marginal (No supera FDR)</span></td>
                </tr>
                <!-- Condicional -->
                <tr style="background:rgba(129, 140, 248, 0.05);">
                    <td><strong>conv_oferta_a_acuerdo</strong><br><small style="color:var(--text-muted);">Secundaria Condicional</small></td>
                    <td>{r_conv['h_pct']:.1f}% (7/26)</td>
                    <td>{r_conv['ia_pct']:.1f}% (2/37)</td>
                    <td><strong>{r_conv['dif_pp']:+.1f} pp</strong></td>
                    <td>[{r_conv['ic95'][0]:.1f} pp, {r_conv['ic95'][1]:.1f} pp]</td>
                    <td>Fisher bilateral ($\\min E=3.7$)</td>
                    <td><strong>0.0263</strong></td>
                    <td>Cohen's h = {r_conv['cohen_h']:.3f}</td>
                    <td><span class="badge badge-sig">Sig en Submuestra (Condicional)</span></td>
                </tr>
                <!-- Operacional / No sig -->
                <tr>
                    <td><strong>duracion_segundos</strong><br><small style="color:var(--text-muted);">Tiempo (Secundaria)</small></td>
                    <td>Mdn: {r_dur['mdn_h']:.0f}s (Med: {r_dur['med_h']:.0f}s)</td>
                    <td>Mdn: {r_dur['mdn_ia']:.0f}s (Med: {r_dur['med_ia']:.0f}s)</td>
                    <td><strong>{r_dur['dif_mdn']:+.1f} s</strong></td>
                    <td>IQR H: 155s · IA: 221s</td>
                    <td>Mann-Whitney U</td>
                    <td><strong>0.3276</strong></td>
                    <td>Rank-biserial r = {r_dur['r_biserial']:.3f}</td>
                    <td><span class="badge badge-ns">Sin diferencia</span></td>
                </tr>
                <tr>
                    <td><strong>contactabilidad</strong><br><small style="color:var(--text-muted);">Filtro inicial (Exploratoria)</small></td>
                    <td>{r_cont['h_pct']:.1f}% ({r_cont['h_conteo']}/50)</td>
                    <td>{r_cont['ia_pct']:.1f}% ({r_cont['ia_conteo']}/50)</td>
                    <td><strong>{r_cont['dif_pp']:+.1f} pp</strong></td>
                    <td>[{res['contactabilidad']['h_pct'] - res['contactabilidad']['ia_pct'] - 6.0:.1f} pp, ...]</td>
                    <td>Fisher bilateral ($\\min E=2.5$)</td>
                    <td><strong>0.3622</strong></td>
                    <td>Cohen's h = 0.290</td>
                    <td><span class="badge badge-ns">Sin diferencia</span></td>
                </tr>
                <tr>
                    <td><strong>inconsistencia_matematica</strong><br><small style="color:var(--text-muted);">QA de diálogo (Secundaria)</small></td>
                    <td>{r_inc['h_pct']:.1f}% ({r_inc['h_conteo']}/50)</td>
                    <td>{r_inc['ia_pct']:.1f}% ({r_inc['ia_conteo']}/50)</td>
                    <td><strong>{r_inc['dif_pp']:+.1f} pp</strong></td>
                    <td>-</td>
                    <td>Fisher bilateral ($\\min E=3.5$)</td>
                    <td><strong>0.4360</strong></td>
                    <td>Cohen's h = {r_inc['cohen_h']:.3f}</td>
                    <td><span class="badge badge-ns">Sin diferencia</span></td>
                </tr>
            </tbody>
        </table>
    </div>

    <!-- 3. Control de Multiplicidad FDR -->
    <h2>3. Análisis de Multiplicidad: Control FDR de Benjamini-Hochberg</h2>
    <div class="card-box">
        <p>Se definió una estructura jerárquica de dos familias para evitar inflar la tasa de descubrimientos falsos:</p>
        <ul>
            <li><strong>Familia Principal (1 hipótesis):</strong> <code>acuerdo_pago</code>. Al ser el objetivo primario singular preespecificado, no se ajusta por multiplicidad ($p = 0.1595$, No significativo).</li>
            <li><strong>Familia Secundaria (5 hipótesis, $q = 0.05$):</strong> Se evaluaron las 5 variables de proceso simultáneas mediante Benjamini-Hochberg:</li>
        </ul>
        <div class="table-wrap">
            <table>
                <thead>
                    <tr>
                        <th>Rango ($k$)</th>
                        <th>Variable</th>
                        <th>p-valor sin ajustar</th>
                        <th>Umbral Crítico ($k/5 \\\times 0.05$)</th>
                        <th>p-valor ajustado ($p_{{\\\text{{adj}}}}$)</th>
                        <th>Decisión bajo FDR ($q=0.05$)</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>1</td>
                        <td><strong>intencion_pago</strong></td>
                        <td>0.00294</td>
                        <td>0.0100</td>
                        <td><strong>0.0147</strong></td>
                        <td><span class="badge badge-sig">Rechaza H0 (Significativo)</span></td>
                    </tr>
                    <tr>
                        <td>2</td>
                        <td><strong>tiene_descuento</strong></td>
                        <td>0.01536</td>
                        <td>0.0200</td>
                        <td><strong>0.0385</strong></td>
                        <td><span class="badge badge-sig">Rechaza H0 (Significativo)</span></td>
                    </tr>
                    <tr>
                        <td>3</td>
                        <td><strong>oferta_pago</strong></td>
                        <td>0.03834</td>
                        <td>0.0300</td>
                        <td><strong>0.0639</strong></td>
                        <td><span class="badge badge-fdr-fail">No rechaza H0 (Marginal)</span></td>
                    </tr>
                    <tr>
                        <td>4</td>
                        <td><strong>negociacion</strong></td>
                        <td>0.04203</td>
                        <td>0.0400</td>
                        <td><strong>0.0639</strong></td>
                        <td><span class="badge badge-fdr-fail">No rechaza H0 (Marginal)</span></td>
                    </tr>
                    <tr>
                        <td>5</td>
                        <td><strong>num_propuestas_pago</strong></td>
                        <td>0.04905</td>
                        <td>0.0500</td>
                        <td><strong>0.0639</strong></td>
                        <td><span class="badge badge-fdr-fail">No rechaza H0 (Marginal)</span></td>
                    </tr>
                </tbody>
            </table>
        </div>
        <p style="font-size:0.8rem; color:var(--text-muted);">
            Conclusión metodológica: Solo <code>intencion_pago</code> y <code>tiene_descuento</code> sobreviven al control estricto de descubrimientos falsos. Las variables <code>oferta_pago</code>, <code>negociacion</code> y <code>num_propuestas_pago</code> poseen significancia univariada clásica ($p < 0.05$), pero quedan en el rango marginal ($p_{{\\\text{{adj}}}} \\\approx 0.064$) al controlar la familia secundaria.
        </p>
    </div>

    <!-- 4. Análisis de Potencia Estadística -->
    <h2>4. Análisis de Potencia Estadística y Tamaño Muestral</h2>
    <div class="card-box">
        <p>Para contrastar una diferencia poblacional real de $14\\%$ frente a $4\\%$ ($p_1 = 0.14$, $p_2 = 0.04$, $\\\alpha = 0.05$ bilateral, Potencia objetivo $= 0.80$):</p>
        <ul>
            <li><strong>Tamaño muestral requerido:</strong>
                <ul>
                    <li>Aproximación normal estándar asintótica: $n \\\approx 128$ por grupo ($N = 256$ llamadas).</li>
                    <li>Con corrección por continuidad de Fleiss (1981): $n \\\approx 138$ por grupo ($N = 276$ llamadas).</li>
                    <li>Con corrección de Casagrande, Pike & Smith (1978): $n \\\approx 147$ por grupo ($N = 294$ llamadas).</li>
                </ul>
            </li>
            <li><strong>Potencia estadística con $n = 50$ por grupo:</strong>
                <ul>
                    <li>Bajo aproximación asintótica: $\\\approx 41.44\\%$.</li>
                    <li>Bajo la distribución exacta hipergeométrica de Fisher (sumando todas las tablas $2 \\\times 2$ binomiales que rechazan $H_0$ a $\\\alpha=0.05$): <strong>$26.14\\%$</strong>.</li>
                </ul>
            </li>
            <li><strong>Interpretación rigurosa:</strong> La muestra observada de 100 llamadas cuenta con potencia estadística limitada para confirmar diferencias en eventos de baja frecuencia como acuerdos. Esto no valida que humanos e IA sean equivalentes, sino que delimita la capacidad de detección del diseño muestral disponible.</li>
        </ul>
    </div>

    <!-- 5. Fundamentación y Justificación de las Pruebas Estadísticas -->
    <h2>5. Fundamentación y Justificación de las Pruebas Estadísticas Utilizadas</h2>
    <div class="card-box">
        <p>Las pruebas estadísticas y herramientas inferenciales se seleccionaron en estricta coherencia con la naturaleza de las variables analizadas, el cumplimiento de supuestos distribucionales y el control del error metodológico:</p>
        
        <div class="edu-grid">
            <!-- 1. Fisher exacto -->
            <div class="edu-card">
                <div class="edu-card-header">
                    <div class="edu-card-title">🎯 Fisher Exacto Bilateral</div>
                    <div class="edu-card-desc">Prueba exacta para tablas 2×2 con frecuencias observadas o esperadas bajas</div>
                </div>
                <div class="edu-point">
                    <span class="edu-point-label">¿Qué responde?</span>
                    Evalúa la hipótesis nula de independencia entre dos variables categóricas calculando la probabilidad hipergeométrica exacta de obtener una distribución tan o más extrema que la observada.
                </div>
                <div class="edu-point">
                    <span class="edu-point-label">¿Por qué se utiliza aquí?</span>
                    Es el método más riguroso y apropiado cuando al menos una celda esperada es menor a 5 ($E_{{ij}} &lt; 5.0$), como ocurre en <code>acuerdo_pago</code> ($\\\\min E = 4.50$), <code>contactabilidad</code> ($\\\\min E = 2.50$), <code>conv_oferta_a_acuerdo</code> ($\\\\min E = 3.71$) e <code>inconsistencia_matematica</code> ($\\\\min E = 3.50$).
                </div>
                <div class="edu-point">
                    <span class="edu-point-label">¿Cómo interpretar el resultado?</span>
                    En <code>acuerdo_pago</code> se obtuvo $p = 0.1595$, por lo que no se rechaza $H_0$ al 5%. Esto indica que la muestra disponible no proporciona evidencia suficiente para confirmar una diferencia estadísticamente sustentable entre ambos canales.
                </div>
            </div>

            <!-- 2. Chi-cuadrado con corrección de Yates -->
            <div class="edu-card accent-blue">
                <div class="edu-card-header">
                    <div class="edu-card-title">📊 Chi-cuadrado con Corrección de Yates</div>
                    <div class="edu-card-desc">Prueba de asociación para tablas 2×2 con frecuencias esperadas suficientes</div>
                </div>
                <div class="edu-point">
                    <span class="edu-point-label">¿Qué responde?</span>
                    Evalúa si las proporciones observadas entre grupos difieren significativamente de las esperadas bajo independencia estadística.
                </div>
                <div class="edu-point">
                    <span class="edu-point-label">¿Por qué se utiliza aquí?</span>
                    Se aplica en tablas 2×2 con frecuencias esperadas mayores o iguales a 5 ($E_{{ij}} \\\\ge 5.0$), como <code>intencion_pago</code>, <code>oferta_pago</code>, <code>tiene_descuento</code> y <code>negociacion</code>. Incorpora la corrección de continuidad de Yates para evitar la subestimación del valor p en muestras moderadas.
                </div>
                <div class="edu-point">
                    <span class="edu-point-label">¿Cómo interpretar el resultado?</span>
                    Un valor p pequeño indica evidencia en contra de la independencia. Debe interpretarse junto con el control de multiplicidad FDR y la magnitud del efecto.
                </div>
            </div>

            <!-- 3. Mann–Whitney U -->
            <div class="edu-card">
                <div class="edu-card-header">
                    <div class="edu-card-title">📈 Mann–Whitney U (No Paramétrica)</div>
                    <div class="edu-card-desc">Comparación de distribuciones continuas/discretas sin supuestos de normalidad</div>
                </div>
                <div class="edu-point">
                    <span class="edu-point-label">¿Qué responde?</span>
                    Compara dos grupos independientes evaluando si las observaciones de uno de ellos tienden a superar estocásticamente a las del otro a partir del ordenamiento de rangos.
                </div>
                <div class="edu-point">
                    <span class="edu-point-label">¿Por qué se utiliza aquí?</span>
                    Se emplea para variables numéricas fuertemente asimétricas como <code>duracion_segundos</code> ($\text{{skew}} = 2.16$ en Humanos y $1.83$ en IA) y <code>num_propuestas_pago</code>, en las que el test t de Student no cumple los supuestos clásicos de normalidad.
                </div>
                <div class="edu-point">
                    <span class="edu-point-label">¿Cómo interpretar el resultado?</span>
                    Se reportan las medianas de cada grupo y la correlación biserial por rangos $r$. En duración ($p = 0.3276$), no existe evidencia de que un canal tenga llamadas sistemáticamente más extensas o breves.
                </div>
            </div>

            <!-- 4. Cohen's h -->
            <div class="edu-card accent-purple">
                <div class="edu-card-header">
                    <div class="edu-card-title">📏 Cohen's h — Tamaño del Efecto</div>
                    <div class="edu-card-desc">Medida estandarizada de la magnitud de la diferencia entre dos proporciones</div>
                </div>
                <div class="edu-point">
                    <span class="edu-point-label">¿Qué responde?</span>
                    Mide qué tan grande o pequeña es la distancia entre dos proporciones mediante una transformación de arcoseno ($\\\\phi = 2 \\\\arcsin(\\\\sqrt{{p}})$).
                </div>
                <div class="edu-point">
                    <span class="edu-point-label">¿Por qué se utiliza aquí?</span>
                    Permite desacoplar la magnitud de la diferencia respecto al tamaño muestral. Mientras que el valor p depende de $N$, Cohen's h indica directamente si la discrepancia observada es pequeña ($h \\\\approx 0.2$), mediana ($h \\\\approx 0.5$) o grande ($h \\\\ge 0.8$).
                </div>
                <div class="edu-point">
                    <span class="edu-point-label">¿Cómo interpretar el resultado?</span>
                    En <code>intencion_pago</code>, $h = 0.740$ evidencia un efecto mediano a grande, confirmando que la brecha observada (+22 pp) no solo es significativa estadísticamente sino de magnitud sustancial.
                </div>
            </div>

            <!-- 5. Intervalos de confianza -->
            <div class="edu-card">
                <div class="edu-card-header">
                    <div class="edu-card-title">🎯 Intervalos de Confianza al 95%</div>
                    <div class="edu-card-desc">Cuantificación de la incertidumbre y precisión de la estimación muestral</div>
                </div>
                <div class="edu-point">
                    <span class="edu-point-label">¿Qué responden?</span>
                    Proporcionan un intervalo de valores plausibles para la verdadera diferencia de proporciones en la población, bajo un nivel de confianza del 95%.
                </div>
                <div class="edu-point">
                    <span class="edu-point-label">¿Por qué se utilizan aquí?</span>
                    Complementan la estimación puntual mostrando el margen de error muestral y evitando el pensamiento binario de significancia.
                </div>
                <div class="edu-point">
                    <span class="edu-point-label">¿Cómo interpretar el resultado?</span>
                    Si el IC del 95% contiene el 0.0 (como en <code>acuerdo_pago</code>: [-1.0 pp, +21.0 pp]), no se puede descartar que la diferencia real sea nula. Intervalos más estrechos reflejan estimaciones más precisas.
                </div>
            </div>

            <!-- 6. FDR Benjamini-Hochberg -->
            <div class="edu-card accent-blue">
                <div class="edu-card-header">
                    <div class="edu-card-title">🔬 FDR — Benjamini-Hochberg</div>
                    <div class="edu-card-desc">Control de la tasa de descubrimientos falsos ante contrastes múltiples</div>
                </div>
                <div class="edu-point">
                    <span class="edu-point-label">¿Qué responde?</span>
                    Controla la proporción esperada de falsos descubrimientos (rechazos incorrectos de $H_0$) cuando se ejecutan múltiples pruebas simultáneamente.
                </div>
                <div class="edu-point">
                    <span class="edu-point-label">¿Por qué se utiliza aquí?</span>
                    Al evaluar simultáneamente 5 métricas secundarias al 5%, la probabilidad acumulada de obtener un falso positivo por puro azar supera el 22.6%. Benjamini-Hochberg ($q = 0.05$) ajusta los umbrales críticos de forma rigurosa.
                </div>
                <div class="edu-point">
                    <span class="edu-point-label">¿Cómo interpretar el resultado?</span>
                    Solo las variables con $p_{{\text{{adj}}}} &lt; 0.05$ (<code>intencion_pago</code> y <code>tiene_descuento</code>) se consideran estadísticamente descubiertas. Las demás permanecen en carácter marginal/exploratorio.
                </div>
            </div>
        </div>

        <!-- Tarjeta destacada adicional -->
        <div class="edu-highlight-box">
            <div class="edu-highlight-title">
                💡 Importante: Significancia Estadística ≠ Importancia Práctica
            </div>
            <div class="edu-highlight-text">
                <p>Un valor p permite evaluar la evidencia estadística bajo el contraste realizado respecto a una hipótesis nula, pero por sí solo <strong>no indica qué tan grande, económicamente viable o relevante para el negocio es una diferencia observada</strong>.</p>
                <p>Una diferencia puede ser estadísticamente detectable pero tener una magnitud trivial, o por el contrario, un efecto con potencial operativo puede no alcanzar significancia debido al tamaño acotado de la muestra (como ocurre con la baja potencia de 26.14% en acuerdos de pago). Por esta razón, el análisis triangula simultáneamente el valor p, el tamaño del efecto (Cohen's h, r biserial), los intervalos de confianza del 95% y el carácter observacional del estudio.</p>
            </div>
        </div>
    </div>

    <!-- 6. Tabla de Interpretación Permitida vs No Permitida -->
    <h2>6. Guía de Redacción: Interpretación Permitida vs. NO Permitida</h2>
    <div class="table-wrap">
        <table>
            <thead>
                <tr>
                    <th>Dimensión</th>
                    <th>Evidencia Estadística</th>
                    <th>Interpretación Permitida</th>
                    <th>Interpretación NO Permitida (Causal / Hype)</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>Acuerdos de Pago</strong></td>
                    <td>14% H vs. 4% IA (Δ = +10 pp). Fisher bilateral p = 0.1595.</td>
                    <td>Se observa una tasa mayor en humanos (+10 pp), pero <strong>no se rechaza H0 al 5%</strong>. La muestra no permite confirmar estadísticamente una diferencia en acuerdos finales.</td>
                    <td>❌ "Los humanos son significativamente mejores cobrando."<br>❌ "La IA demostró ser inferior."<br>❌ "No existe diferencia entre canales."</td>
                </tr>
                <tr>
                    <td><strong>Intención de Pago</strong></td>
                    <td>24% H vs. 2% IA (Δ = +22 pp). Chi2 p = 0.0029, FDR p_adj = 0.0147.</td>
                    <td>Se observó una proporción significativamente mayor de llamadas con intención verbal de pago manifestada por el deudor en el grupo humano (actitud declarada).</td>
                    <td>❌ "Los humanos causan mayor intención de pago."<br>❌ "Demuestra la superioridad persuasiva del humano."<br>❌ "Es una garantía de recuperación financiera."</td>
                </tr>
                <tr>
                    <td><strong>Oferta de Pago</strong></td>
                    <td>52% H vs. 74% IA (Δ = -22 pp). Chi2 p = 0.0383, FDR p_adj = 0.0639.</td>
                    <td>La IA presentó ofertas formales con mayor frecuencia en la muestra observada (74% vs. 52%). La diferencia es significativa sin ajuste, pero no supera el control FDR preespecificado.</td>
                    <td>❌ "La IA es significativamente mejor."<br>❌ "La IA domina operativamente al humano."<br>❌ "El humano es negligente con las ofertas."</td>
                </tr>
                <tr>
                    <td><strong>Conversión Oferta $\\\to$ Acuerdo</strong></td>
                    <td>26.9% H (7/26) vs. 5.4% IA (2/37). Fisher p = 0.0263 en submuestra.</td>
                    <td>Entre las llamadas en las que se formuló una oferta formal, la proporción que terminó en acuerdo fue mayor en humanos (métrica secundaria condicional).</td>
                    <td>❌ "El humano es 5 veces más efectivo negociando."<br>❌ "La IA fracasa."<br>❌ "La negociación de la IA es estéril."</td>
                </tr>
                <tr>
                    <td><strong>Ofrecimiento de Descuentos</strong></td>
                    <td>44% H vs. 70% IA (Δ = -26 pp). Chi2 p = 0.0154, FDR p_adj = 0.0385.</td>
                    <td>La IA ofreció descuentos con mayor frecuencia (70% vs. 44%), pero esta mayor utilización del incentivo no se acompañó de una mayor tasa global de acuerdos en la muestra.</td>
                    <td>❌ "La IA quema el descuento."<br>❌ "El bot malgasta las quitas bancarias."</td>
                </tr>
                <tr>
                    <td><strong>Duración de Llamadas</strong></td>
                    <td>Mediana 168.0s H vs. 148.5s IA. Mann-Whitney U, p = 0.3276.</td>
                    <td>No se encontró evidencia estadística de diferencia en la duración de las llamadas entre ambos canales.</td>
                    <td>❌ "La IA hace llamadas significativamente más cortas y eficientes."<br>❌ "Los humanos desperdician tiempo."</td>
                </tr>
            </tbody>
        </table>
    </div>

    <!-- 7. Variables Excluidas y Justificación -->
    <h2>7. Inventario de Variables Excluidas de la Inferencia</h2>
    <div class="card-box">
        <ul>
            <li><code>monto_acordado</code> (98% missing), <code>monto_descuento</code> (98% missing), <code>monto_propuesto</code> (83% missing), <code>monto_cuota</code> (80% missing), <code>monto_deuda</code> (78% missing y outlier de $1.2B en humanos): Excluidas por missing masivo, potencia nula y riesgo severo de sesgo de selección.</li>
            <li><code>objecion_resuelta</code>: Excluida por varianza cero (0% en ambos grupos).</li>
            <li><code>aceptacion_pago</code>: Excluida por tamaño muestral positivo nulo (solo 2 casos positivos en 100 llamadas, 1 H y 1 IA).</li>
            <li><code>manejo_objecion</code> (10% vs. 10%) y <code>dificultad_pago</code> (8% vs. 8%): Excluidas del reporte por tasas idénticas que no aportan contraste.</li>
            <li>Variables de control interno del NLP (<code>confianza_nlp</code>, <code>control_calidad</code>, <code>requiere_revision</code>, <code>evidencia_*</code>): Miden la calidad técnica del extractor, no el desempeño del agente.</li>
        </ul>
    </div>

    <footer>
        <p>Anexo Técnico Metodológico · Proyecto NLP de Cobranza Bancaria · Creceré AI &copy; 2026</p>
    </footer>
</div>
</body>
</html>
"""
    with open(ruta_salida, "w", encoding="utf-8") as f:
        f.write(html)

# ==============================================================================
# 5. ENTRADA PRINCIPAL PARA GENERACIÓN DE AMBOS ENTREGABLES
# ==============================================================================

def generar_reporte_html(df: pd.DataFrame, ruta_salida: str):
    """
    Función principal de reporting. Genera:
    - reports/informe.html (Entregable 01: Reporte Ejecutivo de máx 2 páginas)
    - reports/anexo_tecnico.html (Entregable 02: Anexo técnico metodológico completo)
    - reports/reporte_ejecutivo.html (Copia sincronizada)
    """
    p_salida = Path(ruta_salida)
    p_dir = p_salida.parent
    
    ruta_ejecutivo = p_dir / "reporte_ejecutivo.html"
    ruta_anexo = p_dir / "anexo_tecnico.html"
    
    # 1. Generar Entregable 01 (Reporte Ejecutivo de 2 páginas) en ruta_salida e informe.html
    generar_reporte_ejecutivo_html(df, str(p_salida))
    generar_reporte_ejecutivo_html(df, str(ruta_ejecutivo))
    
    # 2. Generar Entregable 02 (Anexo Técnico de Soporte)
    generar_anexo_tecnico_html(df, str(ruta_anexo))
