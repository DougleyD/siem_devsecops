from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from datetime import datetime
from app.services.email_service import EmailService
from app.models.users import User
from app import db
from werkzeug.security import check_password_hash
import re

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':
        # Se for pedido de envio de código
        if 'send_code' in request.form:
            email = request.form.get('email')
            
            if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
                flash('Por favor, insira um email válido', 'error')
                return render_template('auth/register.html', title='EventTrace | Register')
            
            # Gera e armazena o código
            code = EmailService.generate_verification_code()
            session['verification_data'] = {
                'code': code,
                'email': email,
                'expires_at': EmailService.get_code_expiration()
            }
            
            # Envia o e-mail
            if EmailService.send_verification_email(email, code):
                flash('Código de verificação enviado para seu e-mail', 'success')
            else:
                flash('Erro ao enviar código. Tente novamente.', 'error')
            
            return render_template('auth/register.html', title='EventTrace | Register')
        
        # Processa registro completo
        username = request.form.get('username')
        email = request.form.get('email')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        user_code = request.form.get('code')
        
        #1. Validação do nome (mínimo 5 caracteres, apenas letras e espaços)
        if not re.match(r'^[a-zA-ZÀ-ÿ\s]{5,}$', username):
            flash('Nome deve ter pelo menos 5 caracteres e apenas letras', 'error')
            return render_template('auth/register.html', title='EventTrace | Register')

        #2. Validação de senha (mínimo 8 caracteres, pelo menos 1 letra, 1 número e 1 caracter especial)
        if not re.match(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d!@#$%^&*]{8,}$', password1):
            flash('Senha deve ter pelo menos 8 caracteres, com letras, números e símbolos (!@#$%^&*)', 'error')
            return render_template('auth/register.html', title='EventTrace | Register')

        #3. Confirmação de senha
        if password1 != password2:
            flash('As senhas não coincidem', 'error')
            return render_template('auth/register.html', title='EventTrace | Register')
        
        #4. Verifica o código
        verification_data = session.get('verification_data')

        if not verification_data or user_code != verification_data['code'] or email != verification_data['email']:
            flash('Código inválido ou e-mail não corresponde', 'error')
            return render_template('auth/register.html', title='EventTrace | Register')
        
        if datetime.now().timestamp() > verification_data['expires_at']:
            flash('Código expirado. Solicite um novo.', 'error')
            return render_template('auth/register.html', title='EventTrace | Register')

        
        # Verifica se email já existe
        if User.query.filter_by(email=email).first():
            flash('Email já cadastrado', 'error')
            return render_template('auth/register.html', title='EventTrace | Register')

        # Cria novo usuário
        try:
            new_user = User(username=username, email=email)
            new_user.set_password(password1)
            
            db.session.add(new_user)
            db.session.commit()
            
            # Limpa a session após registro bem-sucedido
            session.pop('verification_data', None)

            flash('Registro realizado com sucesso! Você será redirecionado em 4 segundos...', 'success')
            return render_template('auth/register.html', title='EventTrace | Register',
                    url=url_for('auth.login'),
                    delay=4)
        
        except Exception as e:
            db.session.rollback()
            flash('Erro ao registrar usuário', 'error')
            return render_template('auth/register.html', title='EventTrace | Register')

    return render_template('auth/register.html', title='EventTrace | Register')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        # Verifica credenciais básicas
        if not user or not check_password_hash(user.password_hash, password):
            flash('E-mail ou senha incorretos', 'error')
            return render_template('auth/login.html', title='EventTrace | Login')
        
        flash('Autenticação bem sucedida', 'success')
        return render_template('auth/login.html', title='EventTrace | Login')
        
    return render_template('auth/login.html', title='EventTrace | Login')