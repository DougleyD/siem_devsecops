from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.services.auth_service import login_required
from app.services.email_service import EmailService
from app.services.mfa_service import MFAService
from datetime import datetime
from app.models.users import User
from app import db
import re


auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'authenticated' in session:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        # Se for pedido de envio de código
        if 'send_code' in request.form:
            email = request.form.get('email')
            
            if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
                flash('Por favor, insira um email válido', 'error')
                return render_template('auth/register.html', title='EventTrace | Register')
            
            # Verifica se email já existe
            if User.query.filter_by(email=email).first():
                flash('Email já cadastrado', 'error')
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

        # Cria novo usuário
        try:
            new_user = User(username=username, email=email)
            new_user.set_password(password1)
            
            db.session.add(new_user)
            db.session.commit()
            
            # Limpa a session após registro bem-sucedido
            session.pop('verification_data', None)

            flash('Registro realizado com sucesso!', 'success')
            return redirect(url_for('auth.login'))
        
        except Exception as e:
            db.session.rollback()
            flash('Erro ao registrar usuário', 'error')
            return render_template('auth/register.html', title='EventTrace | Register')

    return render_template('auth/register.html', title='EventTrace | Register')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'authenticated' in session:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            flash('E-mail ou senha incorretos', 'error')
            return render_template('auth/login.html', title='EventTrace | Login')
        
        # Gera token de sessão seguro (não usa o ID)
        session_token = user.generate_session_token()
        session['session_token'] = session_token
        
        if not user.tfa_enabled:
            return redirect(url_for('auth.setup_mfa'))
        
        return redirect(url_for('auth.verify_mfa'))
        
    return render_template('auth/login.html', title='EventTrace | Login')

@auth_bp.route('/logout')
def logout():
    if 'session_token' in session:
        user = User.query.filter_by(session_token=session['session_token']).first()
        if user:
            user.session_token = None
            user.session_expiration = None
            db.session.commit()
    session.clear()
    return redirect(url_for('auth.login'))

@auth_bp.route('/setup_mfa', methods=['GET', 'POST'])
@login_required
def setup_mfa(user):
    if 'authenticated' in session:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        code = request.form.get('code')
        
        if MFAService.verify_code(user.tfa_secret, code):
            user.tfa_enabled = True
            db.session.commit()
            flash('MFA configurado com sucesso!', 'success')
            session['authenticated'] = True
            return redirect(url_for('main.dashboard'))
            
        flash('Código inválido', 'error')
    
    # Verifica se precisa gerar um código inicial (apenas se não existir)
    if not user.tfa_secret:
        user.tfa_secret = MFAService.generate_secret()
        user.tfa_expiration = MFAService.get_expiration_date()
        db.session.commit()
    
    qr_code = MFAService.generate_qr_code(user.tfa_secret, user.email)
    return render_template('auth/setup_mfa.html', 
                         title='EventTrace | Setup MFA', 
                         qr_code=qr_code)

@auth_bp.route('/verify_mfa', methods=['GET', 'POST'])
@login_required
def verify_mfa(user):
    if 'authenticated' in session:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        code = request.form.get('code')
        
        if MFAService.verify_code(user.tfa_secret, code):
            session['authenticated'] = True
            return redirect(url_for('main.dashboard'))
            
        flash('Código inválido', 'error')
    
    return render_template('auth/verify_mfa.html', title='EventTrace | Verify MFA')


@auth_bp.route('/refresh_mfa', methods=['POST','GET'])
@login_required
def refresh_mfa(user):
    if request.method == 'GET':
        return redirect(url_for('auth.setup_mfa'))
        
    # Gera novo segredo e atualiza a expiração
    user.tfa_secret = MFAService.generate_secret()
    user.tfa_expiration = MFAService.get_expiration_date()
    db.session.commit()
    
    flash('Novo código MFA gerado com sucesso', 'success')
    return redirect(url_for('auth.setup_mfa'))

@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if 'authenticated' in session:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        # Se for pedido de envio de código
        if 'send_code' in request.form:
            email = request.form.get('email')
            
            if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
                flash('Por favor, insira um email válido', 'error')
                return render_template('auth/forgot_password.html', title='EventTrace | Forgot Password')
            
            # Verifica se email já existe
            if User.query.filter_by(email=email).first():
        
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
                
                return render_template('auth/forgot_password.html', title='EventTrace | Forgot Password')

            flash('E-mail não encontrado. Tente novamente.', 'error')
            return render_template('auth/forgot_password.html', title='EventTrace | Forgot Password')

        # Processa registro completo
        email = request.form.get('email')
        user_code = request.form.get('code')
                
        # Verifica o código
        verification_data = session.get('verification_data')

        if not verification_data or user_code != verification_data['code'] or email != verification_data['email']:
            flash('Código inválido ou e-mail não corresponde', 'error')
            return render_template('auth/forgot_password.html', title='EventTrace | Forgot Password')
        
        if datetime.now().timestamp() > verification_data['expires_at']:
            flash('Código expirado. Solicite um novo.', 'error')
            return render_template('auth/forgot_password.html', title='EventTrace | Forgot Password')
            
        # Limpa a session após registro bem-sucedido
        session.pop('verification_data', None)

        # Armazena o email na session para usar na atualização de senha
        session['reset_email'] = email
        return redirect(url_for('auth.update_password'))
    
    return render_template('auth/forgot_password.html', title='EventTrace | Forgot Password')

@auth_bp.route('/update_password', methods=['GET', 'POST'])
def update_password():
    if 'authenticated' in session:
        return redirect(url_for('main.dashboard'))
    
    # Verifica se há um email na session (vindo do forgot_password)
    reset_email = session.get('reset_email')
    if not reset_email:
        flash('Por favor, inicie o processo de recuperação de senha primeiro', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
    
        #1. Validação de senha (mínimo 8 caracteres, pelo menos 1 letra, 1 número e 1 caracter especial)
        if not re.match(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d!@#$%^&*]{8,}$', password1):
            flash('Senha deve ter pelo menos 8 caracteres, com letras, números e símbolos (!@#$%^&*)', 'error')
            return render_template('auth/update_password.html', title='EventTrace | Update Password')

        #2. Confirmação de senha
        if password1 != password2:
            flash('As senhas não coincidem', 'error')
            return render_template('auth/update_password.html', title='EventTrace | Update Password')
        
        # Busca o usuário pelo email
        user = User.query.filter_by(email=reset_email).first()

         # Atualiza a senha
        user.set_password(password1)
        db.session.commit()
        
        # Limpa o email da session após a alteração
        session.pop('reset_email', None)
        
        flash('Senha alterada com sucesso!', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/update_password.html', title='EventTrace | Update Password')