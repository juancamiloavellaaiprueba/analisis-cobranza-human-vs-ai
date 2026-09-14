import re
import pandas as pd
from src.cleaning import normalizar_texto
from src.nlp_rules import limpiar_preguntas_agente

def detectar_aceptacion_test(texto: str) -> bool:
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
            if not re.search(r"(?:pero|sin embargo|esta bien|bueno)\s+si\s+acepto", t):
                return False

    # 1. Patrones de aceptación explícita de pago
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

    # 2. Respuesta afirmativa a la pregunta de acuerdo de pago: ej. '¿Estamos de acuerdo...? De acuerdo.'
    if re.search(r"(?:estamos|esta|queda)\s+de\s+acuerdo[^?]*\?\s*de\s+acuerdo", t_raw, re.IGNORECASE):
        return True

    # 3. Patrones afirmativos generales
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
            # Excluir muletillas del agente: 'de acuerdo señor', 'de acuerdo le comento'
            contexto_post = t[m.start():min(len(t), m.end() + 40)]
            if re.search(r"\bde acuerdo\s+(?:senor|senora|caballero|don|dona|voy a|le voy|le envio|le comento|permitame)\b", contexto_post):
                continue
                
            # Excluir si está vinculado a un callback / llamado administrativo o gestión de contacto
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

tests = [
    ("si, de acuerdo, llameme manana", False),
    ("si, estoy de acuerdo con pagar $300.000 el 15", True),
    ("de acuerdo con las cuotas", True),
    ("si senora, acepto ese plan", True),
    ("de acuerdo", False),
    ("si, de acuerdo", True),
    ("estoy de acuerdo", True),
    ("no acepto", False),
    ("no estoy de acuerdo", False),
    ("de acuerdo senor, voy a revisar la informacion", False),
    ("no me sirve", False),
    ("acepto", True)
]

for frase, exp in tests:
    res = detectar_aceptacion_test(frase)
    assert res == exp, f"FAILED: {frase} -> got {res}, expected {exp}"

df = pd.read_csv("data/processed/dataset_final.csv")
for cid in [5, 37, 85]:
    t = df[df['id'] == cid].iloc[0]['transcripcion_limpia']
    print(f"ID {cid} aceptacion:", detectar_aceptacion_test(t))
print("ALL CHECKS PASSED!")
