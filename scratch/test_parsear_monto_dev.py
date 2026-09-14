import re
import numpy as np

NUMEROS_ESCRITOS = {
    'un': 1, 'uno': 1, 'dos': 2, 'tres': 3, 'cuatro': 4, 'cinco': 5,
    'seis': 6, 'siete': 7, 'ocho': 8, 'nueve': 9, 'diez': 10,
    'once': 11, 'doce': 12, 'veinte': 20, 'veinticuatro': 24,
    'treinta': 30, 'cincuenta': 50, 'cien': 100, 'ciento': 100,
    'doscientos': 200, 'trescientos': 300, 'quinientos': 500
}

def parsear_monto_test(texto_monto):
    if texto_monto is None or not str(texto_monto).strip():
        return np.nan
    t = str(texto_monto).strip().lower()
    if t in ['n/a', '-', 'ninguno', 'no aplica', 'nan', 'null']:
        return np.nan

    # Excluir cuotas aisladas
    if re.search(r'^\s*\d+\s+cuotas?\s*$', t):
        return np.nan

    # Evidencia monetaria requerida
    tiene_evidencia_monetaria = bool(
        re.search(r'[\$]|mil|millon|pesos|cop\b', t) or
        re.search(r'\b\d{1,3}(?:\.\d{3})+\b', t) or
        re.search(r'\b\d{4,}\b', t)
    )
    if not tiene_evidencia_monetaria:
        return np.nan

    # 1. Millones con posible resto en miles (ej. 2 millones 110 mil)
    patron_millon_compuesto = (
        r"(\d+|" + "|".join(NUMEROS_ESCRITOS.keys()) + r")\s+millones?(?:\s+(?:de\s+)?(\d+|" +
        "|".join(NUMEROS_ESCRITOS.keys()) + r")\s*mil)?"
    )
    m_millon = re.search(patron_millon_compuesto, t)
    if m_millon:
        n1_str = m_millon.group(1).replace(',', '.')
        val_millon = float(n1_str) if n1_str.replace('.', '').isdigit() else float(NUMEROS_ESCRITOS.get(n1_str, np.nan))
        resto_miles = 0.0
        if m_millon.group(2):
            n2_str = m_millon.group(2).replace(',', '.')
            resto_miles = float(n2_str) if n2_str.replace('.', '').isdigit() else float(NUMEROS_ESCRITOS.get(n2_str, 0.0))
        if not np.isnan(val_millon):
            return val_millon * 1_000_000.0 + resto_miles * 1_000.0

    # 2. Miles (ej. 500 mil, dos mil pesos, 200 mil)
    patron_mil = r"(\d+|" + "|".join(NUMEROS_ESCRITOS.keys()) + r")\s*mil(?:\s+(\d+))?"
    m_mil = re.search(patron_mil, t)
    if m_mil:
        num_str = m_mil.group(1).replace(',', '.')
        val = float(num_str) if num_str.replace('.', '').isdigit() else float(NUMEROS_ESCRITOS.get(num_str, np.nan))
        if not np.isnan(val):
            resto = float(m_mil.group(2)) if m_mil.group(2) and m_mil.group(2).isdigit() else 0.0
            return val * 1_000.0 + resto

    # 3. Numérico directo con $ o formato 500.000 o >= 1000
    m_num = re.search(r"[$]?\s*([\d]{1,3}(?:[\.,][\d]{3})+|[\d]{4,})", t)
    if m_num:
        cadena = m_num.group(1).replace('$', '').replace(' ', '')
        if cadena.count('.') > 1 or (cadena.count('.') == 1 and len(cadena.split('.')[1]) == 3):
            cadena = cadena.replace('.', '')
        cadena = cadena.replace(',', '.')
        try:
            val = float(cadena)
            if val >= 1000.0:
                return val
        except ValueError:
            pass

    return np.nan

tests = [
    ('dos', np.nan),
    ('tres', np.nan),
    ('cuatro', np.nan),
    ('uno', np.nan),
    ('a dos', np.nan),
    ('por dos', np.nan),
    ('dos y eso', np.nan),
    ('tengo dos problemas', np.nan),
    ('15 cuotas', np.nan),
    ('dos mil pesos', 2000.0),
    ('$2.000', 2000.0),
    ('2.000 pesos', 2000.0),
    ('2000 pesos', 2000.0),
    ('doscientos mil', 200000.0),
    ('$200.000', 200000.0),
    ('una cuota de 200 mil', 200000.0),
    ('pagaria 300 mil', 300000.0),
    ('2 millones 110 mil', 2110000.0),
    ('2 millones 600 mil pesos', 2600000.0),
    ('10 millones', 10000000.0),
    ('500 mil', 500000.0),
    ('$500.000', 500000.0)
]

all_passed = True
for inp, exp in tests:
    res = parsear_monto_test(inp)
    ok = (np.isnan(res) and np.isnan(exp)) or (res == exp)
    if not ok:
        print(f'FAIL: {repr(inp)} -> got {res}, expected {exp}')
        all_passed = False
    else:
        print(f'OK: {repr(inp)} -> {res}')
print('All passed:', all_passed)
