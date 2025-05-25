from flask import Blueprint, redirect, render_template, url_for

from app.services.auth_service import login_required

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def root():
   return redirect(url_for('auth.login'))

@main_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard(user):
   return render_template('application/dashboard.html', title='EventTrace | Dashboard', user=user)
