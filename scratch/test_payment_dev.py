import sys
sys.path.insert(0, ".")
import re
import numpy as np
import pandas as pd
from src.cleaning import normalizar_texto

MONTO_MINIMO_COP = 1000.0

NUMEROS_ESCRITOS = {
    "un": 1, "uno": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
    "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10,
    "once": 11, "doce": 12, "veinte": 20, "veinticuatro": 24,
    "treinta": 30, "cincuenta": 50, "cien": 100, "ciento": 100,
    "doscientos": 200, "trescientos": 300, "quinientos": 500
}

_PATRON_NUMERICO = r"[$]?\s*([\d]{1,3}(?:[\.,][\d]{3})+|[\d]{4,})"
_PATRON_MIL = r"(\d+|" + "|".join(NUMEROS_ESCRITOS.keys()) + r")\s*mil(?:\s+(\d+))?"
_PATRON_MILLON = (
    r"(\d+|" + "|".join(NUMEROS_ESCRITOS.keys()) +
    r")\s+millones?(?:\s+(?:de\s+)?(\d+|" + "|".join(NUMEROS_ESCRITOS.keys()) + r")\s*mil)?"
)

def parsear_monto_nuevo(texto_monto):
    if texto_monto is None or not str(texto_monto).strip():
        return np.nan
    t = str(texto_monto).strip().lower()
    if t in ["n/a", "-", "ninguno", "no aplica", "nan", "null"]:
        return np.nan

    # Excluir cuotas aisladas
    if re.search(r"^\s*\d+\s+cuotas?\s*$", t):
        return np.nan

    # Evidencia monetaria requerida: $, mil, millon, pesos, cop, o formato numérico >= 1000
    tiene_evidencia_monetaria = bool(
        re.search(r"[\$]|mil|millon|pesos|cop\b", t) or
        re.search(r"\b\d{1,3}(?:\.\d{3})+\b", t) or
        re.search(r"\b\d{4,}\b", t)
    )
    if not tiene_evidencia_monetaria:
        return np.nan

    # 1. Millones con posible resto en miles (ej. 2 millones 110 mil)
    m_millon = re.search(_PATRON_MILLON, t)
    if m_millon:
        num_str = m_millon.group(1).replace(",", ".")
        val = float(num_str) if num_str.replace(".", "").isdigit() else float(NUMEROS_ESCRITOS.get(num_str, np.nan))
        resto = 0.0
        if m_millon.group(2):
            n2_str = m_millon.group(2).replace(",", ".")
            resto = float(n2_str) if n2_str.replace(".", "").isdigit() else float(NUMEROS_ESCRITOS.get(n2_str, 0.0))
        if not np.isnan(val):
            return val * 1_000_000.0 + resto * 1_000.0

    # 2. Miles
    m_mil = re.search(_PATRON_MIL, t)
    if m_mil:
        num_str = m_mil.group(1).replace(",", ".")
        val = float(num_str) if num_str.replace(".", "").isdigit() else float(NUMEROS_ESCRITOS.get(num_str, np.nan))
        if not np.isnan(val):
            resto = float(m_mil.group(2)) if m_mil.group(2) and m_mil.group(2).isdigit() else 0.0
            return val * 1_000.0 + resto

    # 3. Numérico directo
    m_num = re.search(_PATRON_NUMERICO, t)
    if m_num:
        cadena = m_num.group(1).replace("$", "").replace(" ", "")
        if cadena.count(".") > 1 or (cadena.count(".") == 1 and len(cadena.split(".")[1]) == 3):
            cadena = cadena.replace(".", "")
        cadena = cadena.replace(",", ".")
        try:
            val = float(cadena)
            if val >= MONTO_MINIMO_COP:
                return val
        except ValueError:
            pass

    return np.nan

def extraer_cuotas_nuevo(texto: str):
    t = normalizar_texto(texto)
    res = {"numero_cuotas": np.nan, "monto_cuota": np.nan}
    if not t:
        return res
        
    patron = r"(?:en\s+)?(\d+|" + "|".join(NUMEROS_ESCRITOS.keys()) + r")\s+cuotas?"
    m = re.search(patron, t)
    if m:
        c_str = m.group(1)
        res["numero_cuotas"] = float(c_str) if c_str.isdigit() else float(NUMEROS_ESCRITOS.get(c_str, np.nan))

    # Monto por cuota explícito (asociado a cuotas o pagos mensuales)
    m2 = re.search(
        r"(?:cuotas?(?:\s+mensuales)?(?:\s+cada\s+una)?\s+(?:de|por|por\s+valor\s+de)|cada\s+una\s+(?:por|de)|cuota\s+(?:de|por)|pagos?\s+mensuales?\s+de)\s+([$]?\s*[\d\.,\s]+(?:\bmillones?\b(?:\s+[\d\.,\s]+\s*\bmil\b)?|\bmil\b)?)",
        t
    )
    if m2:
        val = parsear_monto_nuevo(m2.group(1))
        # Excluir años típicos si no tienen formato monetario
        if not np.isnan(val) and val not in [2018.0, 2019.0, 2020.0, 2021.0, 2022.0, 2023.0, 2024.0, 2025.0, 2026.0]:
            res["monto_cuota"] = val
            
    return res

def extraer_condiciones_economicas_nuevo(texto: str):
    t = normalizar_texto(texto)
    c_cuotas = extraer_cuotas_nuevo(t)
    
    # Descuento
    from src.payment_extraction import extraer_descuento, extraer_fecha_compromiso
    c_desc = extraer_descuento(t)
    fecha = extraer_fecha_compromiso(t)
    
    deuda = np.nan
    propuesto = np.nan
    acordado = np.nan
    
    patron_monto_captura = r"([$]?\s*[\d\.,\s]+(?:\bmillones?\b(?:\s+[\d\.,\s]+\s*\bmil\b)?|\bmil\b)?)"

    # 1. Monto de la deuda
    m_deuda = re.search(r"(?:deuda|saldo|total|debe)\s+(?:es\s+de\s+|por\s+valor\s+de\s+|de\s+)?" + patron_monto_captura, t)
    if m_deuda:
        deuda = parsear_monto_nuevo(m_deuda.group(1))
        
    # 2. Monto propuesto por el agente
    m_prop = re.search(r"(?:le\s+propongo|le\s+ofrezco|le\s+planteo|le\s+queda\s+en|pago\s+de|cuota\s+de|propuesta\s+de|pagando\s+unicamente)\s+" + patron_monto_captura, t)
    if m_prop:
        propuesto = parsear_monto_nuevo(m_prop.group(1))
        
    # 3. Monto acordado
    # Contrapropuesta del cliente aceptada: ej. "solo puedo pagar 300.000"
    m_contra = re.search(r"(?:solo\s+puedo\s+pagar|unicamente\s+puedo\s+pagar|le\s+puedo\s+pagar|solo\s+tengo)\s+" + patron_monto_captura, t)
    if m_contra:
        m_val = parsear_monto_nuevo(m_contra.group(1))
        if not np.isnan(m_val):
            if any(ok in t for ok in ["esta bien", "bueno", "si acepto", "acepto", "perfecto", "listo", "de acuerdo"]):
                acordado = m_val

    # Aceptación de monto explícito por el cliente: ej. "acepto pagar los 300.000"
    m_acep_monto = re.search(r"(?:acepto\s+pagar|me\s+comprometo\s+a\s+pagar|pagare|voy\s+a\s+pagar)\s+(?:los\s+)?" + patron_monto_captura, t)
    if m_acep_monto and np.isnan(acordado):
        m_val = parsear_monto_nuevo(m_acep_monto.group(1))
        if not np.isnan(m_val):
            acordado = m_val

    # Acuerdo confirmado explícito: ej. "el acuerdo es por 830 mil", "confirmamos el acuerdo en 250 mil"
    # No incluir preguntas del agente: "¿me confirma si acepta el acuerdo por...?"
    if np.isnan(acordado):
        m_acuerdo = re.search(r"(?:el\s+acuerdo\s+es\s+por|confirmamos\s+(?:el\s+)?acuerdo\s+en)\s+" + patron_monto_captura, t)
        if m_acuerdo:
            m_val = parsear_monto_nuevo(m_acuerdo.group(1))
            if not np.isnan(m_val):
                acordado = m_val

    return {
        "monto_deuda": deuda,
        "monto_propuesto": propuesto,
        "monto_acordado": acordado,
        "numero_cuotas": c_cuotas["numero_cuotas"],
        "monto_cuota": c_cuotas["monto_cuota"],
        "tiene_descuento": c_desc["tiene_descuento"],
        "monto_descuento": c_desc["monto_descuento"],
        "porcentaje_descuento": c_desc["porcentaje_descuento"],
        "fecha_compromiso": fecha
    }

df = pd.read_csv("data/processed/dataset_final.csv")
for cid in [55, 85]:
    t = df[df['id'] == cid].iloc[0]['transcripcion_limpia']
    print(f"=== ID {cid} ===")
    cond = extraer_condiciones_economicas_nuevo(t)
    for k, v in cond.items():
        print(f"  {k}: {v}")
