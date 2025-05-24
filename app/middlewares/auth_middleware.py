from datetime import datetime, timedelta
from flask import request, session, redirect, url_for
from app.models.users import User
'''
def setup_auth_middleware(app):
   @app.before_request
   def check_session():
      exempt_routes = ['auth.register', 'auth.login', 'auth.logout', 'static']
      
      if request.endpoint in exempt_routes:
         return
      
      if 'session_token' not in session:
         return redirect(url_for('auth.login'))
      
      user = User.verify_session_token(session['session_token'])
      if not user:
         session.clear()
         return redirect(url_for('auth.login'))
      
      user.session_expiration = datetime.utcnow() + timedelta(minutes=30)
      from app import db
      db.session.commit()
   '''