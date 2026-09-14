# Informe Metodológico Fase 3: Validación Humana Completa de los 100 Registros y Preparación Rigurosa de Fase 3.5

**Proyecto:** Análisis Comparativo de Gestión de Cobranza (Agentes Humanos vs Agentes IA)  
**Fase:** 3 — Validación Humana y Auditoría de Variables NLP  
**Fecha:** 2026-09-12  
**Estado:** FASE 3 — INFRAESTRUCTURA COMPLETA, VALIDACIÓN HUMANA PENDIENTE.  

---

## 1. Estado de la Validación Humana

La infraestructura de validación para los 100 registros ha sido consolidada en [`data/validation/dataset_validacion.xlsx`](file:///d:/Prueba_Juan_Camilo_Avella/proyecto_cobranza_nlp/data/validation/dataset_validacion.xlsx). 

> **Aclaración Metodológica Central:**  
> A la fecha de este informe, las columnas de validación humana se encuentran **100% vacías** (`NaN`). Ninguna etiqueta ha sido simulada, extrapolada ni copiada de las predicciones del NLP. Por tanto, la validación humana real está **PENDIENTE** de realización manual por parte del revisor humano. No se calculan métricas oficiales de rendimiento del modelo (Precision, Recall, F1, Accuracy) ni matrices de confusión definitivas, pues no existe aún un Gold Standard humano completado.

---

## 2. Registros Totales y Distribución

- **Total de llamadas en el dataset:** 100
- **IDs únicos:** 100 (rango consecutivo 1 a 100, sin duplicados ni faltantes).
- **Distribución por tipo de agente:**
  - **Agentes Humanos:** 50 llamadas (IDs 1 al 50)
  - **Agentes de Inteligencia Artificial (IA):** 50 llamadas (IDs 51 al 100)
- **Consistencia de fuentes:** 100% de alineación entre [`data/processed/dataset_final.csv`](file:///d:/Prueba_Juan_Camilo_Avella/proyecto_cobranza_nlp/data/processed/dataset_final.csv) y [`data/validation/dataset_validacion.xlsx`](file:///d:/Prueba_Juan_Camilo_Avella/proyecto_cobranza_nlp/data/validation/dataset_validacion.xlsx).

---

## 3. Número de Etiquetas Humanas Reales

- **Etiquetas humanas diligenciadas:** 0 / 100 (0%).
- **Etiquetas humanas pendientes:** 100 / 100 (100%).
- **Estado de columnas:** Las 11 columnas `_validada` / `_validado` y las columnas de control (`nivel_confianza_validacion`, `evidencia_validacion`, `observacion_validacion`, `validador`, `fecha_validacion`) se mantienen rigurosamente en blanco.

---

## 4. Variables Preparadas para Validación Humana

En el archivo Excel se han dispuesto las 11 variables requeridas, separando en bloques auditables las predicciones automáticas del NLP de las casillas destinadas al juicio humano:

| # | Variable Humana (`_validada`) | Variable NLP de Referencia (`_nlp`) | Tipo de Dato | Definición Operativa |
| :-: | :--- | :--- | :-: | :--- |
| 1 | `contactabilidad_validada` | `contactabilidad_nlp` | Binaria (0/1) | 1 = Diálogo efectivo con una persona; 0 = Buzón o audio vacío. |
| 2 | `oferta_pago_validada` | `oferta_pago_nlp` | Binaria (0/1) | 1 = Asesor presenta alternativa concreta de pago o descuento. |
| 3 | `aceptacion_pago_validada` | `aceptacion_pago_nlp` | Binaria (0/1) | 1 = Cliente aprueba explícitamente pagar una propuesta económica. |
| 4 | `acuerdo_pago_validado` | `acuerdo_pago_nlp` | Binaria (0/1) | 1 = Compromiso formal del cliente + al menos una condición vinculante. |
| 5 | `negociacion_validada` | `negociacion_nlp` | Binaria (0/1) | 1 = Intercambio y exploración de contrapropuestas o plazos. |
| 6 | `objecion_validada` | `tiene_objecion_nlp` | Binaria / Categórica | 1 = Cliente reporta impedimento (dinero, fecha, desempleo, saldo). |
| 7 | `intencion_pago_validada` | `intencion_pago_nlp` | Binaria (0/1) | 1 = Voluntad futura manifiesta de pagar, aun sin acuerdo formal. |
| 8 | `dificultad_pago_validada` | `dificultad_pago_nlp` | Binaria (0/1) | 1 = Manifestación expresa de iliquidez o insolvencia económica. |
| 9 | `monto_acordado_validado` | `monto_acordado_nlp` | Numérico (COP) | Monto exacto pactado al cierre. Vacío si no hubo acuerdo. |
| 10 | `fecha_compromiso_validada` | `fecha_compromiso_nlp` | Texto de fecha | Fecha límite o plazo futuro acordado para el pago. |
| 11 | `resultado_validado` | `resultado_final_nlp` | Categórica | `acuerdo_pago`, `propuesta_rechazada`, `dificultad_sin_acuerdo`, etc. |

---

## 5. Discrepancias Identificadas en Auditoría Técnica

A partir de la inspección técnica de las transcripciones y del código NLP, se detectaron discrepancias conceptuales que justificaron las correcciones quirúrgicas de la Fase 3.5, pendientes de homologación humana formal:

1. **ID 37 (Aceptación de llamada vs pago):** El cliente respondió *"Sí, de acuerdo"* a la propuesta del asesor de llamarlo al día siguiente a las 4:00 pm. El NLP original clasificaba esto como aceptación de pago.
2. **ID 55 (Truncamiento léxico de montos):** Expresión coloquial *"a dos"* y alternancia en regex `(?:mil|millones?)` truncaban *"2 millones 110 mil"* a `$2.000 COP`.
3. **ID 85 (Aritmética generativa del agente IA):** El agente virtual ofreció saldar en `$830.000` pero formuló *"15 pagos mensuales de 60 mil pesos cada uno"* ($15 \times 60.000 = \$900.000$). Hay una discrepancia interna de `$70.000`.

---

## 6. Casos de Atención Especial para el Revisor Humano

El validador humano debe prestar atención prioritaria a:
- **ID 37:** Verificar que *"sí, de acuerdo"* es una respuesta a la llamada de seguimiento a las 4 pm y no un compromiso de pago.
- **ID 55:** Determinar humanamente el monto propuesto real y confirmar que el cliente no aceptó la propuesta.
- **ID 85:** Registrar la inconsistencia matemática en observaciones sin modificar los valores literales expresados.
- **ID 99:** Revisar el compromiso final y la fecha límite ante la presencia de expresiones temporales escalonadas.
- **Auditoría de los 9 Acuerdos NLP:** Revisar obligatoriamente las 9 llamadas clasificadas con `acuerdo_pago = 1` (**IDs 1, 2, 5, 7, 8, 29, 47, 85 y 99**).

---

## 7. Problemas de Extracción Detectados
- **Fechas Relativas:** Expresiones como *"mañana"*, *"el viernes"* o *"quincena"* son extraídas literalmente. El validador humano debe estandarizar cómo interpretar estas fechas relativas.
- **Fechas Históricas:** Se logró blindar el extractor para evitar fechas pasadas de origen de la deuda (ej. 2017, 2021), pero el validador debe vigilar que ninguna fecha de corte bancario se catalogue erróneamente como promesa de pago.

---

## 8. Inconsistencias Lógicas y Aritméticas
- Se incorporó la bandera `inconsistencia_matematica_acuerdo` en el pipeline.
- En total, 7 llamadas en el dataset presentan diferencias entre el monto total mencionado y la multiplicación de cuotas por valor de cuota (ej. ID 85, ID 99). Estas llamadas están señaladas con prioridad ALTA en [`docs/plantilla_revision_humana.md`](file:///d:/Prueba_Juan_Camilo_Avella/proyecto_cobranza_nlp/docs/plantilla_revision_humana.md).

---

## 9. Política de Privacidad y Estado de PII
- **Diagnóstico:** Las transcripciones contienen nombres de clientes, asesores, números telefónicos de contacto, correos electrónicos y direcciones físicas reales.
- **Control:** Las transcripciones en crudo y el Excel con datos personales se mantienen **estrictamente locales**. No se deben publicar en repositorios abiertos de GitHub hasta que se ejecute la fase de anonimización y enmascaramiento.

---

## 10. Estado del Repositorio y Git
- Los archivos de trabajo residen en el entorno local del proyecto.
- Se mantiene sincronización entre la ruta de trabajo y el directorio espejo.
- No se han subido datos sensibles a entornos remotos.

---

## 11. Pruebas Automatizadas Ejecutadas
- Se ejecutó la suite completa de pruebas:
  ```bash
  python -m pytest -q
  ```
- **Resultado:** 48 tests pasados en 1.10s (0 fallos, 0 errores, 0 regresiones).

---

## 12. Pendientes de la Fase
1. Realización de la revisión manual por parte del validador humano en [`data/validation/dataset_validacion.xlsx`](file:///d:/Prueba_Juan_Camilo_Avella/proyecto_cobranza_nlp/data/validation/dataset_validacion.xlsx).
2. Cálculo de métricas formales de validación (Precision, Recall, F1, Accuracy, matrices de confusión) una vez existan etiquetas humanas completas.
3. Anonimización de transcripciones previa a publicación en GitHub.

---

## 13. Recomendaciones Concretas para Fase 3.5

Las recomendaciones se dividen rigurosamente entre lo confirmado y lo técnico preliminar:

### A. Problemas Confirmados Mediante Validación Humana:
* **0 problemas confirmados:** Dado que ningún revisor humano ha diligenciado aún el dataset de validación, **no se pueden declarar errores humanos definitivos** ni matrices de confusión oficiales.

### B. Candidatos a Problema Detectados Técnicamente (Pendientes de Confirmación Humana):
1. **ID 37 (Candidato a Falso Positivo de Aceptación):** El filtro contextual de llamadas administrativas resolvió la distorsión algorítmica; el validador humano debe ratificar si `aceptacion_pago_validada = 0`.
2. **ID 55 (Candidato a Extracción Monetaria Defectuosa):** Se corrigió la alternancia regex y la exigencia de evidencia monetaria; el validador humano debe ratificar que `monto_acordado_validado = NaN`.
3. **ID 85 (Inconsistencia Matemática en Diálogo IA):** La bandera algorítmica `inconsistencia_matematica_acuerdo = 1` está activa; el validador humano debe consignar en observaciones la discrepancia entre $830.000 y 15 × $60.000 = $900.000.
4. **Fechas Relativas:** Estandarizar si términos como *"mañana"* se validan como fecha válida o si se exige fecha calendario.

---

## 14. Resultado Final y Criterio de Salida

**FASE 3 — INFRAESTRUCTURA COMPLETA, VALIDACIÓN HUMANA PENDIENTE.**
