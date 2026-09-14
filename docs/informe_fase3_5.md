# Informe Técnico Fase 3.5: Correcciones Quirúrgicas del NLP Basadas en Auditoría

**Proyecto:** Análisis Comparativo de Gestión de Cobranza (Humanos vs IA)  
**Fase:** 3.5 — Correcciones Quirúrgicas del NLP  
**Fecha:** 2026-09-12  
**Estado:** APROBADO — Listo para Validación Humana  

---

## 1. Contexto y Alcance Metodológico

En la Fase 3 se consolidó la infraestructura de validación humana con 100 llamadas (50 Humanas y 50 IA), separando estrictamente las predicciones algorítmicas de las columnas de validación humana en [`data/validation/dataset_validacion.xlsx`](file:///d:/Prueba_Juan_Camilo_Avella/proyecto_cobranza_nlp/data/validation/dataset_validacion.xlsx). 

> **Aclaración Metodológica Crítica:**  
> A la fecha no existe un Gold Standard humano completado. Por ende, este informe **NO** calcula Precision, Recall, F1 ni matrices de confusión oficiales, ni asume que las correcciones técnicas equivalen a validación humana. Esta fase se limitó a ejecutar intervenciones **quirúrgicas y generalizables** sobre defectos del procesamiento de lenguaje natural identificados en la auditoría técnica.

---

## 2. Detalle de Correcciones Quirúrgicas Realizadas

### Corrección 1: ID 37 — Falso Positivo de Aceptación Contextual vs Administrativa
- **Variable afectada:** `aceptacion_pago`.
- **Comportamiento anterior:** `aceptacion_pago = 1` (debido a la frase *"sí, de acuerdo"* emitida por el deudor en respuesta a una llamada de seguimiento administrativo: *"entonces yo el día de mañana a las cuatro de la tarde me indica... Sí, de acuerdo"*).
- **Comportamiento nuevo:** `aceptacion_pago = 0`.
- **Causa raíz:** `detectar_aceptacion()` capturaba cualquier *"sí, de acuerdo"* sin verificar si el contexto inmediato correspondía a trámites administrativos (agendamiento de callback, confirmación de datos, envíos informativos).
- **Intervención técnica general:** Se incorporó un filtro contextual en [`src/nlp_rules.py`](file:///d:/Prueba_Juan_Camilo_Avella/proyecto_cobranza_nlp/src/nlp_rules.py) que identifica marcadores de agendamiento/contacto (`llámeme mañana`, `yo me comunico mañana`, `mañana a las cuatro`, `contactar`, `marcar`, `por correo`, etc.) y exige vínculo semántico con condiciones económicas (`pagar`, `cuota`, `plan`, `monto`, `valor`, `$`, `pesos`) para que una aceptación genérica sea clasificada como compromiso de pago.

### Corrección 2: ID 55 — Falso Positivo Monetario y Truncamiento Léxico
- **Variables afectadas:** `monto_propuesto`, `monto_acordado`, `monto_cuota`.
- **Comportamiento anterior:** `monto_propuesto = 2000.0`, `monto_acordado = 2000.0`, `monto_cuota = 2021.0`.
- **Comportamiento nuevo:** `monto_propuesto = 2110000.0`, `monto_acordado = NaN`, `monto_cuota = 2110000.0`.
- **Causa raíz:** 
  1. En expresiones regulares, la alternancia `(?:mil|millones?)` evaluaba `mil` antes de `millones`, haciendo que *"acuerdo por 2 millones 110 mil"* se truncara en *"acuerdo por 2 mil"*, evaluándose como `$2.000 COP`.
  2. `parsear_monto()` no exigía evidencia monetaria suficiente, lo que permitía que números cardinales o palabras aisladas se convirtieran en montos.
  3. `extraer_condiciones_economicas()` capturaba la pregunta inquisitiva del agente (*"¿me confirma si acepta el acuerdo por...?"*) como si fuese un acuerdo pactado, a pesar de que el cliente rechazó la propuesta.
  4. El año histórico `2021` se extraía erróneamente como cuota.
- **Intervención técnica general:**
  - En [`src/payment_extraction.py`](file:///d:/Prueba_Juan_Camilo_Avella/proyecto_cobranza_nlp/src/payment_extraction.py), se corrigieron las alternancias a `(?:\bmillones?\b(?:\s+[\d\.,\s]+\s*\bmil\b)?|\bmil\b)`.
  - Se agregó soporte nativo para montos compuestos (*"2 millones 110 mil"* -> `2110000.0`).
  - Se exigió evidencia monetaria explícita (`$`, `mil`, `millon`, `pesos`, `cop`, separador de miles `>= 1000`).
  - Se blindó `extraer_cuotas()` para no capturar fechas históricas ni montos de descuento como cuotas.

### Corrección 3: ID 85 — Inconsistencia Matemática del Diálogo Original
- **Variables afectadas:** `monto_acordado`, `numero_cuotas`, `monto_cuota`, `inconsistencia_matematica_acuerdo`.
- **Comportamiento anterior:** `monto_acordado = 830000.0`, `numero_cuotas = 15.0`, `monto_cuota = 30000.0` (capturado de la mención del descuento de 30 mil).
- **Comportamiento nuevo:** `monto_acordado = 830000.0`, `numero_cuotas = 15.0`, `monto_cuota = 60000.0`, `inconsistencia_matematica_acuerdo = 1`.
- **Causa raíz:** En el audio original, el agente IA incurre en un error aritmético al formular: saldo de `$830.000` diferido en *"15 pagos mensuales de 60 mil pesos cada uno"* ($15 \times 60.000 = \$900.000$). Existe una brecha de `$70.000`.
- **Intervención técnica general:**
  - **No alteración de datos:** Se preservaron intactos los valores literales del diálogo ($830.000 acordado, 15 cuotas, $60.000 por cuota) sin forzar ajustes artificiales.
  - **Bandera auditable:** Se creó la variable `inconsistencia_matematica_acuerdo` (1 si `monto_total != monto_cuota * numero_cuotas` con cuotas > 1 y tolerancia > $100 COP; 0 si es consistente o no verificable).
  - La llamada ID 85 queda correctamente identificada con `inconsistencia_matematica_acuerdo = 1` y remitida a revisión en `control_calidad = 'revisar'`.

---

## 3. Tabla Obligatoria Antes / Después (Auditoría Técnica)

| Caso (ID) | Variable | Valor Antes | Valor Después | Motivo Técnico de la Corrección |
| :---: | :--- | :---: | :---: | :--- |
| **37** | `aceptacion_pago` | 1 | **0** | *"Sí, de acuerdo"* aceptaba agendamiento de llamada administrativa a las 4 pm, no un pago. |
| **37** | `control_calidad` | revisar | **ok** | Ya no genera alerta de discrepancia al tener `aceptacion_pago = 0` y `acuerdo_pago = 0`. |
| **55** | `monto_propuesto` | 2000.0 | **2110000.0** | Corrección de truncamiento de regex en *"2 millones 110 mil"*; refleja la propuesta real. |
| **55** | `monto_acordado` | 2000.0 | **NaN** | El cliente rechazó la propuesta; la pregunta del asesor ya no se registra como acuerdo. |
| **55** | `monto_cuota` | 2021.0 | **2110000.0** | Se eliminó la captura del año histórico 2021 como valor de cuota. |
| **85** | `monto_cuota` | 30000.0 | **60000.0** | Se corrigió la asociación léxica: 30 mil era el descuento, 60 mil era la cuota mensual. |
| **85** | `inconsistencia_matematica_acuerdo` | *(No existía)* | **1** | Se detecta brecha aritmética del bot IA ($830.000 vs 15 × $60.000 = $900.000) sin alterar montos. |

---

## 4. Control de Regresión y Pruebas Unitarias

Se ejecutó la suite completa de pruebas mediante `pytest`:
- **Tests previos Fase 3:** 34 pasados.
- **Nuevos tests Fase 3.5 ([`tests/test_fase3_5_correcciones.py`](file:///d:/Prueba_Juan_Camilo_Avella/proyecto_cobranza_nlp/tests/test_fase3_5_correcciones.py)):** 14 pasados.
- **Total ejecutado:** **48 tests pasados, 0 fallos, 0 regresiones.**

### Detalle de Nuevas Pruebas Agregadas:
1. `test_aceptacion_administrativa`: Valida que llamadas de seguimiento, envíos al correo y *"llámeme mañana"* retornen `False`.
2. `test_aceptacion_de_pago`: Valida que acuerdos con cuotas, montos explícitos o planes retornen `True`.
3. `test_de_acuerdo_aislado_sin_contexto`: Valida que `"de acuerdo"` aislado o muletillas de cortesía retornen `False`.
4. `test_numero_cardinal_aislado_sin_dinero`: Valida que cardinales aislados (`dos`, `tres`, `uno`, `a dos`, `por dos`, `tengo dos problemas`) retornen `np.nan`.
5. `test_dos_mil_pesos`: Valida que `"dos mil pesos"` y `"2.000 pesos"` retornen `2000.0`.
6. `test_signo_pesos_dos_mil`: Valida que `"$2.000"` y `"$ 2000"` retornen `2000.0`.
7. `test_cuotas_sin_monto`: Valida que `"15 cuotas"` retorne cuotas=15 y monto=`np.nan` (no $15.000).
8. `test_dos_cuotas_de_trescientos_mil`: Valida que `"dos cuotas de 300 mil"` retorne cuotas=2 y monto=300000.0.
9. `test_inconsistencia_matematica_acuerdo`: Valida que el escenario de 15 cuotas de 60 mil con total de 830 mil levante `inconsistencia_matematica_acuerdo = 1`.
10. `test_consistencia_matematica_acuerdo`: Valida que acuerdos consistentes (ej. 2 cuotas de 400 mil para total 800 mil) mantengan bandera = 0.
11. `test_preservacion_negaciones`: Valida que expresiones negativas (`no puedo pagar`, `no tengo dinero`, `no acepto`, `no puedo comprometerme`) no activen compromiso ni intención positiva.

---

## 5. Revisión de Distribuciones (Humanos vs IA)

Distribución en el dataset regenerado ([`data/processed/dataset_final.csv`](file:///d:/Prueba_Juan_Camilo_Avella/proyecto_cobranza_nlp/data/processed/dataset_final.csv)) sobre los 100 registros (50 Humanos, 50 IA):

| Variable | Fase 3 (Humano / IA / Total) | Fase 3.5 (Humano / IA / Total) | Comentario de Variación |
| :--- | :---: | :---: | :--- |
| **oferta_pago** | 26 / 37 / **63** | 26 / 37 / **63** | Sin cambios (100% estable). |
| **aceptacion_pago** | 2 / 1 / **3** | 1 / 1 / **2** | -1 llamada (ID 37 corregida: era aceptación de callback, no de pago). |
| **acuerdo_pago** | 7 / 2 / **9** | 7 / 2 / **9** | Sin cambios (las 9 llamadas de acuerdo se mantienen). |
| **negociacion** | 24 / 35 / **59** | 24 / 35 / **59** | Sin cambios. |
| **tiene_objecion** | 8 / 5 / **13** | 8 / 5 / **13** | Sin cambios. |
| **intencion_pago** | 12 / 1 / **13** | 12 / 1 / **13** | Sin cambios. |
| **dificultad_pago** | 4 / 4 / **8** | 4 / 4 / **8** | Sin cambios. |
| **inconsistencia_mat.** | *(No medida)* | 2 / 5 / **7** | 7 casos donde la estructura de cuotas del diálogo no multiplica el saldo total. |

---

## 6. Pendientes para Fases Futuras

1. **Extracción de Fechas (Fase Futura):**
   - Se mantiene el extractor actual que prioriza fechas futuras. En auditorías futuras se puede agregar desambiguación para distinguir promesas de pago concretas vs fechas de corte o vencimiento bancario administrativo.
2. **Validación Humana Formal (Fase 4):**
   - Consignar las etiquetas humanas en [`data/validation/dataset_validacion.xlsx`](file:///d:/Prueba_Juan_Camilo_Avella/proyecto_cobranza_nlp/data/validation/dataset_validacion.xlsx).
   - Solo tras contar con el Gold Standard humano se calcularán matrices de confusión, métricas de desempeño del NLP (F1, Precision, Recall) y pruebas de significancia estadística definitiva.

---

## 7. Recomendación Final

**FASE 3.5 APROBADA — LISTO PARA VALIDACIÓN HUMANA**
