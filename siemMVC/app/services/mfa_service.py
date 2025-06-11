# services/tfa_service.py
import pyotp
import qrcode
import io
import base64
from datetime import datetime, timedelta

class MFAService:
    @staticmethod
    def generate_secret():
        return pyotp.random_base32()
    
    @staticmethod
    def generate_qr_code(secret, email):
        totp = pyotp.totp.TOTP(secret)
        uri = totp.provisioning_uri(name=email, issuer_name="EventTrace")
        
        img = qrcode.make(uri)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode()
    
    @staticmethod
    def verify_code(secret, code):
        totp = pyotp.totp.TOTP(secret)
        return totp.verify(code)
    
    @staticmethod
    def get_expiration_date():
        return datetime.utcnow() + timedelta(days=15)
    
    @staticmethod
    def is_secret_expired(expiration_date):
        if not expiration_date:
            return True
        return datetime.utcnow() > expiration_date