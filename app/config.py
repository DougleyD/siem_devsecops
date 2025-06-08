from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    SECRET_KEY = f"{os.getenv('SECRET')}"
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SENDER = os.getenv('EMAIL_SENDER')
    MAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    MAIL_SERVER = os.getenv('EMAIL_SERVER')
    MAIL_PORT = int(os.getenv('EMAIL_PORT', 465))  # Converte para int com valor padrão
    MAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'True').lower() in ['true', '1', 't']
    MAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'False').lower() in ['true', '1', 't']

