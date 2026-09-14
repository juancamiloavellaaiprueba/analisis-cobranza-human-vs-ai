import sys
sys.path.insert(0, ".")
from src.payment_extraction import parsear_monto, extraer_cuotas
import numpy as np

print("dos:", parsear_monto("dos"))
print("dos mil pesos:", parsear_monto("dos mil pesos"))
print("$2.000:", parsear_monto("$2.000"))
print("15 cuotas:", parsear_monto("15 cuotas"))
print("dos cuotas de 300 mil:", extraer_cuotas("dos cuotas de 300 mil"))
