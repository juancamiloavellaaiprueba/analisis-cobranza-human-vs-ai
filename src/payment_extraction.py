"""
src/payment_extraction.py
Extraccion de entidades financieras en Pesos Colombianos (COP), cuotas, descuentos y fechas.
"""
import re
from typing import Dict, Any, Optional
import numpy as np
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

def parsear_monto(texto_monto: Optional[str]) -> float:
    """
    Convierte cadena con formato de pesos COP a float. Retorna np.nan si no es valido.
    Exige evidencia monetaria suficiente para no confundir números cardinales aislados
    ('dos', 'tres', 'a dos') o conteos de cuotas ('15 cuotas') con dinero.
    """
    if texto_monto is None or not str(texto_monto).strip():
        return np.nan
    t = str(texto_monto).strip().lower()
    if t in ["n/a", "-", "ninguno", "no aplica", "nan", "null"]:
        return np.nan

    # Excluir menciones aisladas de cuotas sin monto monetario
    if re.search(r"^\s*\d+\s+cuotas?\s*$", t):
        return np.nan

    # Evidencia monetaria requerida: $, mil, millon/millones, pesos, cop,
    # o formato numérico con separador de miles o >= 4 dígitos
    tiene_evidencia_monetaria = bool(
        re.search(r"[\$]|mil|millon|pesos|cop\b", t) or
        re.search(r"\b\d{1,3}(?:\.\d{3})+\b", t) or
        re.search(r"\b\d{4,}\b", t)
    )
    if not tiene_evidencia_monetaria:
        return np.nan

    # 1. Millones con posible resto en miles (ej. '2 millones 110 mil', '10 millones')
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

    # 2. Miles (ej. '500 mil', 'dos mil pesos', '200 mil')
    m_mil = re.search(_PATRON_MIL, t)
    if m_mil:
        num_str = m_mil.group(1).replace(",", ".")
        val = float(num_str) if num_str.replace(".", "").isdigit() else float(NUMEROS_ESCRITOS.get(num_str, np.nan))
        if not np.isnan(val):
            resto = float(m_mil.group(2)) if m_mil.group(2) and m_mil.group(2).isdigit() else 0.0
            return val * 1_000.0 + resto

    # 3. Numerico directo con $ o formato 500.000 o >= 1000
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

def extraer_cuotas(texto: str) -> Dict[str, float]:
    """Extrae numero de cuotas y valor por cuota vinculada."""
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
        val = parsear_monto(m2.group(1))
        # Descartar si el valor coincide con años históricos (ej. 'de 2021')
        if not np.isnan(val) and val not in [2018.0, 2019.0, 2020.0, 2021.0, 2022.0, 2023.0, 2024.0, 2025.0, 2026.0]:
            res["monto_cuota"] = val

    return res

def extraer_descuento(texto: str) -> Dict[str, Any]:
    """Extrae informacion de condonaciones y descuentos."""
    t = normalizar_texto(texto)
    res = {"tiene_descuento": False, "monto_descuento": np.nan, "porcentaje_descuento": np.nan}
    if not any(p in t for p in ["descuento", "rebaja", "condonacion", "quita"]):
        return res
    if any(re.search(p, t) for p in [r"\bno hay descuento\b", r"\bsin descuento\b", r"\bno aplica descuento\b"]):
        return res

    res["tiene_descuento"] = True
    m_pct = re.search(r"descuento\s+del?\s+(\d+(?:[.,]\d+)?)\s*%", t)
    if m_pct:
        try:
            res["porcentaje_descuento"] = float(m_pct.group(1).replace(",", "."))
        except ValueError:
            pass

    m_monto = re.search(
        r"descuento\s+de\s+([$]?\s*[\d\.,\s]+(?:\bmillones?\b(?:\s+[\d\.,\s]+\s*\bmil\b)?|\bmil\b)?)",
        t
    )
    if m_monto:
        res["monto_descuento"] = parsear_monto(m_monto.group(1))

    return res

def extraer_fecha_compromiso(texto: str) -> Optional[str]:
    """
    Extrae la fecha o plazo comprometido, descartando fechas históricas de origen de la deuda
    y asegurando que correspondan a una promesa o condición de pago futuro.
    """
    t = normalizar_texto(texto)
    if not t:
        return None

    # Descartar menciones históricas de deuda previa (ej. 'se originó el 27 de diciembre de 2017')
    t_sin_historico = re.sub(
        r"(?:deuda|obligacion|credito|mora|saldo)\s+(?:se\s+origino|originad[oa]|radicad[oa]|venci[oa]|desde)\s+(?:el\s+)?\d{1,2}\s+de\s+[a-z]+(?:\s+de\s+\d{4})?",
        " ",
        t
    )
    t_sin_historico = re.sub(
        r"(?:se\s+origino|originad[oa]|radicad[oa]|venci[oa]|adquirid[oa]|mora\s+desde)\s+(?:el\s+)?\d{1,2}\s+de\s+[a-z]+(?:\s+de\s+\d{4})?",
        " ",
        t_sin_historico
    )
    t_sin_historico = re.sub(
        r"\b\d{1,2}\s+de\s+[a-z]+\s+de\s+(?:19\d\d|200\d|201\d|202[0-3])\b",
        " ",
        t_sin_historico
    )

    # 1. Priorizar fechas ligadas a compromiso o pago futuro (tomar la última acordada si hubo negociación)
    patrones_compromiso = [
        r"(?:pago|pagare|cancelo|cancelar|abonar|consignar|consigno|pagar|puedo\s+pagar|comprometo\s+a\s+pagar|para|hasta|a\s+mas\s+tardar|primera\s+cuota(?:\s+se\s+paga|\s+es|\s+para)?)\s+(?:el\s+)?(\d{1,2}\s+de\s+(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre))",
        r"(?:pago|pagare|cancelo|cancelar|abonar|consignar|consigno|pagar|puedo\s+pagar|comprometo\s+a\s+pagar|para|hasta|a\s+mas\s+tardar|primera\s+cuota(?:\s+se\s+paga|\s+es|\s+para)?)\s+(?:el\s+dia\s+|el\s+)(\d{1,2})\b(?!\s+de\s+[a-z]+)",
        r"(?:pago|pagare|cancelo|cancelar|abonar|consignar|consigno|pagar|puedo\s+pagar|comprometo\s+a\s+pagar|para|hasta)\s+(?:el\s+)?(proximo\s+viernes|el\s+viernes|el\s+lunes|el\s+martes|el\s+miercoles|el\s+jueves|el\s+sabado|el\s+domingo|manana|fin\s+de\s+mes|quincena)"
    ]
    coincidencias_compromiso = []
    for p in patrones_compromiso:
        for m in re.finditer(p, t_sin_historico):
            coincidencias_compromiso.append((m.start(), m.group(1).strip()))

    if coincidencias_compromiso:
        # Ordenar por posición y retornar la última acordada en la conversación
        coincidencias_compromiso.sort(key=lambda x: x[0])
        return coincidencias_compromiso[-1][1]

    # 2. Patrones generales si existe contexto de pago en el texto filtrado
    if any(k in t_sin_historico for k in ["pago", "pagar", "pagare", "cuota", "acuerdo", "compromiso", "cancelar"]):
        patrones_generales = [
            r"\b(\d{1,2}\s+de\s+(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre))\b",
            r"\b(?:el\s+dia|el)\s+(\d{1,2})\b(?!\s+de\s+[a-z]+)",
            r"\b(proximo\s+viernes|el\s+viernes|el\s+lunes|el\s+martes|el\s+miercoles|el\s+jueves|el\s+sabado|el\s+domingo)\b",
            r"\b(manana|hoy|este\s+fin\s+de\s+semana)\b",
            r"\b(fin\s+de\s+mes|quincena|proximo\s+mes)\b"
        ]
        coincidencias_gen = []
        for p in patrones_generales:
            for m in re.finditer(p, t_sin_historico):
                coincidencias_gen.append((m.start(), m.group(1).strip()))
        if coincidencias_gen:
            coincidencias_gen.sort(key=lambda x: x[0])
            return coincidencias_gen[-1][1]

    return None

def extraer_condiciones_economicas(texto: str) -> Dict[str, Any]:
    """Consolida la extracción monetaria de una conversación con diferenciación estricta propuesta vs acordado."""
    t = normalizar_texto(texto)
    c_cuotas = extraer_cuotas(t)
    c_desc = extraer_descuento(t)
    fecha = extraer_fecha_compromiso(t)

    deuda = np.nan
    propuesto = np.nan
    acordado = np.nan

    patron_monto_captura = r"([$]?\s*[\d\.,\s]+(?:\bmillones?\b(?:\s+[\d\.,\s]+\s*\bmil\b)?|\bmil\b)?)"

    # 1. Monto de la deuda
    m_deuda = re.search(r"(?:deuda|saldo|total|debe)\s+(?:es\s+de\s+|por\s+valor\s+de\s+|de\s+)?" + patron_monto_captura, t)
    if m_deuda:
        deuda = parsear_monto(m_deuda.group(1))

    # 2. Monto propuesto por el agente
    m_prop = re.search(r"(?:le\s+propongo|le\s+ofrezco|le\s+planteo|le\s+queda\s+en|pago\s+de|cuota\s+de|propuesta\s+de|pagando\s+unicamente)\s+" + patron_monto_captura, t)
    if m_prop:
        propuesto = parsear_monto(m_prop.group(1))

    # 3. Monto acordado: SOLO si el cliente expresa monto específico aceptado, contrapropuesta aceptada o acuerdo explícito
    # Contrapropuesta del cliente: ej. "solo puedo pagar 300.000"
    m_contra = re.search(r"(?:solo\s+puedo\s+pagar|unicamente\s+puedo\s+pagar|le\s+puedo\s+pagar|solo\s+tengo)\s+" + patron_monto_captura, t)
    if m_contra:
        m_val = parsear_monto(m_contra.group(1))
        if not np.isnan(m_val):
            if any(ok in t for ok in ["esta bien", "bueno", "si acepto", "acepto", "perfecto", "listo", "de acuerdo"]):
                acordado = m_val

    # Aceptación de monto explícito por el cliente: ej. "acepto pagar los 300.000"
    m_acep_monto = re.search(r"(?:acepto\s+pagar|me\s+comprometo\s+a\s+pagar|pagare|voy\s+a\s+pagar)\s+(?:los\s+)?" + patron_monto_captura, t)
    if m_acep_monto and np.isnan(acordado):
        m_val = parsear_monto(m_acep_monto.group(1))
        if not np.isnan(m_val):
            acordado = m_val

    # Acuerdo confirmado explícito: ej. "el acuerdo es por 830 mil", "confirmamos el acuerdo en 250 mil"
    # No considerar preguntas del agente como acuerdo confirmado
    if np.isnan(acordado):
        m_acuerdo = re.search(r"(?:el\s+acuerdo\s+es\s+por|confirmamos\s+(?:el\s+)?acuerdo\s+en)\s+" + patron_monto_captura, t)
        if m_acuerdo:
            m_val = parsear_monto(m_acuerdo.group(1))
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
