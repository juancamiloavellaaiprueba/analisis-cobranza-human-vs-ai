"""
src/objection_analysis.py
Detección, clasificación y manejo de objeciones financieras y de contacto.
"""
import re
from typing import Dict, Any, Optional
from src.cleaning import normalizar_texto

CATEGORIAS_OBJECIONES = {
    "economica": [
        r"no tengo plata", r"no tengo dinero", r"no me alcanza", r"situacion dificil",
        r"no cuento con los recursos", r"imposible pagar", r"no puedo pagar"
    ],
    "desempleo": [
        r"sin trabajo", r"desempleado", r"perdi el empleo", r"no estoy trabajando"
    ],
    "fecha_pago": [
        r"el salario me llega despues", r"pagan a fin de mes", r"no me han pagado",
        r"hasta la otra quincena", r"despues del 15", r"no puedo pagar este mes"
    ],
    "monto": [
        r"no puedo pagar ese monto", r"muy alto", r"cuota muy alta", r"cobro excesivo",
        r"demasiada plata", r"muchos intereses", r"usura"
    ],
    "desacuerdo_deuda": [
        r"no reconozco esa deuda", r"ya pague", r"yo no pedi eso", r"no es mi deuda",
        r"fraude", r"suplantacion", r"ya cancele", r"tengo el soporte"
    ],
    "falta_recursos": [
        r"no tengo liquidez", r"quiebra", r"gastos medicos", r"emergencia familiar"
    ],
    "otra": [
        r"numero equivocado", r"aqui no vive", r"llameme despues", r"estoy ocupado"
    ]
}

def limpiar_preguntas_agente(texto: str) -> str:
    """Elimina preguntas formuladas por el asesor/agente para no confundirlas con objeciones del cliente."""
    t = texto
    patrones = [
        r"¿[^?]*?tiene\s+(?:alguna\s+)?dificultad[^?]*?\?",
        r"¿[^?]*?que\s+(?:le\s+impide|dificultad\s+tiene)[^?]*?\?",
        r"¿[^?]*?por\s+que\s+no\s+ha\s+podido\s+pagar[^?]*?\?",
        r"¿[^?]*?cual\s+es\s+el\s+motivo[^?]*?\?"
    ]
    for p in patrones:
        t = re.sub(p, " ", t, flags=re.IGNORECASE)
    return t

def detectar_objecion(texto: str) -> Optional[str]:
    """
    Identifica la categoría principal de objeción expresada por el deudor.
    Filtra preguntas inquisitivas del agente para evitar falsos positivos.
    """
    t_raw = normalizar_texto(texto)
    if not t_raw:
        return None
    t = limpiar_preguntas_agente(t_raw)
    
    for cat, patrones in CATEGORIAS_OBJECIONES.items():
        for p in patrones:
            if re.search(r"\b" + p + r"\b", t):
                return cat
    return None

def analizar_objeciones(texto: str) -> Dict[str, Any]:
    """
    Evalúa si existe objeción principal, su evidencia y si el agente ofreció alternativas.
    Nota: Se modela una objeción principal por llamada conforme al alcance actual del proyecto.
    """
    t_raw = normalizar_texto(texto)
    tipo = detectar_objecion(t_raw)
    tiene_obj = tipo is not None
    
    num_obj = 1 if tiene_obj else 0
    evidencia = ""
    if tiene_obj:
        t = limpiar_preguntas_agente(t_raw)
        for cat, patrones in CATEGORIAS_OBJECIONES.items():
            for p in patrones:
                m = re.search(r"\b" + p + r"\b", t)
                if m:
                    evidencia = m.group(0)
                    break
            if evidencia:
                break
                
    # Detección de manejo por el agente (ofrece alternativas de pago)
    manejo = 1 if tiene_obj and any(re.search(r"\b" + p + r"\b", t_raw) for p in [
        "alternativa", "cuotas", "plazo", "descuento", "le puedo ofrecer", "revisar una opcion"
    ]) else 0
    
    return {
        "tiene_objecion": 1 if tiene_obj else 0,
        "num_objeciones": num_obj,
        "tipo_objecion": tipo if tipo else "ninguna",
        "manejo_objecion": manejo,
        "objecion_resuelta": 0,
        "evidencia_objecion": evidencia
    }
