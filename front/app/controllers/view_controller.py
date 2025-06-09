from flask import Blueprint, render_template, redirect, url_for, send_file, current_app
from flask import session
from app.services.auth_service import login_required
from app.services.log_service import get_mongo_logs
from app.models.agente import Agente
from app import db
import os

view_bp = Blueprint('view', __name__)

@view_bp.route('/events')
def events():
    try:
        logs = get_decrypted_logs()
    except Exception as e:
        logs = []
        print(f"[ERRO] Falha ao obter logs: {e}")

    user = session.get("user")  # garante que a variável `user` será enviada ao template

    return render_template('application/events.html', logs=logs, user=user)

@view_bp.route('/download', methods=['GET'])
@login_required
def download(user):
    try:
        file_path = os.path.join(current_app.root_path, 'static', 'agent', 'agent.py')

        if not os.path.exists(file_path):
            raise FileNotFoundError("Arquivo não encontrado")

        return send_file(
            file_path,
            as_attachment=True,
            download_name="agent.py",
            mimetype='application/octet-stream'
        )
    except Exception as e:
        current_app.logger.error(f"Erro ao fazer download: {str(e)}")
        return redirect(url_for('view.error_page'))

@view_bp.route('/manage', methods=['GET'])
@login_required
def manage(user):
    agentes_aprovados = Agente.query.filter_by(aprovado=True).all()
    agentes_pendentes = Agente.query.filter_by(aprovado=False).all()

    return render_template(
        'application/manage.html',
        title='EventTrace | Manage Agent',
        user=user,
        agentes_aprovados=agentes_aprovados,
        agentes_pendentes=agentes_pendentes
    )

@view_bp.route('/notification', methods=['GET'])
@login_required
def notification(user):
    return render_template('application/notification.html', title='EventTrace | Notification Event', user=user)

@view_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard(user):
    logs = get_mongo_logs()
    return render_template('application/dashboard.html', title='EventTrace | Dashboard', logs=logs, user=user)

