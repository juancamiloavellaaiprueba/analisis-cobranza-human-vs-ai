"""
src/nlp_rules.py
Reglas contextuales de NLP, análisis de negación, detección de intención vs acuerdo y dinámica conversacional.
"""
import re
from typing import Dict, Any, Tuple, List, Optional
import numpy as np
from src.cleaning import normalizar_texto

PALABRAS_NEGACION = ["no", "nunca", "jamas", "tampoco", "nada", "ni", "imposible", "dificil"]

PATRONES_PREGUNTAS_AGENTE = [
    r"¿[^?]*?(?:puede|podria|va\s+a|estaria\s+dispuesto\s+a|desea|quiere)\s+pagar[^?]*?\?",
    r"¿[^?]*?(?:esta|estaria|queda)\s+de\s+acuerdo[^?]*?\?",
    r"¿[^?]*?(?:acepta|aceptaria)\s+el\s+(?:acuerdo|pago|plan)[^?]*?\?",
    r"¿[^?]*?tiene\s+(?:alguna\s+)?dificultad[^?]*?\?"
]

def limpiar_preguntas_agente(texto: str) -> str:
    """Elimina preguntas explícitas del agente para evitar falsos positivos de compromiso o acuerdo."""
    t = texto
    for p in PATRONES_PREGUNTAS_AGENTE:
        t = re.sub(p, " ", t, flags=re.IGNORECASE)
    return t

def analizar_negacion_contextual(texto: str, palabra_clave: str, ventana_tokens: int = 5) -> Tuple[bool, str]:
    """
    Analiza las ocurrencias del término clave considerando cláusulas adversativas
    ('pero sí', 'sin embargo sí') y ventanas previas.
    Retorna (negado, tipo_polaridad).
    """
    t = normalizar_texto(texto)
    target = normalizar_texto(palabra_clave)
    
    if target not in t:
        return False, "no_encontrado"
        
    coincidencias = list(re.finditer(rf"\b{re.escape(target)}\b", t))
    if not coincidencias:
        return False, "no_encontrado"
        
    # Verificar si existe una cláusula adversativa que sobreescriba una negación previa
    # Ejemplo: "no tengo dinero hoy, pero sí puedo pagar el 15"
    patron_recuperacion = rf"(?:pero|sin embargo|aunque)\s+(?:si\s+)?(?:puedo|voy\s+a|cancelo|pago)\s+{re.escape(target)}"
    if re.search(patron_recuperacion, t):
        return False, "positivo"
        
    negaciones_encontradas = []
    for match in coincidencias:
        inicio = match.start()
        texto_previo = t[:inicio].strip()
        tokens_previos = texto_previo.split()[-ventana_tokens:] if texto_previo else []
        negado = any(tok in PALABRAS_NEGACION for tok in tokens_previos)
        negaciones_encontradas.append(negado)
        
    # Si la última ocurrencia está explícitamente negada, predomina la negación
    if negaciones_encontradas[-1]:
        if any(m in t for m in ["no puedo", "no cuento", "no tengo plata", "no tengo dinero", "imposible pagar", "dificil"]):
            return True, "dificultad"
        return True, "negativo"
        
    # Si todas están negadas
    if all(negaciones_encontradas):
        return True, "negativo"
        
    return False, "positivo"

def detectar_compromiso_pago(texto: str) -> bool:
    """
    Evalúa si el texto denota compromiso o intención positiva de pago atribuible al deudor.
    Diferencia 'voy a pagar' de 'no voy a pagar', 'no puedo pagar' y preguntas del agente.
    """
    t_raw = normalizar_texto(texto)
    if not t_raw:
        return False
        
    # Caso contraste afirmativo posterior: "no puedo pagar hoy, pero si puedo pagar el 15"
    if re.search(r"(?:pero|sin embargo|aunque)\s+si\s+(?:puedo|voy\s+a|pagare|cancelo)\s+pagar", t_raw):
        return True
    if re.search(r"(?:no\s+puedo\s+pagar\s+hoy|no\s+tengo\s+plata\s+hoy)[^.]*?(?:pero|aunque|sin embargo)\s+(?:si\s+)?(?:puedo|voy\s+a|cancelo|pago)", t_raw):
        return True

    # Remover preguntas del agente para que no cuenten como compromiso del cliente
    t = limpiar_preguntas_agente(t_raw)
    
    # Patrones de negación / rechazo explícito
    patrones_negados = [
        r"no voy a pagar", r"no quiero pagar", r"no puedo pagar",
        r"jamas voy a pagar", r"nunca pagare", r"imposible pagar",
        r"no puedo comprometerme", r"no pienso pagar", r"no puedo hacer (?:un|otro) acuerdo"
    ]
    for p in patrones_negados:
        if re.search(rf"\b{p}\b", t):
            # Si no hay una posterior afirmación salvadora, es rechazo
            if not re.search(r"(?:pero|sin embargo|aunque)\s+(?:si\s+)?(?:puedo|voy\s+a)\s+pagar", t):
                return False
            
    # Patrones de compromiso positivo en primera persona o confirmación directa
    patrones_positivos = [
        r"yo voy a pagar", r"si voy a pagar", r"me comprometo a pagar",
        r"me comprometo con", r"cancelo el", r"pagare el",
        r"si me comprometo", r"hago el pago", r"realizo el pago",
        r"si puedo pagar", r"yo pago el", r"pago el", r"voy a pagar",
        r"puedo pagar"
    ]
    for p in patrones_positivos:
        m = re.search(rf"\b{p}\b", t)
        if m:
            # Validar que no sea pregunta del agente (ej. "¿usted puede pagar?")
            inicio = max(0, m.start() - 30)
            contexto_previo = t[inicio:m.start()]
            if any(q in contexto_previo for q in ["usted ", "usted puede", "podria usted", "le queda facil"]):
                continue
            return True
            
    return False

def detectar_aceptacion(texto: str) -> bool:
    """
    Evalúa si el cliente denota aceptación verbal inequívoca a una propuesta de pago.
    Descarta 'de acuerdo' aislado o cuando corresponde a acuerdos administrativos
    (agendamiento de llamada, confirmación de datos, envíos informativos) o muletillas del agente.
    """
    t_raw = normalizar_texto(texto)
    if not t_raw:
        return False
        
    t = limpiar_preguntas_agente(t_raw)
    
    # Patrones de rechazo
    patrones_rechazo = [
        r"no acepto", r"no estoy de acuerdo", r"desacuerdo",
        r"no me sirve", r"no autorizo", r"no me parece",
        r"no puedo comprometerme", r"no puedo pagar", r"muy alto no puedo"
    ]
    for p in patrones_rechazo:
        if re.search(rf"\b{p}\b", t):
            # Si hay rechazo explícito y no hay una aceptación posterior explícita ("está bien, sí acepto")
            if not re.search(r"(?:pero|sin embargo|esta bien|bueno)\s+si\s+acepto", t):
                return False

    # 1. Patrones de aceptación explícita vinculados a condiciones de pago
    patrones_pago_explicitos = [
        r"\b(?:si,?\s+)?acepto\s+(?:el\s+acuerdo|la\s+propuesta|las\s+cuotas|pagar|el\s+plan|ese\s+plan|esa\s+opcion|el\s+pago|las\s+condiciones)\b",
        r"\b(?:si\s+senora?,\s+)?acepto\s+ese\s+plan\b",
        r"\b(?:si,?\s+)?(?:estoy\s+de\s+acuerdo|de\s+acuerdo)\s+(?:con|en)\s+(?:pagar|el\s+pago|la\s+cuota|las\s+cuotas|el\s+plan|la\s+propuesta|el\s+acuerdo|los\s+[$]?\d+|el\s+valor|el\s+monto)\b",
        r"\bde\s+acuerdo\s+(?:con\s+la\s+cuota|me\s+sirve|lo\s+pago)\b",
        r"\b(?:si,?\s+)?(?:me\s+sirve\s+esa\s+opcion|perfecto\s+me\s+sirve)\b",
        r"\bme\s+parece\s+bien\s+(?:esa\s+opcion|el\s+acuerdo|la\s+propuesta|el\s+plan)\b"
    ]
    for p in patrones_pago_explicitos:
        if re.search(p, t):
            return True

    # 2. Respuesta afirmativa del cliente a la pregunta de acuerdo: ej. "¿Estamos de acuerdo...? De acuerdo."
    if re.search(r"(?:estamos|esta|queda)\s+de\s+acuerdo[^?]*\?\s*de\s+acuerdo", t_raw, re.IGNORECASE):
        return True

    # 3. Patrones afirmativos generales: requieren no ser acuerdos administrativos de llamadas/datos
    patrones_generales = [
        r"\bsi\s+acepto\b",
        r"\bacepto\b",
        r"\bsi\s+estoy\s+de\s+acuerdo\b",
        r"\bestoy\s+de\s+acuerdo\b",
        r"\bsi,?\s+de\s+acuerdo\b",
        r"\bsi\s+me\s+sirve\b"
    ]

    for p in patrones_generales:
        for m in re.finditer(p, t):
            # Excluir si es muletilla típica del agente: "de acuerdo señor", "de acuerdo le voy", "de acuerdo permítame"
            contexto_post = t[m.start():min(len(t), m.end() + 40)]
            if re.search(r"\bde acuerdo\s+(?:senor|senora|caballero|don|dona|voy a|le voy|le envio|le comento|permitame)\b", contexto_post):
                continue
                
            # Excluir si está vinculado a un callback / llamado administrativo o gestión de contacto sin pago
            inicio_ctx = max(0, m.start() - 65)
            fin_ctx = min(len(t), m.end() + 65)
            ctx_inmediato = t[inicio_ctx:fin_ctx]
            
            es_administrativo = bool(
                re.search(r"\b(?:llam(?:ar|arme|eme|o)|comunic(?:ar|arme|eme|o)|contact(?:ar|arme|eme|o)|marc(?:ar|arme|eme|o))\b", ctx_inmediato) or
                re.search(r"\b(?:manana\s+(?:a\s+las|en\s+la\s+tarde|sobre\s+las)|yo\s+me\s+comunico|yo\s+lo\s+llamo|me\s+indica|yo\s+le\s+marco)\b", ctx_inmediato)
            )
            tiene_pago_inmediato = bool(
                re.search(r"\b(?:pagar|cuota|cuotas|plan|monto|valor|saldo|consignar|abonar)\b", ctx_inmediato)
            )
            if es_administrativo and not tiene_pago_inmediato:
                continue

            return True

    return False

def clasificar_intencion_y_dificultad(texto: str) -> Tuple[int, int]:
    """
    Retorna (intencion_pago, dificultad_pago).
    Garantiza que preguntas del agente ('¿puede pagar el viernes?') no se clasifiquen
    como intención positiva si el cliente responde negativamente o con dificultad.
    """
    t_raw = normalizar_texto(texto)
    t = limpiar_preguntas_agente(t_raw)
    
    tiene_dificultad = 1 if any(re.search(rf"\b{p}\b", t_raw) for p in [
        "no puedo pagar", "no tengo plata", "no tengo dinero",
        "sin trabajo", "desempleado", "no me alcanza", "situacion dificil",
        "no tengo liquidez", "muy alto no puedo"
    ]) else 0
    
    # Intención positiva: requiere afirmación o compromiso genuino
    tiene_intencion = 1 if (
        detectar_compromiso_pago(texto) or
        any(re.search(rf"\b{p}\b", t) for p in [
            "quiero pagar", "si quiero pagar", "tengo la intencion",
            "me interesa pagar", "deseo ponerme al dia"
        ])
    ) else 0
    
    # Si cliente dice "no puedo", la intención decae a 0 a menos que diga "quiero pagar pero no puedo"
    if "no puedo" in t and "quiero pagar" not in t and not re.search(r"pero\s+si\s+(?:puedo|voy\s+a)\s+pagar", t):
        tiene_intencion = 0
        
    return tiene_intencion, tiene_dificultad

def inferir_dinamica_conversacional(texto: str) -> Tuple[int, str]:
    """Estima el número de preguntas del agente y el tipo de respuesta predominante del cliente."""
    num_preguntas = len(re.findall(r"\?|¿|\b(me confirma|podria|seria tan amable|le gustaria)\b", texto.lower()))
    t = normalizar_texto(texto)
    
    if any(m in t for m in ["no voy a pagar", "no quiero pagar", "no acepto"]):
        tipo_resp = "negativa_rechazo"
    elif any(m in t for m in ["no puedo pagar", "no tengo plata", "desempleado"]):
        tipo_resp = "dificultad"
    elif any(m in t for m in ["si claro", "si acepto", "estoy de acuerdo", "perfecto me sirve"]):
        tipo_resp = "afirmativa"
    elif any(m in t for m in ["voy a mirar", "dejeme pensar", "no se si pueda", "tal vez"]):
        tipo_resp = "indecisa"
    elif any(m in t for m in ["llameme despues", "estoy ocupado"]):
        tipo_resp = "evasiva"
    else:
        tipo_resp = "neutra"
        
    return num_preguntas, tipo_resp
