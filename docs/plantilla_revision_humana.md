# Plantilla y Protocolo de Revisión Humana de las 100 Llamadas

**Archivo de trabajo:** [`data/validation/dataset_validacion.xlsx`](file:///d:/Prueba_Juan_Camilo_Avella/proyecto_cobranza_nlp/data/validation/dataset_validacion.xlsx)  
**Total de registros a auditar:** 100 (50 Agentes Humanos, 50 Agentes IA)  
**Estado actual:** PENDIENTE DE VALIDACIÓN HUMANA (Columnas humanas 100% vacías)  

---

## 1. Instrucciones Paso a Paso para la Validación Manual

1. Abra el archivo Excel [`data/validation/dataset_validacion.xlsx`](file:///d:/Prueba_Juan_Camilo_Avella/proyecto_cobranza_nlp/data/validation/dataset_validacion.xlsx) en su editor de hojas de cálculo.
2. La hoja contiene dos bloques claramente separados:
   - **Columnas NLP (referencia auditable):** `contactabilidad_nlp`, `acuerdo_pago_nlp`, `aceptacion_pago_nlp`, `oferta_pago_nlp`, `negociacion_nlp`, `tiene_objecion_nlp`, `intencion_pago_nlp`, `dificultad_pago_nlp`, `monto_propuesto_nlp`, `monto_acordado_nlp`, `fecha_compromiso_nlp`, `resultado_final_nlp`, etc.
   - **Columnas Humanas (a diligenciar por el validador):** `contactabilidad_validada`, `oferta_pago_validada`, `aceptacion_pago_validada`, `acuerdo_pago_validado`, `negociacion_validada`, `objecion_validada`, `intencion_pago_validada`, `dificultad_pago_validada`, `monto_acordado_validado`, `fecha_compromiso_validada`, `resultado_validado`, `nivel_confianza_validacion`, `evidencia_validacion`, `observacion_validacion`, `validador`, `fecha_validacion`.
3. **Secuencia de revisión recomendada:**
   - **Fase A (Eje del compromiso):** Leer la columna `transcripcion` y evaluar primero: `contactabilidad_validada`, `oferta_pago_validada`, `aceptacion_pago_validada`, `acuerdo_pago_validado` y `resultado_validado`.
   - **Fase B (Dinámica y condiciones):** Evaluar `negociacion_validada`, `objecion_validada`, `intencion_pago_validada`, `dificultad_pago_validada`, `monto_acordado_validado` y `fecha_compromiso_validada`.
   - **Fase C (Auditoría y trazabilidad):** Completar `nivel_confianza_validacion` (`alto`, `medio`, `bajo`), citar la frase clave en `evidencia_validacion`, indicar notas en `observacion_validacion` (ej. si detecta inconsistencia matemática), y registrar `validador` y `fecha_validacion`.

---

## 2. Niveles de Prioridad de Revisión

- **ALTA:** Registros críticos que incluyen:
  - Casos auditados especiales: ID 37, 55, 85, 99.
  - Acuerdos detectados por el NLP: ID 1, 2, 5, 7, 8, 29, 47, 85, 99.
  - Inconsistencias matemáticas en diálogo (cuotas vs saldo total).
- **MEDIA:** Registros con contacto efectivo donde se presentaron propuestas o dificultades financieras sin acuerdo formal.
- **BAJA:** Registros sin contacto efectivo (buzones de voz o audios vacíos) de verificación rápida.

---

## 3. Matriz Completa de los 100 Registros para Validación

| ID | Agente | Cont. | Oferta | Acep. | Acuerdo | Monto Acordado | Fecha Comp. | Resultado NLP | Prioridad | Motivo de Prioridad |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :---: | :--- |
| 1 | Humano | 1 | 1 | 0 | 1 | - | 5 de agosto | acuerdo_pago | ALTA | Acuerdo clasificado por NLP (auditoria prioritaria) |
| 2 | Humano | 1 | 1 | 0 | 1 | - | 31 de agosto | acuerdo_pago | ALTA | Acuerdo clasificado por NLP (auditoria prioritaria) |
| 3 | Humano | 1 | 0 | 0 | 0 | - | - | contactado_sin_propuesta | MEDIA | Contacto efectivo: contactado_sin_propuesta |
| 4 | Humano | 0 | 0 | 0 | 0 | - | - | no_contactado | BAJA | Sin contacto efectivo (buzon o audio vacio) |
| 5 | Humano | 1 | 1 | 1 | 1 | - | 18 | acuerdo_pago | ALTA | Acuerdo clasificado por NLP (auditoria prioritaria) |
| 6 | Humano | 1 | 1 | 0 | 0 | - | hoy | negociacion_sin_acuerdo | MEDIA | Se mencionaron cuotas pero no se concreto acuerdo de pago |
| 7 | Humano | 1 | 1 | 0 | 1 | - | 30 | acuerdo_pago | ALTA | Acuerdo clasificado por NLP (auditoria prioritaria) |
| 8 | Humano | 1 | 1 | 0 | 1 | - | manana | acuerdo_pago | ALTA | Acuerdo clasificado por NLP (auditoria prioritaria) |
| 9 | Humano | 1 | 1 | 0 | 0 | - | 20 de agosto | dificultad_sin_acuerdo | MEDIA | Se mencionaron cuotas pero no se concreto acuerdo de pago |
| 10 | Humano | 1 | 1 | 0 | 0 | - | 25 | negociacion_sin_acuerdo | MEDIA | Se mencionaron cuotas pero no se concreto acuerdo de pago |
| 11 | Humano | 1 | 1 | 0 | 0 | - | el sabado | negociacion_sin_acuerdo | MEDIA | Se mencionaron cuotas pero no se concreto acuerdo de pago |
| 12 | Humano | 1 | 0 | 0 | 0 | - | 30 de junio | contactado_sin_propuesta | MEDIA | Contacto efectivo: contactado_sin_propuesta |
| 13 | Humano | 1 | 0 | 0 | 0 | - | - | contactado_sin_propuesta | MEDIA | Contacto efectivo: contactado_sin_propuesta |
| 14 | Humano | 1 | 0 | 0 | 0 | - | 15 de julio | contactado_sin_propuesta | MEDIA | Contacto efectivo: contactado_sin_propuesta |
| 15 | Humano | 1 | 0 | 0 | 0 | - | manana | contactado_sin_propuesta | MEDIA | Contacto efectivo: contactado_sin_propuesta |
| 16 | Humano | 1 | 1 | 0 | 0 | - | - | negociacion_sin_acuerdo | MEDIA | Contacto efectivo: negociacion_sin_acuerdo |
| 17 | Humano | 1 | 0 | 0 | 0 | - | manana | contactado_sin_propuesta | MEDIA | Contacto efectivo: contactado_sin_propuesta |
| 18 | Humano | 1 | 0 | 0 | 0 | - | - | contactado_sin_propuesta | MEDIA | Contacto efectivo: contactado_sin_propuesta |
| 19 | Humano | 1 | 0 | 0 | 0 | - | 30 de agosto | contactado_sin_propuesta | MEDIA | Contacto efectivo: contactado_sin_propuesta |
| 20 | Humano | 1 | 0 | 0 | 0 | - | 24 | contactado_sin_propuesta | MEDIA | Contacto efectivo: contactado_sin_propuesta |
| 21 | Humano | 1 | 0 | 0 | 0 | - | manana | contactado_sin_propuesta | MEDIA | Contacto efectivo: contactado_sin_propuesta |
| 22 | Humano | 1 | 0 | 0 | 0 | - | hoy | contactado_sin_propuesta | MEDIA | Contacto efectivo: contactado_sin_propuesta |
| 23 | Humano | 1 | 0 | 0 | 0 | - | hoy | contactado_sin_propuesta | MEDIA | Contacto efectivo: contactado_sin_propuesta |
| 24 | Humano | 1 | 0 | 0 | 0 | - | - | dificultad_sin_acuerdo | MEDIA | Contacto efectivo: dificultad_sin_acuerdo |
| 25 | Humano | 1 | 1 | 0 | 0 | - | 15 de agosto | propuesta_rechazada | MEDIA | Contacto efectivo: propuesta_rechazada |
| 26 | Humano | 1 | 0 | 0 | 0 | - | 28 | contactado_sin_propuesta | MEDIA | Contacto efectivo: contactado_sin_propuesta |
| 27 | Humano | 1 | 1 | 0 | 0 | - | 30 | negociacion_sin_acuerdo | MEDIA | Se mencionaron cuotas pero no se concreto acuerdo de pago |
| 28 | Humano | 1 | 1 | 0 | 0 | - | hoy | negociacion_sin_acuerdo | MEDIA | Se mencionaron cuotas pero no se concreto acuerdo de pago |
| 29 | Humano | 1 | 1 | 0 | 1 | - | 15 de agosto | acuerdo_pago | ALTA | Acuerdo clasificado por NLP (auditoria prioritaria) |
| 30 | Humano | 1 | 1 | 0 | 0 | - | manana | negociacion_sin_acuerdo | MEDIA | Se mencionaron cuotas pero no se concreto acuerdo de pago |
| 31 | Humano | 1 | 1 | 0 | 0 | - | 20 | negociacion_sin_acuerdo | MEDIA | Se mencionaron cuotas pero no se concreto acuerdo de pago |
| 32 | Humano | 1 | 0 | 0 | 0 | - | 23 de abril | propuesta_rechazada | MEDIA | Contacto efectivo: propuesta_rechazada |
| 33 | Humano | 1 | 1 | 0 | 0 | - | 30 | propuesta_rechazada | MEDIA | Contacto efectivo: propuesta_rechazada |
| 34 | Humano | 1 | 0 | 0 | 0 | - | manana | contactado_sin_propuesta | MEDIA | Contacto efectivo: contactado_sin_propuesta |
| 35 | Humano | 1 | 0 | 0 | 0 | - | hoy | contactado_sin_propuesta | MEDIA | Contacto efectivo: contactado_sin_propuesta |
| 36 | Humano | 1 | 1 | 0 | 0 | - | 10 de julio | negociacion_sin_acuerdo | MEDIA | Contacto efectivo: negociacion_sin_acuerdo |
| 37 | Humano | 1 | 0 | 0 | 0 | - | manana | contactado_sin_propuesta | ALTA | Caso critico auditado (atencion especial) |
| 38 | Humano | 1 | 1 | 0 | 0 | - | 15 de julio | negociacion_sin_acuerdo | MEDIA | Contacto efectivo: negociacion_sin_acuerdo |
| 39 | Humano | 1 | 1 | 0 | 0 | - | 15 de agosto | negociacion_sin_acuerdo | ALTA | Inconsistencia matematica cuotas vs total |
| 40 | Humano | 1 | 1 | 0 | 0 | - | - | negociacion_sin_acuerdo | MEDIA | Contacto efectivo: negociacion_sin_acuerdo |
| 41 | Humano | 1 | 0 | 0 | 0 | - | - | contactado_sin_propuesta | MEDIA | Contacto efectivo: contactado_sin_propuesta |
| 42 | Humano | 1 | 0 | 0 | 0 | - | - | propuesta_rechazada | MEDIA | Contacto efectivo: propuesta_rechazada |
| 43 | Humano | 1 | 1 | 0 | 0 | - | manana | propuesta_rechazada | MEDIA | Se mencionaron cuotas pero no se concreto acuerdo de pago |
| 44 | Humano | 1 | 1 | 0 | 0 | - | manana | negociacion_sin_acuerdo | MEDIA | Se mencionaron cuotas pero no se concreto acuerdo de pago |
| 45 | Humano | 1 | 0 | 0 | 0 | - | manana | contactado_sin_propuesta | MEDIA | Contacto efectivo: contactado_sin_propuesta |
| 46 | Humano | 1 | 1 | 0 | 0 | - | - | negociacion_sin_acuerdo | MEDIA | Contacto efectivo: negociacion_sin_acuerdo |
| 47 | Humano | 1 | 1 | 0 | 1 | - | 19 de julio | acuerdo_pago | ALTA | Acuerdo clasificado por NLP (auditoria prioritaria) |
| 48 | Humano | 1 | 0 | 0 | 0 | - | hoy | dificultad_sin_acuerdo | MEDIA | Contacto efectivo: dificultad_sin_acuerdo |
| 49 | Humano | 1 | 1 | 0 | 0 | - | hoy | negociacion_sin_acuerdo | ALTA | Inconsistencia matematica cuotas vs total |
| 50 | Humano | 1 | 0 | 0 | 0 | - | el sabado | propuesta_rechazada | MEDIA | Contacto efectivo: propuesta_rechazada |
| 51 | Ia | 1 | 1 | 0 | 0 | - | hoy | negociacion_sin_acuerdo | MEDIA | Contacto efectivo: negociacion_sin_acuerdo |
| 52 | Ia | 1 | 1 | 0 | 0 | - | hoy | negociacion_sin_acuerdo | MEDIA | Se mencionaron cuotas pero no se concreto acuerdo de pago |
| 53 | Ia | 1 | 1 | 0 | 0 | - | hoy | negociacion_sin_acuerdo | MEDIA | Contacto efectivo: negociacion_sin_acuerdo |
| 54 | Ia | 1 | 1 | 0 | 0 | - | hoy | negociacion_sin_acuerdo | MEDIA | Contacto efectivo: negociacion_sin_acuerdo |
| 55 | Ia | 1 | 1 | 0 | 0 | - | 30 de julio | negociacion_sin_acuerdo | ALTA | Caso critico auditado (atencion especial) |
| 56 | Ia | 1 | 0 | 0 | 0 | - | - | contactado_sin_propuesta | MEDIA | Contacto efectivo: contactado_sin_propuesta |
| 57 | Ia | 1 | 1 | 0 | 0 | - | hoy | negociacion_sin_acuerdo | MEDIA | Contacto efectivo: negociacion_sin_acuerdo |
| 58 | Ia | 1 | 1 | 0 | 0 | - | 13 de agosto | negociacion_sin_acuerdo | MEDIA | Contacto efectivo: negociacion_sin_acuerdo |
| 59 | Ia | 1 | 1 | 0 | 0 | - | - | propuesta_rechazada | MEDIA | Contacto efectivo: propuesta_rechazada |
| 60 | Ia | 1 | 0 | 0 | 0 | - | - | contactado_sin_propuesta | MEDIA | Contacto efectivo: contactado_sin_propuesta |
| 61 | Ia | 1 | 1 | 0 | 0 | - | 4 de agosto | negociacion_sin_acuerdo | MEDIA | Contacto efectivo: negociacion_sin_acuerdo |
| 62 | Ia | 1 | 1 | 0 | 0 | - | 21 de agosto | negociacion_sin_acuerdo | MEDIA | Contacto efectivo: negociacion_sin_acuerdo |
| 63 | Ia | 1 | 1 | 0 | 0 | - | 11 de junio | negociacion_sin_acuerdo | MEDIA | Contacto efectivo: negociacion_sin_acuerdo |
| 64 | Ia | 1 | 1 | 0 | 0 | - | hoy | negociacion_sin_acuerdo | MEDIA | Contacto efectivo: negociacion_sin_acuerdo |
| 65 | Ia | 1 | 1 | 0 | 0 | - | hoy | propuesta_rechazada | MEDIA | Contacto efectivo: propuesta_rechazada |
| 66 | Ia | 0 | 0 | 0 | 0 | - | - | no_contactado | BAJA | Sin contacto efectivo (buzon o audio vacio) |
| 67 | Ia | 1 | 1 | 0 | 0 | - | 30 de junio | negociacion_sin_acuerdo | ALTA | Inconsistencia matematica cuotas vs total |
| 68 | Ia | 1 | 1 | 0 | 0 | - | hoy | negociacion_sin_acuerdo | MEDIA | Contacto efectivo: negociacion_sin_acuerdo |
| 69 | Ia | 1 | 1 | 0 | 0 | - | 31 de agosto | propuesta_rechazada | MEDIA | Contacto efectivo: propuesta_rechazada |
| 70 | Ia | 1 | 1 | 0 | 0 | - | - | negociacion_sin_acuerdo | MEDIA | Contacto efectivo: negociacion_sin_acuerdo |
| 71 | Ia | 0 | 0 | 0 | 0 | - | - | no_contactado | BAJA | Sin contacto efectivo (buzon o audio vacio) |
| 72 | Ia | 1 | 1 | 0 | 0 | - | hoy | negociacion_sin_acuerdo | MEDIA | Se mencionaron cuotas pero no se concreto acuerdo de pago |
| 73 | Ia | 1 | 1 | 0 | 0 | - | hoy | dificultad_sin_acuerdo | MEDIA | Se mencionaron cuotas pero no se concreto acuerdo de pago |
| 74 | Ia | 1 | 1 | 0 | 0 | - | hoy | dificultad_sin_acuerdo | MEDIA | Contacto efectivo: dificultad_sin_acuerdo |
| 75 | Ia | 1 | 1 | 0 | 0 | - | el jueves | negociacion_sin_acuerdo | MEDIA | Contacto efectivo: negociacion_sin_acuerdo |
| 76 | Ia | 1 | 1 | 0 | 0 | - | hoy | negociacion_sin_acuerdo | MEDIA | Contacto efectivo: negociacion_sin_acuerdo |
| 77 | Ia | 1 | 0 | 0 | 0 | - | - | contactado_sin_propuesta | MEDIA | Contacto efectivo: contactado_sin_propuesta |
| 78 | Ia | 1 | 1 | 0 | 0 | - | 24 de junio | propuesta_rechazada | MEDIA | Contacto efectivo: propuesta_rechazada |
| 79 | Ia | 1 | 0 | 0 | 0 | - | - | contactado_sin_propuesta | MEDIA | Contacto efectivo: contactado_sin_propuesta |
| 80 | Ia | 1 | 1 | 0 | 0 | - | - | negociacion_sin_acuerdo | MEDIA | Se mencionaron cuotas pero no se concreto acuerdo de pago |
| 81 | Ia | 1 | 1 | 0 | 0 | - | - | negociacion_sin_acuerdo | MEDIA | Contacto efectivo: negociacion_sin_acuerdo |
| 82 | Ia | 1 | 1 | 0 | 0 | - | hoy | negociacion_sin_acuerdo | MEDIA | Contacto efectivo: negociacion_sin_acuerdo |
| 83 | Ia | 1 | 1 | 0 | 0 | - | hoy | negociacion_sin_acuerdo | MEDIA | Se mencionaron cuotas pero no se concreto acuerdo de pago |
| 84 | Ia | 1 | 0 | 0 | 0 | - | - | contactado_sin_propuesta | MEDIA | Contacto efectivo: contactado_sin_propuesta |
| 85 | Ia | 1 | 1 | 1 | 1 | $830,000 | 5 de agosto | acuerdo_pago | ALTA | Caso critico auditado (atencion especial) |
| 86 | Ia | 0 | 0 | 0 | 0 | - | - | no_contactado | BAJA | Sin contacto efectivo (buzon o audio vacio) |
| 87 | Ia | 1 | 1 | 0 | 0 | - | 8 de julio | negociacion_sin_acuerdo | ALTA | Inconsistencia matematica cuotas vs total |
| 88 | Ia | 1 | 1 | 0 | 0 | - | hoy | negociacion_sin_acuerdo | MEDIA | Se mencionaron cuotas pero no se concreto acuerdo de pago |
| 89 | Ia | 1 | 1 | 0 | 0 | - | 15 de agosto | propuesta_rechazada | ALTA | Inconsistencia matematica cuotas vs total |
| 90 | Ia | 0 | 0 | 0 | 0 | - | - | no_contactado | BAJA | Sin contacto efectivo (buzon o audio vacio) |
| 91 | Ia | 1 | 1 | 0 | 0 | - | hoy | negociacion_sin_acuerdo | MEDIA | Contacto efectivo: negociacion_sin_acuerdo |
| 92 | Ia | 1 | 0 | 0 | 0 | - | - | contactado_sin_propuesta | MEDIA | Contacto efectivo: contactado_sin_propuesta |
| 93 | Ia | 1 | 1 | 0 | 0 | - | 31 | dificultad_sin_acuerdo | MEDIA | Contacto efectivo: dificultad_sin_acuerdo |
| 94 | Ia | 1 | 1 | 0 | 0 | - | hoy | dificultad_sin_acuerdo | MEDIA | Contacto efectivo: dificultad_sin_acuerdo |
| 95 | Ia | 1 | 0 | 0 | 0 | - | - | contactado_sin_propuesta | MEDIA | Contacto efectivo: contactado_sin_propuesta |
| 96 | Ia | 1 | 1 | 0 | 0 | - | 31 de julio | negociacion_sin_acuerdo | MEDIA | Se mencionaron cuotas pero no se concreto acuerdo de pago |
| 97 | Ia | 1 | 1 | 0 | 0 | - | hoy | negociacion_sin_acuerdo | MEDIA | Se mencionaron cuotas pero no se concreto acuerdo de pago |
| 98 | Ia | 1 | 0 | 0 | 0 | - | - | contactado_sin_propuesta | MEDIA | Contacto efectivo: contactado_sin_propuesta |
| 99 | Ia | 1 | 1 | 0 | 1 | $250,000 | 31 de julio | acuerdo_pago | ALTA | Caso critico auditado (atencion especial) |
| 100 | Ia | 1 | 0 | 0 | 0 | - | - | contactado_sin_propuesta | MEDIA | Contacto efectivo: contactado_sin_propuesta |
