# 1. IMPORTACIÓN DE LIBRERÍAS
import simpy                  # Librería de simulación de eventos discretos (para simular los correos llegando en tiempo real)
import math                   # Para factoriales y potencias de las fórmulas M/M/s
import random                 # Para generar llegadas aleatorias exponenciales en la simulación
import numpy as np            # Manejo de arreglos numéricos
import matplotlib.pyplot as plt # Generación de las gráficas para el informe

# 2. DEFINICIÓN DE PARÁMETROS DEL PROBLEMA (IA DE GESTIÓN DE CORREOS)
LAMBDA_CORREOS = 100.0  # Llegan 100 correos/solicitudes por minuto en hora pico
MU_SERVIDOR = 25.0      # Cada nodo en GCP/Azure procesa 25 correos por minuto (2.4 seg por correo)
LIMITE_SLA_SEG = 3.0    # Meta: La respuesta total (cola + procesamiento) no debe tardar más de 3 segundos

# ==============================================================================
# PARTE A: FÓRMULAS MATEMÁTICAS EXACTAS DEL MODELO MULTICANAL M/M/s
# ==============================================================================
def modelo_matematico_mms(lmbda, mu, s):
    r = lmbda / mu          # Tráfico ofrecido (necesitamos mínimo 4 nodos porque 100/25 = 4)
    rho = r / s             # Factor de utilización del clúster (% de ocupación de las GPUs)
    
    if rho >= 1.0:
        return None         # Si rho >= 1, la fila crece infinitamente y el servidor colapsa
    
    # Fórmula de Po: Probabilidad de que no haya ningún correo en el sistema
    sumatoria = sum([(r ** n) / math.factorial(n) for n in range(s)])
    ultimo_termino = ((r ** s) / math.factorial(s)) * (1.0 / (1.0 - rho))
    P0 = 1.0 / (sumatoria + ultimo_termino)
    
    # Fórmula de Lq: Número promedio de correos esperando en la cola de la API
    Lq = (P0 * (r ** s) * rho) / (math.factorial(s) * ((1.0 - rho) ** 2))
    
    # Fórmula de Wq: Tiempo promedio que un correo pasa esperando en la fila (convertido a segundos)
    Wq_seg = (Lq / lmbda) * 60.0
    
    # Fórmula de Ws: Tiempo total de respuesta (Espera en fila Wq + Tiempo de inferencia de IA 1/mu)
    Ws_seg = Wq_seg + ((1.0 / mu) * 60.0)
    
    return {'s': s, 'rho': rho * 100, 'P0': P0, 'Lq': Lq, 'Wq_seg': Wq_seg, 'Ws_seg': Ws_seg}

# ==============================================================================
# PARTE B: SIMULACIÓN EN TIEMPO REAL CON LA LIBRERÍA SIMPY
# ==============================================================================
def procesar_correo_ia(env, servidor_gcp, mu, lista_tiempos_totales):
    llegada = env.now  # Registra el segundo exacto en que el correo entra a la API
    
    # Solicita un nodo de IA en GCP/Azure; si están todos ocupados, SimPy lo mete en cola automáticamente
    with servidor_gcp.request() as peticion:
        yield peticion  # Espera su turno en la fila
        
        # Una vez asignado el nodo, simula el tiempo que tarda la IA en redactar el correo (distribución exponencial)
        tiempo_procesamiento = random.expovariate(mu / 60.0) # Convertido a segundos
        yield env.timeout(tiempo_procesamiento)
        
        # Registra cuánto tiempo total pasó desde que llegó hasta que la IA terminó de responder
        salida = env.now
        lista_tiempos_totales.append(salida - llegada)

def generador_trafico_correos(env, s, lmbda, mu, lista_tiempos):
    # Crea el clúster en la nube con 's' servidores (nodos) en paralelo
    cluster_gcp = simpy.Resource(env, capacity=s)
    
    while True:
        # Los correos van llegando de forma aleatoria según un proceso de Poisson
        tiempo_entre_llegadas = random.expovariate(lmbda / 60.0)
        yield env.timeout(tiempo_entre_llegadas)
        # Lanza el proceso de atención para cada correo nuevo
        env.process(procesar_correo_ia(env, cluster_gcp, mu, lista_tiempos))

def ejecutar_simulacion_simpy(s, lmbda, mu, tiempo_simulacion_seg=20000):
    random.seed(42)         # Semilla fija para que los resultados sean reproducibles en tu informe
    env = simpy.Environment()
    tiempos_respuesta = []
    
    # Inicia el generador de correos y corre la simulación durante 20,000 segundos virtuales
    env.process(generador_trafico_correos(env, s, lmbda, mu, tiempos_respuesta))
    env.run(until=tiempo_simulacion_seg)
    
    # Retorna el promedio de tiempo total de respuesta (Ws) medido en la simulación
    return np.mean(tiempos_respuesta)

# ==============================================================================
# 3. EJECUCIÓN Y COMPARACIÓN DE ESCENARIOS (DE 5 A 10 SERVIDORES EN GCP/AZURE)
# ==============================================================================
resultados = []
print("=== RESULTADOS: TEORÍA DE COLAS (M/M/s) + SIMULACIÓN SIMPY ===")
print(f"Tasa llegada: {LAMBDA_CORREOS} correos/min | Tasa servicio: {MU_SERVIDOR} correos/min por nodo (2.4s base)")
print(f"Meta SLA: Tiempo de respuesta total (Ws) <= {LIMITE_SLA_SEG} segundos\n")
print(f"{'Nodos(s)':<9} | {'Uso Cloud(%)':<13} | {'Po (Vacío)':<11} | {'Cola (Lq)':<10} | {'Espera Wq(s)':<13} | {'Total Teórico Ws':<17} | {'Total SimPy Ws':<15} | {'¿Cumple SLA?'}")
print("-" * 118)

for s in range(5, 11):
    metricas = modelo_matematico_mms(LAMBDA_CORREOS, MU_SERVIDOR, s)
    ws_simulado = ejecutar_simulacion_simpy(s, LAMBDA_CORREOS, MU_SERVIDOR)
    metricas['Ws_simpy'] = ws_simulado
    
    cumple = "SÍ CUMPLE" if metricas['Ws_seg'] <= LIMITE_SLA_SEG else "NO (Lento)"
    resultados.append(metricas)
    
    print(f"{s:<9} | {metricas['rho']:>11.1f}% | {metricas['P0']:>10.4f} | {metricas['Lq']:>9.2f} | {metricas['Wq_seg']:>11.2f} s | {metricas['Ws_seg']:>15.2f} s | {ws_simulado:>13.2f} s | {cumple}")

# Identificamos cuántos nodos necesitamos encender para bajar de 3 segundos
optimo = [r for r in resultados if r['Ws_seg'] <= LIMITE_SLA_SEG][0]
nodos_base = 5 # Mínimo de nodos para que el sistema no colapse (porque con 4 el uso es 100%)
nodos_extra = optimo['s'] - nodos_base

print("\n=== CONCLUSIÓN PARA EL PROYECTO ===")
print(f"-> Con la capacidad mínima operativa ({nodos_base} nodos), la respuesta tarda {resultados[0]['Ws_seg']:.2f} segundos (incumple el límite de 3s).")
print(f"-> Se deben encender {nodos_extra} nodo(s) extra (Total: {optimo['s']} instancias en GCP/Azure) para bajar el tiempo total a {optimo['Ws_seg']:.2f} segundos.")

# ==============================================================================
# 4. GRÁFICAS COMPARATIVAS PARA EL INFORME
# ==============================================================================
nodos = [r['s'] for r in resultados]
ws_teorico = [r['Ws_seg'] for r in resultados]
ws_simpy = [r['Ws_simpy'] for r in resultados]
wq_teorico = [r['Wq_seg'] for r in resultados]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

# Gráfica 1: Comparación Fórmula M/M/s vs Simulación SimPy (Tiempo Total Ws)
ax1.plot(nodos, ws_teorico, marker='o', linewidth=2.5, color='#1f77b4', label='Fórmula Exacta M/M/s (Ws)')
ax1.plot(nodos, ws_simpy, marker='s', linestyle='--', linewidth=2, color='#ff7f0e', label='Simulación SimPy (Ws)')
ax1.axhline(y=LIMITE_SLA_SEG, color='red', linestyle='-.', linewidth=2, label='Meta SLA Máximo (3.0 seg)')
ax1.scatter(optimo['s'], optimo['Ws_seg'], color='green', s=180, zorder=5, label=f"Óptimo: {optimo['s']} Nodos ({optimo['Ws_seg']:.2f}s)")
ax1.set_title('Tiempo Total de Respuesta de IA (Cola + Inferencia)')
ax1.set_xlabel('Nodos Activos en GCP / Azure (s)')
ax1.set_ylabel('Tiempo Total de Respuesta Ws (Segundos)')
ax1.set_xticks(nodos)
ax1.grid(True, linestyle=':', alpha=0.7)
ax1.legend()

# Gráfica 2: Desglose de Cuello de Botella (Espera en Cola Wq vs Ocupación de Servidores)
ax2_ocupacion = ax2.twinx()
barras = ax2.bar(nodos, wq_teorico, color='#aec7e8', width=0.45, label='Espera en Fila Wq (seg)')
linea_rho = ax2_ocupacion.plot(nodos, [r['rho'] for r in resultados], color='#d62728', marker='D', linewidth=2, label='Uso del Clúster (%)')

ax2.set_title('Reducción del Cuello de Botella (Fila Wq vs Uso de Cloud)')
ax2.set_xlabel('Nodos Activos en GCP / Azure (s)')
ax2.set_ylabel('Tiempo de Espera en Cola Wq (Segundos)', color='#1f77b4')
ax2_ocupacion.set_ylabel('Porcentaje de Utilización del Clúster (%)', color='#d62728')
ax2.set_xticks(nodos)
ax2.grid(True, linestyle=':', alpha=0.5)

plt.tight_layout()
plt.savefig('simulacion_colas_ia_gcp.png', dpi=300)
plt.show()