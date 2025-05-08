from pymongo import MongoClient
import pandas as pd
from pymongo.server_api import ServerApi
from datetime import datetime, timedelta
import numpy as np
import os

# Importamos la configuración (preferiblemente desde variables de entorno en producción)
from config import MONGODB_URI, DB_NAME, COLLECTION_NAME 

def load_data_from_mongodb():
    """
    Carga los datos desde MongoDB y realiza la preparación inicial necesaria.
    """
    # Conexión a MongoDB usando configuración
    uri = MONGODB_URI
    client = MongoClient(uri, server_api=ServerApi('1'))

    # Nombre de la base de datos y la colección desde configuración
    db_name = DB_NAME
    collection_name = COLLECTION_NAME

    # Accedemos a la base de datos y la colección
    db = client[db_name]
    collection = db[collection_name]

    # Cargamos los datos de la colección en un DataFrame de pandas (limitado a 1500 documentos)
    data = collection.find().limit(10000)
    df = pd.DataFrame(list(data))
    
    # Realizamos la preparación inicial de los datos
    prepare_data(df)
    
    return df

def prepare_data(df):
    """
    Prepara los datos para el análisis, realizando transformaciones y limpieza necesarias.
    """
    # Asegurarse que la columna transactionDateTime sea de tipo datetime
    if 'transactionDateTime' in df.columns:
        df['transactionDateTime'] = pd.to_datetime(df['transactionDateTime'])
        df['transaction_date'] = df['transactionDateTime'].dt.date
    
    # Asegurarse que la columna isFraud sea numérica (0 o 1)
    if 'isFraud' in df.columns:
        df['isFraud'] = df['isFraud'].astype(int)
    
    # Para manejo de valores faltantes en columnas clave
    for col in ['cardCVV', 'enteredCVV', 'acqCountry', 'merchantCountryCode', 
                'expirationDateKeyInMatch', 'cardPresent']:
        if col in df.columns and df[col].isna().any():
            # Si son columnas de tipo texto o código
            if col in ['cardCVV', 'enteredCVV', 'acqCountry', 'merchantCountryCode']:
                df[col] = df[col].fillna("Unknown")
            # Si son columnas booleanas
            elif col in ['expirationDateKeyInMatch', 'cardPresent']:
                df[col] = df[col].fillna(False)

    # Crear columna de monto por rangos para análisis
    if 'transactionAmount' in df.columns:
        df['amount_range'] = pd.cut(
            df['transactionAmount'], 
            bins=[0, 50, 200, 500, 1000, float('inf')],
            labels=['0-50', '51-200', '201-500', '501-1000', '>1000']
        )
    
    return df

# Funciones para calcular KPIs relacionados con robo de identidad
def calculate_identity_theft_kpis(df):
    kpis = {}
    
    # Total de transacciones
    kpis['total_transactions'] = len(df)
    
    # Total de transacciones fraudulentas
    kpis['fraud_transactions'] = df['isFraud'].sum()
    
    # Tasa de fraude
    kpis['fraud_rate'] = kpis['fraud_transactions'] / kpis['total_transactions'] * 100
    
    # Casos de discrepancia de CVV (posible indicador de robo de identidad)
    cvv_mismatch = df['cardCVV'] != df['enteredCVV']
    kpis['cvv_mismatch_count'] = cvv_mismatch.sum()
    kpis['cvv_mismatch_fraud_rate'] = df[cvv_mismatch]['isFraud'].mean() * 100 if cvv_mismatch.sum() > 0 else 0
    
    # Casos de tarjeta no presente físicamente (mayor riesgo de robo de identidad)
    card_not_present = ~df['cardPresent']
    kpis['card_not_present_count'] = card_not_present.sum()
    kpis['card_not_present_fraud_rate'] = df[card_not_present]['isFraud'].mean() * 100 if card_not_present.sum() > 0 else 0
    
    # Discrepancia geográfica (país de adquisición vs país del comerciante)
    geo_mismatch = df['acqCountry'] != df['merchantCountryCode']
    kpis['geo_mismatch_count'] = geo_mismatch.sum()
    kpis['geo_mismatch_fraud_rate'] = df[geo_mismatch]['isFraud'].mean() * 100 if geo_mismatch.sum() > 0 else 0
    
    # Fecha de expiración no coincide
    exp_date_mismatch = ~df['expirationDateKeyInMatch']
    kpis['exp_date_mismatch_count'] = exp_date_mismatch.sum()
    kpis['exp_date_mismatch_fraud_rate'] = df[exp_date_mismatch]['isFraud'].mean() * 100 if exp_date_mismatch.sum() > 0 else 0
    
    # Estimación de casos de robo de identidad (combinación de factores)
    identity_theft_indicators = (cvv_mismatch | exp_date_mismatch | geo_mismatch) & card_not_present
    kpis['potential_identity_theft_count'] = identity_theft_indicators.sum()
    kpis['potential_identity_theft_rate'] = kpis['potential_identity_theft_count'] / kpis['total_transactions'] * 100
    
    return kpis

# Función para preparar datos para visualizaciones
def prepare_visualization_data(df):
    viz_data = {}
    
    # Tendencia temporal de fraudes
    if 'transaction_date' not in df.columns:
        df['transaction_date'] = pd.to_datetime(df['transactionDateTime']).dt.date
    
    fraud_trend = df.groupby('transaction_date').agg(
        transactions=('accountNumber', 'count'),
        fraud_cases=('isFraud', 'sum')
    ).reset_index()
    fraud_trend['fraud_rate'] = fraud_trend['fraud_cases'] / fraud_trend['transactions'] * 100
    viz_data['fraud_trend'] = fraud_trend
    
    # Distribución geográfica de fraudes
    fraud_by_country = df[df['isFraud'] == True].groupby('merchantCountryCode').size().reset_index(name='fraud_count')
    fraud_by_country = fraud_by_country.sort_values('fraud_count', ascending=False).head(10)
    viz_data['fraud_by_country'] = fraud_by_country
    
    # Categorías de comercios con mayor tasa de fraude
    merchant_fraud = df.groupby('merchantCategoryCode').agg(
        transactions=('accountNumber', 'count'),
        fraud_cases=('isFraud', 'sum')
    ).reset_index()
    merchant_fraud['fraud_rate'] = merchant_fraud['fraud_cases'] / merchant_fraud['transactions'] * 100
    merchant_fraud = merchant_fraud.sort_values('fraud_rate', ascending=False).head(10)
    viz_data['merchant_fraud'] = merchant_fraud
    
    # Distribución por montos de transacción
    if 'amount_range' not in df.columns:
        df['amount_range'] = pd.cut(
            df['transactionAmount'], 
            bins=[0, 50, 200, 500, 1000, float('inf')],
            labels=['0-50', '51-200', '201-500', '501-1000', '>1000']
        )
    
    amount_dist = df.groupby('amount_range').agg(
        transactions=('accountNumber', 'count'),
        fraud_cases=('isFraud', 'sum')
    ).reset_index()
    amount_dist['fraud_rate'] = amount_dist['fraud_cases'] / amount_dist['transactions'] * 100
    viz_data['amount_dist'] = amount_dist
    
    # Indicadores de robo de identidad
    id_theft_indicators = pd.DataFrame({
        'indicador': [
            'CVV no coincide', 
            'Tarjeta no presente', 
            'País diferente', 
            'Fecha exp. no coincide'
        ],
        'casos': [
            (df['cardCVV'] != df['enteredCVV']).sum(),
            (~df['cardPresent']).sum(),
            (df['acqCountry'] != df['merchantCountryCode']).sum(),
            (~df['expirationDateKeyInMatch']).sum()
        ],
        'tasa_fraude': [
            df[df['cardCVV'] != df['enteredCVV']]['isFraud'].mean() * 100 if (df['cardCVV'] != df['enteredCVV']).sum() > 0 else 0,
            df[~df['cardPresent']]['isFraud'].mean() * 100 if (~df['cardPresent']).sum() > 0 else 0,
            df[df['acqCountry'] != df['merchantCountryCode']]['isFraud'].mean() * 100 if (df['acqCountry'] != df['merchantCountryCode']).sum() > 0 else 0,
            df[~df['expirationDateKeyInMatch']]['isFraud'].mean() * 100 if (~df['expirationDateKeyInMatch']).sum() > 0 else 0
        ]
    })
    viz_data['id_theft_indicators'] = id_theft_indicators
    
    return viz_data

if __name__ == "__main__":
    # Test de carga de datos
    df = load_data_from_mongodb()
    print(f"Datos cargados: {len(df)} registros")
    print(f"Columnas: {df.columns.tolist()}")