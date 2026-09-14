"""
scripts/03_extraer_variables.py
Extracción de variables analíticas, condiciones económicas, objeciones y generación de dataset_final.csv.
"""
import sys
import re
import logging
from pathlib import Path
from typing import Dict, Any
import pandas as pd
import numpy as np

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.cleaning import normalizar_texto
from src.nlp_rules import (
    detectar_compromiso_pago,
    detectar_aceptacion,
    clasificar_intencion_y_dificultad,
    inferir_dinamica_conversacional
)
from src.payment_extraction import extraer_condiciones_economicas
from src.objection_analysis import analizar_objeciones

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("03_extraer_variables")

def procesar_llamada(row: Dict[str, Any]) -> Dict[str, Any]:
    raw_orig = str(row.get("transcripcion_original", "") or row.get("transcripcion", ""))
    raw_clean = str(row.get("transcripcion_limpia", "") or row.get("texto", raw_orig))
    t = normalizar_texto(raw_clean)
    
    # 1. Variables principales
    id_val = int(row.get("id", 0))
    archivo = str(row.get("archivo", ""))
    tipo_agente = str(row.get("tipo_agente", ""))
    duracion = float(row.get("duracion_segundos", 0.0))
    palabras = int(row.get("num_palabras", len(raw_clean.split())))
    
    # Contactabilidad
    es_buzon = bool(row.get("es_buzon_voz", False))
    if es_buzon or len(t) < 15:
        contactabilidad = 0
        evid_cont = "Buzon de voz o audio vacio"
    else:
        contactabilidad = 1
        evid_cont = t[:70]
        
    # 2. Condiciones economicas
    cond = extraer_condiciones_economicas(t)
    
    # 3. Objeciones
    obj = analizar_objeciones(t)
    
    # 4. Negociacion y oferta
    tiene_oferta = 1 if (
        any(p in t for p in ["ofrezco", "propongo", "alternativa", "le queda facil", "descuento", "plan de pago"])
        or not np.isnan(cond["monto_propuesto"])
        or not np.isnan(cond["numero_cuotas"])
    ) and contactabilidad == 1 else 0
    
    evid_oferta = "Propuesta de pago formulada" if tiene_oferta == 1 else ""
    
    tiene_negociacion = 1 if tiene_oferta == 1 and any(p in t for p in [
        "cuotas", "rebaja", "otra opcion", "descuento", "plazo", "reestructurar"
    ]) else 0
    evid_neg = "Negociacion de alternativas de pago" if tiene_negociacion == 1 else ""
    num_propuestas = 2 if tiene_negociacion == 1 else (1 if tiene_oferta == 1 else 0)
    
    # 5. Aceptacion y compromiso
    aceptacion = 1 if detectar_aceptacion(t) and contactabilidad == 1 else 0
    evid_acep = "Aceptacion verbal del cliente" if aceptacion == 1 else ""
    
    intencion, dificultad = clasificar_intencion_y_dificultad(t)
    num_preg, tipo_resp = inferir_dinamica_conversacional(raw_clean)
    
    # 6. Jerarquía de Acuerdo de Pago y Validación Contextual
    cond_vinculante = (
        not np.isnan(cond["monto_acordado"]) or
        not np.isnan(cond["monto_propuesto"]) or
        cond["fecha_compromiso"] is not None or
        not np.isnan(cond["numero_cuotas"])
    )
    
    compromiso_directo = detectar_compromiso_pago(t)
    
    # Detección de rechazo explícito o dificultad activa no superada
    cliente_rechaza = (
        any(r in t for r in [
            "no puedo pagar", "no voy a pagar", "no acepto", "no me sirve",
            "no puedo comprometerme", "imposible pagar", "muy alto no puedo"
        ])
        and not re.search(r"(?:pero|sin embargo|aunque)\s+si\s+(?:puedo|voy\s+a|pagare)\s+pagar", t)
        and not ("solo puedo pagar" in t and any(ok in t for ok in ["esta bien", "bueno", "listo", "perfecto"]))
    )
    
    # Criterio estricto de acuerdo: contacto efectivo + oferta expresa + aceptación/compromiso + condición vinculante + sin rechazo activo
    if (
        contactabilidad == 1
        and tiene_oferta == 1
        and (aceptacion == 1 or compromiso_directo)
        and cond_vinculante
        and not cliente_rechaza
    ):
        acuerdo = 1
        confianza = 0.90
        resultado = "acuerdo_pago"
        # Objeción resuelta únicamente si hubo objeción, manejo con alternativas y el cliente aceptó el acuerdo
        obj_resuelta = 1 if (obj["tiene_objecion"] == 1 and obj["manejo_objecion"] == 1 and aceptacion == 1) else 0
        evid_monto = cond['monto_acordado'] if not np.isnan(cond['monto_acordado']) else cond['monto_propuesto']
        evid_acuerdo = f"Acuerdo vinculante (fecha: {cond['fecha_compromiso']}, monto: {evid_monto})"
    elif contactabilidad == 0:
        acuerdo = 0
        confianza = 0.95
        resultado = "no_contactado"
        obj_resuelta = 0
        evid_acuerdo = ""
    elif contactabilidad == 1 and (cliente_rechaza or obj["tiene_objecion"] == 1):
        acuerdo = 0
        confianza = 0.85
        resultado = "dificultad_sin_acuerdo" if (dificultad == 1 or obj["tipo_objecion"] in ["economica", "desempleo"]) else "propuesta_rechazada"
        obj_resuelta = 0
        evid_acuerdo = ""
    elif tiene_negociacion == 1:
        acuerdo = 0
        confianza = 0.80
        resultado = "negociacion_sin_acuerdo"
        obj_resuelta = 0
        evid_acuerdo = ""
    elif tiene_oferta == 1:
        acuerdo = 0
        confianza = 0.75
        resultado = "propuesta_rechazada"
        obj_resuelta = 0
        evid_acuerdo = ""
    else:
        acuerdo = 0
        confianza = 0.70
        resultado = "contactado_sin_propuesta" if contactabilidad == 1 else "otro"
        obj_resuelta = 0
        evid_acuerdo = ""
        
    # 7. Inconsistencia matemática del acuerdo (diálogo original con inconsistencia cuotas vs total)
    inconsistencia_matematica = 0
    monto_comparar = cond["monto_acordado"] if not np.isnan(cond["monto_acordado"]) else cond["monto_propuesto"]
    if (
        not np.isnan(monto_comparar)
        and not np.isnan(cond["monto_cuota"])
        and not np.isnan(cond["numero_cuotas"])
        and cond["numero_cuotas"] > 1
    ):
        esperado = cond["monto_cuota"] * cond["numero_cuotas"]
        if abs(monto_comparar - esperado) > max(100.0, 0.01 * monto_comparar):
            inconsistencia_matematica = 1

    return {
        # A. Contacto
        "id": id_val,
        "archivo": archivo,
        "tipo_agente": tipo_agente,
        "duracion_segundos": duracion,
        "num_palabras": palabras,
        "contactabilidad": contactabilidad,
        
        # B. Cobranza
        "oferta_pago": tiene_oferta,
        "aceptacion_pago": aceptacion,
        "acuerdo_pago": acuerdo,
        "resultado_final": resultado,
        
        # C. Negociacion
        "negociacion": tiene_negociacion,
        "num_propuestas_pago": num_propuestas,
        
        # D. Objeciones
        "tiene_objecion": obj["tiene_objecion"],
        "num_objeciones": obj["num_objeciones"],
        "tipo_objecion": obj["tipo_objecion"],
        "manejo_objecion": obj["manejo_objecion"],
        "objecion_resuelta": obj_resuelta,
        
        # E. Variables Economicas
        "monto_deuda": cond["monto_deuda"],
        "monto_propuesto": cond["monto_propuesto"],
        "monto_acordado": cond["monto_acordado"],
        "numero_cuotas": cond["numero_cuotas"],
        "monto_cuota": cond["monto_cuota"],
        "inconsistencia_matematica_acuerdo": inconsistencia_matematica,
        "tiene_descuento": cond["tiene_descuento"],
        "monto_descuento": cond["monto_descuento"],
        "fecha_compromiso": cond["fecha_compromiso"],
        
        # F. Variables de Conversacion
        "num_preguntas_agente": num_preg,
        "tipo_respuesta_cliente": tipo_resp,
        "intencion_pago": intencion,
        "dificultad_pago": dificultad,
        
        # G. Variables de Control
        "confianza_nlp": confianza,
        "control_calidad": "ok",
        "requiere_revision": 0,
        
        # H. Evidencias
        "evidencia_contactabilidad": evid_cont,
        "evidencia_oferta": evid_oferta,
        "evidencia_aceptacion": evid_acep,
        "evidencia_acuerdo": evid_acuerdo,
        "evidencia_objecion": obj["evidencia_objecion"],
        "evidencia_negociacion": evid_neg,
        
        # Candidatos para validacion
        "acuerdo_pago_candidato": acuerdo,
        "acuerdo_pago_validado": np.nan,
        "objecion_candidato": obj["tipo_objecion"],
        "objecion_validada": np.nan,
        "resultado_final_candidato": resultado,
        "resultado_final_validado": np.nan,
        
        # Textos originales
        "transcripcion_original": raw_orig,
        "transcripcion_limpia": raw_clean
    }

def main():
    entrada = ROOT_DIR / "data" / "processed" / "dataset_limpio_procesado.csv"
    logger.info(f"Cargando dataset desde {entrada}...")
    df = pd.read_csv(entrada, encoding="utf-8")
    
    registros = []
    for _, fila in df.iterrows():
        registros.append(procesar_llamada(fila.to_dict()))
        
    df_final = pd.DataFrame(registros)
    salida_final = ROOT_DIR / "data" / "processed" / "dataset_final.csv"
    salida_final.parent.mkdir(parents=True, exist_ok=True)
    df_final.to_csv(salida_final, index=False, encoding="utf-8")
    
    logger.info(f"dataset_final.csv generado exitosamente en {salida_final} ({len(df_final)} filas, {df_final.shape[1]} columnas)")

if __name__ == "__main__":
    main()
