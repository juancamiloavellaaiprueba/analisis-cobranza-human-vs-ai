# Registro de Discrepancias: Predicción NLP vs Validación Humana

Este documento registra de forma auditable las discrepancias identificadas entre las predicciones algorítmicas del pipeline de NLP y las etiquetas asignadas por revisores humanos en [`data/validation/dataset_validacion.xlsx`](file:///d:/Prueba_Juan_Camilo_Avella/proyecto_cobranza_nlp/data/validation/dataset_validacion.xlsx).

---

## 1. Categorías Estandarizadas de Causa Raíz
1. `atribución de hablante`: El modelo no distinguió si el emisor era el asesor o el cliente.
2. `negación`: Omisión o interpretación errónea de una cláusula negativa o adversativa.
3. `"de acuerdo" contextual`: El término se empleó para aceptar una llamada o trámite distinto al pago.
4. `pregunta del asesor`: Pregunta inquisitiva del asesor clasificada erróneamente como compromiso del cliente.
5. `fecha histórica`: Extracción de fechas pasadas de origen o castigo de la deuda.
6. `monto ambiguo`: Confusión en cifras expresadas verbalmente.
7. `falta de cierre`: Conversación inconclusa o llamada cortada clasificada como acuerdo.
8. `objeción`: Duda clasificada como objeción formal o viceversa.
9. `transcripción Whisper`: Alucinación, palabra ininteligible o truncamiento del audio.
10. `otra`: Casos atípicos no clasificados en las anteriores.

---

## 2. Matriz de Discrepancias Identificadas en Auditoría de Transcripciones

| ID | Variable | NLP Fase 3 | NLP Fase 3.5 | Tipo de Error | Evidencia Conversacional | Resolución en Fase 3.5 |
| :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| **37** | `aceptacion_pago` | 1 | **0** | Falso positivo semántico | Asesor: *"el día de mañana a las cuatro de la tarde me indica"* -> Cliente: *"Sí, de acuerdo"*. Acepta llamada de seguimiento, no un pago. | Resuelto: Filtro de acuerdos administrativos de contacto en `detectar_aceptacion()`. |
| **55** | `monto_propuesto` / `monto_acordado` | 2000.0 | **Prop: 2.110.000 / Acord: NaN** | Error de extracción léxica y alternancia regex | Cliente: *"porque a dos y eso me tiene como preocupado..."*. Alternancia `(?:mil\|millones?)` truncaba *"2 millones 110 mil"*. | Resuelto: Regex corregido, montos compuestos soportados y exigencia de evidencia monetaria en `parsear_monto()`. |
| **85** | `monto_acordado` / cuotas | 830000.0 / cuota 30k | **830000.0 / cuota 60k (inc=1)** | Inconsistencia matemática del agente IA | La IA ofrece descuento a $830.000 pero propone *"15 cuotas mensuales de 60 mil pesos cada una"* (15 × $60.000 = $900.000). | Resuelto: Se extraen valores literales fieles y se levanta `inconsistencia_matematica_acuerdo = 1`. |
| **22** | `aceptacion_pago` | 0 | **0** | Corrección validada | Asesor usa muletilla *"de acuerdo señor"*. Cliente solo dice que irá la próxima semana. | Preservado: Exclusión de muletillas del asesor. |
| **74** | `acuerdo_pago` | 0 | **0** | Corrección validada | La IA insiste y el cliente rechaza explícitamente: *"No, ya lo sé. No puedo pagar"*. | Preservado: Regla de rechazo activo. |
| **89** | `acuerdo_pago` | 0 | **0** | Corrección validada | Cliente indica *"no puedo pagar esa suma"*. La IA reproduce script de despedida. | Preservado: Filtrado de cierres automáticos con rechazo previo. |

> **Nota metodológica:** Las filas anteriores registran los hallazgos de la auditoría técnica de código y texto. El registro definitivo de 100 llamadas se completará a medida que los validadores humanos consignen sus decisiones en [`data/validation/dataset_validacion.xlsx`](file:///d:/Prueba_Juan_Camilo_Avella/proyecto_cobranza_nlp/data/validation/dataset_validacion.xlsx).
