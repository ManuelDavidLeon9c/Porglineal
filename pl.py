# 1. IMPORTACIÓN DE LIBRERÍAS
import numpy as np
from scipy.optimize import minimize  # Función principal para resolver problemas de optimización no lineal

# 2. DEFINICIÓN DE LA FUNCIÓN OBJETIVO (El motor de valor que queremos minimizar)
def costo_total_operativo(x):
    # Extraemos las variables de decisión del vector 'x'
    x1 = x[0]  # x1: Cantidad de servidores de Backend / CPU
    x2 = x[1]  # x2: Cantidad de servidores de Caché / CDN
    
    # Costo lineal: Alquiler mensual fijo por cada servidor activo
    costo_infraestructura = 120 * x1 + 80 * x2
    
    # Costo no lineal: Penalización económica por latencia y cuellos de botella.
    # Al estar x1 y x2 dividiendo, se crea una curva: los primeros servidores reducen 
    # drásticamente la latencia, pero cada servidor extra aporta un beneficio menor (rendimientos decrecientes).
    penalizacion_latencia = (15000 / x1) + (8000 / x2) + (5000 / (x1 * x2))
    
    # Retornamos la suma total que el algoritmo intentará reducir al mínimo posible
    return costo_infraestructura + penalizacion_latencia

# 3. DEFINICIÓN DE LAS RESTRICCIONES (La región factible del sistema)
# Nota: En scipy.optimize, todas las desigualdades ('ineq') se escriben asumiendo que la fórmula es >= 0.

# Restricción 1: No superar el presupuesto de alquiler fijo de $4,500 USD
# Matemáticamente: 120*x1 + 80*x2 <= 4500  ---> Pasando a restar: 4500 - (120*x1 + 80*x2) >= 0
def restriccion_presupuesto(x):
    return 4500 - (120 * x[0] + 80 * x[1])

# Restricción 2: Tener al menos 15 servidores en total en el clúster por políticas de redundancia
# Matemáticamente: x1 + x2 >= 15  --->  x1 + x2 - 15 >= 0
def restriccion_minimo_nodos(x):
    return x[0] + x[1] - 15

# Empaquetamos las restricciones en una lista de diccionarios para que Scipy las entienda
restricciones = [
    {'type': 'ineq', 'fun': restriccion_presupuesto},
    {'type': 'ineq', 'fun': restriccion_minimo_nodos}
]

# 4. LÍMITES DE LAS VARIABLES (Condiciones de no negatividad y límites físicos)
# Ponemos un mínimo de 1 servidor de cada tipo (para evitar división por cero y caídas del servicio) y máximo 100
limites = [(1, 100), (1, 100)]

# 5. PUNTO DE PARTIDA (Semilla inicial para el algoritmo iterativo)
# Como la PNL navega por superficies curvas, necesita un punto inicial (x1=5, x2=5) desde donde empezar a descender
punto_inicial = [5.0, 5.0]

# 6. EJECUCIÓN DEL SOLUCIONADOR (Optimización)
# Usamos el método 'SLSQP' (Sequential Least Squares Programming), que utiliza gradientes e internamente
# evalúa las condiciones Karush-Kuhn-Tucker (KKT) para hallar el óptimo respetando restricciones.
resultado = minimize(
    fun=costo_total_operativo,  # Función a minimizar
    x0=punto_inicial,           # Punto de inicio
    method='SLSQP',             # Algoritmo matemático de resolución no lineal
    bounds=limites,             # Límites de x1 y x2
    constraints=restricciones   # Lista de restricciones del problema
)

# 7. IMPRESIÓN E INTERPRETACIÓN DE RESULTADOS
print("=== RESULTADOS DE LA OPTIMIZACIÓN DE INFRAESTRUCTURA ===")
print(f"¿Se encontró una solución óptima?: {resultado.success}")
print(f"Estado del motor matemático: {resultado.message}\n")

# Extraemos los valores óptimos encontrados
opt_x1 = resultado.x[0]
opt_x2 = resultado.x[1]
costo_minimo = resultado.fun

print(f"Servidores Backend (x1) óptimos: {opt_x1:.2f} (Aprox. {round(opt_x1)} nodos)")
print(f"Servidores Caché (x2) óptimos:   {opt_x2:.2f} (Aprox. {round(opt_x2)} nodos)")
print(f"Costo Total Operativo Mínimo:    ${costo_minimo:.2f} USD/mes\n")

# Verificación de cómo quedaron los recursos (Holguras)
gasto_alquiler = 120 * opt_x1 + 80 * opt_x2
perdida_latencia = costo_minimo - gasto_alquiler
print("--- Desglose Financiero en el Punto Óptimo ---")
print(f"Gasto directo en servidores:     ${gasto_alquiler:.2f} USD (Presupuesto máx: $4500 USD)")
print(f"Penalización residual latencia:  ${perdida_latencia:.2f} USD")
print(f"Total de servidores activos:     {opt_x1 + opt_x2:.2f} nodos (Mínimo exigido: 15)")