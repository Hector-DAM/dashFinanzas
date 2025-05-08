import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta

# Importamos las funciones desde nuestro módulo data_loader
from data_loader import (
    load_data_from_mongodb,
    calculate_identity_theft_kpis,
    prepare_visualization_data
)

# Cargamos los datos al iniciar la aplicación
df = load_data_from_mongodb()

# Crear la aplicación Dash
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server  # Esto es lo que Render utilizará

# Layout del dashboard
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Dashboard de Robo de Identidad en Transacciones Bancarias", 
                        className="text-center bg-primary text-white p-3 mb-4"), 
                width=12)
    ]),
    
    # Filtros
    dbc.Row([
        dbc.Col([
            html.H5("Filtros", className="text-primary"),
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.Label("Rango de fechas:"),
                        dcc.DatePickerRange(
                            id='date-range',
                            start_date=df['transactionDateTime'].min().date(),
                            end_date=df['transactionDateTime'].max().date(),
                            start_date_placeholder_text="Fecha inicial",
                            end_date_placeholder_text="Fecha final",
                            className="mb-2"
                        ),
                    ]),
                    html.Div([
                        html.Label("País:"),
                        dcc.Dropdown(
                            id='country-filter',
                            options=[{'label': country, 'value': country} 
                                    for country in sorted(df['merchantCountryCode'].unique())],
                            multi=True,
                            placeholder="Seleccionar países"
                        ),
                    ], className="mb-2"),
                    html.Div([
                        html.Label("Categoría de comercio:"),
                        dcc.Dropdown(
                            id='merchant-category-filter',
                            options=[{'label': f"Categoría {cat}", 'value': cat} 
                                    for cat in sorted(df['merchantCategoryCode'].unique())],
                            multi=True,
                            placeholder="Seleccionar categorías"
                        ),
                    ], className="mb-2"),
                    dbc.Button("Aplicar filtros", id="apply-filter", color="primary", className="mt-2"),
                ])
            ], className="mb-4")
        ], width=12)
    ]),
    
    # KPIs principales
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Total Transacciones", className="card-title text-center"),
                    html.H3(id="total-transactions", className="card-text text-center text-primary"),
                ])
            ], className="mb-4")
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Transacciones Fraudulentas", className="card-title text-center"),
                    html.H3(id="fraud-transactions", className="card-text text-center text-danger"),
                    html.P(id="fraud-rate", className="card-text text-center")
                ])
            ], className="mb-4")
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Posible Robo de Identidad", className="card-title text-center"),
                    html.H3(id="identity-theft-count", className="card-text text-center text-warning"),
                    html.P(id="identity-theft-rate", className="card-text text-center")
                ])
            ], className="mb-4")
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("CVV No Coincide", className="card-title text-center"),
                    html.H3(id="cvv-mismatch", className="card-text text-center text-info"),
                    html.P(id="cvv-mismatch-rate", className="card-text text-center")
                ])
            ], className="mb-4")
        ], width=3)
    ]),
    
    # Gráficos principales
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Tendencia Temporal de Fraudes"),
                dbc.CardBody([
                    dcc.Graph(id='fraud-trend-chart')
                ])
            ], className="mb-4")
        ], width=8),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Indicadores de Robo de Identidad"),
                dbc.CardBody([
                    dcc.Graph(id='identity-theft-indicators-chart')
                ])
            ], className="mb-4")
        ], width=4)
    ]),
    
    # Segunda fila de gráficos
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Top 10 Países con Mayor Fraude"),
                dbc.CardBody([
                    dcc.Graph(id='fraud-by-country-chart')
                ])
            ], className="mb-4")
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Tasa de Fraude por Categoría de Comercio"),
                dbc.CardBody([
                    dcc.Graph(id='merchant-category-chart')
                ])
            ], className="mb-4")
        ], width=6)
    ]),
    
    # Tercera fila de gráficos
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Distribución de Fraudes por Monto de Transacción"),
                dbc.CardBody([
                    dcc.Graph(id='amount-distribution-chart')
                ])
            ], className="mb-4")
        ], width=12)
    ]),
    
    # Tabla detallada de alertas recientes
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H5("Alertas Recientes de Posible Robo de Identidad"),
                    html.Small("Top 10 transacciones con mayor probabilidad de ser robo de identidad")
                ]),
                dbc.CardBody([
                    html.Div(id='recent-alerts-table')
                ])
            ], className="mb-4")
        ], width=12)
    ]),
    
    # Footer
    dbc.Row([
        dbc.Col(html.Footer([
            html.P("Dashboard creado para análisis de robos de identidad - © 2025", className="text-center")
        ]), width=12)
    ])
], fluid=True)

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
    Input('apply-filter', 'n_clicks'),
    [
        State('date-range', 'start_date'),
        State('date-range', 'end_date'),
        State('country-filter', 'value'),
        State('merchant-category-filter', 'value')
    ]
)
def update_dashboard(n_clicks, start_date, end_date, countries, merchant_categories):
    # Utilizamos una copia global de los datos
    filtered_df = df.copy()
    
    # Aplicar filtros si están disponibles
    if start_date and end_date:
        filtered_df = filtered_df[(pd.to_datetime(filtered_df['transactionDateTime']).dt.date >= pd.to_datetime(start_date).date()) & 
                              (pd.to_datetime(filtered_df['transactionDateTime']).dt.date <= pd.to_datetime(end_date).date())]
    
    if countries and len(countries) > 0:
        filtered_df = filtered_df[filtered_df['merchantCountryCode'].isin(countries)]
        
    if merchant_categories and len(merchant_categories) > 0:
        filtered_df = filtered_df[filtered_df['merchantCategoryCode'].isin(merchant_categories)]
    
    # Calcular KPIs
    kpis = calculate_identity_theft_kpis(filtered_df)
    viz_data = prepare_visualization_data(filtered_df)
    
    # Crear gráficos
    # 1. Tendencia temporal de fraudes
    fraud_trend_fig = px.line(
        viz_data['fraud_trend'], 
        x='transaction_date', 
        y=['transactions', 'fraud_cases'],
        title='Tendencia de Transacciones y Fraudes',
        labels={'value': 'Cantidad', 'transaction_date': 'Fecha', 'variable': 'Tipo'}
    )
    
    # Añadimos la tasa de fraude como un eje secundario
    fraud_trend_fig.add_bar(
        x=viz_data['fraud_trend']['transaction_date'],
        y=viz_data['fraud_trend']['fraud_rate'],
        name='Tasa de Fraude (%)',
        yaxis='y2'
    )
    
    fraud_trend_fig.update_layout(
        yaxis2=dict(
            title='Tasa de Fraude (%)',
            titlefont=dict(color='red'),
            tickfont=dict(color='red'),
            anchor='x',
            overlaying='y',
            side='right'
        ),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
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
        color_continuous_scale='Reds'
    )
    
    # 3. Distribución geográfica de fraudes
    fraud_by_country_fig = px.bar(
        viz_data['fraud_by_country'],
        x='merchantCountryCode',
        y='fraud_count',
        title='Top 10 Países con Mayor Número de Fraudes',
        labels={'fraud_count': 'Casos de Fraude', 'merchantCountryCode': 'País'},
        color='fraud_count',
        color_continuous_scale='Blues'
    )
    
    # 4. Categorías de comercios con mayor tasa de fraude
    merchant_category_fig = px.bar(
        viz_data['merchant_fraud'],
        x='merchantCategoryCode',
        y='fraud_rate',
        title='Top 10 Categorías de Comercio con Mayor Tasa de Fraude',
        labels={'fraud_rate': 'Tasa de Fraude (%)', 'merchantCategoryCode': 'Categoría'},
        color='fraud_rate',
        color_continuous_scale='Oranges'
    )
    
    # 5. Distribución por montos
    amount_dist_fig = px.bar(
        viz_data['amount_dist'],
        x='amount_range',
        y=['transactions', 'fraud_cases'],
        title='Distribución de Transacciones y Fraudes por Monto',
        labels={'value': 'Cantidad', 'amount_range': 'Rango de Monto ($)', 'variable': 'Tipo'},
        barmode='group'
    )
    
    amount_dist_fig.add_scatter(
        x=viz_data['amount_dist']['amount_range'],
        y=viz_data['amount_dist']['fraud_rate'],
        name='Tasa de Fraude (%)',
        yaxis='y2',
        mode='lines+markers'
    )
    
    amount_dist_fig.update_layout(
        yaxis2=dict(
            title='Tasa de Fraude (%)',
            titlefont=dict(color='red'),
            tickfont=dict(color='red'),
            anchor='x',
            overlaying='y',
            side='right'
        ),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    # Tabla de alertas recientes
    # Identificar transacciones con alta probabilidad de ser robo de identidad
    id_theft_indicators = (
        (filtered_df['cardCVV'] != filtered_df['enteredCVV']) | 
        (~filtered_df['expirationDateKeyInMatch']) | 
        (filtered_df['acqCountry'] != filtered_df['merchantCountryCode'])
    ) & (~filtered_df['cardPresent'])
    
    potential_id_theft = filtered_df[id_theft_indicators].copy()
    
    # Calcula un "score" simple de riesgo de robo de identidad
    potential_id_theft['risk_score'] = 0
    potential_id_theft.loc[potential_id_theft['cardCVV'] != potential_id_theft['enteredCVV'], 'risk_score'] += 3
    potential_id_theft.loc[~potential_id_theft['expirationDateKeyInMatch'], 'risk_score'] += 2
    potential_id_theft.loc[potential_id_theft['acqCountry'] != potential_id_theft['merchantCountryCode'], 'risk_score'] += 2
    potential_id_theft.loc[~potential_id_theft['cardPresent'], 'risk_score'] += 1
    
    # Ordenar por score de riesgo y tomar los top 10
    recent_alerts = potential_id_theft.sort_values('risk_score', ascending=False).head(10)
    
    # Crear tabla de alertas
    alert_table = dbc.Table([
        html.Thead(
            html.Tr([
                html.Th("Cliente ID"),
                html.Th("Fecha/Hora"),
                html.Th("Monto"),
                html.Th("Comercio"),
                html.Th("País"),
                html.Th("Score de Riesgo"),
                html.Th("Indicadores")
            ])
        ),
        html.Tbody([
            html.Tr([
                html.Td(row['customerId']),
                html.Td(str(row['transactionDateTime'])),
                html.Td(f"${row['transactionAmount']:.2f}"),
                html.Td(row['merchantName']),
                html.Td(f"{row['merchantCountryCode']}"),
                html.Td(html.Span(f"{row['risk_score']}", 
                                 className="badge bg-danger" if row['risk_score'] > 5 else "badge bg-warning")),
                html.Td(
                    ", ".join([
                        "CVV incorrecto" if row['cardCVV'] != row['enteredCVV'] else "",
                        "Fecha exp. incorrecta" if not row['expirationDateKeyInMatch'] else "",
                        "País diferente" if row['acqCountry'] != row['merchantCountryCode'] else "",
                        "Tarjeta no presente" if not row['cardPresent'] else ""
                    ]).strip(", ")
                )
            ]) for _, row in recent_alerts.iterrows()
        ])
    ], bordered=True, hover=True, striped=True, responsive=True, className="table-sm")
    
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

if __name__ == '__main__':
    # Importamos la configuración
    from config import DEBUG, HOST, PORT
    
    # Iniciamos la aplicación con los parámetros de configuración
    app.run(debug=DEBUG, host=HOST, port=PORT)