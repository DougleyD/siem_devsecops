import smtplib
from email.message import EmailMessage
from flask import current_app
import secrets
from datetime import datetime, timedelta

class EmailService:
    @staticmethod
    def send_verification_email(recipient_email, code):
        """
        Envia e-mail com código de verificação
        Args:
            recipient_email (str): E-mail do destinatário
            code (str): Código de verificação
        Returns:
            bool: True se o e-mail foi enviado com sucesso
        """
        msg = EmailMessage()
        msg['Subject'] = 'Seu Código de Verificação - EventTrace'
        msg['From'] = current_app.config['MAIL_SENDER']
        msg['To'] = recipient_email
        msg.set_content(f'''
        Olá 😀
        
        Seu código de verificação no EventTrace é: {code}
        
        Este código expira em 5 minutos ⏳
        
        Atenciosamente,
        Equipe EventTrace
        ''')

        try:
            with smtplib.SMTP_SSL(
                current_app.config['MAIL_SERVER'],
                current_app.config['MAIL_PORT']
            ) as server:
                server.login(
                    current_app.config['MAIL_SENDER'],
                    current_app.config['MAIL_PASSWORD']
                )
                server.send_message(msg)
            current_app.logger.info(f'E-mail de verificação enviado para {recipient_email}')
            return True
        except Exception as e:
            current_app.logger.error(f'Erro ao enviar e-mail: {str(e)}')
            return False

    @staticmethod
    def generate_verification_code():
        """Gera código numérico de 6 dígitos seguro"""
        return str(secrets.randbelow(900000) + 100000)

    @staticmethod
    def get_code_expiration(minutes=5):
        """Retorna timestamp de expiração do código"""
        return (datetime.now() + timedelta(minutes=minutes)).timestamp()