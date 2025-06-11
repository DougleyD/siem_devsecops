from app import db
from datetime import datetime

class Agent(db.Model):
    __tablename__ = 'agent'

    id = db.Column(db.Integer, primary_key=True)
    identificador_host = db.Column(db.String(255), unique=True, nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    aprovado_em = db.Column(db.DateTime)
    notes = db.Column(db.Text)                       
    status = db.Column(db.String(10))
    ip_agente = db.Column(db.String(100))
    aprovado = db.Column(db.Boolean, default=False)
    collect_resources = db.Column(db.Boolean, default=False)
    collect_system = db.Column(db.Boolean, default=False)     
    collect_auth = db.Column(db.Boolean, default=False)       
    collect_web = db.Column(db.Boolean, default=False) 
    chave_fernet = db.Column(db.String(255), nullable=False)
    chave_publica = db.Column(db.Text)
    ultimo_contato = db.Column(db.DateTime)