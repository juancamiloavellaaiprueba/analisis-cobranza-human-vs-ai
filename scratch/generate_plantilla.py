import pandas as pd
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
df = pd.read_csv(ROOT_DIR / "data" / "processed" / "dataset_final.csv")

lines = [
    "# Plantilla y Protocolo de Revisión Humana de las 100 Llamadas\n",
    "**Archivo de trabajo:** [`data/validation/dataset_validacion.xlsx`](file:///d:/Prueba_Juan_Camilo_Avella/proyecto_cobranza_nlp/data/validation/dataset_validacion.xlsx)  ",
    "**Total de registros a auditar:** 100 (50 Agentes Humanos, 50 Agentes IA)  ",
    "**Estado actual:** PENDIENTE DE VALIDACIÓN HUMANA (Columnas humanas 100% vacías)  \n",
    "---\n",
    "## 1. Instrucciones Paso a Paso para la Validación Manual\n",
    "1. Abra el archivo Excel [`data/validation/dataset_validacion.xlsx`](file:///d:/Prueba_Juan_Camilo_Avella/proyecto_cobranza_nlp/data/validation/dataset_validacion.xlsx) en su editor de hojas de cálculo.",
    "2. La hoja contiene dos bloques claramente separados:",
    "   - **Columnas NLP (referencia auditable):** `contactabilidad_nlp`, `acuerdo_pago_nlp`, `aceptacion_pago_nlp`, `oferta_pago_nlp`, `negociacion_nlp`, `tiene_objecion_nlp`, `intencion_pago_nlp`, `dificultad_pago_nlp`, `monto_propuesto_nlp`, `monto_acordado_nlp`, `fecha_compromiso_nlp`, `resultado_final_nlp`, etc.",
    "   - **Columnas Humanas (a diligenciar por el validador):** `contactabilidad_validada`, `oferta_pago_validada`, `aceptacion_pago_validada`, `acuerdo_pago_validado`, `negociacion_validada`, `objecion_validada`, `intencion_pago_validada`, `dificultad_pago_validada`, `monto_acordado_validado`, `fecha_compromiso_validada`, `resultado_validado`, `nivel_confianza_validacion`, `evidencia_validacion`, `observacion_validacion`, `validador`, `fecha_validacion`.",
    "3. **Secuencia de revisión recomendada:**",
    "   - **Fase A (Eje del compromiso):** Leer la columna `transcripcion` y evaluar primero: `contactabilidad_validada`, `oferta_pago_validada`, `aceptacion_pago_validada`, `acuerdo_pago_validado` y `resultado_validado`.",
    "   - **Fase B (Dinámica y condiciones):** Evaluar `negociacion_validada`, `objecion_validada`, `intencion_pago_validada`, `dificultad_pago_validada`, `monto_acordado_validado` y `fecha_compromiso_validada`.",
    "   - **Fase C (Auditoría y trazabilidad):** Completar `nivel_confianza_validacion` (`alto`, `medio`, `bajo`), citar la frase clave en `evidencia_validacion`, indicar notas en `observacion_validacion` (ej. si detecta inconsistencia matemática), y registrar `validador` y `fecha_validacion`.\n",
    "---\n",
    "## 2. Niveles de Prioridad de Revisión\n",
    "- **ALTA:** Registros críticos que incluyen:",
    "  - Casos auditados especiales: ID 37, 55, 85, 99.",
    "  - Acuerdos detectados por el NLP: ID 1, 2, 5, 7, 8, 29, 47, 85, 99.",
    "  - Inconsistencias matemáticas en diálogo (cuotas vs saldo total).",
    "- **MEDIA:** Registros con contacto efectivo donde se presentaron propuestas o dificultades financieras sin acuerdo formal.",
    "- **BAJA:** Registros sin contacto efectivo (buzones de voz o audios vacíos) de verificación rápida.\n",
    "---\n",
    "## 3. Matriz Completa de los 100 Registros para Validación\n",
    "| ID | Agente | Cont. | Oferta | Acep. | Acuerdo | Monto Acordado | Fecha Comp. | Resultado NLP | Prioridad | Motivo de Prioridad |",
    "| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :---: | :--- |"
]

for _, r in df.iterrows():
    cid = int(r["id"])
    tagente = str(r["tipo_agente"]).capitalize()
    acuerdo = int(r.get("acuerdo_pago", 0))
    acep = int(r.get("aceptacion_pago", 0))
    oferta = int(r.get("oferta_pago", 0))
    cont = int(r.get("contactabilidad", 0))
    ctrl = str(r.get("control_calidad", "ok"))
    inc = int(r.get("inconsistencia_matematica_acuerdo", 0))
    res = str(r.get("resultado_final", ""))
    monto_ac = r.get("monto_acordado")
    monto_str = f"${monto_ac:,.0f}" if pd.notna(monto_ac) else "-"
    fecha = str(r.get("fecha_compromiso", "")) if pd.notna(r.get("fecha_compromiso")) else "-"

    if cid in [37, 55, 85, 99]:
        prio = "ALTA"
        motivo = "Caso critico auditado (atencion especial)"
    elif acuerdo == 1:
        prio = "ALTA"
        motivo = "Acuerdo clasificado por NLP (auditoria prioritaria)"
    elif inc == 1:
        prio = "ALTA"
        motivo = "Inconsistencia matematica cuotas vs total"
    elif ctrl == "revisar":
        prio = "MEDIA"
        motivo = str(r.get("motivo_control", "Alerta de control de calidad")).replace(";", ",")
    elif cont == 0:
        prio = "BAJA"
        motivo = "Sin contacto efectivo (buzon o audio vacio)"
    else:
        prio = "MEDIA"
        motivo = f"Contacto efectivo: {res}"

    lines.append(f"| {cid} | {tagente} | {cont} | {oferta} | {acep} | {acuerdo} | {monto_str} | {fecha} | {res} | {prio} | {motivo} |")

out_file = ROOT_DIR / "docs" / "plantilla_revision_humana.md"
with open(out_file, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print(f"plantilla_revision_humana.md generado exitosamente en {out_file}.")
