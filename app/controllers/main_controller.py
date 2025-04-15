from flask import Blueprint, redirect, render_template, url_for

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def root():
   return redirect(url_for('auth.login'))

@main_bp.route('/dashboard', methods=['GET'])
def dashboard():
   return render_template('application/dashboard.html', title='EventTracer | Dashboard')