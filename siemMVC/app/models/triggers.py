from datetime import datetime
from app import db

class Trigger(db.Model):
    __tablename__ = 'trigger'
    id = db.Column(db.Integer, primary_key=True)
    alert_types = db.Column(db.String(500), nullable=False)  # JSON string
    target_hosts = db.Column(db.String(500), nullable=False)
    severity = db.Column(db.String(20), nullable=False)
    webhook_name = db.Column(db.String(100), db.ForeignKey('webhook.name'), nullable=False)
    custom_message = db.Column(db.Text)
    created_by = db.Column(db.String(120), db.ForeignKey('user.email'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    webhook = db.relationship('Webhook', backref='triggers_rel')
    creator = db.relationship('User', backref='triggers')
