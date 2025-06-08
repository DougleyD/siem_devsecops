from datetime import datetime
from cryptography.fernet import Fernet
from app import db
from app.services.crypto_service import encrypt_data, decrypt_data

class Agent(db.Model):
    __tablename__ = 'agents'
    
    id = db.Column(db.String(64), primary_key=True)  # ID único do agent
    approval_timestamp = db.Column(db.DateTime)      # Timestamp de aprovação
    notes = db.Column(db.Text)                       # Notas/observações
    status = db.Column(db.String(10))                # Status (up/down)
    is_approved = db.Column(db.Boolean, default=False)  # Status de aprovação
    collect_resources = db.Column(db.Boolean, default=False)  # Coletar logs de recursos
    collect_system = db.Column(db.Boolean, default=False)     # Coletar logs do sistema
    collect_auth = db.Column(db.Boolean, default=False)       # Coletar logs de autenticação
    collect_web = db.Column(db.Boolean, default=False)        # Coletar logs web
    encrypted_fernet_key = db.Column(db.LargeBinary)          # Chave Fernet criptografada
    encryption_nonce = db.Column(db.LargeBinary)              # Nonce para criptografia
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_fernet_key(self, key):
        """Armazena a chave Fernet de forma segura"""
        self.encrypted_fernet_key, self.encryption_nonce = encrypt_data(key)

    def get_fernet_key(self):
        """Recupera a chave Fernet descriptografada"""
        if not self.encrypted_fernet_key:
            return None
        return decrypt_data(self.encrypted_fernet_key, self.encryption_nonce)

    def generate_new_fernet_key(self):
        """Gera e armazena uma nova chave Fernet"""
        new_key = Fernet.generate_key()
        self.set_fernet_key(new_key)
        return new_key

    def __repr__(self):
        return f'<Agent {self.id} - {self.status}>'