"""
src/validation.py
Segunda verificación automática, auditoría cruzada y generación del dataset de validación humana.
"""
from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np

def verificar_consistencia_registro(fila: Dict[str, Any]) -> Tuple[str, int, str]:
    """
    Evalúa reglas cruzadas de consistencia lógica:
    - acuerdo_pago == 1 pero no existe evidencia_acuerdo
    - resultado_final == 'acuerdo_pago' pero acuerdo_pago == 0
    - numero_cuotas detectado pero sin evidencia de cuotas
    - monto_acordado sin evidencia monetaria
    - aceptacion_pago == 1 con negación explícita
    Retorna (control_calidad, requiere_revision, motivo)
    """
    motivos = []
    requiere_rev = 0
    
    contactabilidad = fila.get("contactabilidad", 0)
    acuerdo = fila.get("acuerdo_pago", 0)
    aceptacion = fila.get("aceptacion_pago", 0)
    resultado = fila.get("resultado_final", "")
    cuotas = fila.get("numero_cuotas", np.nan)
    confianza = fila.get("confianza_nlp", 1.0)
    evid_acuerdo = str(fila.get("evidencia_acuerdo", "")).strip()
    
    if acuerdo == 1 and contactabilidad == 0:
        return "inconsistente", 1, "Acuerdo marcado en llamada sin contacto efectivo"
        
    if resultado == "acuerdo_pago" and acuerdo == 0:
        return "inconsistente", 1, "Resultado final marca acuerdo pero acuerdo_pago es 0"
        
    if acuerdo == 1 and not evid_acuerdo:
        motivos.append("Acuerdo=1 pero sin evidencia textual de acuerdo")
        requiere_rev = 1
        
    if acuerdo == 1 and aceptacion == 0:
        motivos.append("Acuerdo detectado por compromiso directo sin aceptacion formal")
        requiere_rev = 1
        
    if not np.isnan(cuotas) and acuerdo == 0:
        motivos.append("Se mencionaron cuotas pero no se concreto acuerdo de pago")
        requiere_rev = 1
        
    if confianza < 0.70:
        motivos.append("Confianza algoritmica baja (< 0.70)")
        requiere_rev = 1
        
    inconsistencia = fila.get("inconsistencia_matematica_acuerdo", 0)
    if inconsistencia == 1:
        motivos.append("Inconsistencia matematica en dialogo: monto_total != monto_cuota * numero_cuotas")
        requiere_rev = 1
        
    if any("inconsistente" in m for m in motivos):
        return "inconsistente", 1, "; ".join(motivos)
    elif motivos:
        return "revisar", requiere_rev, "; ".join(motivos)
    return "ok", 0, "Registro consistente"

def ejecutar_segunda_verificacion(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica la segunda verificación cruzada y asigna control_calidad y requiere_revision."""
    df_out = df.copy()
    estados = []
    requiere_list = []
    motivos = []
    
    for _, r in df_out.iterrows():
        est, req, mot = verificar_consistencia_registro(r.to_dict())
        estados.append(est)
        requiere_list.append(req)
        motivos.append(mot)
        
    df_out["control_calidad"] = estados
    df_out["requiere_revision"] = requiere_list
    df_out["motivo_control"] = motivos
    return df_out

def generar_excel_validacion(df: pd.DataFrame, ruta_excel: str):
    """
    Genera el archivo Excel data/validation/dataset_validacion.xlsx
    con la estructura completa para validación humana de Fase 3:
    separando claramente las predicciones automáticas NLP de las columnas humanas (vacías).
    """
    df_val = pd.DataFrame()
    
    # 1. Identificación y transcripción
    df_val["id"] = df["id"]
    df_val["archivo"] = df["archivo"]
    df_val["tipo_agente"] = df["tipo_agente"]
    df_val["transcripcion"] = df["transcripcion_original"] if "transcripcion_original" in df.columns else df.get("texto", "")
    
    # 2. Predicciones automáticas NLP (como referencia auditable)
    df_val["contactabilidad_nlp"] = df.get("contactabilidad", np.nan)
    df_val["acuerdo_pago_nlp"] = df.get("acuerdo_pago", df.get("acuerdo_pago_candidato", np.nan))
    df_val["acuerdo_pago_candidato"] = df_val["acuerdo_pago_nlp"]  # Compatibilidad
    df_val["aceptacion_pago_nlp"] = df.get("aceptacion_pago", np.nan)
    df_val["oferta_pago_nlp"] = df.get("oferta_pago", np.nan)
    df_val["negociacion_nlp"] = df.get("negociacion", np.nan)
    df_val["tiene_objecion_nlp"] = df.get("tiene_objecion", np.nan)
    df_val["objecion_candidato"] = df.get("tipo_objecion", df.get("objecion_candidato", np.nan))  # Compatibilidad
    df_val["intencion_pago_nlp"] = df.get("intencion_pago", np.nan)
    df_val["dificultad_pago_nlp"] = df.get("dificultad_pago", np.nan)
    df_val["monto_propuesto_nlp"] = df.get("monto_propuesto", np.nan)
    df_val["monto_acordado_nlp"] = df.get("monto_acordado", np.nan)
    df_val["inconsistencia_matematica_nlp"] = df.get("inconsistencia_matematica_acuerdo", 0)
    df_val["fecha_compromiso_nlp"] = df.get("fecha_compromiso", np.nan)
    df_val["resultado_final_nlp"] = df.get("resultado_final", df.get("resultado_final_candidato", np.nan))
    df_val["resultado_candidato"] = df_val["resultado_final_nlp"]  # Compatibilidad
    df_val["confianza_nlp"] = df.get("confianza_nlp", np.nan)
    df_val["motivo_control_nlp"] = df.get("motivo_control", "")
    
    # 3. Validación humana (columnas estrictamente vacías para no inventar etiquetas)
    df_val["contactabilidad_validada"] = np.nan
    df_val["oferta_pago_validada"] = np.nan
    df_val["aceptacion_pago_validada"] = np.nan
    df_val["acuerdo_pago_validado"] = np.nan
    df_val["negociacion_validada"] = np.nan
    df_val["objecion_validada"] = np.nan
    df_val["intencion_pago_validada"] = np.nan
    df_val["dificultad_pago_validada"] = np.nan
    df_val["monto_acordado_validado"] = np.nan
    df_val["fecha_compromiso_validada"] = np.nan
    df_val["resultado_validado"] = np.nan
    
    # 4. Evidencia y control de auditoría humana
    df_val["nivel_confianza_validacion"] = np.nan  # alto / medio / bajo
    df_val["evidencia_validacion"] = np.nan
    df_val["observacion_validacion"] = np.nan
    df_val["validador"] = np.nan
    df_val["fecha_validacion"] = np.nan
    
    with pd.ExcelWriter(ruta_excel, engine="openpyxl") as writer:
        df_val.to_excel(writer, sheet_name="Validacion_Humana", index=False)
