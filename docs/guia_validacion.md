# Guía Metodológica de Validación Humana y Auditoría de Variables NLP

## 1. Objetivo y Principio Metodológico

Esta guía establece los criterios operativos y metodológicos para que un revisor humano audite y valide manualmente las transcripciones de las 100 llamadas de cobranza bancaria (50 de agentes Humanos y 50 de agentes de Inteligencia Artificial) en [`data/validation/dataset_validacion.xlsx`](file:///d:/Prueba_Juan_Camilo_Avella/proyecto_cobranza_nlp/data/validation/dataset_validacion.xlsx).

> **Principio de Oro:**  
> Las etiquetas humanas deben reflejar con fidelidad lo que realmente ocurrió en la conversación según el juicio independiente del validador. **NO** deben marcarse para justificar las predicciones del NLP ni para optimizar artificialmente las métricas del modelo. Si una columna humana está vacía, representa que la validación humana real está pendiente.

---

## 2. Definiciones Operativas de las 11 Variables de Validación

### 2.1. Contactabilidad (`contactabilidad_validada`)
* **1 = Interacción efectiva:** Existe diálogo directo y comunicación bidireccional con el titular o una persona real en la línea.
* **0 = Sin contacto efectivo:** Buzón de voz, mensaje pregrabado, llamada cortada de inmediato, tono de ocupado, silencio o ausencia de respuesta humana.
* *Regla clave:* No inferir contacto simplemente porque exista texto transcrito (un mensaje de buzón genera transcripción pero `contactabilidad = 0`).

### 2.2. Oferta de Pago (`oferta_pago_validada`)
* **1 = Oferta concreta formulada:** El asesor presenta al menos una alternativa de pago específica: monto a cancelar, descuento, plan de cuotas, fecha límite, condonación o reestructuración.
* **0 = Sin oferta económica real:** Llamada meramente inquisitiva, cobro preventivo sin propuesta, verificación de datos sin opciones financieras, o llamada cortada antes de presentar alternativas.

### 2.3. Aceptación de Pago (`aceptacion_pago_validada`)
* **1 = Aceptación inequívoca del deudor:** El cliente aprueba expresamente una propuesta económica o condición de pago presentada (`"sí, acepto pagar"`, `"sí, me sirve ese plan"`, `"estoy de acuerdo con la cuota"`).
* **0 = Sin aceptación de pago:** El cliente rechaza, duda, guarda silencio o emite afirmaciones administrativas.
* *Regla fundamental:* `"de acuerdo"` **NO** significa automáticamente aceptación de pago. Si el cliente acepta recibir una llamada posterior (`"sí, de acuerdo, llámeme mañana"`), autoriza el envío de información (`"de acuerdo, envíeme por WhatsApp"`) o confirma un dato personal (`"de acuerdo, ese es mi correo"`), debe marcarse `aceptacion_pago_validada = 0`.

### 2.4. Acuerdo de Pago (`acuerdo_pago_validado`)
* **1 = Compromiso vinculante completo:** Existe compromiso formal y deliberado del deudor acompañado de al menos una condición concreta del pago: monto, cuota, número de cuotas, plazo o fecha límite.
* **0 = Sin acuerdo vinculante:** No hay compromiso, la llamada quedó inconclusa, el cliente dijo que "mirará si puede", o solo se acordó una llamada de seguimiento futuro.
* *Regla clave:* No marcar acuerdo únicamente porque el agente utilice la palabra "acuerdo" (ej. *"hacemos el acuerdo de que lo llamo mañana"* no es acuerdo de pago).

### 2.5. Negociación (`negociacion_validada`)
* **1 = Intercambio y exploración de condiciones:** Hubo interacción bidireccional sobre los términos del pago: contrapropuesta del cliente, solicitud de rebaja, ajuste de fecha según quincena, o evaluación de diferentes números de cuotas.
* **0 = Sin negociación:** El cliente aceptó o rechazó inmediatamente la primera alternativa sin debatir condiciones ni formular contraofertas.

### 2.6. Objeción (`objecion_validada`)
* **1 = Expresión de impedimento o dificultad:** El cliente manifiesta una barrera para pagar: falta de liquidez, desempleo, fecha inoportuna, desacuerdo con el saldo, o cuota excesiva.
* **0 = Sin objeción:** El deudor atiende fluidamente sin plantear reparos ni obstáculos.

### 2.7. Intención de Pago (`intencion_pago_validada`)
* **1 = Disposición positiva del cliente:** El deudor expresa voluntad o deseo de ponerse al día (`"yo quiero pagar"`, `"tengo la intención pero no me alcanza hoy"`, `"apenas consiga trabajo cancelo"`), incluso si en la llamada no se consolida un acuerdo formal.
* **0 = Sin intención:** Negativa tajante (`"no voy a pagar"`), indiferencia, evasión o falta de manifestación de voluntad.
* *Regla clave:* No atribuir intención al cliente por preguntas inductivas formuladas por el agente.

### 2.8. Dificultad de Pago (`dificultad_pago_validada`)
* **1 = Problema de capacidad económica manifiesto:** El cliente reporta expresamente insolvencia, desempleo, enfermedad, sobreendeudamiento o retraso en su salario.
* **0 = Sin reporte de dificultad:** No se mencionan problemas económicos.

### 2.9. Monto Acordado (`monto_acordado_validado`)
* **Valor numérico (COP):** Registrar única y exclusivamente el monto final comprometido y aceptado por el deudor.
* **`NaN` / Vacío:** Si no hubo acuerdo, si la llamada se cortó o si el valor es ambiguo.
* *Reglas clave:*
  - No registrar el saldo total de la deuda ni la propuesta inicial si el cliente no la aceptó.
  - Si existe una inconsistencia matemática (ej. ID 85), registrar el valor verbalmente pactado y documentar la anomalía en `observacion_validacion`.

### 2.10. Fecha de Compromiso (`fecha_compromiso_validada`)
* **Texto de fecha futura:** Registrar la fecha límite o fecha de pago pactada para el cumplimiento (`"15 de agosto"`, `"5 de agosto"`, `"31 de julio"`).
* **`NaN` / Vacío:** Si no hubo compromiso de pago.
* *Reglas clave:*
  - No capturar fechas históricas de origen o castigo de la deuda (ej. *"se originó en 2017"*).
  - Si la fecha es relativa (`"mañana"`, `"el viernes"`, `"fin de mes"`), consignar la expresión y aclarar en observaciones.

### 2.11. Resultado Final (`resultado_validado`)
Categoría derivada del análisis integral:
* `acuerdo_pago`: Contacto efectivo con compromiso concreto de pago.
* `propuesta_rechazada`: Hubo propuesta del asesor pero el cliente la rechazó.
* `dificultad_sin_acuerdo`: El cliente manifestó imposibilidad económica sin concretar pago.
* `negociacion_sin_acuerdo`: Se discutieron opciones pero no se cerró el compromiso.
* `contactado_sin_propuesta`: Hubo contacto pero no se presentó alternativa de pago.
* `no_contactado`: Buzón de voz, número equivocado o llamada cortada sin contacto.

---

## 3. Casos de Atención Especial para la Revisión Manual

El validador debe prestar especial atención a los siguientes registros:

### Caso ID 37:
* **Situación:** El asesor indica *"yo el día de mañana a las cuatro de la tarde me indica"* y el cliente responde *"Sí, de acuerdo"*.
* **Criterio metodológico:** Se trata de un **caso candidato a discrepancia NLP**, pendiente de confirmación mediante etiqueta humana. Debe evaluarse si el deudor aceptó un pago o si únicamente autorizó una llamada de seguimiento.

### Caso ID 55:
* **Situación:** En el diálogo aparecen frases coloquiales como *"porque a dos y eso me tiene como preocupado"*, y posteriormente montos reales de millones con descuento.
* **Criterio metodológico:** Evaluar el diálogo completo para determinar si hubo propuesta real y si el cliente realmente aceptó o rechazó comprometerse con el pago.

### Caso ID 85:
* **Situación:** La IA formula un acuerdo por un saldo de `$830.000` diferido en *"15 pagos mensuales de 60 mil pesos cada uno"* ($15 \times 60.000 = \$900.000$). Hay una discrepancia de `$70.000`.
* **Criterio metodológico:** Registrar como **inconsistencia matemática del agente IA**. Mantener `$830.000` en monto acordado y registrar la discrepancia en observaciones sin alterar los montos verbales.

### Caso ID 99:
* **Situación:** Conversación con expresiones temporales y compromisos escalonados.
* **Criterio metodológico:** Revisar minuciosamente la fecha de corte y la intención vinculante del deudor.

### Auditoría de Acuerdos NLP (9 casos):
Revisar con prioridad máxima los registros clasificados como acuerdo por el NLP: **1, 2, 5, 7, 8, 29, 47, 85 y 99**. Verificar si en cada uno de ellos existe consentimiento inequívoco del deudor con condiciones económicas específicas.

---

## 4. Evidencia y Nivel de Confianza

### Evidencia Textual (`evidencia_validacion`):
* Consignar una cita textual breve o fragmento de la conversación que sustente la decisión.
* *Ejemplo:* `"Cliente confirma: 'sí señora, acepto pagar los 250 mil el 30'"`.
* No inventar frases ni parafrasear distorsionando el sentido original.

### Nivel de Confianza (`nivel_confianza_validacion`):
* **`alto`:** La evidencia en el texto es inequívoca, directa y sin ambigüedad.
* **`medio`:** Interpretación clara pero informal o con leve elipsis en el diálogo.
* **`bajo`:** Diálogo ruidoso, oraciones cortadas o transcripción incompleta donde la decisión depende de inferencia.

---

## 5. Validación de Calidad e Inconsistencias Lógicas

Antes de cerrar la validación humana, verificar que no existan contradicciones lógicas en las etiquetas:
1. `acuerdo_pago_validado = 1` con `contactabilidad_validada = 0` (Imposible acordar sin contacto).
2. `acuerdo_pago_validado = 1` con `oferta_pago_validada = 0` (No puede haber acuerdo sin propuesta previa).
3. `monto_acordado_validado` con valor numérico pero `acuerdo_pago_validado = 0`.
4. `aceptacion_pago_validada = 1` sin evidencia de propuesta de pago.
5. `resultado_validado = 'acuerdo_pago'` pero `acuerdo_pago_validado = 0`.

Cualquier inconsistencia detectada debe corregirse con base en la lectura de la transcripción y documentarse en observaciones.

---

## 6. Protección de Datos Personales (PII)

Las transcripciones contienen información sensible (nombres, cédulas, números telefónicos, correos y direcciones).
1. **Confidencialidad:** Mantener el archivo Excel y las transcripciones exclusivamente en el entorno de trabajo local.
2. **Repositorio público:** Ningún archivo que contenga datos personales sin anonimizar debe subirse a repositorios públicos de GitHub.
