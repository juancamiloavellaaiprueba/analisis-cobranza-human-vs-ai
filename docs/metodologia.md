# Metodologia Analitica y Pipeline NLP

## 1. Origen de Datos
El estudio se fundamenta en un corpus de 100 llamadas de cobranza bancaria (50 de agentes humanos y 50 de agentes de inteligencia artificial), anonimizadas mediante identificadores alfanumericos.

## 2. Preprocesamiento y Limpieza
- Normalizacion de caracteres Unicode (NFKD), eliminacion de tildes y conversion a minusculas.
- Filtro de anomalías: identificacion de buzones de voz y alucinaciones linguisticas de Whisper en silencios de audio.
- Preservacion estricta de datos originales inmutables en `data/raw/`.

## 3. Extraccion NLP y Negacion Contextual
Para mitigar falsos positivos originados por busquedas literales:
- Se implemento un motor de negacion en ventana deslizante de 5 tokens previos.
- Diferenciacion semantica obligatoria:
  - `"voy a pagar"` -> Intencion positiva (`intencion_pago=1`).
  - `"no voy a pagar"` -> Rechazo explícito (`intencion_pago=0`).
  - `"no puedo pagar"` -> Dificultad economica (`dificultad_pago=1`, `intencion_pago=0`).
  - `"no puedo comprometerme"` -> Ausencia de compromiso.

## 4. Extraccion Financiera (Pesos Colombianos - COP)
- Resolucion de valores monetarios con separador de miles (`$500.000`, `300000`), cardinales compuestos (`500 mil`, `10 millones`) y cuotas (`dos cuotas de cien mil`).
- Los valores ausentes se representan formalmente como `NaN` (`np.nan`), nunca como `0`.

## 5. Jerarquia de Cierre y Acuerdo de Pago
El acuerdo formal exige:
1. Contactabilidad positiva.
2. Aceptacion o intencion positiva no negada.
3. Condicion vinculante (monto acordado o fecha limite establecida).

## 6. Segunda Verificacion y Control de Calidad
Se auditan contradicciones logicas entre variables:
- `acuerdo_pago == 1` con `aceptacion_pago == 0`.
- Mencion de cuotas sin formalizacion de compromiso.
Generando estados: `'ok'`, `'revisar'`, `'inconsistente'`.

## 7. Validacion Humana
Los registros etiquetados como `'revisar'` se exportan a `data/validation/dataset_validacion.xlsx` para revision experta.
