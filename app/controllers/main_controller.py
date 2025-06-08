from flask import Blueprint, flash, redirect, render_template, session, url_for

from app.services.auth_service import login_required

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def root():
   return redirect(url_for('auth.login'))

@main_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard(user):
   if 'authenticated' not in session:
      flash('Por favor, faça login para acessar esta página', 'error')
      return redirect(url_for('auth.login'))
   return render_template('application/dashboard.html', title='EventTrace | Dashboard', user=user)
