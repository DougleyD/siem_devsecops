from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.users import User
from app import db
import re

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        # Validações básicas de preenchimento
        if not all([username, email, password1, password2]):
            flash('Todos os campos são obrigatórios', 'error')
            return render_template('auth/register.html')

        # Validação do nome (mínimo 5 caracteres, apenas letras e espaços)
        if not re.match(r'^[a-zA-ZÀ-ÿ\s]{5,}$', username):
            flash('Nome deve ter pelo menos 5 caracteres e apenas letras', 'error')
            return render_template('auth/register.html')

        # Validação de email
        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            flash('Por favor, insira um email válido', 'error')
            return render_template('auth/register.html')

        # Validação de senha (mínimo 8 caracteres, pelo menos 1 letra e 1 número)
        if not re.match(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$', password1):
            flash('Senha deve ter pelo menos 8 caracteres, com letras e números', 'error')
            return render_template('auth/register.html')

        # Confirmação de senha
        if password1 != password2:
            flash('As senhas não coincidem', 'error')
            return render_template('auth/register.html')

        # Verifica se email já existe
        if User.query.filter_by(email=email).first():
            flash('Email já cadastrado', 'error')
            return render_template('auth/register.html')

        # Cria novo usuário
        try:
            new_user = User(username=username, email=email)
            new_user.set_password(password1)
            
            db.session.add(new_user)
            db.session.commit()
            
            flash('Registro realizado com sucesso!', 'success')
            return render_template('auth/register.html')
            
        except Exception as e:
            db.session.rollback()
            flash('Erro ao registrar usuário', 'error')
            return render_template('auth/register.html')

    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('auth/login.html', title='Login')