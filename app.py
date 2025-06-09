import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
import json
import re

# Importamos las funciones desde nuestro módulo data_loader
from data_loader import (
    load_data_from_mongodb,
    calculate_identity_theft_kpis,
    prepare_visualization_data
)

# Importamos el email sender (manejamos el import con try/except)
try:
    from email_sender import EmailAlertSender, send_dashboard_alerts
except ImportError:
    print("Warning: email_sender module not found. Email functionality will be disabled.")
    EmailAlertSender = None
    send_dashboard_alerts = None

# Cargamos los datos al iniciar la aplicación
df = load_data_from_mongodb()

# Crear la aplicación Dash con tema y hojas de estilo personalizadas
app = dash.Dash(
    __name__, 
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.1.1/css/all.min.css",
        "https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap"
    ],
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ],
    assets_folder='assets',
    suppress_callback_exceptions=True  # Agregamos esta línea para suprimir errores de componentes dinámicos
)

server = app.server

# Modal para vista previa del email
email_preview_modal = dbc.Modal([
    dbc.ModalHeader(dbc.ModalTitle([
        html.I(className="fas fa-eye me-2"),
        "Vista Previa del Email"
    ])),
    dbc.ModalBody([
        html.Div(id="email-preview-content")
    ]),
    dbc.ModalFooter(
        dbc.Button("Cerrar", id="close-email-preview", className="ms-auto", color="secondary")
    ),
], id="email-preview-modal", size="xl", scrollable=True)

# Modal para el aviso de privacidad
privacy_modal = dbc.Modal([
    dbc.ModalHeader(dbc.ModalTitle([
        html.I(className="fas fa-lock me-2"),
        "Aviso de Privacidad"
    ])),
    dbc.ModalBody([
        html.H5("Política de privacidad para el Dashboard de Detección de Robo de Identidad", className="mb-3"),
        
        html.P([
            html.Strong("Fecha de última actualización: "), 
            "9 de Mayo de 2025"
        ], className="mb-3"),
        
        html.P([
            "Esta política de privacidad describe cómo recopilamos, usamos y compartimos la información relacionada con las transacciones bancarias para la detección de fraudes y robos de identidad."
        ], className="mb-3"),

        html.P([
            "Este aviso de privacidad se fundamenta en las siguientes disposiciones legales:"
        ]),

        html.Ul([
            html.Li("Artículo 16 de la Constitución Política de los Estados Unidos Mexicanos"),
            html.Li("Nueva Ley Federal de Protección de Datos Personales en Posesión de los Particulares (NLFPDPPP), vigente desde marzo de 2025"),
            html.Li("Reglamento de la Ley Federal de Protección de Datos Personales en Posesión de los Particulares"),
            html.Li("Lineamientos del Aviso de Privacidad emitidos por la autoridad competente"),
            html.Li("Estándares internacionales: ISO/IEC 27001, ISO/IEC 27002, ISO/IEC 29100")
        ], className="mb-3"),
        
        html.P([
            "Este aviso describe cómo recopilamos, usamos y compartimos la información relacionada con las transacciones bancarias para la detección de fraudes y robos de identidad, en cumplimiento con la normativa mexicana vigente."
        ], className="mb-3"),
        
        html.H6("Información que recopilamos", className="mt-4 mb-2"),
        html.P([
            "Para el funcionamiento de este dashboard, procesamos los siguientes datos:"
        ]),
        html.Ul([
            html.Li("Datos de transacciones bancarias (fecha, hora, monto)"),
            html.Li("Información del comerciante (país, categoría, identificador)"),
            html.Li("Detalles de autenticación de tarjetas (CVV, coincidencias de fechas)"),
            html.Li("Indicadores de presencia física de tarjeta"),
            html.Li("Información geográfica de la transacción"),
        ], className="mb-3"),
        
        html.H6("Cómo usamos la información", className="mt-4 mb-2"),
        html.P([
            "La información recopilada se utiliza exclusivamente para:"
        ]),
        html.Ul([
            html.Li("Detección y prevención de actividades fraudulentas"),
            html.Li("Identificación de posibles casos de robo de identidad"),
            html.Li("Análisis estadístico para mejorar los sistemas de seguridad"),
            html.Li("Generación de alertas de seguridad para revisión"),
        ], className="mb-3"),
        
        html.H6("Seguridad de los datos", className="mt-4 mb-2"),
        html.P([
            "Implementamos medidas técnicas y organizativas apropiadas para proteger los datos personales contra pérdida, mal uso, acceso no autorizado, divulgación, alteración y destrucción."
        ], className="mb-3"),
        
        html.H6("Compartir información", className="mt-4 mb-2"),
        html.P([
            "No compartimos la información procesada con terceros excepto cuando sea requerido por ley o para proteger nuestros derechos legales."
        ], className="mb-3"),
        
        html.H6("Conservación de datos", className="mt-4 mb-2"),
        html.P([
            "Los datos utilizados en este dashboard se conservan durante el período necesario para cumplir con los fines establecidos en esta política de privacidad, a menos que se requiera un período de retención más largo por ley."
        ], className="mb-3"),
        
        html.H6("Sus derechos", className="mt-4 mb-2"),
        html.P([
            "Dependiendo de su ubicación, puede tener ciertos derechos en relación con sus datos personales, incluido el derecho a acceder, corregir, eliminar, restringir el procesamiento, la portabilidad de datos y objetar."
        ], className="mb-3"),
        
        html.H6("Cambios a esta política", className="mt-4 mb-2"),
        html.P([
            "Podemos actualizar esta política de privacidad periódicamente para reflejar cambios en nuestras prácticas. Le recomendamos revisar esta política regularmente."
        ], className="mb-3"),
        
        html.H6("Documento Adicional", className="mt-4 mb-2"),
        html.P([
            "Para más detalles sobre nuestras prácticas de privacidad, consulte nuestro ",
            html.A([
                html.I(className="fas fa-file-alt me-1"),
                "Aviso de Privacidad"
            ], href="/assets/aviso_privacidad_completo.pdf", target="_blank", className="text-decoration-none"),
            " que está disponible en formato PDF."
            ], className="mb-3"),

        html.H6("Contacto", className="mt-4 mb-2"),
        html.P([
            "Si tiene preguntas sobre esta política de privacidad, contáctenos en: ",
            html.A("privacidad@empresa.com", href="mailto:privacidad@empresa.com")
        ], className="mb-3"),
    ]),
    dbc.ModalFooter(
        dbc.Button("Cerrar", id="close-privacy", className="ms-auto", color="primary")
    ),
], id="privacy-modal", size="lg", scrollable=True)

# Sección de configuración de email
email_config_section = dbc.Row([
    dbc.Col([
        html.H5([
            html.I(className="fas fa-envelope me-2"), 
            "Configuración de Alertas por Email"
        ], className="text-primary mb-3"),
        dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.Label([
                        html.I(className="fas fa-users me-2"), 
                        "Destinatarios de alertas:"
                    ]),
                    dcc.Textarea(
                        id='email-recipients',
                        placeholder="Ingrese los emails separados por comas\nejemplo: admin@empresa.com, seguridad@empresa.com",
                        style={'width': '100%', 'height': 80},
                        className="mb-3"
                    ),
                ]),
                html.Div([
                    html.Label([
                        html.I(className="fas fa-edit me-2"), 
                        "Asunto personalizado (opcional):"
                    ]),
                    dcc.Input(
                        id='email-subject',
                        type='text',
                        placeholder="Asunto del email (se generará automáticamente si se deja vacío)",
                        style={'width': '100%'},
                        className="mb-3"
                    ),
                ]),
                html.Div([
                    dbc.Checklist(
                        options=[
                            {"label": " Adjuntar archivo CSV con los datos", "value": "attach_csv"},
                            {"label": " Enviar solo si hay alertas de alto riesgo (score > 5)", "value": "high_risk_only"}
                        ],
                        value=["attach_csv"],
                        id="email-options",
                        inline=True,
                        className="mb-3"
                    )
                ]),
                html.Div([
                    dbc.Button([
                        html.I(className="fas fa-paper-plane me-2"), 
                        "Enviar Reporte por Email"
                    ], 
                    id="send-email-btn", 
                    color="success", 
                    className="me-2",
                    disabled=True),
                    dbc.Button([
                        html.I(className="fas fa-eye me-2"), 
                        "Vista Previa del Email"
                    ], 
                    id="preview-email-btn", 
                    color="info", 
                    outline=True)
                ], className="d-grid gap-2 d-md-flex justify-content-md-start"),
                html.Div(id="email-status", className="mt-3")
            ])
        ], className="email-config-card")
    ], width=12)
])

# Layout del dashboard
app.layout = dbc.Container([
    
    dbc.Row([
        dbc.Col(html.H1([
                html.I(className="fas fa-shield-alt me-2"), 
                "Dashboard de Robo de Identidad en Transacciones Bancarias"
            ], 
            className="text-center app-header"), 
            width=12)
    ]),

    # Filtros
    dbc.Row([
        dbc.Col([
            html.H5([
                html.I(className="fas fa-filter me-2"), 
                "Filtros"
            ], className="text-primary mb-3"),
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.Label([
                            html.I(className="fas fa-calendar-alt me-2"), 
                            "Rango de fechas:"
                        ]),
                        dcc.DatePickerRange(
                            id='date-range',
                            start_date=df['transactionDateTime'].min().date(),
                            end_date=df['transactionDateTime'].max().date(),
                            start_date_placeholder_text="Fecha inicial",
                            end_date_placeholder_text="Fecha final",
                            className="mb-3 w-100"
                        ),
                    ]),
                    html.Div([
                        html.Label([
                            html.I(className="fas fa-globe-americas me-2"), 
                            "País:"
                        ]),
                        dcc.Dropdown(
                            id='country-filter',
                            options=[{'label': country, 'value': country} 
                                    for country in sorted(df['merchantCountryCode'].unique())],
                            multi=True,
                            placeholder="Seleccionar países",
                            className="mb-3"
                        ),
                    ]),
                    html.Div([
                        html.Label([
                            html.I(className="fas fa-store me-2"), 
                            "Categoría de comercio:"
                        ]),
                        dcc.Dropdown(
                            id='merchant-category-filter',
                            options=[{'label': f"Categoría {cat}", 'value': cat} 
                                    for cat in sorted(df['merchantCategoryCode'].unique())],
                            multi=True,
                            placeholder="Seleccionar categorías",
                            className="mb-3"
                        ),
                    ]),
                    dbc.Button([
                        html.I(className="fas fa-search me-2"), 
                        "Aplicar filtros"
                    ], id="apply-filter", color="primary", className="filter-button mt-2")
                ])
            ], className="filters-card")
        ], width=12)
    ], className="mb-4"),
    
    # Sección de configuración de email
    html.Hr(className="my-4"),
    email_config_section,
    
    # KPIs principales
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-credit-card fa-2x text-primary mb-3")
                    ], className="text-center"),
                    html.H5("Total Transacciones", className="card-title text-center"),
                    html.H3(id="total-transactions", className="card-text text-center text-primary"),
                ])
            ], className="kpi-card kpi-total mb-4")
        ], width=12, lg=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-exclamation-triangle fa-2x text-danger mb-3")
                    ], className="text-center"),
                    html.H5("Transacciones Fraudulentas", className="card-title text-center"),
                    html.H3(id="fraud-transactions", className="card-text text-center text-danger"),
                    html.P(id="fraud-rate", className="card-text text-center")
                ])
            ], className="kpi-card kpi-fraud mb-4")
        ], width=12, lg=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-user-secret fa-2x text-warning mb-3")
                    ], className="text-center"),
                    html.H5("Posible Robo de Identidad", className="card-title text-center"),
                    html.H3(id="identity-theft-count", className="card-text text-center text-warning"),
                    html.P(id="identity-theft-rate", className="card-text text-center")
                ])
            ], className="kpi-card kpi-identity mb-4")
        ], width=12, lg=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-key fa-2x text-success mb-3")
                    ], className="text-center"),
                    html.H5("CVV No Coincide", className="card-title text-center"),
                    html.H3(id="cvv-mismatch", className="card-text text-center text-success"),
                    html.P(id="cvv-mismatch-rate", className="card-text text-center")
                ])
            ], className="kpi-card kpi-cvv mb-4")
        ], width=12, lg=3)
    ], className="mb-4"),
    
    # Gráficos principales
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-chart-line me-2"), 
                    "Tendencia Temporal de Fraudes"
                ]),
                dbc.CardBody([
                    dcc.Graph(id='fraud-trend-chart')
                ])
            ], className="chart-card")
        ], width=12, lg=8),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-fingerprint me-2"), 
                    "Indicadores de Robo de Identidad"
                ]),
                dbc.CardBody([
                    dcc.Graph(id='identity-theft-indicators-chart')
                ])
            ], className="chart-card")
        ], width=12, lg=4)
    ]),
    
    # Segunda fila de gráficos
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-globe me-2"), 
                    "Top 10 Países con Mayor Fraude"
                ]),
                dbc.CardBody([
                    dcc.Graph(id='fraud-by-country-chart')
                ])
            ], className="chart-card")
        ], width=12, lg=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-store me-2"), 
                    "Tasa de Fraude por Categoría de Comercio"
                ]),
                dbc.CardBody([
                    dcc.Graph(id='merchant-category-chart')
                ])
            ], className="chart-card")
        ], width=12, lg=6)
    ]),
    
    # Tercera fila de gráficos
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="fas fa-dollar-sign me-2"), 
                    "Distribución de Fraudes por Monto de Transacción"
                ]),
                dbc.CardBody([
                    dcc.Graph(id='amount-distribution-chart')
                ])
            ], className="chart-card")
        ], width=12)
    ]),
    
    # Tabla detallada de alertas recientes
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H5([
                        html.I(className="fas fa-bell me-2"), 
                        "Alertas Recientes de Posible Robo de Identidad"
                    ]),
                    html.Small([
                        html.I(className="fas fa-info-circle me-1"), 
                        "Top 10 transacciones con mayor probabilidad de ser robo de identidad"
                    ])
                ]),
                dbc.CardBody([
                    html.Div(id='recent-alerts-table', className="alerts-table")
                ])
            ], className="chart-card")
        ], width=12)
    ]),
    
    # Footer con enlace de aviso de privacidad
    dbc.Row([
        dbc.Col(html.Footer([
            html.P([
                html.I(className="fas fa-shield-alt me-2"),
                "Dashboard creado para análisis de robos de identidad - © 2025 ",
                html.A("Aviso de Privacidad", id="privacy-link", href="#", className="privacy-link ms-2")
            ])
        ], className="footer"), width=12)
    ]),
    
    # Modales - IMPORTANTE: Los modales deben estar dentro del layout principal
    email_preview_modal,
    privacy_modal

], fluid=True)

# Función auxiliar para obtener datos filtrados
def get_filtered_data(start_date, end_date, countries, merchant_categories):
    """Aplica filtros a los datos y retorna el DataFrame filtrado"""
    filtered_df = df.copy()
    
    if start_date and end_date:
        filtered_df = filtered_df[
            (pd.to_datetime(filtered_df['transactionDateTime']).dt.date >= pd.to_datetime(start_date).date()) & 
            (pd.to_datetime(filtered_df['transactionDateTime']).dt.date <= pd.to_datetime(end_date).date())
        ]
    
    if countries and len(countries) > 0:
        filtered_df = filtered_df[filtered_df['merchantCountryCode'].isin(countries)]
        
    if merchant_categories and len(merchant_categories) > 0:
        filtered_df = filtered_df[filtered_df['merchantCategoryCode'].isin(merchant_categories)]
    
    return filtered_df

# Función auxiliar para calcular score de riesgo y generar alertas
def generate_risk_alerts(filtered_df, high_risk_only=False):
    """Genera alertas de riesgo basadas en indicadores de robo de identidad"""
    # Identificar transacciones con alta probabilidad de ser robo de identidad
    id_theft_indicators = (
        (filtered_df['cardCVV'] != filtered_df['enteredCVV']) | 
        (~filtered_df['expirationDateKeyInMatch']) | 
        (filtered_df['acqCountry'] != filtered_df['merchantCountryCode'])
    ) & (~filtered_df['cardPresent'])
    
    potential_id_theft = filtered_df[id_theft_indicators].copy()
    
    if len(potential_id_theft) == 0:
        return potential_id_theft
    
    # Calcula un "score" de riesgo de robo de identidad
    potential_id_theft['risk_score'] = 0
    potential_id_theft.loc[potential_id_theft['cardCVV'] != potential_id_theft['enteredCVV'], 'risk_score'] += 3
    potential_id_theft.loc[~potential_id_theft['expirationDateKeyInMatch'], 'risk_score'] += 2
    potential_id_theft.loc[potential_id_theft['acqCountry'] != potential_id_theft['merchantCountryCode'], 'risk_score'] += 2
    potential_id_theft.loc[~potential_id_theft['cardPresent'], 'risk_score'] += 1
    
    # Filtrar por alto riesgo si se especifica
    if high_risk_only:
        potential_id_theft = potential_id_theft[potential_id_theft['risk_score'] > 5]
    
    return potential_id_theft.sort_values('risk_score', ascending=False)

# Función para simular envío de email (reemplazar con implementación real)
def simulate_email_send(recipients, subject, kpis, alerts_count, attach_csv=False, high_risk_only=False):
    """
    Simula el envío de email. Reemplazar con implementación real.
    Retorna (success: bool, message: str)
    """
    try:
        # Aquí irían las llamadas reales a tu sistema de email
        # Por ejemplo:
        # if EmailAlertSender and send_dashboard_alerts:
        #     result = send_dashboard_alerts(recipients, subject, filtered_df, kpis, attach_csv, high_risk_only)
        #     return True, f"Email enviado exitosamente a {len(recipients)} destinatarios"
        
        # Simulación de envío exitoso
        import time
        time.sleep(1)  # Simular tiempo de procesamiento
        
        return True, f"Email enviado exitosamente a {len(recipients)} destinatario(s)"
        
    except Exception as e:
        return False, f"Error al enviar email: {str(e)}"

# Callbacks para actualizar los componentes del dashboard
@app.callback(
    [
        Output('total-transactions', 'children'),
        Output('fraud-transactions', 'children'),
        Output('fraud-rate', 'children'),
        Output('identity-theft-count', 'children'),
        Output('identity-theft-rate', 'children'),
        Output('cvv-mismatch', 'children'),
        Output('cvv-mismatch-rate', 'children'),
        Output('fraud-trend-chart', 'figure'),
        Output('identity-theft-indicators-chart', 'figure'),
        Output('fraud-by-country-chart', 'figure'),
        Output('merchant-category-chart', 'figure'),
        Output('amount-distribution-chart', 'figure'),
        Output('recent-alerts-table', 'children')
    ],
    [Input('apply-filter', 'n_clicks')],
    [
        State('date-range', 'start_date'),
        State('date-range', 'end_date'),
        State('country-filter', 'value'),
        State('merchant-category-filter', 'value')
    ]
)
def update_dashboard(n_clicks, start_date, end_date, countries, merchant_categories):
    # Obtener datos filtrados
    filtered_df = get_filtered_data(start_date, end_date, countries, merchant_categories)
    
    # Calcular KPIs
    kpis = calculate_identity_theft_kpis(filtered_df)
    viz_data = prepare_visualization_data(filtered_df)
    
    # Definir un template de colores personalizado para los gráficos
    custom_template = go.layout.Template()
    custom_template.layout.plot_bgcolor = 'rgba(248, 249, 250, 0.5)'
    custom_template.layout.paper_bgcolor = 'rgba(255, 255, 255, 0)'
    custom_template.layout.font = dict(family="Segoe UI, sans-serif")
    custom_template.layout.margin = dict(l=40, r=40, t=40, b=40)
    
    # Crear gráficos mejorados
    # 1. Tendencia temporal de fraudes
    fraud_trend_fig = px.line(
        viz_data['fraud_trend'], 
        x='transaction_date', 
        y=['transactions', 'fraud_cases'],
        title='Tendencia de Transacciones y Fraudes',
        labels={'value': 'Cantidad', 'transaction_date': 'Fecha', 'variable': 'Tipo'},
        color_discrete_map={'transactions': '#3498db', 'fraud_cases': '#e74c3c'}
    )
    
    # Añadimos la tasa de fraude como un eje secundario
    fraud_trend_fig.add_bar(
        x=viz_data['fraud_trend']['transaction_date'],
        y=viz_data['fraud_trend']['fraud_rate'],
        name='Tasa de Fraude (%)',
        marker_color='rgba(255, 152, 0, 0.6)',
        yaxis='y2'
    )
    
    fraud_trend_fig.update_layout(
        template=custom_template,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        yaxis=dict(title=dict(text='Cantidad', font=dict(size=12)), gridcolor='rgba(230, 230, 230, 0.8)'),
        yaxis2=dict(
            title=dict(text='Tasa de Fraude (%)', font=dict(color='#ff9800', size=12)),
            tickfont=dict(color='#ff9800'),
            anchor='x',
            overlaying='y',
            side='right',
            gridcolor='rgba(255, 152, 0, 0.1)'
        ),
        hovermode='x unified'
    )
    
    # 2. Indicadores de robo de identidad
    id_theft_indicators_fig = px.bar(
        viz_data['id_theft_indicators'],
        y='indicador',
        x='tasa_fraude',
        orientation='h',
        title='Tasa de Fraude por Indicador',
        labels={'tasa_fraude': 'Tasa de Fraude (%)', 'indicador': 'Indicador'},
        color='tasa_fraude',
        color_continuous_scale=[(0, "#bb7eec"), (0.5, "#4da6fe"), (1, "#fe485a")]
    )
    
    id_theft_indicators_fig.update_layout(
        template=custom_template,
        xaxis=dict(title=dict(text='Tasa de Fraude (%)', font=dict(size=12)), gridcolor='rgba(230, 230, 230, 0.8)'),
        yaxis=dict(title='', automargin=True),
    )
    
    # 3. Distribución geográfica de fraudes
    fraud_by_country_fig = px.pie(
        viz_data['fraud_by_country'],
        names='merchantCountryCode',
        values='fraud_count',
        title='Top 10 Países con Mayor Número de Fraudes',
        labels={'fraud_count': 'Casos de Fraude', 'merchantCountryCode': 'País'},
        color='fraud_count',
        color_discrete_sequence=px.colors.sequential.Blues_r
    )
    
    fraud_by_country_fig.update_layout(
        template=custom_template,
        xaxis=dict(title=dict(text='País', font=dict(size=12)), tickangle=45, automargin=True),
        yaxis=dict(title=dict(text='Casos de Fraude', font=dict(size=12)), gridcolor='rgba(230, 230, 230, 0.8)')
    )
    
    # 4. Categorías de comercios con mayor tasa de fraude
    merchant_category_fig = px.bar(
        viz_data['merchant_fraud'],
        x='merchantCategoryCode',
        y='fraud_rate',
        title='Top 10 Categorías de Comercio con Mayor Tasa de Fraude',
        labels={'fraud_rate': 'Tasa de Fraude (%)', 'merchantCategoryCode': 'Categoría'},
        color='fraud_rate',
        color_continuous_scale=[(0, "#ffe0b2"), (0.5, "#ffb74d"), (1, "#e65100")]
    )
    
    merchant_category_fig.update_layout(
        template=custom_template,
        xaxis=dict(title=dict(text='Categoría de Comercio', font=dict(size=12)), tickangle=45, automargin=True),
        yaxis=dict(title=dict(text='Tasa de Fraude (%)', font=dict(size=12)), gridcolor='rgba(230, 230, 230, 0.8)')
    )
    
    # 5. Distribución por montos
    amount_dist_fig = px.bar(
        viz_data['amount_dist'],
        x='amount_range',
        y=['transactions', 'fraud_cases'],
        title='Distribución de Transacciones y Fraudes por Monto',
        labels={'value': 'Cantidad', 'amount_range': 'Rango de Monto ($)', 'variable': 'Tipo'},
        barmode='group',
        color_discrete_map={'transactions': '#3498db', 'fraud_cases': '#e74c3c'},
        log_y=True
    )
    
    amount_dist_fig.add_scatter(
        x=viz_data['amount_dist']['amount_range'],
        y=viz_data['amount_dist']['fraud_rate'],
        name='Tasa de Fraude (%)',
        line=dict(color='#ff9800', width=3),
        marker=dict(size=8, color='#ff9800'),
        yaxis='y2',
        mode='lines+markers'
    )
    
    amount_dist_fig.update_layout(
        template=custom_template,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        xaxis=dict(title=dict(text='Rango de Monto ($)', font=dict(size=12)), tickangle=0, automargin=True),
        yaxis=dict(title=dict(text='Cantidad', font=dict(size=12)), gridcolor='rgba(230, 230, 230, 0.8)'),
        yaxis2=dict(
            title=dict(text='Tasa de Fraude (%)', font=dict(color='#ff9800', size=12)),
            tickfont=dict(color='#ff9800'),
            anchor='x',
            overlaying='y',
            side='right',
            gridcolor='rgba(255, 152, 0, 0.1)'
        ),
        hovermode='x unified'
    )
    
    # Generar tabla de alertas recientes
    recent_alerts = generate_risk_alerts(filtered_df).head(10)
    
    # Crear tabla de alertas mejorada
    if len(recent_alerts) > 0:
        alert_table = dbc.Table([
            html.Thead(
                html.Tr([
                    html.Th([html.I(className="fas fa-id-card me-2"), "Cliente ID"]),
                    html.Th([html.I(className="fas fa-calendar me-2"), "Fecha/Hora"]),
                    html.Th([html.I(className="fas fa-dollar-sign me-2"), "Monto"]),
                    html.Th([html.I(className="fas fa-store me-2"), "Comercio"]),
                    html.Th([html.I(className="fas fa-globe me-2"), "País"]),
                    html.Th([html.I(className="fas fa-exclamation-circle me-2"), "Score de Riesgo"]),
                    html.Th([html.I(className="fas fa-flag me-2"), "Indicadores"])
                ], className="table-primary")
            ),
            html.Tbody([
                html.Tr([
                    html.Td(row['customerId']),
                    html.Td(str(row['transactionDateTime'])),
                    html.Td(f"${row['transactionAmount']:.2f}"),
                    html.Td(row['merchantName']),
                    html.Td([
                        html.I(className="fas fa-map-marker-alt me-1"),
                        f"{row['merchantCountryCode']}"
                    ]),
                    html.Td(html.Span(f"{row['risk_score']}", 
                                     className="badge bg-danger" if row['risk_score'] > 5 else "badge bg-warning")),
                    html.Td([
                        html.Span("CVV incorrecto", className="badge badge-cvv-incorrecto me-1") 
                            if row['cardCVV'] != row['enteredCVV'] else "",
                        html.Span("Fecha exp. incorrecta", className="badge badge-fecha-exp-incorrecta me-1") 
                            if not row['expirationDateKeyInMatch'] else "",
                        html.Span("País diferente", className="badge badge-pais-diferente me-1") 
                            if row['acqCountry'] != row['merchantCountryCode'] else "",
                        html.Span("Tarjeta no presente", className="badge badge-tarjeta-no-presente me-1") 
                            if not row['cardPresent'] else ""
                    ])
                ], className="table-hover") for _, row in recent_alerts.iterrows()
            ])
        ], bordered=True, hover=True, striped=True, responsive=True, className="table-sm")
    else:
        alert_table = dbc.Alert([
            html.I(className="fas fa-info-circle me-2"),
            "No se encontraron alertas de robo de identidad en el período seleccionado."
        ], color="info")
    
    return (
        f"{kpis['total_transactions']:,}",
        f"{kpis['fraud_transactions']:,}",
        f"({kpis['fraud_rate']:.2f}%)",
        f"{kpis['potential_identity_theft_count']:,}",
        f"({kpis['potential_identity_theft_rate']:.2f}%)",
        f"{kpis['cvv_mismatch_count']:,}",
        f"Tasa de fraude: {kpis['cvv_mismatch_fraud_rate']:.2f}%",
        fraud_trend_fig,
        id_theft_indicators_fig,
        fraud_by_country_fig,
        merchant_category_fig,
        amount_dist_fig,
        alert_table
    )

# Callback para el modal de privacidad
@app.callback(
    Output('privacy-modal', 'is_open'),
    [Input('privacy-link', 'n_clicks'), Input('close-privacy', 'n_clicks')],
    [State('privacy-modal', 'is_open')]
)
def toggle_privacy_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

# Callback para habilitar/deshabilitar botón de envío basado en destinatarios
@app.callback(
    Output('send-email-btn', 'disabled'),
    [Input('email-recipients', 'value')]
)
def toggle_send_button(recipients):
    if recipients and recipients.strip():
        return False
    return True

# Callback para vista previa del email
@app.callback(
    [Output('email-preview-modal', 'is_open'),
     Output('email-preview-content', 'children')],
    [Input('preview-email-btn', 'n_clicks'),
     Input('close-email-preview', 'n_clicks')],
    [State('email-preview-modal', 'is_open'),
     State('email-recipients', 'value'),
     State('email-subject', 'value'),
     State('email-options', 'value'),
     State('date-range', 'start_date'),
     State('date-range', 'end_date'),
     State('country-filter', 'value'),
     State('merchant-category-filter', 'value')]
)
def toggle_email_preview(preview_clicks, close_clicks, is_open, recipients, subject, options, 
                        start_date, end_date, countries, merchant_categories):
    ctx = dash.callback_context
    
    if not ctx.triggered:
        return False, []
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == 'close-email-preview':
        return False, []
    
    if trigger_id == 'preview-email-btn' and preview_clicks:
        # Obtener datos filtrados
        filtered_df = get_filtered_data(start_date, end_date, countries, merchant_categories)
        
        # Calcular KPIs para el email
        kpis = calculate_identity_theft_kpis(filtered_df)
        
        # Generar alertas
        high_risk_only = options and 'high_risk_only' in options
        alerts = generate_risk_alerts(filtered_df, high_risk_only)
        
        # Generar contenido del email
        email_subject_text = subject if subject else f"Reporte de Seguridad - Dashboard de Robo de Identidad - {datetime.now().strftime('%d/%m/%Y')}"
        recipient_list = [email.strip() for email in recipients.split(',') if email.strip()] if recipients else []
        
        preview_content = [
            html.Div([
                html.H5("Vista Previa del Email", className="text-primary mb-3"),
                
                html.Div([
                    html.Strong("Para: "), 
                    html.Span(", ".join(recipient_list) if recipient_list else "No se han especificado destinatarios")
                ], className="mb-2"),
                
                html.Div([
                    html.Strong("Asunto: "), 
                    html.Span(email_subject_text)
                ], className="mb-3"),
                
                html.Hr(),
                
                html.Div([
                    html.H6("Contenido del mensaje:", className="mb-3"),
                    
                    html.P(f"Estimado equipo de seguridad,", className="mb-3"),
                    
                    html.P(f"Se adjunta el reporte automatizado del Dashboard de Detección de Robo de Identidad correspondiente al {datetime.now().strftime('%d de %B de %Y')}.", className="mb-3"),
                    
                    html.H6("Resumen Ejecutivo:", className="mb-2"),
                    html.Ul([
                        html.Li(f"Total de transacciones analizadas: {kpis['total_transactions']:,}"),
                        html.Li(f"Transacciones fraudulentas detectadas: {kpis['fraud_transactions']:,} ({kpis['fraud_rate']:.2f}%)"),
                        html.Li(f"Posibles casos de robo de identidad: {kpis['potential_identity_theft_count']:,} ({kpis['potential_identity_theft_rate']:.2f}%)"),
                        html.Li(f"Transacciones con CVV incorrecto: {kpis['cvv_mismatch_count']:,}")
                    ], className="mb-3"),
                    
                    html.H6("Alertas de Riesgo:", className="mb-2"),
                    html.P(f"Se han identificado {len(alerts)} transacciones con {'alto ' if high_risk_only else ''}riesgo de robo de identidad{' (score > 5)' if high_risk_only else ''}.", 
                          className="text-danger mb-3" if len(alerts) > 0 else "text-success mb-3") if len(alerts) > 0 else html.P("No se identificaron alertas de riesgo en este período.", className="text-success mb-3"),
                    
                    html.P("Se recomienda revisar las transacciones marcadas como riesgo para tomar las acciones preventivas correspondientes.", className="mb-3") if len(alerts) > 0 else html.Div(),
                    
                    html.P([
                        "Para más detalles, consulte el dashboard completo en: ",
                        html.A("Dashboard de Seguridad", href="#", className="text-decoration-none")
                    ], className="mb-3"),
                    
                    html.P("Atentamente,", className="mb-1"),
                    html.P("Sistema Automatizado de Detección de Fraudes", className="mb-3"),
                    
                    html.Hr(),
                    
                    html.Small([
                        html.I(className="fas fa-info-circle me-1"),
                        "Este es un reporte automatizado generado por el sistema de detección de robo de identidad."
                    ], className="text-muted")
                ], className="email-body-preview p-3", style={'background-color': '#f8f9fa', 'border-radius': '5px'}),
                
                html.Hr(),
                
                html.Div([
                    html.H6("Opciones seleccionadas:", className="mb-2"),
                    html.Ul([
                        html.Li("✓ Adjuntar archivo CSV con los datos") if options and 'attach_csv' in options else html.Li("✗ No adjuntar archivo CSV"),
                        html.Li("✓ Enviar solo alertas de alto riesgo") if options and 'high_risk_only' in options else html.Li("✗ Incluir todas las alertas")
                    ])
                ], className="mt-3")
            ])
        ]
        
        return True, preview_content
    
    return is_open, []

# Callback para enviar email
@app.callback(
    Output('email-status', 'children'),
    [Input('send-email-btn', 'n_clicks')],
    [State('email-recipients', 'value'),
     State('email-subject', 'value'),
     State('email-options', 'value'),
     State('date-range', 'start_date'),
     State('date-range', 'end_date'),
     State('country-filter', 'value'),
     State('merchant-category-filter', 'value')],
    prevent_initial_call=True
)
def send_email_report(n_clicks, recipients, subject, options, start_date, end_date, countries, merchant_categories):
    if not n_clicks or not recipients:
        return ""
    
    try:
        # Obtener datos filtrados
        filtered_df = get_filtered_data(start_date, end_date, countries, merchant_categories)
        
        # Calcular KPIs
        kpis = calculate_identity_theft_kpis(filtered_df)
        
        # Preparar datos para el email
        recipient_list = [email.strip() for email in recipients.split(',') if email.strip()]
        email_subject = subject if subject else f"Reporte de Seguridad - Dashboard de Robo de Identidad - {datetime.now().strftime('%d/%m/%Y')}"
        
        # Determinar opciones
        attach_csv = options and 'attach_csv' in options
        high_risk_only = options and 'high_risk_only' in options
        
        # Generar alertas con el formato correcto para el email sender
        alerts = generate_risk_alerts(filtered_df, high_risk_only).head(10)  # Top 10 alertas
        
        # Preparar las alertas en el formato que espera tu email_sender
        if len(alerts) > 0:
            # Asegurar que el DataFrame tenga todas las columnas necesarias
            required_columns = ['customerId', 'transactionDateTime', 'transactionAmount', 
                              'merchantName', 'merchantCountryCode', 'risk_score', 
                              'cardCVV', 'enteredCVV', 'expirationDateKeyInMatch', 
                              'acqCountry', 'cardPresent']
            
            # Verificar y agregar columnas faltantes si es necesario
            for col in required_columns:
                if col not in alerts.columns:
                    if col == 'risk_score':
                        alerts[col] = 0  # Ya debería estar calculado
                    else:
                        alerts[col] = 'N/A'  # Valor por defecto
        
        # Verificar si el módulo de email está disponible
        if EmailAlertSender is None or send_dashboard_alerts is None:
            # Usar función de simulación
            success, message = simulate_email_send(
                recipient_list, 
                email_subject, 
                kpis, 
                len(alerts), 
                attach_csv, 
                high_risk_only
            )
        else:
            # Usar implementación real de email con el formato correcto
            try:
                # Asegurar que kpis sea un diccionario válido
                summary_stats = {
                    'total_transactions': kpis.get('total_transactions', 0),
                    'fraud_transactions': kpis.get('fraud_transactions', 0),
                    'fraud_rate': kpis.get('fraud_rate', 0.0),
                    'potential_identity_theft_count': kpis.get('potential_identity_theft_count', 0),
                    'potential_identity_theft_rate': kpis.get('potential_identity_theft_rate', 0.0),
                    'cvv_mismatch_count': kpis.get('cvv_mismatch_count', 0),
                    'cvv_mismatch_fraud_rate': kpis.get('cvv_mismatch_fraud_rate', 0.0)
                }
                
                # Llamar a la función con el formato correcto (3 parámetros según tu implementación)
                result = send_dashboard_alerts(alerts, summary_stats, recipient_list)
                
                if result:
                    success = True
                    message = f"Email enviado exitosamente a {len(recipient_list)} destinatario(s)"
                else:
                    success = False
                    message = "Error: La función send_dashboard_alerts retornó False"
                    
            except Exception as email_error:
                success = False
                message = f"Error al enviar el email: {str(email_error)}"
                
                # Intentar método alternativo si falla
                try:
                    # Crear instancia directa de EmailAlertSender
                    sender = EmailAlertSender()
                    result = sender.send_alert_email(
                        alerts_df=alerts,
                        summary_stats=summary_stats,
                        recipients=recipient_list,
                        subject=email_subject,
                        attach_csv=attach_csv
                    )
                    
                    if result:
                        success = True
                        message = f"Email enviado exitosamente a {len(recipient_list)} destinatario(s) (método directo)"
                    else:
                        success = False
                        message = "Error: EmailAlertSender.send_alert_email retornó False"
                        
                except Exception as direct_error:
                    success = False
                    message = f"Error con método directo: {str(direct_error)}"
        
        # Generar mensaje de respuesta
        if success:
            return dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                html.Div([
                    html.Strong("¡Email enviado exitosamente!"),
                    html.Br(),
                    html.Small([
                        f"Destinatarios: {', '.join(recipient_list)}",
                        html.Br(),
                        f"Asunto: {email_subject}",
                        html.Br(),
                        f"Alertas incluidas: {len(alerts)}",
                        html.Br(),
                        f"Adjunto CSV: {'Sí' if attach_csv else 'No'}",
                        html.Br(),
                        f"Solo alto riesgo: {'Sí' if high_risk_only else 'No'}"
                    ])
                ])
            ], color="success", dismissable=True, duration=10000)
        else:
            return dbc.Alert([
                html.I(className="fas fa-times-circle me-2"),
                html.Div([
                    html.Strong("Error al enviar el email"),
                    html.Br(),
                    html.Small(message)
                ])
            ], color="danger", dismissable=True)
    
    except Exception as e:
        return dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error al procesar la solicitud: {str(e)}"
        ], color="danger", dismissable=True)

if __name__ == '__main__':
    # Importamos la configuración
    from config import DEBUG, HOST, PORT
    
    # Iniciamos la aplicación con los parámetros de configuración
    app.run(debug=DEBUG, port=PORT)