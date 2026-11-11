# ==============================================================================
# PROYECTO FINAL INVESTIGACIÓN DE OPERACIONES - INGENIERÍA DE SISTEMAS
# TEMA 1: PROGRAMACIÓN NO LINEAL (OPTIMIZACIÓN DE INFRAESTRUCTURA CLOUD)
# Archivo: pl.py (Versión Dinámica con Ingreso de Datos y Gráficas Integradas)
# ==============================================================================

import numpy as np
from scipy.optimize import minimize
import matplotlib.pyplot as plt
from matplotlib import cm

def pedir_float(mensaje, defecto):
    entrada = input(f"{mensaje} [Por defecto: {defecto}]: ").strip()
    if entrada == "":
        return float(defecto)
    try:
        val = float(entrada)
        return val if val > 0 else float(defecto)
    except ValueError:
        print(f"  -> Valor no válido. Se usará el valor por defecto ({defecto}).")
        return float(defecto)

# 1. INGRESO DINÁMICO DE DATOS AL INICIO
print("=" * 75)
print(" CONFIGURACIÓN INICIAL - MODELO DE PROGRAMACIÓN NO LINEAL (INFRAESTRUCTURA)")
print("=" * 75)
print("Ingrese los parámetros del problema (o presione ENTER para usar el valor sugerido):")

costo_x1 = pedir_float("1. Costo mensual por servidor Backend/CPU (x1) en USD", 120.0)
costo_x2 = pedir_float("2. Costo mensual por servidor Caché/CDN (x2) en USD", 80.0)
pen_x1 = pedir_float("3. Factor de penalización por latencia de Backend", 15000.0)
pen_x2 = pedir_float("4. Factor de penalización por latencia de Caché", 8000.0)
pen_interaccion = pedir_float("5. Factor de penalización por cuello de botella conjunto (x1*x2)", 5000.0)
presupuesto_max = pedir_float("6. Presupuesto máximo mensual para alquiler fijo en USD", 4500.0)
minimo_nodos = pedir_float("7. Cantidad mínima total de servidores activos (Redundancia)", 15.0)

# 2. DEFINICIÓN DE LA FUNCIÓN OBJETIVO NO LINEAL
def costo_total_operativo(x):
    x1, x2 = x[0], x[1]
    costo_infraestructura = (costo_x1 * x1) + (costo_x2 * x2)
    penalizacion_latencia = (pen_x1 / x1) + (pen_x2 / x2) + (pen_interaccion / (x1 * x2))
    return costo_infraestructura + penalizacion_latencia

# 3. DEFINICIÓN DE LAS RESTRICCIONES (En Scipy 'ineq' significa >= 0)
def restriccion_presupuesto(x):
    return presupuesto_max - (costo_x1 * x[0] + costo_x2 * x[1])

def restriccion_minimo_nodos(x):
    return (x[0] + x[1]) - minimo_nodos

restricciones = [
    {'type': 'ineq', 'fun': restriccion_presupuesto},
    {'type': 'ineq', 'fun': restriccion_minimo_nodos}
]

# 4. LÍMITES Y PUNTO INICIAL
limites = [(1.0, 200.0), (1.0, 200.0)]
punto_inicial = [max(2.0, minimo_nodos / 2.0), max(2.0, minimo_nodos / 2.0)]

# 5. EJECUCIÓN DEL SOLUCIONADOR (SLSQP)
resultado = minimize(
    fun=costo_total_operativo,
    x0=punto_inicial,
    method='SLSQP',
    bounds=limites,
    constraints=restricciones
)

# 6. GENERACIÓN DE INFORMACIÓN Y RESULTADOS FINALES
opt_x1 = resultado.x[0]
opt_x2 = resultado.x[1]
costo_minimo = resultado.fun
gasto_alquiler = (costo_x1 * opt_x1) + (costo_x2 * opt_x2)
perdida_latencia = costo_minimo - gasto_alquiler
holgura_presupuesto = presupuesto_max - gasto_alquiler
holgura_nodos = (opt_x1 + opt_x2) - minimo_nodos

print("" + "=" * 75)
print(" INFORME FINAL DE OPTIMIZACIÓN NO LINEAL (RESULTADOS)")
print("=" * 75)
print(f"¿Se encontró una solución óptima?: {'SÍ' if resultado.success else 'NO'}")
print(f"Estado del motor matemático:       {resultado.message}")

print("--- Variables de Decisión Óptimas ---")
print(f"-> Servidores Backend (x1) óptimos: {opt_x1:.2f} (Aprox. {round(opt_x1)} nodos)")
print(f"-> Servidores Caché (x2) óptimos:   {opt_x2:.2f} (Aprox. {round(opt_x2)} nodos)")
print(f"-> Total de servidores en clúster:  {opt_x1 + opt_x2:.2f} nodos (Mínimo exigido: {minimo_nodos:.0f})")

print("--- Desglose Financiero en el Punto Óptimo ---")
print(f"-> Gasto fijo en alquiler cloud:    ${gasto_alquiler:,.2f} USD/mes (Presupuesto máx: ${presupuesto_max:,.2f} USD)")
print(f"-> Penalización residual latencia:  ${perdida_latencia:,.2f} USD/mes")
print(f"-> COSTO TOTAL OPERATIVO MÍNIMO:    ${costo_minimo:,.2f} USD/mes")

print("--- Análisis de Restricciones (Condiciones KKT) ---")
print(f"-> Holgura de Presupuesto:          ${holgura_presupuesto:,.2f} USD disponibles")
print(f"-> Excedente sobre mínimo de nodos: {holgura_nodos:.2f} nodos adicionales")
print("=" * 75)

# 7. GENERACIÓN DINÁMICA DE GRÁFICAS 3D Y 2D
max_eje = max(30, int(max(opt_x1, opt_x2) * 2.2))
rango_x1 = np.linspace(2, max_eje, 100)
rango_x2 = np.linspace(2, max_eje, 100)
X1, X2 = np.meshgrid(rango_x1, rango_x2)

Z = (costo_x1 * X1 + costo_x2 * X2) + (pen_x1 / X1) + (pen_x2 / X2) + (pen_interaccion / (X1 * X2))

fig = plt.figure(figsize=(14, 6))

# Subgráfico 1: Superficie 3D
ax1 = fig.add_subplot(1, 2, 1, projection='3d')
ax1.plot_surface(X1, X2, Z, cmap=cm.viridis, alpha=0.8, edgecolor='none')
ax1.scatter(opt_x1, opt_x2, costo_minimo, color='red', s=150, marker='*', label='Mínimo Global (Óptimo)')
ax1.set_title('Superficie 3D de Costos Operativos')
ax1.set_xlabel('Nodos Backend (x1)')
ax1.set_ylabel('Nodos Caché (x2)')
ax1.set_zlabel('Costo Total ($ USD)')
ax1.legend()

# Subgráfico 2: Curvas de Nivel y Región Factible
ax2 = fig.add_subplot(1, 2, 2)
curvas = ax2.contourf(X1, X2, Z, levels=30, cmap=cm.viridis, alpha=0.7)
fig.colorbar(curvas, ax=ax2, label='Costo Total ($ USD)')

x2_presupuesto = (presupuesto_max - costo_x1 * rango_x1) / costo_x2
ax2.plot(rango_x1, x2_presupuesto, 'r--', linewidth=2, label=f'Límite Presupuesto (${presupuesto_max:.0f})')

x2_minimo = minimo_nodos - rango_x1
ax2.plot(rango_x1, x2_minimo, 'w--', linewidth=2, label=f'Mínimo Nodos ({minimo_nodos:.0f})')

ax2.scatter(opt_x1, opt_x2, color='red', s=150, marker='*', zorder=5, label=f'Óptimo ({opt_x1:.1f}, {opt_x2:.1f})')
ax2.set_xlim(2, max_eje)
ax2.set_ylim(2, max_eje)
ax2.set_title('Curvas de Nivel y Región Factible')
ax2.set_xlabel('Nodos Backend (x1)')
ax2.set_ylabel('Nodos Caché (x2)')
ax2.legend(loc='upper right')

plt.tight_layout()
plt.savefig('optimizacion_pnl_servidores.png', dpi=300)
print("[INFO] Gráfica guardada como 'optimizacion_pnl_servidores.png'. Mostrando en pantalla...")
plt.show()
