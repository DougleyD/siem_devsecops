# services/auth_service.py
from functools import wraps
from flask import session, redirect, url_for, flash
from app.models.users import User

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'session_token' not in session:
            flash('Por favor, faça login para acessar esta página', 'error')
            return redirect(url_for('auth.login'))

        user = User.verify_session_token(session['session_token'])
        if not user:
            flash('Sessão expirada. Faça login novamente', 'error')
            return redirect(url_for('auth.login'))
        
        return f(user, *args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(user, *args, **kwargs):
        if not user.is_admin:
            return redirect(url_for('main.dashboard'))
        return f(user, *args, **kwargs)
    return decorated_function