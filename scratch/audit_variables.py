import pandas as pd
import numpy as np


df = pd.read_csv("data/processed/dataset_final.csv")

h = df[df["tipo_agente"] == "humano"]
ia = df[df["tipo_agente"] == "ia"]

out = []
out.append(f"TOTAL ROWS: {len(df)}")
out.append(f"TOTAL COLS: {len(df.columns)}")
out.append(f"DISTRIBUTION tipo_agente:\n{df['tipo_agente'].value_counts().to_string()}\n")

out.append("=== VARIABLES AUDIT ===")

for col in df.columns:
    s = df[col]
    val_cnt = s.notna().sum()
    miss_cnt = s.isna().sum()
    miss_pct = (miss_cnt / len(df)) * 100
    n_uniq = s.nunique(dropna=False)
    
    # Classify type
    v_type = "otro"
    if col in ["id"]:
        v_type = "identificador"
    elif col in ["archivo", "transcripcion_original", "transcripcion_limpia", "motivo_control", "evidencia_contactabilidad", "evidencia_oferta", "evidencia_aceptacion", "evidencia_acuerdo", "evidencia_objecion", "evidencia_negociacion"]:
        v_type = "texto"
    elif col in ["fecha_compromiso"]:
        v_type = "fecha / expresion temporal"
    elif col in ["monto_deuda", "monto_propuesto", "monto_acordado", "monto_cuota", "monto_descuento"]:
        v_type = "monto (continuo)"
    elif col in ["duracion_segundos"]:
        v_type = "duracion (continuo)"
    elif col in ["num_palabras", "num_propuestas_pago", "num_objeciones", "numero_cuotas", "num_preguntas_agente"]:
        v_type = "conteo discreto"
    elif col in ["contactabilidad", "oferta_pago", "aceptacion_pago", "acuerdo_pago", "negociacion", "tiene_objecion", "manejo_objecion", "objecion_resuelta", "inconsistencia_matematica_acuerdo", "tiene_descuento", "intencion_pago", "dificultad_pago", "requiere_revision", "acuerdo_pago_candidato"]:
        v_type = "binaria (0/1)"
    elif col in ["tipo_agente", "resultado_final", "tipo_objecion", "tipo_respuesta_cliente", "control_calidad", "objecion_candidato", "resultado_final_candidato"]:
        v_type = "categorica"
    elif col in ["confianza_nlp"]:
        v_type = "score continuo (0-1)"
    elif col in ["acuerdo_pago_validado", "objecion_validada", "resultado_final_validado"]:
        v_type = "columna de validacion humana (en dataset_final vacia)"
        
    # Group stats
    h_s = h[col]
    ia_s = ia[col]
    
    stat_str = ""
    if v_type in ["binaria (0/1)"]:
        h_pos = (h_s == 1).sum() if h_s.dtype != bool else h_s.sum()
        ia_pos = (ia_s == 1).sum() if ia_s.dtype != bool else ia_s.sum()
        h_pct = (h_pos / len(h)) * 100
        ia_pct = (ia_pos / len(ia)) * 100
        stat_str = f"H: {h_pos}/50 ({h_pct:.1f}%) | IA: {ia_pos}/50 ({ia_pct:.1f}%) | Dif: {h_pct - ia_pct:+.1f} pp"
    elif v_type in ["monto (continuo)", "duracion (continuo)", "conteo discreto", "score continuo (0-1)"]:
        h_valid = h_s.dropna()
        ia_valid = ia_s.dropna()
        stat_str = f"H (n={len(h_valid)}): med={h_valid.mean():.2f}, mdn={h_valid.median():.2f}, std={h_valid.std():.2f} | IA (n={len(ia_valid)}): med={ia_valid.mean():.2f}, mdn={ia_valid.median():.2f}, std={ia_valid.std():.2f}"
    elif v_type in ["categorica"]:
        stat_str = f"H: {dict(h_s.value_counts())} | IA: {dict(ia_s.value_counts())}"
    else:
        stat_str = f"Validos: {val_cnt}, Missing: {miss_cnt} ({miss_pct:.1f}%)"
        
    out.append(f"\n--- {col} ---")
    out.append(f"Tipo: {v_type} | Validos: {val_cnt}/100 | Missing: {miss_cnt} ({miss_pct:.1f}%) | Unicos: {n_uniq}")
    out.append(f"Detalle: {stat_str}")

with open("scratch/audit_variables_detalle.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("Saved detailed audit to scratch/audit_variables_detalle.txt")
