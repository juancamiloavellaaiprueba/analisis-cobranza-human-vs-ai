# Diccionario de Variables del Dataset Analitico

Este documento define formalmente las variables del pipeline de cobranza bancaria para contrastar agentes humanos y de inteligencia artificial.

| Variable | Tipo | Descripcion | Valores Posibles | Regla de Construccion | Ejemplo |
|---|---|---|---|---|---|
| `id` | int | Identificador unico secuencial | 1 a 100 | Asignado en ingesta | `1` |
| `archivo` | str | Nombre del archivo de audio/transcripcion | UUID .wav | Identificador de fuente | `0445c357...wav` |
| `tipo_agente` | str | Canal emisor | `'humano'`, `'ia'` | Metadata de llamada | `'humano'` |
| `duracion_segundos` | float | Duracion acustica en segundos | >= 0.0 | Metadato de audio | `308.56` |
| `num_palabras` | int | Total tokens de palabra | >= 0 | Conteo en texto | `724` |
| `contactabilidad` | int | Indicador de contacto efectivo | 0, 1 | 0 si es buzon/vacio; 1 si hay dialogo | `1` |
| `oferta_pago` | int | Presentacion de alternativa o monto | 0, 1 | Mencion de alternativa o cuota | `1` |
| `aceptacion_pago` | int | Conformidad verbal del cliente | 0, 1 | 'acepto', 'de acuerdo' no negados | `1` |
| `acuerdo_pago` | int | Compromiso formal vinculante | 0, 1 | Contacto + aceptacion + condicion vinculante | `1` |
| `resultado_final` | str | Clasificacion final del contacto | Categorias controladas | Jerarquia de desenlace | `'acuerdo_pago'` |
| `monto_deuda` | float | Deuda total exigible en COP | Numero o NaN | Parser en contexto deuda | `800000.0` |
| `monto_propuesto` | float | Monto ofrecido en COP | Numero o NaN | Parser en contexto oferta | `400000.0` |
| `monto_acordado` | float | Monto final aceptado en COP | Numero o NaN | Monto asignado al acuerdo | `400000.0` |
| `numero_cuotas` | float | Cantidad de cuotas | Numero o NaN | 'X cuotas' numerico/texto | `2.0` |
| `monto_cuota` | float | Valor de cada cuota en COP | Numero o NaN | 'de X cada una' | `400000.0` |
| `tiene_descuento` | bool | Indicador de beneficio o quita | True, False | Mencion de beneficio no negado | `True` |
| `monto_descuento` | float | Valor del descuento en COP | Numero o NaN | 'descuento de X' | `100000.0` |
| `fecha_compromiso` | str | Fecha o plazo pactado | Texto o None | Expresion temporal | `'31 de julio'` |
| `negociacion` | int | Discusion de alternativas o plazos | 0, 1 | Contrapropuesta de cuotas/rebaja | `1` |
| `num_propuestas_pago`| int | Conteo de propuestas evaluadas | >= 0 | Oferta inicial + alternativas | `2` |
| `tiene_objecion` | int | Presencia de impedimento expresado | 0, 1 | Deteccion de patrones de reclamo | `1` |
| `num_objeciones` | int | Cantidad de objeciones | >= 0 | Conteo de incidencias | `1` |
| `tipo_objecion` | str | Categoria principal de objecion | Categorias controladas | Clasificador multiclase | `'fecha_pago'` |
| `manejo_objecion` | int | Respuesta del agente con alternativa | 0, 1 | Agente ofrece opcion ante objecion | `1` |
| `objecion_resuelta` | int | Objecion superada con acuerdo | 0, 1 | 1 si hubo acuerdo tras objecion | `0` |
| `num_preguntas_agente` | int | Conteo de interrogantes del agente | >= 0 | Conteo de signos y lemas pregunta | `8` |
| `tipo_respuesta_cliente` | str | Postura predominante del cliente | Categorias controladas | Inferida por lemas clave | `'afirmativa'` |
| `intencion_pago` | int | Voluntad positiva de pago | 0, 1 | Compromiso o disposicion verbal | `1` |
| `dificultad_pago` | int | Expresion de imposibilidad economica | 0, 1 | 'no puedo pagar', 'no tengo plata' | `0` |
| `confianza_nlp` | float | Certidumbre algoritmica | 0.0 a 1.0 | Score ponderado de evidencia | `0.90` |
| `control_calidad` | str | Estado de coherencia logica | `'ok'`, `'revisar'`, `'inconsistente'` | Reglas de validacion cruzada | `'ok'` |

### Categorias de `resultado_final`:
- `no_contactado`: Llamada en buzon de voz o cortada sin dialogo.
- `contactado_sin_propuesta`: Contacto efectivo sin formular propuesta de pago.
- `propuesta_rechazada`: El cliente rechaza la propuesta sin explorar alternativas.
- `negociacion_sin_acuerdo`: Se discutieron cuotas o descuentos sin compromiso vinculante.
- `acuerdo_pago`: Compromiso confirmado con fecha o monto acordado.
- `dificultad_sin_acuerdo`: El cliente manifiesta imposibilidad economica no resuelta.
- `otro`: Conversaciones informativas o sin categoria estandar.
