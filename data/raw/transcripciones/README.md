# Transcripciones de Llamadas de Cobranza (Datos Raw)

Este directorio contiene las **100 transcripciones textuales de llamadas telefónicas** utilizadas como insumo de entrada (*input data*) para el pipeline de procesamiento de lenguaje natural (NLP) y análisis estadístico comparativo del proyecto.

---

## Estructura del Directorio

```text
data/raw/transcripciones/
├── Humanos/    # 50 transcripciones (.txt) correspondientes a llamadas de agentes humanos (IDs 1–50)
├── IA/         # 50 transcripciones (.txt) correspondientes a llamadas de agentes de IA (IDs 51–100)
└── README.md   # Documentación de origen, gobernanza y anonimización de datos
```

- **Total de archivos:** 100 archivos con extensión `.txt`.
- **Nomenclatura:** Cada archivo está identificado con el identificador único universal (UUID) correspondiente a la grabación original de audio (por ejemplo, `0445c357-e465-49ae-8067-bfa91d11b532.txt`), vinculable de forma biunívoca con la columna `archivo` en `data/processed/dataset_final.csv`.

---

## Estado de Censura y Anonimización

De conformidad con las políticas de privacidad, protección de datos personales (Habeas Data) y gobernanza de información bancaria:

1. **Entidades Financieras y Terceros:** Los nombres de las instituciones originadoras de la deuda han sido suprimidos u omitidos en la transcripción.
2. **Datos de Identificación Personal (PII):** Los nombres y apellidos completos de clientes y asesores han sido censurados con pausas elípticas (`...`), asteriscos (`***`, `****`, `*****`) o retirados durante el procesamiento ASR.
3. **Información de Contacto:** No se registran direcciones físicas ni números telefónicos completos activos. Cualquier dígito residual corresponde a fragmentos locales o sintéticos requeridos exclusivamente para validación de protocolo.
4. **Condiciones Económicas:** Las menciones de valores monetarios, plazos de cuotas y fechas de pago son preservadas íntegramente dado que constituyen la materia prima analítica para la evaluación del desempeño de cobranza.

---

## Rol en el Pipeline

Las transcripciones contenidas en esta carpeta alimentan de manera determinística y reproducible los siguientes scripts:
- `scripts/02_limpiar.py`: Normalización de texto, remoción de diacríticos y filtrado de anomalías acústicas.
- `scripts/03_extraer_variables.py`: Ejecución de motores de reglas NLP contextuales (polaridad, ventanas de negación, extracción financiera y clasificación de diálogo).
