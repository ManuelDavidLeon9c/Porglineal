
# 8. IMPORTACIÓN DE LIBRERÍAS GRÁFICAS
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import cm  
import numpy as np
from scipy.optimize import minimize  # Para manejar mapas de colores (colormaps)

# 9. CREACIÓN DE LA MALLA DE DATOS (El "terreno" 3D)
# Generamos vectores de valores para x1 y x2 desde 3 hasta 30 servidores (con 100 puntos intermedios)
rango_x1 = np.linspace(3, 30, 100)
rango_x2 = np.linspace(3, 30, 100)

# np.meshgrid cruza ambos vectores para crear una cuadrícula 2D de coordenadas (X1, X2)
X1, X2 = np.meshgrid(rango_x1, rango_x2)

# Calculamos el costo Z (la altura de la montaña/valle) para cada punto de la cuadrícula
Z = (120 * X1 + 80 * X2) + (15000 / X1) + (8000 / X2) + (5000 / (X1 * X2))

# 10. CONFIGURACIÓN DE LA VENTANA Y SUBGRÁFICOS
# Creamos un lienzo ancho (14x6 pulgadas) para poner el gráfico 3D a la izquierda y el 2D a la derecha
fig = plt.figure(figsize=(14, 6))

# --- GRÁFICO 1: SUPERFICIE 3D DE OPTIMIZACIÓN ---
ax1 = fig.add_subplot(1, 2, 1, projection='3d')

# Dibujamos la superficie curva usando el mapa de color 'viridis' y algo de transparencia (alpha)
superficie = ax1.plot_surface(X1, X2, Z, cmap=cm.viridis, alpha=0.8, edgecolor='none')

# Marcamos el punto óptimo exacto encontrado por Scipy con una estrella roja grande
ax1.scatter(opt_x1, opt_x2, costo_minimo, color='red', s=150, marker='*', label='Mínimo Global (Óptimo)')

# Etiquetas de los ejes para el informe
ax1.set_title('Superficie 3D de Costos Operativos')
ax1.set_xlabel('Nodos Backend (x1)')
ax1.set_ylabel('Nodos Caché (x2)')
ax1.set_zlabel('Costo Total ($ USD)')
ax1.legend()

# --- GRÁFICO 2: CURVAS DE NIVEL Y REGIÓN FACTIBLE (2D) ---
ax2 = fig.add_subplot(1, 2, 2)

# Dibujamos 30 curvas de nivel (vistas desde arriba, como un mapa topográfico)
curvas = ax2.contourf(X1, X2, Z, levels=30, cmap=cm.viridis, alpha=0.7)
fig.colorbar(curvas, ax=ax2, label='Costo Total ($ USD)')

# Dibujamos las líneas de las restricciones para delimitar visualmente la Región Factible
# Restricción 1 (Presupuesto): 120*x1 + 80*x2 = 4500  --> Despejando x2: x2 = (4500 - 120*x1) / 80
x2_presupuesto = (4500 - 120 * rango_x1) / 80
ax2.plot(rango_x1, x2_presupuesto, 'r--', linewidth=2, label='Límite Presupuesto ($4500)')

# Restricción 2 (Mínimo nodos): x1 + x2 = 15  --> Despejando x2: x2 = 15 - x1
x2_minimo = 15 - rango_x1
ax2.plot(rango_x1, x2_minimo, 'w--', linewidth=2, label='Mínimo Nodos (15)')

# Marcamos nuevamente el punto óptimo en el plano 2D
ax2.scatter(opt_x1, opt_x2, color='red', s=150, marker='*', zorder=5, label=f'Óptimo ({opt_x1:.1f}, {opt_x2:.1f})')

# Ajustamos los límites visuales del gráfico 2D para que coincidan con nuestra cuadrícula
ax2.set_xlim(3, 30)
ax2.set_ylim(3, 30)
ax2.set_title('Curvas de Nivel y Región Factible')
ax2.set_xlabel('Nodos Backend (x1)')
ax2.set_ylabel('Nodos Caché (x2)')
ax2.legend(loc='upper right')

# 11. MOSTRAR Y GUARDAR EL GRÁFICO
plt.tight_layout()  # Ajusta los márgenes automáticamente para que no se superpongan los textos
plt.savefig('optimizacion_pnl_servidores.png', dpi=300)  # Guarda la imagen en alta calidad para tu documento
plt.show()  # Muestra la ventana interactiva en pantalla