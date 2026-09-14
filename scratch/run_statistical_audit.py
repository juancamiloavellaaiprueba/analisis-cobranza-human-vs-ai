import pandas as pd
import numpy as np
import math

df = pd.read_csv("data/processed/dataset_final.csv")
h = df[df["tipo_agente"] == "humano"]
ia = df[df["tipo_agente"] == "ia"]

def p_fisher_2x2(a, b, c, d):
    r1, r2 = a + b, c + d
    c1, c2 = a + c, b + d
    n = r1 + r2
    if n == 0 or r1 == 0 or r2 == 0 or c1 == 0 or c2 == 0:
        return 1.0
    def p_hyp(k):
        try:
            return (math.comb(r1, k) * math.comb(r2, c1 - k)) / math.comb(n, c1)
        except:
            return 0.0
    k_min = max(0, r1 - c2)
    k_max = min(r1, c1)
    p_obs = p_hyp(a)
    return float(min(1.0, sum(p_hyp(k) for k in range(k_min, k_max + 1) if p_hyp(k) <= p_obs + 1e-12)))

def chi2_yates(a, b, c, d):
    r1, r2 = a + b, c + d
    c1, c2 = a + c, b + d
    n = r1 + r2
    e11 = (r1 * c1) / n
    e12 = (r1 * c2) / n
    e21 = (r2 * c1) / n
    e22 = (r2 * c2) / n
    esperados = [e11, e12, e21, e22]
    if any(e == 0 for e in esperados): return 0.0, 1.0, esperados
    chi2 = (
        ((abs(a - e11) - 0.5) ** 2) / e11 +
        ((abs(b - e12) - 0.5) ** 2) / e12 +
        ((abs(c - e21) - 0.5) ** 2) / e21 +
        ((abs(d - e22) - 0.5) ** 2) / e22
    )
    p_val = 2.0 * (1.0 - 0.5 * (1.0 + math.erf(math.sqrt(max(0.0, chi2)) / math.sqrt(2.0))))
    return float(chi2), float(min(1.0, max(0.0001, p_val))), esperados

def mann_whitney(s1, s2):
    x1 = s1.dropna().values
    x2 = s2.dropna().values
    n1, n2 = len(x1), len(x2)
    if n1 == 0 or n2 == 0: return np.nan, 1.0, 0.0
    todos = np.concatenate([x1, x2])
    orden = np.argsort(todos)
    rangos = np.empty_like(orden, dtype=float)
    i = 0
    while i < len(todos):
        j = i
        while j < len(todos) - 1 and todos[orden[j]] == todos[orden[j + 1]]:
            j += 1
        rango_prom = (i + j + 2.0) / 2.0
        for k in range(i, j + 1):
            rangos[orden[k]] = rango_prom
        i = j + 1
    r1 = rangos[:n1].sum()
    u1 = n1 * n2 + (n1 * (n1 + 1)) / 2.0 - r1
    u2 = n1 * n2 - u1
    u = min(u1, u2)
    mu_u = (n1 * n2) / 2.0
    sigma_u = math.sqrt((n1 * n2 * (n1 + n2 + 1)) / 12.0)
    z = (abs(u - mu_u) - 0.5) / sigma_u
    p_val = 2.0 * (1.0 - 0.5 * (1.0 + math.erf(abs(z) / math.sqrt(2.0))))
    # Rank biserial correlation
    r_biserial = 1.0 - (2.0 * u1) / (n1 * n2)
    return float(u), float(min(1.0, max(0.0001, p_val))), float(r_biserial)

def ic_95_prop(p1, n1, p2, n2):
    dif = p1 - p2
    se = math.sqrt((p1 * (1.0 - p1) / n1) + (p2 * (1.0 - p2) / n2))
    return (dif - 1.96 * se) * 100, (dif + 1.96 * se) * 100

def cohen_h(p1, p2):
    phi1 = 2 * math.asin(math.sqrt(p1))
    phi2 = 2 * math.asin(math.sqrt(p2))
    return abs(phi1 - phi2)

binary_tests = [
    ("contactabilidad", "Contactabilidad"),
    ("oferta_pago", "Oferta de pago"),
    ("negociacion", "Negociacion"),
    ("acuerdo_pago", "Acuerdo de pago formal"),
    ("tiene_objecion", "Tiene objecion"),
    ("intencion_pago", "Intencion de pago"),
    ("dificultad_pago", "Dificultad de pago"),
    ("tiene_descuento", "Tiene descuento"),
    ("inconsistencia_matematica_acuerdo", "Inconsistencia matematica"),
]

results = []
for col, label in binary_tests:
    a = int(h[col].sum())
    b = 50 - a
    c = int(ia[col].sum())
    d = 50 - c
    p1, p2 = a / 50.0, c / 50.0
    dif = (p1 - p2) * 100
    ic_low, ic_high = ic_95_prop(p1, 50, p2, 50)
    ch2, p_ch2, exp = chi2_yates(a, b, c, d)
    min_exp = min(exp)
    p_fsh = p_fisher_2x2(a, b, c, d)
    h_stat = cohen_h(p1, p2)
    
    # Selection rule
    test_used = "Fisher" if min_exp < 5 else "Chi2 Yates"
    p_selected = p_fsh if test_used == "Fisher" else p_ch2
    
    results.append({
        "col": col, "label": label, "type": "binaria",
        "h_prop": f"{p1*100:.1f}% ({a}/50)", "ia_prop": f"{p2*100:.1f}% ({c}/50)",
        "dif": f"{dif:+.1f}%", "ic95": f"[{ic_low:.1f}%, {ic_high:.1f}%]",
        "test": test_used, "min_exp": f"{min_exp:.1f}",
        "p_val": p_selected, "effect_size": f"Cohen's h={h_stat:.3f}"
    })

num_tests = [
    ("duracion_segundos", "Duracion (s)"),
    ("num_palabras", "Numero de palabras"),
    ("num_propuestas_pago", "Numero de propuestas"),
    ("num_preguntas_agente", "Preguntas del agente"),
]

for col, label in num_tests:
    s_h = h[col].dropna()
    s_ia = ia[col].dropna()
    u, p_val, r_bis = mann_whitney(s_h, s_ia)
    results.append({
        "col": col, "label": label, "type": "numerica",
        "h_prop": f"Med={s_h.mean():.1f}, Mdn={s_h.median():.1f}",
        "ia_prop": f"Med={s_ia.mean():.1f}, Mdn={s_ia.median():.1f}",
        "dif": f"Mdn dif: {s_h.median() - s_ia.median():.1f}",
        "ic95": "-",
        "test": "Mann-Whitney U", "min_exp": "-",
        "p_val": p_val, "effect_size": f"Rank-biserial r={r_bis:.3f}"
    })

res_df = pd.DataFrame(results)

# Benjamini-Hochberg FDR
res_df = res_df.sort_values("p_val").reset_index(drop=True)
m = len(res_df)
alpha = 0.05
res_df["fdr_threshold"] = [(i + 1) / m * alpha for i in range(m)]
res_df["sig_raw"] = res_df["p_val"] < alpha
res_df["sig_fdr"] = res_df["p_val"] <= res_df["fdr_threshold"]

# Cumulative FDR adjustment
p_vals = res_df["p_val"].tolist()
adj_p = []
for i in range(m):
    adj_p.append(min(1.0, p_vals[i] * m / (i + 1)))
for i in range(m - 2, -1, -1):
    adj_p[i] = min(adj_p[i], adj_p[i + 1])
res_df["p_adj_bh"] = adj_p
res_df["sig_bh"] = res_df["p_adj_bh"] < 0.05

with open("scratch/audit_statistical_tests.txt", "w", encoding="utf-8") as f:
    f.write(res_df.to_string())

print("Saved statistical analysis to scratch/audit_statistical_tests.txt")
