# ==============================================================================
# PROYECTO FINAL INVESTIGACIÓN DE OPERACIONES - INGENIERÍA DE SISTEMAS
# TEMA 2: LÍNEAS DE ESPERA M/M/s + SIMULACIÓN SIMPY (APLICATIVO DE IA)
# Archivo: le.py (Versión Dinámica con Ingreso de Datos por Consola)
# ==============================================================================

import simpy
import math
import random
import numpy as np
import matplotlib.pyplot as plt

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

def pedir_int(mensaje, defecto):
    entrada = input(f"{mensaje} [Por defecto: {defecto}]: ").strip()
    if entrada == "":
        return int(defecto)
    try:
        val = int(entrada)
        return val if val > 0 else int(defecto)
    except ValueError:
        print(f"  -> Valor no válido. Se usará el valor por defecto ({defecto}).")
        return int(defecto)

# 1. INGRESO DINÁMICO DE DATOS AL INICIO
print("=" * 80)
print(" CONFIGURACIÓN INICIAL - MODELO DE LÍNEAS DE ESPERA M/M/s (SISTEMA DE IA)")
print("=" * 80)
print("Ingrese los parámetros del tráfico de IA (o presione ENTER para usar el valor sugerido):
")

LAMBDA_CORREOS = pedir_float("1. Tasa de llegada (lambda - solicitudes/correos por minuto)", 100.0)
MU_SERVIDOR = pedir_float("2. Tasa de servicio por servidor (mu - correos por minuto por nodo)", 25.0)
LIMITE_SLA_SEG = pedir_float("3. Tiempo máximo de respuesta permitido por SLA (Ws en segundos)", 3.0)

# Calculamos el mínimo de servidores necesarios para que el sistema sea estable (rho < 1)
nodos_minimos_estables = int(math.floor(LAMBDA_CORREOS / MU_SERVIDOR)) + 1
print(f"
[INFO] Para evitar colapso (utilización >= 100%), el sistema requiere mínimo {nodos_minimos_estables} servidores.")

CANTIDAD_ESCENARIOS = pedir_int("4. ¿Cuántos escenarios consecutivos de servidores desea evaluar?", 6)
TIEMPO_SIMULACION = pedir_int("5. Tiempo de simulación en SimPy (segundos virtuales)", 20000)

# ==============================================================================
# PARTE A: FÓRMULAS MATEMÁTICAS EXACTAS DEL MODELO MULTICANAL M/M/s
# ==============================================================================
def modelo_matematico_mms(lmbda, mu, s):
    r = lmbda / mu
    rho = r / s
    if rho >= 1.0:
        return None
    
    sumatoria = sum([(r ** n) / math.factorial(n) for n in range(s)])
    ultimo_termino = ((r ** s) / math.factorial(s)) * (1.0 / (1.0 - rho))
    P0 = 1.0 / (sumatoria + ultimo_termino)
    
    Lq = (P0 * (r ** s) * rho) / (math.factorial(s) * ((1.0 - rho) ** 2))
    Wq_seg = (Lq / lmbda) * 60.0
    Ws_seg = Wq_seg + ((1.0 / mu) * 60.0)
    
    return {'s': s, 'rho': rho * 100, 'P0': P0, 'Lq': Lq, 'Wq_seg': Wq_seg, 'Ws_seg': Ws_seg}

# ==============================================================================
# PARTE B: SIMULACIÓN EN TIEMPO REAL CON LA LIBRERÍA SIMPY
# ==============================================================================
def procesar_correo_ia(env, servidor_gcp, mu, lista_tiempos_totales):
    llegada = env.now
    with servidor_gcp.request() as peticion:
        yield peticion
        tiempo_procesamiento = random.expovariate(mu / 60.0)
        yield env.timeout(tiempo_procesamiento)
        salida = env.now
        lista_tiempos_totales.append(salida - llegada)

def generador_trafico_correos(env, s, lmbda, mu, lista_tiempos):
    cluster_gcp = simpy.Resource(env, capacity=s)
    while True:
        tiempo_entre_llegadas = random.expovariate(lmbda / 60.0)
        yield env.timeout(tiempo_entre_llegadas)
        env.process(procesar_correo_ia(env, cluster_gcp, mu, lista_tiempos))

def ejecutar_simulacion_simpy(s, lmbda, mu, tiempo_simulacion_seg):
    random.seed(42)
    env = simpy.Environment()
    tiempos_respuesta = []
    env.process(generador_trafico_correos(env, s, lmbda, mu, tiempos_respuesta))
    env.run(until=tiempo_simulacion_seg)
    return np.mean(tiempos_respuesta) if tiempos_respuesta else 0.0

# ==============================================================================
# 3. EJECUCIÓN Y GENERACIÓN DEL INFORME FINAL
# ==============================================================================
resultados = []
rango_nodos = range(nodos_minimos_estables, nodos_minimos_estables + CANTIDAD_ESCENARIOS)
tiempo_base_seg = (1.0 / MU_SERVIDOR) * 60.0

print("
" + "=" * 118)
print(" INFORME FINAL: TEORÍA DE COLAS (M/M/s) + SIMULACIÓN ESTOCÁSTICA SIMPY")
print("=" * 118)
print(f"Tasa llegada (lambda): {LAMBDA_CORREOS} solicitudes/min | Tasa servicio (mu): {MU_SERVIDOR} solicitudes/min ({tiempo_base_seg:.2f}s base)")
print(f"Meta SLA: Tiempo de respuesta total (Ws) <= {LIMITE_SLA_SEG} segundos
")
print(f"{'Nodos(s)':<9} | {'Uso Cloud(%)':<13} | {'Po (Vacío)':<11} | {'Cola (Lq)':<10} | {'Espera Wq(s)':<13} | {'Total Teórico Ws':<17} | {'Total SimPy Ws':<15} | {'¿Cumple SLA?'}")
print("-" * 118)

for s in rango_nodos:
    metricas = modelo_matematico_mms(LAMBDA_CORREOS, MU_SERVIDOR, s)
    ws_simulado = ejecutar_simulacion_simpy(s, LAMBDA_CORREOS, MU_SERVIDOR, TIEMPO_SIMULACION)
    metricas['Ws_simpy'] = ws_simulado
    
    cumple = "SÍ CUMPLE" if metricas['Ws_seg'] <= LIMITE_SLA_SEG else "NO (Lento)"
    resultados.append(metricas)
    
    print(f"{s:<9} | {metricas['rho']:>11.1f}% | {metricas['P0']:>10.4f} | {metricas['Lq']:>9.2f} | {metricas['Wq_seg']:>11.2f} s | {metricas['Ws_seg']:>15.2f} s | {ws_simulado:>13.2f} s | {cumple}")

cumplen_sla = [r for r in resultados if r['Ws_seg'] <= LIMITE_SLA_SEG]

print("
=== CONCLUSIÓN TÉCNICA AUTOMÁTICA ===")
print(f"-> Con la capacidad mínima estable ({nodos_minimos_estables} nodos), la respuesta total tarda {resultados[0]['Ws_seg']:.2f} segundos.")
if cumplen_sla:
    optimo = cumplen_sla[0]
    nodos_extra = optimo['s'] - nodos_minimos_estables
    print(f"-> SOLUCIÓN ÓPTIMA: Se requieren {optimo['s']} instancias activas ({nodos_extra} nodo(s) extra sobre el mínimo)")
    print(f"   para lograr un tiempo de respuesta de {optimo['Ws_seg']:.2f} segundos y cumplir el SLA de {LIMITE_SLA_SEG} segundos.")
else:
    optimo = resultados[-1]
    print(f"-> ATENCIÓN: Ninguno de los escenarios cumple el SLA de {LIMITE_SLA_SEG}s (el tiempo base de procesamiento por nodo ya es de {tiempo_base_seg:.2f}s).")

# ==============================================================================
# 4. GRÁFICAS COMPARATIVAS PARA EL INFORME
# ==============================================================================
nodos = [r['s'] for r in resultados]
ws_teorico = [r['Ws_seg'] for r in resultados]
ws_simpy = [r['Ws_simpy'] for r in resultados]
wq_teorico = [r['Wq_seg'] for r in resultados]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

ax1.plot(nodos, ws_teorico, marker='o', linewidth=2.5, color='#1f77b4', label='Fórmula Exacta M/M/s (Ws)')
ax1.plot(nodos, ws_simpy, marker='s', linestyle='--', linewidth=2, color='#ff7f0e', label='Simulación SimPy (Ws)')
ax1.axhline(y=LIMITE_SLA_SEG, color='red', linestyle='-.', linewidth=2, label=f'Meta SLA Máximo ({LIMITE_SLA_SEG} seg)')
if cumplen_sla:
    ax1.scatter(optimo['s'], optimo['Ws_seg'], color='green', s=180, zorder=5, label=f"Óptimo: {optimo['s']} Nodos ({optimo['Ws_seg']:.2f}s)")
ax1.set_title('Tiempo Total de Respuesta de IA (Cola + Inferencia)')
ax1.set_xlabel('Nodos Activos en GCP / Azure (s)')
ax1.set_ylabel('Tiempo Total de Respuesta Ws (Segundos)')
ax1.set_xticks(nodos)
ax1.grid(True, linestyle=':', alpha=0.7)
ax1.legend()

ax2_ocupacion = ax2.twinx()
ax2.bar(nodos, wq_teorico, color='#aec7e8', width=0.45, label='Espera en Fila Wq (seg)')
ax2_ocupacion.plot(nodos, [r['rho'] for r in resultados], color='#d62728', marker='D', linewidth=2, label='Uso del Clúster (%)')

ax2.set_title('Reducción del Cuello de Botella (Fila Wq vs Uso de Cloud)')
ax2.set_xlabel('Nodos Activos en GCP / Azure (s)')
ax2.set_ylabel('Tiempo de Espera en Cola Wq (Segundos)', color='#1f77b4')
ax2_ocupacion.set_ylabel('Porcentaje de Utilización del Clúster (%)', color='#d62728')
ax2.set_xticks(nodos)
ax2.grid(True, linestyle=':', alpha=0.5)

plt.tight_layout()
plt.savefig('simulacion_colas_ia_gcp.png', dpi=300)
print("
[INFO] Gráfica guardada como 'simulacion_colas_ia_gcp.png'. Mostrando en pantalla...")
plt.show()
