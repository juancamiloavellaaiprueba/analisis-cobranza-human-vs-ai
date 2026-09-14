# Informe de Auditoría y Refactorización Técnica
**Proyecto:** NLP Análisis de Cobranza Bancaria (Prueba Técnica Creceré AI)  
**Fecha:** 2026-09-13  
**Objetivo:** Eliminar código redundante y delegar cálculos genéricos a librerías estándar maduras (`scipy`, `pandas`, `numpy`), preservando intactas las reglas de negocio, métricas estadísticas, dataset procesado y validaciones humanas.

---

## 1. Tabla Comparativa Antes / Después

| Función / Módulo | Situación Previa | Acción Tomada | Motivo Técnico | Riesgo Evaluado |
|---|---|---|---|---|
| `src.reporting.prueba_fisher_exacta_2x2` | Implementación combinatoria manual (`math.comb`, suma hipergeométrica) | **Reemplazar por librería** (`scipy.stats.fisher_exact`) | `scipy.stats.fisher_exact` es el estándar maduro de la industria. Resultados numéricos 100% idénticos ($\Delta p < 10^{-16}$). | Bajo / Nulo |
| `src.reporting.prueba_chi_cuadrado_2x2` | Implementación manual con corrección de Yates y cálculo de función de error `math.erf` | **Reemplazar por librería** (`scipy.stats.chi2_contingency`) | `scipy.stats.chi2_contingency(..., correction=True)` reproduce exactamente la prueba de Yates y frecuencias esperadas ($\Delta p < 10^{-16}$). | Bajo / Nulo |
| `src.reporting.prueba_mann_whitney_u` | Implementación propia con ranking manual, corrección de continuidad y correlación biserial $r$ | **Mantener implementación propia** | `scipy.stats.mannwhitneyu` con ajuste de empates modifica el p-valor de `num_propuestas_pago` de $0.0490$ a $0.0225$, alterando los resultados aprobados de la auditoría. Por la directriz explícita del prompt, se preserva la formulación aprobada. | Alto si se modificaba |
| `src.reporting.calcular_comparativa: cum_adj` | Variable auxiliar `cum_adj = 1.0` no utilizada en el cálculo de FDR | **Eliminar** (Código muerto) | Variable muerta remanente de una versión previa del algoritmo Benjamini-Hochberg. | Nulo |
| `src.reporting.calcular_estadisticos_descriptivos` | Envoltura propia sobre métodos vectorizados de pandas (`mean`, `median`, `std`, `quantile`) | **Mantener** | Encapsula el cálculo uniforme de métricas de dispersión, asimetría, IQR y conteo de outliers para reporting tabular. | Bajo |
| `src.reporting.calcular_ic95_diferencia_proporciones` | Fórmula analítica Wald para dos proporciones independientes | **Mantener** | Función atómica requerida para IC en puntos porcentuales; clara, concisa (8 líneas) y sin necesidad de dependencias externas pesadas. | Bajo |
| `src.reporting.cohen_h` | Cálculo trigonométrico de distancia de arcoseno para proporciones | **Mantener** | Tamaño de efecto estándar para proporciones. Directo en 4 líneas con `math.asin`. | Bajo |
| `src.reporting.generar_reporte_ejecutivo_html` | Generador de HTML para reporte ejecutivo bancario (2 páginas) | **Mantener** | Lógica de presentación y diseño aprobada para el negocio. | Nulo |
| `src.reporting.generar_anexo_tecnico_html` | Generador de HTML para anexo metodológico e inferencial | **Mantener** | Lógica de presentación técnica y gobernanza estadística. | Nulo |
| `src.reporting.generar_reporte_html` | Orquestador de generación y sincronización de entregables | **Mantener** | Función de orquestación del pipeline de entrega. | Nulo |
| `src.cleaning.normalizar_texto` | Lógica de normalización NFKD, remoción de diacríticos y limpieza léxica | **Mantener** | Regla de preprocesamiento específica para transcripciones en español de cobranza. | Alto si se altera |
| `src.cleaning.es_texto_vacio` | Detección de cadenas vacías o NaN | **Mantener** | Wrapper semántico testeado unitariamente. | Bajo |
| `src.cleaning.es_texto_muy_corto` | Filtro de longitud mínima de tokens | **Mantener** | Control de calidad técnica de ASR. | Bajo |
| `src.cleaning.es_buzon_voz` | Expresiones regulares de detección de contestadores y buzones | **Mantener** | Lógica de negocio para contactabilidad. | Alto si se altera |
| `src.cleaning.tiene_error_whisper` | Detección de alucinaciones conocidas de Whisper en silencios | **Mantener** | Lógica de calidad de datos específica del modelo ASR. | Alto si se altera |
| `src.cleaning.contar_palabras` | Conteo de tokens sobre texto limpio | **Mantener** | Utilidad atómica. | Bajo |
| `src.cleaning.limpiar_dataset_transcripciones` | Pipeline tabular de limpieza con pandas | **Mantener** | Vectorización estructurada de limpieza. | Medio |
| `src.nlp_rules.limpiar_preguntas_agente` | Filtrado de preguntas inquisitivas del agente | **Mantener deliberadamente** | Regla de negocio crítica para evitar falsos positivos de aceptación/compromiso. | Crítico |
| `src.nlp_rules.analizar_negacion_contextual` | Ventana contextual de 5 tokens y cláusulas adversativas | **Mantener deliberadamente** | Motor NLP central de preservación de polaridad. | Crítico |
| `src.nlp_rules.detectar_compromiso_pago` | Detección de compromiso expresado por el deudor | **Mantener deliberadamente** | Lógica de dominio de cobranza. | Crítico |
| `src.nlp_rules.detectar_aceptacion` | Aceptación inequívoca a propuestas de pago | **Mantener deliberadamente** | Lógica de dominio de cobranza. | Crítico |
| `src.nlp_rules.clasificar_intencion_y_dificultad` | Clasificación de actitud vs dificultad económica | **Mantener deliberadamente** | Lógica de negocio fundamental para señales intermedias. | Crítico |
| `src.nlp_rules.inferir_dinamica_conversacional` | Clasificación integral de resultado final de la llamada | **Mantener deliberadamente** | Lógica de agregación y calidad técnica. | Crítico |
| `src.objection_analysis.limpiar_preguntas_agente` | Filtro de preguntas de indagación de objeciones | **Mantener deliberadamente** | Regla específica para segmentación de objeciones. | Crítico |
| `src.objection_analysis.detectar_objecion` | Taxonomía de objeciones bancarias (económica, desempleo, monto, etc.) | **Mantener deliberadamente** | Regla de negocio de tipificación de motivos de mora. | Crítico |
| `src.objection_analysis.analizar_objeciones` | Extracción de evidencia y respuesta del negociador | **Mantener deliberadamente** | Extractor de variables analíticas. | Crítico |
| `src.payment_extraction.parsear_monto` | Parser numérico y en palabras para Pesos Colombianos (COP) | **Mantener deliberadamente** | Lógica financiera de dominio (manejo de millones, mil, pesos, separadores). | Crítico |
| `src.payment_extraction.extraer_cuotas` | Extractor de números cardinales y valor por cuota | **Mantener deliberadamente** | Regla financiera de cobranza. | Crítico |
| `src.payment_extraction.extraer_descuento` | Detección de porcentajes y descuentos sobre la deuda | **Mantener deliberadamente** | Regla comercial de cobranza. | Crítico |
| `src.payment_extraction.extraer_fecha_compromiso` | Extractor de fechas, días de quincena y plazos vinculantes | **Mantener deliberadamente** | Regla contractual de compromiso de pago. | Crítico |
| `src.payment_extraction.extraer_condiciones_economicas` | Integrador de variables económicas por llamada | **Mantener deliberadamente** | Pipeline de estructuración financiera. | Crítico |
| `src.validation.verificar_consistencia_registro` | Matriz de consistencia lógica cruzada (NLP vs montos vs acuerdos) | **Mantener deliberadamente** | Reglas de auditoría técnica y detección de contradicciones. | Crítico |
| `src.validation.ejecutar_segunda_verificacion` | Auditoría en lote sobre dataset procesado | **Mantener** | Pipeline de QA interno. | Medio |
| `src.validation.generar_excel_validacion` | Exportación a Excel (`openpyxl`) para auditoría humana | **Mantener** | Artefacto auditable de QA secundario. | Bajo |
| Dependencia: `scikit-learn` | Listada en `requirements.txt` pero no importada en ningún script | **Eliminar de requirements.txt** | Reducción de dependencias muertas; el proyecto no realiza modelado ML predictivo. | Nulo |

---

## 2. Resumen de Hallazgos y Decisiones
1. **Librería SciPy incorporada con éxito:** Se reemplazaron las implementaciones artesanales de Fisher y Chi-cuadrado con corrección de Yates por `scipy.stats.fisher_exact` y `scipy.stats.chi2_contingency`, reduciendo código no estándar y aumentando la confiabilidad estadística.
2. **Preservación explícita de Mann-Whitney U:** Se comprobó que `scipy.stats.mannwhitneyu` con corrección de empates genera una desviación relevante en el p-valor de `num_propuestas_pago` ($0.0225$ vs. $0.0490$ aprobado). Siguiendo las instrucciones de control metodológico, se mantuvo la función propia para garantizar consistencia con los resultados auditados.
3. **Limpieza de dependencias:** Se eliminó `scikit-learn` de `requirements.txt` dado que el alcance del proyecto es analítico-descriptivo e inferencial sobre NLP basado en reglas, eliminando peso innecesario en instalaciones limpias.
4. **Validación de regresión:** Los 51 tests automáticos pasaron con 100% de éxito, demostrando cero impacto funcional en los resultados finales.
5. **Conteo unívoco de funciones de dominio mantenidas:** Exactamente 16 definiciones de función (14 de NLP en `nlp_rules.py`, `objection_analysis.py` y `payment_extraction.py`, más 2 de validación lógica de consistencia en `validation.py`). `limpiar_preguntas_agente` cuenta como 2 funciones distintas al existir independientemente en `nlp_rules.py` y `objection_analysis.py`.
