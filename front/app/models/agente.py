from app import db
from datetime import datetime

class Agente(db.Model):
    __tablename__ = 'agentes'

    id = db.Column(db.Integer, primary_key=True)
    identificador_host = db.Column(db.String(255), unique=True, nullable=False)
    ip_agente = db.Column(db.String(100))
    chave_fernet = db.Column(db.String(255), nullable=False)
    aprovado = db.Column(db.Boolean, default=False)
    chave_publica = db.Column(db.Text)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    aprovado_em = db.Column(db.DateTime)
    ultimo_contato = db.Column(db.DateTime)

