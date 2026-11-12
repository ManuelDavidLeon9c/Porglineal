# ==============================================================================
# PROYECTO FINAL INVESTIGACIÓN DE OPERACIONES - INGENIERÍA DE SISTEMAS
# TEMA 4: REDES DE PROYECTO PERT / CPM (UNIVERSAL Y DINÁMICO POR CONSOLA)
# Archivo: prueba.py
# ==============================================================================

import networkx as nx
import matplotlib.pyplot as plt
import math

actividades = {}
G = nx.DiGraph()

print("=" * 75)
print("       SISTEMA INTERACTIVO UNIVERSAL DE PLANIFICACIÓN PERT / CPM")
print("=" * 75)

# ==========================================================
# 1. SELECCIÓN DE MODALIDAD Y TIPO DE MODELO (CPM O PERT)
# ==========================================================
print("\nSeleccione el modo de carga de datos:")
print("  1. Ingresar un problema NUEVO desde cero (Cualquier proyecto)")
print("  2. Cargar proyecto base de Ing. de Sistemas (Con opción de editar tiempos)")
modo_carga = input("Seleccione una opción (1 o 2) [Por defecto: 1]: ").strip() or "1"

if modo_carga == "2":
    tipo_tiempos = "1"
    datos_base = [
        ("A", "Levantamiento de requisitos", 3.0, []),
        ("B", "Diseño de interfaces UI/UX", 4.0, ["A"]),
        ("C", "Diseño de base de datos segura", 3.0, ["A"]),
        ("D", "Desarrollo del frontend", 6.0, ["B"]),
        ("E", "Desarrollo del backend (Spring Boot)", 7.0, ["C"]),
        ("F", "Integración frontend-backend", 3.0, ["D", "E"]),
        ("G", "Implementación hashing SHA-256", 4.0, ["F"]),
        ("H", "Auditoría de vulnerabilidades", 3.0, ["G"]),
        ("I", "Despliegue en producción cloud", 2.0, ["H"])
    ]
    print("\n--- CONFIGURACIÓN DE DURACIONES DEL PROYECTO BASE ---")
    print("(Presione ENTER para mantener la duración sugerida o escriba un nuevo valor)")
    for cod, nom, dur_def, preds in datos_base:
        entrada_dur = input(f"  Duración para [{cod}] {nom} [Por defecto: {dur_def} días]: ").strip()
        try:
            dur = float(entrada_dur) if entrada_dur != "" else dur_def
            if dur <= 0:
                dur = dur_def
        except ValueError:
            dur = dur_def

        actividades[cod] = {
            "nombre": nom,
            "duracion": dur,
            "varianza": 0.0,
            "predecesoras": preds
        }
    cantidad = len(actividades)

else:
    print("\nSeleccione el método de cálculo de tiempos:")
    print("  1. CPM Determinístico (1 sola duración conocida por actividad)")
    print("  2. PERT Probabilístico (3 tiempos: Optimista 'a', Probable 'm', Pesimista 'b')")
    tipo_tiempos = input("Seleccione método (1 o 2) [Por defecto: 1]: ").strip() or "1"

    while True:
        try:
            cantidad = int(input("\n¿Cuántas actividades tiene el proyecto?: "))
            if cantidad > 0:
                break
            print("Ingrese una cantidad mayor que cero.")
        except ValueError:
            print("Debe ingresar un número entero.")

    print("\nFormato de códigos sugerido: A, B, C... o A1, A2, A3...")
    usar_letras = input("¿Desea usar letras automáticas (A, B, C...) como ID? (S/N) [Por defecto: S]: ").strip().upper() or "S"

    for i in range(1, cantidad + 1):
        if usar_letras == "S" and i <= 26:
            codigo_def = chr(64 + i)  # Genera A, B, C...
        else:
            codigo_def = f"A{i}"      # Genera A1, A2, A3...

        print(f"\n--- REGISTRO DE ACTIVIDAD #{i} (ID asignado: {codigo_def}) ---")
        nombre = input(f"Nombre o descripción de la actividad [{codigo_def}]: ").strip() or f"Actividad {codigo_def}"

        if tipo_tiempos == "2":
            # Ingreso de los 3 tiempos de PERT
            while True:
                try:
                    t_a = float(input("  Tiempo Optimista (a): "))
                    t_m = float(input("  Tiempo Más Probable (m): "))
                    t_b = float(input("  Tiempo Pesimista (b): "))
                    if t_a > 0 and t_a <= t_m <= t_b:
                        duracion = (t_a + 4 * t_m + t_b) / 6.0
                        varianza = ((t_b - t_a) / 6.0) ** 2
                        print(f"  -> Tiempo Esperado (Te) calculado: {duracion:.2f} | Varianza: {varianza:.4f}")
                        break
                    print("  [!] Recuerde que debe cumplirse: 0 < a <= m <= b.")
                except ValueError:
                    print("  [!] Ingrese valores numéricos válidos.")
        else:
            # Ingreso de 1 tiempo fijo de CPM
            while True:
                try:
                    duracion = float(input("  Duración de la actividad (días/semanas): "))
                    if duracion > 0:
                        varianza = 0.0
                        break
                    print("  [!] La duración debe ser mayor que cero.")
                except ValueError:
                    print("  [!] Ingrese una duración numérica válida.")

        actividades[codigo_def] = {
            "nombre": nombre,
            "duracion": duracion,
            "varianza": varianza,
            "predecesoras": []
        }

    # ==========================================================
    # 2. INGRESO DE DEPENDENCIAS (SOLO EN MODO NUEVO)
    # ==========================================================
    print("\n" + "=" * 75)
    print("                        REGISTRO DE DEPENDENCIAS")
    print("=" * 75)
    print("Actividades registradas:")
    for codigo, datos in actividades.items():
        print(f"  {codigo}: {datos['nombre']} (Duración: {datos['duracion']:.2f})")

    for codigo in actividades:
        while True:
            entrada = input(
                f"\n¿Qué actividades preceden a '{codigo}' ({actividades[codigo]['nombre']})?\n"
                "Ingrese códigos separados por coma o presione ENTER si no tiene predecesoras: "
            ).strip()

            if not entrada:
                predecesoras = []
            else:
                predecesoras = [p.strip().upper() for p in entrada.split(",") if p.strip()]

            if len(predecesoras) != len(set(predecesoras)):
                print("  [!] No repita identificadores.")
                continue

            if codigo in predecesoras:
                print("  [!] Una actividad no puede depender de sí misma.")
                continue

            desconocidas = [p for p in predecesoras if p not in actividades]
            if desconocidas:
                print("  [!] Identificadores inexistentes:", desconocidas)
                continue

            actividades[codigo]["predecesoras"] = predecesoras
            break

# ==========================================================
# 3. CONSTRUCCIÓN DEL GRAFO Y VALIDACIÓN DE CICLOS
# ==========================================================
for codigo, datos in actividades.items():
    G.add_node(
        codigo,
        nombre=datos["nombre"],
        duracion=datos["duracion"],
        varianza=datos["varianza"]
    )
    for predecesora in datos["predecesoras"]:
        G.add_edge(predecesora, codigo)

if not nx.is_directed_acyclic_graph(G):
    print("\n[ERROR CRÍTICO]: Se encontraron dependencias circulares (bucle infinito).")
    print("Revise las actividades predecesoras e intente nuevamente.")
    raise SystemExit

orden = list(nx.topological_sort(G))

# ==========================================================
# 4. CÁLCULO DE TIEMPOS TEMPRANOS (FORWARD PASS: ES y EF)
# ==========================================================
for nodo in orden:
    predecesoras = list(G.predecessors(nodo))
    ES = max((G.nodes[p]["EF"] for p in predecesoras), default=0.0)
    EF = ES + G.nodes[nodo]["duracion"]
    G.nodes[nodo]["ES"] = ES
    G.nodes[nodo]["EF"] = EF

# ==========================================================
# 5. DURACIÓN TOTAL Y CÁLCULO DE TIEMPOS TARDÍOS (BACKWARD PASS)
# ==========================================================
finales = [nodo for nodo in G.nodes() if G.out_degree(nodo) == 0]
duracion_proyecto = max(G.nodes[nodo]["EF"] for nodo in finales)

for nodo in reversed(orden):
    sucesoras = list(G.successors(nodo))
    LF = min((G.nodes[s]["LS"] for s in sucesoras), default=duracion_proyecto)
    LS = LF - G.nodes[nodo]["duracion"]
    G.nodes[nodo]["LS"] = LS
    G.nodes[nodo]["LF"] = LF

# ==========================================================
# 6. CÁLCULO DE HOLGURAS E IDENTIFICACIÓN DE RUTA CRÍTICA
# ==========================================================
for nodo in G.nodes():
    holgura = G.nodes[nodo]["LS"] - G.nodes[nodo]["ES"]
    G.nodes[nodo]["holgura"] = round(holgura, 4)
    G.nodes[nodo]["critica"] = abs(holgura) < 1e-5

nodos_criticos = [nodo for nodo in G.nodes() if G.nodes[nodo]["critica"]]
aristas_criticas = [
    (u, v) for u, v in G.edges()
    if G.nodes[u]["critica"] and G.nodes[v]["critica"]
    and abs(G.nodes[u]["EF"] - G.nodes[v]["ES"]) < 1e-5
]

GC = nx.DiGraph()
GC.add_nodes_from(nodos_criticos)
GC.add_edges_from(aristas_criticas)

inicios_criticos = [
    nodo for nodo in GC.nodes()
    if GC.in_degree(nodo) == 0 and abs(G.nodes[nodo]["ES"]) < 1e-5
]
finales_criticos = [
    nodo for nodo in GC.nodes()
    if GC.out_degree(nodo) == 0 and abs(G.nodes[nodo]["EF"] - duracion_proyecto) < 1e-5
]

rutas_criticas = []
for inicio in inicios_criticos:
    for final in finales_criticos:
        rutas_criticas.extend(list(nx.all_simple_paths(GC, inicio, final)))

# ==========================================================
# 7. PRESENTACIÓN DE RESULTADOS EN TABLA
# ==========================================================
print("\n" + "=" * 120)
print("                              RESULTADOS DEL ANÁLISIS PERT / CPM")
print("=" * 120)
print(
    f"{'ID':<6}"
    f"{'ACTIVIDAD':<38}"
    f"{'PREDEC.':<12}"
    f"{'DUR.':>8}"
    f"{'ES':>8}"
    f"{'EF':>8}"
    f"{'LS':>8}"
    f"{'LF':>8}"
    f"{'HOLG.':>9}"
    f"{'ESTADO':>14}"
)
print("-" * 120)

for nodo in orden:
    datos = G.nodes[nodo]
    preds_str = ",".join(actividades[nodo]["predecesoras"]) or "-"
    estado = "CRÍTICA" if datos["critica"] else "HOLGURA"
    print(
        f"{nodo:<6}"
        f"{datos['nombre'][:36]:<38}"
        f"{preds_str[:10]:<12}"
        f"{datos['duracion']:>8.2f}"
        f"{datos['ES']:>8.2f}"
        f"{datos['EF']:>8.2f}"
        f"{datos['LS']:>8.2f}"
        f"{datos['LF']:>8.2f}"
        f"{datos['holgura']:>9.2f}"
        f"{estado:>14}"
    )

print("-" * 120)
print(f"\n-> DURACIÓN TOTAL ESPERADA DEL PROYECTO: {duracion_proyecto:.2f} unidades de tiempo (días/semanas)")

print("\n-> RUTA(S) CRÍTICA(S) IDENTIFICADA(S):")
if rutas_criticas:
    for i, ruta in enumerate(rutas_criticas, 1):
        print(f"   Ruta Crítica #{i}: {' -> '.join(ruta)}")
        if tipo_tiempos == "2":
            var_ruta = sum(G.nodes[n]["varianza"] for n in ruta)
            desv_ruta = math.sqrt(var_ruta)
            print(f"   [PERT] Varianza de la Ruta #{i}: {var_ruta:.4f} | Desviación Estándar (sigma): {desv_ruta:.2f}")
else:
    print("   No se pudo aislar una ruta crítica única.")

print("\n-> RESUMEN DE FLEXIBILIDAD (ACTIVIDADES NO CRÍTICAS):")
no_criticas = [n for n in orden if not G.nodes[n]["critica"]]
if no_criticas:
    for nodo in no_criticas:
        print(f"   [{nodo}] {G.nodes[nodo]['nombre']}: puede retrasarse hasta {G.nodes[nodo]['holgura']:.2f} días sin afectar la entrega.")
else:
    print("   Todas las actividades del proyecto son críticas (Holgura = 0 en toda la red).")

# ==========================================================
# 8. GENERACIÓN DEL DIAGRAMA DE RED VISUAL
# ==========================================================
capas = {}
for nodo in orden:
    predecesoras = list(G.predecessors(nodo))
    capas[nodo] = max((capas[p] for p in predecesoras), default=-1) + 1

nx.set_node_attributes(G, capas, "layer")
pos = nx.multipartite_layout(G, subset_key="layer", align="horizontal", scale=3)

colores_nodos = ["tomato" if G.nodes[n]["critica"] else "lightblue" for n in G.nodes()]
colores_aristas = ["red" if (u, v) in aristas_criticas else "gray" for u, v in G.edges()]
anchos = [3.0 if (u, v) in aristas_criticas else 1.4 for u, v in G.edges()]

etiquetas = {
    nodo: f"{nodo}\nD: {G.nodes[nodo]['duracion']:.1f}\nH: {G.nodes[nodo]['holgura']:.1f}"
    for nodo in G.nodes()
}

ancho_fig = max(13, len(set(capas.values())) * 2.2)
alto_fig = max(7, cantidad * 0.65)

plt.figure(figsize=(ancho_fig, alto_fig))
nx.draw_networkx_nodes(G, pos, node_color=colores_nodos, node_size=2800, edgecolors="black", linewidths=1.5)
nx.draw_networkx_labels(G, pos, labels=etiquetas, font_size=9, font_weight="bold")
nx.draw_networkx_edges(
    G, pos, edge_color=colores_aristas, width=anchos,
    arrows=True, arrowsize=22, node_size=2800, connectionstyle="arc3,rad=0.08"
)

plt.title(
    f"DIAGRAMA DE RED PERT / CPM\nDuración Total del Proyecto: {duracion_proyecto:.2f} días",
    fontsize=15, fontweight="bold"
)
plt.figtext(
    0.5, 0.02,
    "ROJO: Ruta Crítica (Holgura = 0)  |  AZUL: Actividades con Holgura  |  D: Duración  |  H: Holgura",
    ha="center", fontsize=11
)

plt.axis("off")
plt.tight_layout()
plt.savefig("diagrama_pert_cpm.png", dpi=300, bbox_inches="tight")
print("\n[INFO] Diagrama guardado como 'diagrama_pert_cpm.png'. Mostrando en pantalla...")
plt.show()