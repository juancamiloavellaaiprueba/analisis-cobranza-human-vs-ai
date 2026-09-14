# Analisis NLP de Llamadas de Cobranza — Prueba Tecnica Creceré AI

## Objetivo
Evaluar y comparar el desempeno operativo entre agentes humanos y agentes de inteligencia artificial (IA) a partir de una base analitica estructurada construida mediante procesamiento de lenguaje natural (NLP) sobre 100 transcripciones de llamadas de cobranza bancaria (50 de agentes humanos y 50 de agentes de IA).

Pregunta central de investigacion:
> *¿Existen diferencias estadisticamente sustentables entre el desempeno de los agentes humanos y los agentes de IA?*

---

## Arquitectura y Metodologia

El proyecto implementa un pipeline reproducible sin sobreingenieria:
1. **Preprocesamiento y limpieza:** Normalizacion fonetica de texto, remocion de diacriticos, aislamiento de buzones de voz y filtrado de anomalias/alucinaciones de ASR.
2. **Motor de reglas NLP contextuales:** Segmentacion conversacional agente/cliente, extraccion con ventanas de contexto para preservacion estricta de negaciones (e.g., *"no puedo pagar"* vs. *"voy a pagar"*).
3. **Parser de condiciones financieras:** Extraccion deterministica de montos en Pesos Colombianos (COP), numero de cuotas, descuentos porcentuales y fechas vinculantes de compromiso.
4. **Control de calidad y consistencia:** Reglas cruzadas de validacion logica (`ok`, `revisar`, `inconsistente`) para auditar la coherencia entre montos, cuotas y acuerdos cerrados.
5. **Validacion humana (QA secundario):** Auditoria del extractor NLP sobre casos seleccionados (`dataset_validacion_consolidado_final.xlsx`). Esta capa funciona estrictamente como QA de precision del extractor y no sustituye la base analitica de 100 llamadas.
6. **Analisis estadistico inferencial:** Pruebas de hipotesis (Fisher exacto, Chi-cuadrado con correccion de Yates, Mann-Whitney U), intervalos de confianza al 95%, tamanos de efecto (Cohen's h, correlacion biserial por rangos) y control de tasa de falso descubrimiento (FDR Benjamini-Hochberg).

---

## Pipeline de Procesamiento

```
Grabaciones de Audio (.wav, .mp3, etc.)
       │
       ▼
scripts/01_transcribir.py (OpenAI Whisper)
       │
       ▼
data/raw/transcripciones/ (100 .txt: 50 Humanos / 50 IA)
       │
       ▼
data/raw/dataset_limpio.csv
       │
       ▼
scripts/02_limpiar.py
       │
       ▼
scripts/03_extraer_variables.py ──► data/processed/dataset_final.csv (N=100)
       │
       ▼
scripts/04_validar.py ───────────► data/validation/dataset_validacion.xlsx (QA)
       │
       ▼
scripts/05_generar_resultados.py ──► reports/informe.html (Ejecutivo, max 2 paginas)
                                  └─► reports/anexo_tecnico.html (Anexo completo)
```

---

## Estructura de Variables

El dataset analitico procesado (`data/processed/dataset_final.csv`, N=100) consolida 31 variables clave:
- **Identificacion:** `id`, `archivo`, `tipo_agente`, `duracion_segundos`, `num_palabras`.
- **Proceso de cobranza:** `contactabilidad`, `oferta_pago`, `aceptacion_pago`, `acuerdo_pago`, `resultado_final`.
- **Condiciones economicas:** `monto_deuda`, `monto_propuesto`, `monto_acordado`, `numero_cuotas`, `monto_cuota`, `tiene_descuento`, `monto_descuento`, `fecha_compromiso`.
- **Negociacion y objeciones:** `negociacion`, `num_propuestas_pago`, `tiene_objecion`, `num_objeciones`, `tipo_objecion`, `manejo_objecion`, `objecion_resuelta`.
- **Comportamiento:** `num_preguntas_agente`, `tipo_respuesta_cliente`, `intencion_pago`, `dificultad_pago`, `confianza_nlp`, `control_calidad`, `inconsistencia_matematica_acuerdo`.
- **Evidencias textuales:** Fragmentos literales que sustentan cada decision algoritmica.

---

## Metodologia Estadistica

Se adopta una estricta jerarquia inferencial pre-especificada para evitar inflacion de error tipo I y sobreinterpretacion:

1. **Familia Principal (Resultado Final):**
   - Variable: `acuerdo_pago` (cierre formal vinculante con monto/fecha/plazo).
   - Prueba: Test exacto de Fisher bilateral (apropiado por frecuencias esperadas < 5).
   - Nivel de significancia: $\alpha = 0.05$ (sin ajuste por multiplicidad).
2. **Familia Secundaria (Proceso y Comportamiento):**
   - 5 hipotesis pre-especificadas: `intencion_pago`, `tiene_descuento`, `oferta_pago`, `negociacion`, `num_propuestas_pago`.
   - Control de multiplicidad: Benjamini-Hochberg (FDR) con $q = 0.05$.
3. **Metrica Condicional:**
   - `conv_oferta_a_acuerdo`: Evaluada condicionalmente sobre el subconjunto de llamadas que recibieron oferta formal (Humanos $n=26$, IA $n=37$).
4. **Variables Excluidas de Inferencia Headline:**
   - Variables monetarias continuas (`monto_acordado`, `monto_propuesto`, etc.): Alto porcentaje de datos faltantes (78%–98% missing), lo que genera sesgo de seleccion y potencia estadistica nula.
   - Variables sin varianza (`objecion_resuelta` con 0% en ambos grupos) o eventos ultra-raros (`aceptacion_pago` con 2 casos).

---

## Resultados Principales

Todos los estadisticos fueron calculados deterministica y reproduciblemente sobre `data/processed/dataset_final.csv` ($N = 100$; Humanos = 50, IA = 50):

| Variable / Metrica | Humanos (n=50) | IA (n=50) | Diferencia (H - IA) | IC 95% | Prueba Estadistica | p-valor (raw) | p-ajustado (FDR) | Conclusion Estadistica |
|---|---|---|---|---|---|---|---|---|
| **A. Resultado Principal** | | | | | | | | |
| `acuerdo_pago` | 14.0% (7/50) | 4.0% (2/50) | +10.0 pp | [-1.0 pp, +21.0 pp] | Fisher exacto | p = 0.1595 | N/A | **No se rechaza H0** (Cohen's h = 0.364) |
| **B. Senales Destacadas** | | | | | | | | |
| `intencion_pago` | 24.0% (12/50) | 2.0% (1/50) | +22.0 pp | [+9.5 pp, +34.5 pp] | Chi2 con Yates | p = 0.0029 | p = 0.0147 | **Sobrevive FDR** (Cohen's h = 0.740) |
| `oferta_pago` | 52.0% (26/50) | 74.0% (37/50) | -22.0 pp | [-40.4 pp, -3.6 pp] | Chi2 con Yates | p = 0.0383 | p = 0.0639 | **No sobrevive FDR** (Cohen's h = 0.461) |
| **C. Metrica Condicional** | | | | | | | | |
| `conv_oferta_a_acuerdo` | 26.9% (7/26) | 5.4% (2/37) | +21.5 pp | [+3.0 pp, +40.1 pp] | Fisher exacto | p = 0.0263 | N/A | Diferencia condicional (Cohen's h = 0.622) |
| **D. Metricas Secundarias** | | | | | | | | |
| `tiene_descuento` | 44.0% (22/50) | 70.0% (35/50) | -26.0 pp | [-44.7 pp, -7.3 pp] | Chi2 con Yates | p = 0.0154 | p = 0.0385 | **Sobrevive FDR** (Cohen's h = 0.532) |
| `negociacion` | 48.0% (24/50) | 70.0% (35/50) | -22.0 pp | [-40.8 pp, -3.2 pp] | Chi2 con Yates | p = 0.0420 | p = 0.0639 | **No sobrevive FDR** (Cohen's h = 0.452) |
| `num_propuestas_pago` | Mdn: 1.0 (Med: 1.0) | Mdn: 2.0 (Med: 1.4) | Mdn dif: -1.0 | N/A | Mann-Whitney U | p = 0.0490 | p = 0.0639 | **No sobrevive FDR** (r = -0.229) |
| `duracion_segundos` | Mdn: 168.0s (236.7s) | Mdn: 148.5s (217.9s)| Mdn dif: +19.5s| N/A | Mann-Whitney U | p = 0.3276 | N/A | No significativo (r = +0.114) |
| `inconsistencia_matematica` | 4.0% (2/50) | 10.0% (5/50) | -6.0 pp | [-15.9 pp, +3.9 pp] | Fisher exacto | p = 0.4360 | N/A | No significativo (Cohen's h = 0.241) |

---

## Analisis de Potencia Estadistica

Para detectar una diferencia como la observada en acuerdos (14% vs. 4%) con $\alpha = 0.05$ bilateral y potencia del 80%:
- El tamano muestral requerido es de aproximadamente $n \approx 138$ llamadas por grupo (Fleiss con correccion de continuidad; $N \approx 276$) o $n \approx 147$ por grupo (Casagrande-Pike-Smith; $N \approx 294$).
- Con la muestra actual de $n = 50$ por grupo, la potencia exacta bajo el test de Fisher es de aproximadamente **26.14%** (asintotica $\approx 41.44\%$).
- **Interpretacion metodologica:** La baja potencia limita la capacidad del estudio para detectar estadisticamente diferencias en eventos de baja frecuencia como los acuerdos de pago. Esto fundamenta el resultado de que **no se rechaza $H_0$**, pero no debe utilizarse para asegurar que la diferencia observada sea confirmable.

---

## Limitaciones y Alcance Metodologico

- **Diseno observacional:** El conjunto de datos proviene de registros operativos sin asignacion aleatoria controlada entre tipos de cliente y canal; por tanto, **no permite inferir causalidad** entre el tipo de agente y el resultado de la llamada.
- **Baja frecuencia de acuerdos:** Al tratarse de un evento poco frecuente en cobranza temprana (9 acuerdos totales en 100 llamadas), las estimaciones con $N=100$ tienen amplios margenes de error.
- **Métricas condicionales:** La conversion oferta $\to$ acuerdo se mide sobre subconjuntos autoseleccionados con denominadores desiguales (26 vs. 37 llamadas).
- **Valores monetarios con alto missing:** Debido a la alta proporcion de llamadas sin cierre o sin mencion explicita de montos, los valores en pesos no permiten contrastes inferenciales validos.
- **Diarizacion heuristica:** La separacion de roles (agente vs. cliente) se basa en patrones lexicos y turnos sobre ASR mono-canal, lo que puede introducir ruido en llamadas de baja inteligibilidad.

---

## Como Reproducir el Proyecto

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Ejecutar la suite completa de tests automatizados (58 tests)
python -m pytest tests/ -v

# 3. Transcripción de audios (Opcional - solo si se dispone de nuevas grabaciones):
# Las 100 transcripciones auditadas ya se encuentran inmutables en data/raw/transcripciones/
python scripts/01_transcribir.py --input data/raw/audios --output data/raw/transcripciones --model base --language es

# 4. Ejecutar pipeline de procesamiento, extracción y validación
python scripts/02_limpiar.py
python scripts/03_extraer_variables.py
python scripts/04_validar.py
python scripts/05_generar_resultados.py

# 5. Los reportes finales estaran disponibles en:
# - reports/informe.html (Reporte ejecutivo bancario, max 2 paginas)
# - reports/anexo_tecnico.html (Anexo tecnico y metodologico completo)
```
