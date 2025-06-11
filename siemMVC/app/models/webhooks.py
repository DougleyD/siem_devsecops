from datetime import date, datetime
from app import db

class Webhook(db.Model):
   __tablename__ = 'webhook'
   id = db.Column(db.Integer, primary_key=True)
   name = db.Column(db.String(100), unique=True, nullable=False)
   url = db.Column(db.String(500), nullable=False)
   expiration_date = db.Column(db.Date)
   created_by = db.Column(db.String(120), db.ForeignKey('user.email'), nullable=False)
   created_at = db.Column(db.DateTime, default=datetime.utcnow)
   
   creator = db.relationship('User', backref='webhooks')
   triggers = db.relationship('Trigger', backref='webhook_rel', lazy='dynamic')

   @property
   def is_expired(self):
      """Verifica se o webhook está vencido"""
      if self.expiration_date:
         return self.expiration_date < date.today()
      return False