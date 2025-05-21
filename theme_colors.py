"""
Módulo para definir la paleta de colores del dashboard.
Esto permite mantener consistencia visual en toda la aplicación.
"""

# Colores primarios
PRIMARY = '#3498db'       # Azul
SECONDARY = '#2c3e50'     # Azul oscuro
SUCCESS = '#2ecc71'       # Verde
DANGER = '#e74c3c'        # Rojo
WARNING = '#f39c12'       # Naranja
INFO = '#3498db'          # Azul claro
LIGHT = '#f8f9fa'         # Gris claro
DARK = '#343a40'          # Gris oscuro

# Colores para las categorías específicas
TRANSACTION_COLOR = '#3498db'
FRAUD_COLOR = '#e74c3c'
IDENTITY_THEFT_COLOR = '#f39c12'
CVV_MISMATCH_COLOR = '#2ecc71'

# Paletas de colores para gráficos
# Cada lista proporciona una secuencia de colores relacionados
BLUE_PALETTE = ['#edf8fb', '#b2e2e2', '#66c2a4', '#2ca25f', '#006d2c']
RED_PALETTE = ['#fee5d9', '#fcae91', '#fb6a4a', '#de2d26', '#a50f15']
ORANGE_PALETTE = ['#feedde', '#fdbe85', '#fd8d3c', '#e6550d', '#a63603']
GREEN_PALETTE = ['#edf8e9', '#bae4b3', '#74c476', '#31a354', '#006d2c']
PURPLE_PALETTE = ['#f2f0f7', '#cbc9e2', '#9e9ac8', '#756bb1', '#54278f']

# Colores para mapas de calor y gráficos de intensidad
SEQUENTIAL_COLORS = [
    (0.0, '#f8f9fa'),
    (0.2, '#d4e6f1'),
    (0.4, '#a9cce3'),
    (0.6, '#7fb3d5'),
    (0.8, '#5499c7'),
    (1.0, '#2980b9')
]

DIVERGING_COLORS = [
    (0.0, '#e74c3c'),
    (0.1, '#f1948a'),
    (0.2, '#f5b7b1'), 
    (0.3, '#fadbd8'),
    (0.4, '#fdedec'),
    (0.5, '#ffffff'),
    (0.6, '#ebf5fb'),
    (0.7, '#d6eaf8'),
    (0.8, '#aed6f1'),
    (0.9, '#85c1e9'),
    (1.0, '#3498db')
]

# Colores para indicadores específicos de fraude
# Esta parte es para configurar los colores de las etiquetas de los indicadores

FRAUD_INDICATORS = {
    'CVV incorrecto': '#e74c3c',
    'Fecha exp. incorrecta': '#f39c12',
    'País diferente': '#3498db',
    'Tarjeta no presente': '#95a5a6'
}

# Función para obtener una paleta de colores para un determinado número de categorías
def get_color_palette(num_categories, palette_type='blue'):
    """
    Devuelve una paleta de colores con el número solicitado de categorías.
    
    Args:
        num_categories: Número de colores necesarios
        palette_type: Tipo de paleta ('blue', 'red', 'orange', 'green', 'purple')
    
    Returns:
        Una lista con los colores seleccionados
    """
    palette_map = {
        'blue': BLUE_PALETTE,
        'red': RED_PALETTE,
        'orange': ORANGE_PALETTE,
        'green': GREEN_PALETTE,
        'purple': PURPLE_PALETTE
    }
    
    palette = palette_map.get(palette_type.lower(), BLUE_PALETTE)
    
    # Si necesitamos más colores de los disponibles en la paleta base
    if num_categories <= len(palette):
        return palette[:num_categories]
    else:
        # Generamos colores adicionales interpolando entre los existentes
        import matplotlib.pyplot as plt
        import numpy as np
        
        # Usamos un mapa de colores de matplotlib para generar más colores
        cmap_name = {
            'blue': 'Blues',
            'red': 'Reds',
            'orange': 'Oranges',
            'green': 'Greens',
            'purple': 'Purples'
        }.get(palette_type.lower(), 'Blues')
        
        cmap = plt.cm.get_cmap(cmap_name, num_categories)
        return [plt.colors.rgb2hex(cmap(i)) for i in range(num_categories)]
