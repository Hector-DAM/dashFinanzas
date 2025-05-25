import plotly.graph_objects as go

def create_custom_template():
    """
    Crea una plantilla personalizada para los gráficos Plotly con
    un aspecto visual mejorado.
    """
    custom_template = go.layout.Template()
    
    # Colores base
    colors = {
        'primary': '#3498db',
        'secondary': '#2c3e50',
        'success': '#2ecc71',
        'danger': '#e74c3c',
        'warning': '#62deec',
        'info': '#3498db',
        'light': '#f8f9fa',
        'dark': '#343a40',
    }
    
    # Configuración básica de la plantilla
    custom_template.layout = go.Layout(
        font=dict(family="Segoe UI, Roboto, sans-serif", size=12, color=colors['dark']),
        title=dict(
            font=dict(family="Segoe UI, Roboto, sans-serif", size=18, color=colors['secondary']),
            x=0.5,
            xanchor='center'
        ),
        plot_bgcolor='rgba(248, 249, 250, 0.5)',
        paper_bgcolor='rgba(255, 255, 255, 0)',
        colorway=[
            colors['primary'], 
            colors['danger'], 
            colors['success'], 
            colors['warning'], 
            '#9b59b6', 
            '#1abc9c', 
            '#34495e', 
            '#f1c40f', 
            '#e67e22', 
            '#16a085'
        ],
        margin=dict(l=40, r=40, t=50, b=40),
        hovermode='closest',
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(230, 230, 230, 0.5)',
            linecolor='#d4d4d4',
            title=dict(
                font=dict(family="Segoe UI, Roboto, sans-serif", size=13, color=colors['secondary'])
            ),
            tickfont=dict(family="Segoe UI, Roboto, sans-serif", size=11, color=colors['dark']),
            zeroline=False
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(230, 230, 230, 0.5)',
            linecolor='#d4d4d4',
            title=dict(
                font=dict(family="Segoe UI, Roboto, sans-serif", size=13, color=colors['secondary'])
            ),
            tickfont=dict(family="Segoe UI, Roboto, sans-serif", size=11, color=colors['dark']),
            zeroline=False
        ),
        legend=dict(
            font=dict(family="Segoe UI, Roboto, sans-serif", size=11, color=colors['dark']),
            bgcolor='rgba(255, 255, 255, 0.7)',
            bordercolor='rgba(230, 230, 230, 0.5)',
            borderwidth=1
        ),
        hoverlabel=dict(
            font=dict(family="Segoe UI, Roboto, sans-serif", size=11),
            bgcolor='rgba(255, 255, 255, 0.95)',
            bordercolor='rgba(230, 230, 230, 0.8)',
            font_color=colors['dark']
        ),
        annotations=[
            dict(
                text="",  # Placeholder para posibles anotaciones
                showarrow=False,
                font=dict(family="Segoe UI, Roboto, sans-serif", size=10, color=colors['secondary'])
            )
        ]
    )
    
    # Estilo para los diferentes tipos de gráficos
    
    # Barras
    custom_template.data.bar = [
        go.Bar(
            marker=dict(
                line=dict(width=0.5, color='rgba(255, 255, 255, 0.5)'),
                opacity=0.85
            ),
            error_x=dict(thickness=1, width=4, color='#333'),
            error_y=dict(thickness=1, width=4, color='#333')
        )
    ]
    
    # Líneas
    custom_template.data.scatter = [
        go.Scatter(
            marker=dict(
                size=8,
                symbol='circle',
                line=dict(width=1, color='rgba(255, 255, 255, 0.8)')
            ),
            line=dict(width=2.5),
            error_x=dict(thickness=1, width=4, color='#333'),
            error_y=dict(thickness=1, width=4, color='#333')
        )
    ]
    
    # Pie
    custom_template.data.pie = [
        go.Pie(
            marker=dict(
                line=dict(color='rgba(255, 255, 255, 0.8)', width=1)
            ),
            textfont=dict(size=12, color='white'),
            insidetextorientation='radial',
            textinfo='percent+label',
            hoverinfo='label+percent+value',
            rotation=45
        )
    ]
    
    return custom_template

# Crear plantilla personalizada para gráficos de tendencia temporal
def create_trend_template():
    base_template = create_custom_template()
    trend_template = go.layout.Template(base_template)
    
    # Personalizaciones específicas para gráficos de tendencia
    trend_template.layout.update(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=7, label="7D", step="day", stepmode="backward"),
                    dict(count=1, label="1M", step="month", stepmode="backward"),
                    dict(count=3, label="3M", step="month", stepmode="backward"),
                    dict(count=6, label="6M", step="month", stepmode="backward"),
                    dict(count=1, label="1A", step="year", stepmode="backward"),
                    dict(step="all", label="Todo")
                ]),
                bgcolor='rgba(255, 255, 255, 0.8)',
                activecolor='rgba(52, 152, 219, 0.8)'
            ),
            rangeslider=dict(visible=False),
            type='date'
        )
    )
    
    return trend_template

# Estilos para diferentes tipos de gráficos
chart_styles = {
    'pie': {
        'hole': 0.4,
        'marker': {
            'colors': [
                '#3498db', '#e74c3c', '#2ecc71', '#f39c12', 
                '#9b59b6', '#1abc9c', '#34495e', '#f1c40f'
            ],
            'line': {'color': 'white', 'width': 2}
        },
        'textinfo': 'percent+label',
        'pull': [0.05, 0, 0, 0, 0]
    },
    'bar': {
        'opacity': 0.85,
        'marker_line_width': 1,
        'marker_line_color': 'white'
    },
    'line': {
        'line_width': 3,
        'marker_size': 8,
        'marker_symbol': 'circle',
        'marker_line_width': 1,
        'marker_line_color': 'white'
    }
}
