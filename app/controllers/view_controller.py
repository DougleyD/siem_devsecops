from flask import Blueprint, redirect, render_template, url_for, send_file, current_app
from app.services.auth_service import login_required
import os
   
from app.services.auth_service import login_required

view_bp = Blueprint('view', __name__)

@view_bp.route('/events', methods=['GET'])
@login_required
def events(user):
   return render_template('application/events.html', title='EventTrace | Event View', user=user)

@view_bp.route('/download', methods=['GET'])
@login_required
def download(user):
    try:
        # Caminho para o arquivo que será disponibilizado para download
        file_path = os.path.join(current_app.root_path, 'static', 'agent', 'agent.py')
        
        # Verifica se o arquivo existe
        if not os.path.exists(file_path):
            raise FileNotFoundError("Arquivo não encontrado")
            
        # Envia o arquivo como anexo para download
        return send_file(
            file_path,
            as_attachment=True,
            download_name="agent.py",  # Nome que aparecerá no download
            mimetype='application/octet-stream'
        )
    except Exception as e:
        current_app.logger.error(f"Erro ao fazer download: {str(e)}")
        return redirect(url_for('view.error_page'))