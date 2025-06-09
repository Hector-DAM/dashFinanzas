import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import pandas as pd
from datetime import datetime
import os
from typing import Optional, List, Dict, Any
import logging
import tempfile

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailAlertSender:
    def __init__(self):
        """
        Inicializa el EmailAlertSender con configuración desde variables de entorno.
        
        Variables de entorno requeridas:
        - EMAIL_SMTP_SERVER: Servidor SMTP (default: smtp.gmail.com)
        - EMAIL_SMTP_PORT: Puerto SMTP (default: 587)
        - EMAIL_ADDRESS: Dirección de email del remitente
        - EMAIL_PASSWORD: Contraseña o app password del email
        - EMAIL_FROM_NAME: Nombre del remitente (opcional)
        """
        # Configuración del servidor SMTP desde variables de entorno
        self.smtp_server = os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('EMAIL_SMTP_PORT', '587'))
        
        # Credenciales desde variables de entorno
        self.email_address = os.getenv('EMAIL_ADDRESS')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.from_name = os.getenv('EMAIL_FROM_NAME', 'Dashboard de Seguridad')
        
        # Validar que las credenciales estén configuradas
        if not self.email_address or not self.email_password:
            logger.error("Las variables de entorno EMAIL_ADDRESS y EMAIL_PASSWORD son requeridas")
            raise ValueError("Credenciales de email no configuradas. Verifique las variables de entorno.")
        
        logger.info(f"EmailAlertSender inicializado con servidor {self.smtp_server}:{self.smtp_port}")

    def _create_html_report(self, alerts_df: pd.DataFrame, summary_stats: Dict[str, Any]) -> str:
        """
        Crea un reporte HTML con las alertas y estadísticas.
        
        Args:
            alerts_df: DataFrame con las alertas de riesgo
            summary_stats: Diccionario con estadísticas del dashboard
            
        Returns:
            str: Contenido HTML del reporte
        """
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; border-bottom: 3px solid #007bff; padding-bottom: 20px; margin-bottom: 30px; }}
                .header h1 {{ color: #007bff; margin: 0; font-size: 24px; }}
                .header p {{ color: #666; margin: 5px 0 0 0; }}
                .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px; }}
                .stat-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }}
                .stat-card.fraud {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }}
                .stat-card.identity {{ background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); color: #333; }}
                .stat-card.cvv {{ background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); color: #333; }}
                .stat-number {{ font-size: 28px; font-weight: bold; margin-bottom: 5px; }}
                .stat-label {{ font-size: 14px; opacity: 0.9; }}
                .alerts-section {{ margin-top: 30px; }}
                .alerts-section h2 {{ color: #dc3545; border-left: 4px solid #dc3545; padding-left: 15px; }}
                .alert-table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
                .alert-table th {{ background-color: #f8f9fa; color: #333; padding: 12px; text-align: left; border-bottom: 2px solid #dee2e6; }}
                .alert-table td {{ padding: 10px 12px; border-bottom: 1px solid #dee2e6; }}
                .alert-table tr:hover {{ background-color: #f8f9fa; }}
                .risk-score {{ padding: 4px 8px; border-radius: 4px; color: white; font-weight: bold; }}
                .risk-high {{ background-color: #dc3545; }}
                .risk-medium {{ background-color: #fd7e14; }}
                .risk-low {{ background-color: #ffc107; color: #333; }}
                .badge {{ display: inline-block; padding: 2px 6px; margin: 1px; border-radius: 3px; font-size: 11px; color: white; }}
                .badge-cvv {{ background-color: #dc3545; }}
                .badge-exp {{ background-color: #fd7e14; }}
                .badge-country {{ background-color: #6610f2; }}
                .badge-card {{ background-color: #20c997; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; text-align: center; color: #666; font-size: 12px; }}
                .no-alerts {{ text-align: center; padding: 40px; background-color: #d4edda; color: #155724; border-radius: 8px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🛡️ Reporte de Seguridad - Dashboard de Robo de Identidad</h1>
                    <p>Generado el {datetime.now().strftime('%d de %B de %Y a las %H:%M')}</p>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number">{summary_stats.get('total_transactions', 0):,}</div>
                        <div class="stat-label">Total Transacciones</div>
                    </div>
                    <div class="stat-card fraud">
                        <div class="stat-number">{summary_stats.get('fraud_transactions', 0):,}</div>
                        <div class="stat-label">Fraudes Detectados ({summary_stats.get('fraud_rate', 0):.2f}%)</div>
                    </div>
                    <div class="stat-card identity">
                        <div class="stat-number">{summary_stats.get('potential_identity_theft_count', 0):,}</div>
                        <div class="stat-label">Posible Robo Identidad ({summary_stats.get('potential_identity_theft_rate', 0):.2f}%)</div>
                    </div>
                    <div class="stat-card cvv">
                        <div class="stat-number">{summary_stats.get('cvv_mismatch_count', 0):,}</div>
                        <div class="stat-label">CVV Incorrectos</div>
                    </div>
                </div>
        """
        
        if len(alerts_df) > 0:
            html_content += f"""
                <div class="alerts-section">
                    <h2>🚨 Alertas de Alto Riesgo Detectadas</h2>
                    <p>Se han identificado <strong>{len(alerts_df)}</strong> transacciones con indicadores de posible robo de identidad:</p>
                    
                    <table class="alert-table">
                        <thead>
                            <tr>
                                <th>Cliente ID</th>
                                <th>Fecha/Hora</th>
                                <th>Monto</th>
                                <th>Comercio</th>
                                <th>País</th>
                                <th>Score Riesgo</th>
                                <th>Indicadores</th>
                            </tr>
                        </thead>
                        <tbody>
            """
            
            for _, row in alerts_df.iterrows():
                risk_class = "risk-high" if row.get('risk_score', 0) > 5 else "risk-medium" if row.get('risk_score', 0) > 3 else "risk-low"
                
                # Generar badges de indicadores
                indicators = []
                if row.get('cardCVV') != row.get('enteredCVV'):
                    indicators.append('<span class="badge badge-cvv">CVV Incorrecto</span>')
                if not row.get('expirationDateKeyInMatch', True):
                    indicators.append('<span class="badge badge-exp">Fecha Exp. Incorrecta</span>')
                if row.get('acqCountry') != row.get('merchantCountryCode'):
                    indicators.append('<span class="badge badge-country">País Diferente</span>')
                if not row.get('cardPresent', True):
                    indicators.append('<span class="badge badge-card">Tarjeta No Presente</span>')
                
                html_content += f"""
                            <tr>
                                <td>{row.get('customerId', 'N/A')}</td>
                                <td>{str(row.get('transactionDateTime', 'N/A'))[:19]}</td>
                                <td>${row.get('transactionAmount', 0):.2f}</td>
                                <td>{row.get('merchantName', 'N/A')}</td>
                                <td>{row.get('merchantCountryCode', 'N/A')}</td>
                                <td><span class="risk-score {risk_class}">{row.get('risk_score', 0)}</span></td>
                                <td>{''.join(indicators)}</td>
                            </tr>
                """
            
            html_content += """
                        </tbody>
                    </table>
                </div>
            """
        else:
            html_content += """
                <div class="no-alerts">
                    <h3>✅ No se detectaron alertas de alto riesgo</h3>
                    <p>Todas las transacciones del período analizado están dentro de los parámetros normales de seguridad.</p>
                </div>
            """
        
        html_content += f"""
                <div class="footer">
                    <p>Este reporte fue generado automáticamente por el Sistema de Detección de Robo de Identidad.</p>
                    <p>Para más información, consulte el dashboard completo o contacte al equipo de seguridad.</p>
                    <p><strong>Confidencial:</strong> Este documento contiene información sensible y debe ser tratado con la debida confidencialidad.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content

    def _create_csv_attachment(self, alerts_df: pd.DataFrame) -> str:
        """
        Crea un archivo CSV temporal con las alertas.
        
        Args:
            alerts_df: DataFrame con las alertas
            
        Returns:
            str: Ruta al archivo CSV temporal
        """
        try:
            # Crear archivo temporal
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8')
            
            # Seleccionar columnas relevantes para el CSV
            columns_to_include = [
                'customerId', 'transactionDateTime', 'transactionAmount', 
                'merchantName', 'merchantCountryCode', 'risk_score',
                'cardCVV', 'enteredCVV', 'expirationDateKeyInMatch', 
                'acqCountry', 'cardPresent'
            ]
            
            # Filtrar columnas que existen en el DataFrame
            available_columns = [col for col in columns_to_include if col in alerts_df.columns]
            
            # Guardar CSV
            alerts_df[available_columns].to_csv(temp_file.name, index=False, encoding='utf-8')
            temp_file.close()
            
            logger.info(f"CSV temporal creado: {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Error al crear archivo CSV: {str(e)}")
            return None

    def send_alert_email(self, alerts_df: pd.DataFrame, summary_stats: Dict[str, Any], 
                        recipients: List[str], subject: Optional[str] = None, 
                        attach_csv: bool = True) -> bool:
        """
        Envía un email con las alertas de seguridad.
        
        Args:
            alerts_df: DataFrame con las alertas de riesgo
            summary_stats: Diccionario con estadísticas del dashboard
            recipients: Lista de direcciones de email destinatarias
            subject: Asunto del email (opcional)
            attach_csv: Si adjuntar archivo CSV con los datos
            
        Returns:
            bool: True si el email se envió exitosamente, False en caso contrario
        """
        try:
            # Validar que hay destinatarios
            if not recipients:
                logger.error("No se especificaron destinatarios")
                return False
            
            # Limpiar lista de destinatarios
            clean_recipients = [email.strip() for email in recipients if email.strip()]
            if not clean_recipients:
                logger.error("No hay destinatarios válidos")
                return False
            
            # Generar asunto si no se proporciona
            if not subject:
                alert_count = len(alerts_df)
                date_str = datetime.now().strftime('%d/%m/%Y')
                if alert_count > 0:
                    subject = f"🚨 ALERTA DE SEGURIDAD - {alert_count} transacciones sospechosas detectadas - {date_str}"
                else:
                    subject = f"✅ Reporte de Seguridad - Sin alertas detectadas - {date_str}"
            
            # Crear mensaje
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.email_address}>"
            msg['To'] = ', '.join(clean_recipients)
            msg['Subject'] = subject
            
            # Crear contenido HTML
            html_content = self._create_html_report(alerts_df, summary_stats)
            
            # Crear contenido de texto plano como respaldo
            text_content = f"""
Reporte de Seguridad - Dashboard de Robo de Identidad
Generado el {datetime.now().strftime('%d de %B de %Y a las %H:%M')}

RESUMEN EJECUTIVO:
- Total de transacciones: {summary_stats.get('total_transactions', 0):,}
- Fraudes detectados: {summary_stats.get('fraud_transactions', 0):,} ({summary_stats.get('fraud_rate', 0):.2f}%)
- Posible robo de identidad: {summary_stats.get('potential_identity_theft_count', 0):,} ({summary_stats.get('potential_identity_theft_rate', 0):.2f}%)
- CVV incorrectos: {summary_stats.get('cvv_mismatch_count', 0):,}

ALERTAS:
{"Se detectaron " + str(len(alerts_df)) + " transacciones con riesgo de robo de identidad." if len(alerts_df) > 0 else "No se detectaron alertas de alto riesgo en este período."}

Este reporte fue generado automáticamente por el Sistema de Detección de Robo de Identidad.
Para más información, consulte el dashboard completo.
            """
            
            # Adjuntar contenido
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            html_part = MIMEText(html_content, 'html', 'utf-8')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Adjuntar CSV si se solicita y hay alertas
            csv_file_path = None
            if attach_csv and len(alerts_df) > 0:
                csv_file_path = self._create_csv_attachment(alerts_df)
                if csv_file_path:
                    try:
                        with open(csv_file_path, 'rb') as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                        
                        encoders.encode_base64(part)
                        filename = f"alertas_seguridad_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {filename}'
                        )
                        msg.attach(part)
                        logger.info(f"Archivo CSV adjuntado: {filename}")
                    except Exception as e:
                        logger.warning(f"No se pudo adjuntar el archivo CSV: {str(e)}")
            
            # Enviar email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.email_address, self.email_password)
                server.send_message(msg, to_addrs=clean_recipients)
            
            logger.info(f"Email enviado exitosamente a {len(clean_recipients)} destinatario(s): {', '.join(clean_recipients)}")
            
            # Limpiar archivo temporal si existe
            if csv_file_path and os.path.exists(csv_file_path):
                try:
                    os.unlink(csv_file_path)
                    logger.info(f"Archivo temporal eliminado: {csv_file_path}")
                except Exception as e:
                    logger.warning(f"No se pudo eliminar el archivo temporal: {str(e)}")
            
            return True
            
        except smtplib.SMTPAuthenticationError:
            logger.error("Error de autenticación SMTP. Verifique las credenciales de email.")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"Error SMTP: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error al enviar email: {str(e)}")
            return False

def send_dashboard_alerts(alerts_df: pd.DataFrame, summary_stats: Dict[str, Any], 
                         recipients: List[str], subject: Optional[str] = None, 
                         attach_csv: bool = True) -> bool:
    """
    Función de conveniencia para enviar alertas del dashboard.
    
    Args:
        alerts_df: DataFrame con las alertas de riesgo
        summary_stats: Diccionario con estadísticas del dashboard
        recipients: Lista de direcciones de email destinatarias
        subject: Asunto del email (opcional)
        attach_csv: Si adjuntar archivo CSV con los datos
        
    Returns:
        bool: True si el email se envió exitosamente, False en caso contrario
    """
    try:
        sender = EmailAlertSender()
        return sender.send_alert_email(alerts_df, summary_stats, recipients, subject, attach_csv)
    except ValueError as e:
        logger.error(f"Error de configuración: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error al enviar alertas: {str(e)}")
        return False