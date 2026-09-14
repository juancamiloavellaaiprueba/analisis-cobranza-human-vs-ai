import math
import numpy as np

p1 = 0.14
p2 = 0.04
alpha = 0.05
power_target = 0.80
n_current = 50

# 1. Normal approximation without continuity correction
# Pooled under H0, unpooled under H1
z_alpha = 1.959963984540054  # two-sided alpha=0.05
z_beta = 0.8416212335729143   # power=0.80

p_bar = (p1 + p2) / 2.0
q_bar = 1.0 - p_bar
p1_q1 = p1 * (1.0 - p1)
p2_q2 = p2 * (1.0 - p2)

delta = abs(p1 - p2)

# Formula (pooled H0, unpooled H1)
term1 = z_alpha * math.sqrt(2.0 * p_bar * q_bar)
term2 = z_beta * math.sqrt(p1_q1 + p2_q2)
n_normal = ((term1 + term2) ** 2) / (delta ** 2)

# Unpooled formula
se_unpooled = math.sqrt(p1_q1 + p2_q2)
n_unpooled = (((z_alpha + z_beta) ** 2) * (p1_q1 + p2_q2)) / (delta ** 2)

# Fleiss continuity correction formula:
# n_cc = (n / 4) * (1 + sqrt(1 + 2 / (n * delta)))^2
n_fleiss = (n_normal / 4.0) * ((1.0 + math.sqrt(1.0 + 2.0 / (n_normal * delta))) ** 2)

# Casagrande, Pike and Smith (1978) formula:
n_cps = n_normal * (1.0 + math.sqrt(1.0 + 4.0 / (n_normal * delta))) ** 2 / 4.0

# Power calculation with n = 50 per group under normal approximation
# z_b = (delta * sqrt(n) - z_alpha * sqrt(2 * p_bar * q_bar)) / sqrt(p1_q1 + p2_q2)
z_b_50 = (delta * math.sqrt(n_current) - z_alpha * math.sqrt(2.0 * p_bar * q_bar)) / math.sqrt(p1_q1 + p2_q2)
power_normal_50 = 0.5 * (1.0 + math.erf(z_b_50 / math.sqrt(2.0)))

# Power under unpooled approximation
z_b_unpooled_50 = (delta - z_alpha * math.sqrt((p1_q1 + p2_q2) / n_current)) / math.sqrt((p1_q1 + p2_q2) / n_current)
power_unpooled_50 = 0.5 * (1.0 + math.erf(z_b_unpooled_50 / math.sqrt(2.0)))

# Exact binomial / Fisher power calculation
def exact_fisher_power(n1, n2, p1, p2, alpha=0.05):
    # Enumerate all (x1, x2) combinations under Binomial(n1, p1) and Binomial(n2, p2)
    # Check if two-sided Fisher test p <= alpha
    from math import comb
    
    # Precompute hypergeometric distribution for all possible margins
    rejection_count = 0.0
    for x1 in range(n1 + 1):
        prob_x1 = comb(n1, x1) * (p1 ** x1) * ((1 - p1) ** (n1 - x1))
        for x2 in range(n2 + 1):
            prob_x2 = comb(n2, x2) * (p2 ** x2) * ((1 - p2) ** (n2 - x2))
            prob_joint = prob_x1 * prob_x2
            
            # Fisher exact two-sided test for table [[x1, n1-x1], [x2, n2-x2]]
            # Margin r1 = n1, r2 = n2, c1 = x1 + x2, c2 = n1 + n2 - c1
            r1, r2 = n1, n2
            c1, c2 = x1 + x2, n1 + n2 - (x1 + x2)
            n_tot = r1 + r2
            
            # P-value of observed table
            def p_hyper(k):
                try:
                    return (comb(r1, k) * comb(r2, c1 - k)) / comb(n_tot, c1)
                except:
                    return 0.0
            
            k_min = max(0, r1 - c2)
            k_max = min(r1, c1)
            p_obs = p_hyper(x1)
            p_val = sum(p_hyper(k) for k in range(k_min, k_max + 1) if p_hyper(k) <= p_obs + 1e-12)
            
            if p_val <= alpha:
                rejection_count += prob_joint
                
    return rejection_count

power_exact_50 = exact_fisher_power(50, 50, p1, p2, alpha=0.05)

print("=== RESULTADOS DE POTENCIA Y TAMAÑO MUESTRAL ===")
print(f"Parámetros: p1 = {p1}, p2 = {p2}, delta = {delta}, alpha = {alpha} (two-sided), target power = {power_target}")
print(f"1. Normal estándar (Pooled H0 / Unpooled H1): n = {n_normal:.2f} (~{math.ceil(n_normal)} por grupo)")
print(f"2. Normal no agrupada (Unpooled): n = {n_unpooled:.2f} (~{math.ceil(n_unpooled)} por grupo)")
print(f"3. Con corrección por continuidad (Fleiss): n = {n_fleiss:.2f} (~{math.ceil(n_fleiss)} por grupo)")
print(f"4. Con corrección por continuidad (Casagrande-Pike-Smith): n = {n_cps:.2f} (~{math.ceil(n_cps)} por grupo)")
print(f"\nPotencia con n = 50 por grupo:")
print(f"- Aproximación normal (Pooled/Unpooled): {power_normal_50*100:.2f}%")
print(f"- Aproximación normal (Unpooled z): {power_unpooled_50*100:.2f}%")
print(f"- Exacta de Fisher (Binomial exacta): {power_exact_50*100:.2f}%")
