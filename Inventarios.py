# ==============================================================================
# PROYECTO FINAL INVESTIGACIÓN DE OPERACIONES - INGENIERÍA DE SISTEMAS
# TEMA 3: INVENTARIOS PEPS, UEPS, KARDEX Y CLASIFICACIÓN ABC (RECURSOS DIGITALES)
# Archivo: Inventarios.py (Versión Dinámica: Ingreso Inicial + Reporte Final Completo)
# ==============================================================================

from datetime import datetime, timedelta
import matplotlib.pyplot as plt

inventario = {}
kardex = []
catalogo = {}

def registrar_recurso(codigo, nombre, categoria, costo_mensual):
    codigo = codigo.upper().strip()
    if codigo not in inventario:
        inventario[codigo] = []
    catalogo[codigo] = {
        "nombre": nombre,
        "categoria": categoria,
        "costo_mensual": float(costo_mensual)
    }

def registrar_movimiento(codigo, tipo, cantidad, costo, usuario):
    saldo = sum(lote["cantidad"] for lote in inventario[codigo])
    valor = sum(lote["cantidad"] * lote["costo"] for lote in inventario[codigo])

    kardex.append({
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "codigo": codigo,
        "recurso": catalogo[codigo]["nombre"],
        "tipo": tipo,
        "cantidad": cantidad,
        "costo": costo,
        "total": cantidad * costo,
        "saldo": saldo,
        "valor_inventario": valor,
        "usuario": usuario
    })

def entrada(codigo, cantidad, costo, vencimiento, usuario="Administrador", silencioso=False):
    codigo = codigo.upper().strip()
    if codigo not in inventario or cantidad <= 0 or costo < 0:
        print("  [!] Error: Código no existente o cantidades no válidas.")
        return

    try:
        fecha_venc = datetime.strptime(vencimiento, "%Y-%m-%d").date()
    except ValueError:
        print("  [!] Formato de fecha inválido. Se asignará vencimiento a 90 días.")
        fecha_venc = datetime.now().date() + timedelta(days=90)

    lote = {
        "cantidad": int(cantidad),
        "costo": float(costo),
        "vencimiento": fecha_venc
    }

    inventario[codigo].append(lote)
    registrar_movimiento(codigo, "ENTRADA", int(cantidad), float(costo), usuario)

    if not silencioso:
        print(f"  -> Entrada registrada correctamente para {catalogo[codigo]['nombre']}.")

def salida(codigo, cantidad, metodo="PEPS", usuario="Desarrollador", silencioso=False):
    codigo = codigo.upper().strip()
    metodo = metodo.upper().strip()
    if codigo not in inventario or cantidad <= 0:
        print("  [!] Error: Código no registrado o cantidad inválida.")
        return

    lotes = inventario[codigo]
    disponible = sum(l["cantidad"] for l in lotes)

    if cantidad > disponible:
        print(f"  [!] No hay existencias suficientes (Disponible: {disponible}).")
        return

    if metodo == "PEPS":
        lotes.sort(key=lambda x: x["vencimiento"])
    elif metodo == "UEPS":
        lotes.sort(key=lambda x: x["vencimiento"], reverse=True)
    else:
        print("  [!] Método no válido. Use PEPS o UEPS.")
        return

    pendiente = int(cantidad)
    costo_total = 0.0

    for lote in list(lotes):
        if pendiente == 0:
            break
        consumido = min(pendiente, lote["cantidad"])
        costo_total += consumido * lote["costo"]
        lote["cantidad"] -= consumido
        pendiente -= consumido
        if lote["cantidad"] == 0:
            lotes.remove(lote)

    costo_promedio = costo_total / cantidad
    registrar_movimiento(codigo, f"SALIDA ({metodo})", int(cantidad), costo_promedio, usuario)

    if not silencioso:
        print(f"  -> Salida registrada con {metodo}. Costo total descargado: ${costo_total:,.2f}")

def mostrar_inventario():
    print("
" + "=" * 85)
    print(" 1. ESTADO ACTUAL DEL INVENTARIO DIGITAL (EXISTENCIAS Y VALORACIÓN)")
    print("=" * 85)
    print(f"{'Código':<8} | {'Recurso Digital':<20} | {'Categoría':<24} | {'Disponible':<10} | {'Valor Total ($)'}")
    print("-" * 85)

    valor_global = 0
    for codigo, lotes in inventario.items():
        cantidad = sum(l["cantidad"] for l in lotes)
        valor = sum(l["cantidad"] * l["costo"] for l in lotes)
        valor_global += valor
        print(f"{codigo:<8} | {catalogo[codigo]['nombre']:<20} | {catalogo[codigo]['categoria']:<24} | {cantidad:<10} | ${valor:>13,.2f}")
    print("-" * 85)
    print(f"VALOR TOTAL DEL INVENTARIO EN POOL CORPORATIVO: ${valor_global:,.2f}")

def mostrar_kardex():
    print("
" + "=" * 115)
    print(" 2. REGISTRO HISTÓRICO DE KARDEX (ENTRADAS Y SALIDAS PEPS / UEPS)")
    print("=" * 115)
    print(f"{'Fecha':<16} | {'Recurso':<16} | {'Movimiento':<14} | {'Cant.':<6} | {'Costo Unit.':<13} | {'Costo Total':<14} | {'Saldo':<6} | {'Usuario'}")
    print("-" * 115)

    for m in kardex:
        print(
            f"{m['fecha']:<16} | "
            f"{m['recurso']:<16} | "
            f"{m['tipo']:<14} | "
            f"{m['cantidad']:<6} | "
            f"${m['costo']:>11,.2f} | "
            f"${m['total']:>12,.2f} | "
            f"{m['saldo']:<6} | "
            f"{m['usuario']}"
        )

def clasificacion_abc(graficar=True):
    print("
" + "=" * 95)
    print(" 3. CLASIFICACIÓN ABC DE RECURSOS DIGITALES (CRITERIO DE PARETO)")
    print("=" * 95)
    print(f"{'Recurso Digital':<20} | {'Costo Mensual ($)':<18} | {'Participación (%)':<18} | {'Acumulado (%)':<15} | {'Clase ABC'}")
    print("-" * 95)

    recursos = sorted(catalogo.items(), key=lambda x: x[1]["costo_mensual"], reverse=True)
    total = sum(datos["costo_mensual"] for datos in catalogo.values())

    acumulado = 0.0
    nombres_graf = []
    costos_graf = []
    acumulados_graf = []
    colores_graf = []

    for codigo, datos in recursos:
        costo = datos["costo_mensual"]
        porcentaje = (costo / total * 100) if total else 0
        acumulado += porcentaje

        if acumulado <= 80.0:
            clase = "A (Crítico)"
            colores_graf.append("#d62728")
        elif acumulado <= 95.0:
            clase = "B (Intermedio)"
            colores_graf.append("#ff7f0e")
        else:
            clase = "C (Básico)"
            colores_graf.append("#2ca02c")

        nombres_graf.append(datos["nombre"])
        costos_graf.append(costo)
        acumulados_graf.append(acumulado)

        print(f"{datos['nombre']:<20} | ${costo:>16,.2f} | {porcentaje:>16.2f}% | {acumulado:>13.2f}% | {clase}")

    if graficar and nombres_graf:
        fig, ax1 = plt.subplots(figsize=(10, 5.5))
        barras = ax1.bar(nombres_graf, costos_graf, color=colores_graf, alpha=0.85, label="Costo Mensual ($)")
        ax1.set_xlabel("Recursos Digitales y Licencias Cloud")
        ax1.set_ylabel("Costo Mensual ($)", color="#1f77b4")
        ax1.tick_params(axis='x', rotation=15)

        ax2 = ax1.twinx()
        ax2.plot(nombres_graf, acumulados_graf, color="black", marker="o", linewidth=2, label="% Acumulado Pareto")
        ax2.axhline(80, color="red", linestyle="--", alpha=0.6, label="Límite Clase A (80%)")
        ax2.axhline(95, color="orange", linestyle="--", alpha=0.6, label="Límite Clase B (95%)")
        ax2.set_ylabel("Porcentaje Acumulado (%)")
        ax2.set_ylim(0, 105)
        ax2.legend(loc="center right")

        plt.title("Diagrama de Pareto - Clasificación ABC de Licencias y APIs")
        plt.tight_layout()
        plt.savefig("inventario_abc_pareto.png", dpi=300)
        print("
[INFO] Gráfica ABC guardada como 'inventario_abc_pareto.png'.")
        plt.show()

def alertas_vencimiento(dias=60):
    print("
" + "=" * 85)
    print(f" 4. ALERTAS PREVENTIVAS DE VENCIMIENTO DE TOKENS/LICENCIAS (Próximos {dias} días)")
    print("=" * 85)

    hoy = datetime.now().date()
    limite = hoy + timedelta(days=dias)
    encontrado = False

    for codigo, lotes in inventario.items():
        for lote in lotes:
            fecha = lote["vencimiento"]
            if fecha <= limite:
                encontrado = True
                estado = "VENCIDO (CRÍTICO)" if fecha < hoy else "PRÓXIMO A VENCER (APLICAR PEPS)"
                print(
                    f"-> Recurso: {catalogo[codigo]['nombre']:<16} | "
                    f"Cantidad Lote: {lote['cantidad']:<6} | "
                    f"Vence: {fecha} | "
                    f"Estado: {estado}"
                )

    if not encontrado:
        print(f"-> Todos los lotes tienen vigencia superior a {dias} días.")

def cargar_datos_base():
    registrar_recurso("R01", "ChatGPT API", "Créditos de IA", 1200000)
    registrar_recurso("R02", "Microsoft 365", "Suscripciones", 450000)
    registrar_recurso("R03", "Azure Cloud", "Servicios en la nube", 2500000)
    registrar_recurso("R04", "IntelliJ IDEA", "Licencias IDE", 350000)
    registrar_recurso("R05", "Figma Pro", "Diseño UI/UX", 150000)
    registrar_recurso("R06", "Plugins Dev", "Herramientas", 50000)

    entrada("R01", 1000, 1200, "2026-11-25", "Admin TI", silencioso=True)
    entrada("R01", 1500, 1300, "2027-02-15", "Admin TI", silencioso=True)
    entrada("R02", 20, 22500, "2027-01-15", "Compras", silencioso=True)
    entrada("R03", 500, 4000, "2027-03-15", "Arquitectura", silencioso=True)
    entrada("R04", 10, 35000, "2027-01-10", "Líder Dev", silencioso=True)
    entrada("R05", 15, 10000, "2027-02-10", "Diseño", silencioso=True)
    entrada("R06", 50, 1000, "2027-04-10", "Soporte", silencioso=True)

    # Simulamos dos salidas iniciales (una PEPS y una UEPS) para que el KARDEX muestre ambos métodos
    salida("R01", 600, "PEPS", "Equipo IA Backend", silencioso=True)
    salida("R04", 3, "UEPS", "Dev SecOps", silencioso=True)

def ejecutar_flujo_dinamico():
    print("=" * 85)
    print(" CONFIGURACIÓN INICIAL - SISTEMA DE INVENTARIOS PEPS, UEPS, KARDEX Y ABC")
    print("=" * 85)
    modo = input("¿Desea iniciar con la base de datos de ejemplo precargada? (S/N) [Por defecto: S]: ").strip().upper()
    if modo != "N":
        cargar_datos_base()
        print("  -> Se cargaron 6 recursos digitales base y sus movimientos iniciales.")

    # Ingreso de nuevos recursos al inicio
    try:
        n_nuevos = int(input("
1. ¿Cuántos recursos digitales NUEVOS desea registrar ahora? [Por defecto: 0]: ").strip() or "0")
    except ValueError:
        n_nuevos = 0

    for i in range(n_nuevos):
        print(f"
--- Registro del Recurso Nuevo #{i+1} ---")
        cod = input("  Código del recurso (ej. R07): ").strip().upper() or f"R0{len(catalogo)+1}"
        nom = input("  Nombre del recurso (ej. AWS Credits): ").strip() or f"Recurso {cod}"
        cat = input("  Categoría (ej. Cloud / IA): ").strip() or "Licencias Software"
        costo_m = float(input("  Presupuesto/Costo mensual estimado ($) para ABC: ").strip() or "300000")
        registrar_recurso(cod, nom, cat, costo_m)

        cant_ini = int(input("  Cantidad inicial a ingresar en Kardex: ").strip() or "10")
        costo_u = float(input("  Costo unitario de adquisición ($): ").strip() or "15000")
        venc = input("  Fecha de vencimiento (AAAA-MM-DD) [Enter = 2026-12-01]: ").strip() or "2026-12-01"
        usu = input("  Usuario responsable: ").strip() or "Administrador"
        entrada(cod, cant_ini, costo_u, venc, usu)

    # Ingreso de movimientos (Entradas o Salidas PEPS/UEPS) al inicio antes de generar el reporte
    try:
        n_movs = int(input("
2. ¿Cuántos movimientos (Entradas / Salidas PEPS o UEPS) desea registrar ahora? [Por defecto: 1]: ").strip() or "1")
    except ValueError:
        n_movs = 0

    for j in range(n_movs):
        print(f"
--- Movimiento #{j+1} ---")
        print("  Códigos disponibles:", ", ".join([f"{k} ({v['nombre']})" for k, v in catalogo.items()]))
        tipo_m = input("  Tipo de operación (1 = Entrada, 2 = Salida PEPS, 3 = Salida UEPS) [Por defecto: 2]: ").strip() or "2"
        cod_m = input("  Código del recurso [Por defecto: R01]: ").strip().upper() or "R01"
        cant_m = int(input("  Cantidad de unidades/tokens [Por defecto: 200]: ").strip() or "200")
        usu_m = input("  Usuario o departamento solicitante [Por defecto: Ing. Sistemas]: ").strip() or "Ing. Sistemas"

        if tipo_m == "1":
            costo_m = float(input("  Costo unitario de entrada ($): ").strip() or "1200")
            venc_m = input("  Fecha de vencimiento (AAAA-MM-DD): ").strip() or "2027-01-30"
            entrada(cod_m, cant_m, costo_m, venc_m, usu_m)
        elif tipo_m == "3":
            salida(cod_m, cant_m, "UEPS", usu_m)
        else:
            salida(cod_m, cant_m, "PEPS", usu_m)

    try:
        dias_alerta = int(input("
3. Ingrese el umbral de días para alertas de vencimiento [Por defecto: 60]: ").strip() or "60")
    except ValueError:
        dias_alerta = 60

    # GENERACIÓN AUTOMÁTICA DE TODA LA INFORMACIÓN AL FINAL
    print("

" + "#" * 95)
    print(" REPORTE CONSOLIDADO GENERADO AUTOMÁTICAMENTE")
    print("#" * 95)
    mostrar_inventario()
    mostrar_kardex()
    alertas_vencimiento(dias_alerta)
    clasificacion_abc(graficar=True)

if __name__ == "__main__":
    ejecutar_flujo_dinamico()
