# models/users.py
from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
from datetime import timedelta

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    tfa_secret = db.Column(db.String(255))
    tfa_enabled = db.Column(db.Boolean, default=False)
    tfa_expiration = db.Column(db.DateTime)
    is_admin = db.Column(db.Boolean, default=False)
    session_token = db.Column(db.String(100), unique=True)
    session_expiration = db.Column(db.DateTime)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_session_token(self):
        """Gera um token de sessão seguro e define a expiração"""
        self.session_token = secrets.token_urlsafe(32)
        self.session_expiration = datetime.utcnow() + timedelta(minutes=120)
        db.session.commit()
        return self.session_token

    @staticmethod
    def verify_session_token(token):
        """Verifica se o token de sessão é válido"""
        user = User.query.filter_by(session_token=token).first()
        if user and user.session_expiration > datetime.utcnow():
            return user
        return None