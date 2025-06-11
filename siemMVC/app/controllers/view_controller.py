from datetime import datetime
from flask import Blueprint, flash, render_template, redirect, request, url_for, send_file, current_app, session
from app.services.auth_service import login_required
from app.services.log_service import get_mongo_logs
from siemMVC.app.models.agents import Agent
from app.models.triggers import Trigger
from app.models.webhooks import Webhook
from app import db
import os

view_bp = Blueprint('view', __name__)

@view_bp.route('/events', methods=['GET'])
@login_required
def events(user):
    if 'authenticated' not in session:
        flash('Por favor, faça login para acessar esta página', 'error')
        return redirect(url_for('auth.login'))
    
    events_data = [
        {
            "timestamp": "2023-05-15 14:30:22",
            "event_id": "1495",
            "agent_id": "00100",
            "hostname": "Daniel",
            "ip": "192.168.31.134",
            "description": "Authentication failure",
            "category": "SSH failed",
            "details": {
                "user": "daniel",
                "file_directory": "/home/daniel/Documents",
                "service": "SSH",
                "port": 22,
                "directory": "N/A",
                "authentication": "Failed (3 attempts)",
                "web": "N/A"
            },
            "json_data": {
                "event": {
                    "timestamp": "2023-05-15T14:30:22Z",
                    "id": 1495,
                    "type": "authentication",
                    "outcome": "failure"
                },
                "agent": {
                    "id": "00100",
                    "hostname": "Daniel",
                    "ip": "192.168.31.134"
                },
                "details": {
                    "user": "daniel",
                    "directory": "/home/daniel/Documents",
                    "service": "SSH",
                    "port": 22,
                    "authentication": {
                        "status": "failed",
                        "attempts": 3
                    }
                }
            }
        },
        {
            "timestamp": "2023-05-15 15:45:10",
            "event_id": "1496",
            "agent_id": "00101",
            "hostname": "Server01",
            "ip": "192.168.31.135",
            "description": "Unauthorized access attempt",
            "category": "Security",
            "details": {
                "user": "root",
                "file_directory": "/var/log",
                "service": "FTP",
                "port": 21,
                "directory": "/var/www",
                "authentication": "Failed (1 attempt)",
                "web": "N/A"
            },
            "json_data": {
                "event": {
                    "timestamp": "2023-05-15T15:45:10Z",
                    "id": 1496,
                    "type": "access",
                    "outcome": "failure"
                },
                "agent": {
                    "id": "00101",
                    "hostname": "Server01",
                    "ip": "192.168.31.135"
                },
                "details": {
                    "user": "root",
                    "directory": "/var/log",
                    "service": "FTP",
                    "port": 21,
                    "authentication": {
                        "status": "failed",
                        "attempts": 1
                    }
                }
            }
        }
    ]
    
    return render_template(
        'application/events.html',
        title='EventTrace | Event View',
        user=user,
        events=events_data
    )

@view_bp.route('/download', methods=['GET'])
@login_required
def download(user):
    try:
        file_path = os.path.join(current_app.root_path, 'static', 'download', 'agent.py')

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
    agentes_aprovados = Agent.query.filter_by(aprovado=True).all()
    agentes_pendentes = Agent.query.filter_by(aprovado=False).all()

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

@view_bp.route('/notification', methods=['GET'])
@login_required
def notification(user):
    if 'authenticated' not in session:
      flash('Por favor, faça login para acessar esta página', 'error')
      return redirect(url_for('auth.login'))
  
    # Lista os webhooks e triggers do usuário
    webhooks = Webhook.query.filter_by(created_by=user.email).all()
    triggers = Trigger.query.filter_by(created_by=user.email).all()
    
    return render_template(
        'application/notification.html',
        title='EventTrace | Notification Event',
        user=user,
        webhooks=webhooks,
        triggers=triggers
    )

@view_bp.route('/notification/webhook', methods=['POST', 'GET'])
@login_required
def handle_webhook(user):
    if request.method == 'GET':
        return redirect(url_for('view.notification'))
    
    if 'authenticated' not in session:
      flash('Por favor, faça login para acessar esta página', 'error')
      return redirect(url_for('auth.login'))
  
    # Verifica se é ação de deletar webhook
    if 'delete_id' in request.form:
        webhook_id = request.form['delete_id']
        try:
            webhook = Webhook.query.get(webhook_id)
            if not webhook:
                flash('Webhook não encontrado!', 'webhook_error')
            elif webhook.created_by != user.email and not user.is_admin:
                flash('Não autorizado!', 'webhook_error')
            else:
                # Verifica se existem triggers associadas
                if Trigger.query.filter_by(webhook_name=webhook.name).count() > 0:
                    flash('Não é possível excluir: existem triggers associadas a este webhook!', 'webhook_error')
                else:
                    db.session.delete(webhook)
                    db.session.commit()
                    flash('Webhook deletado com sucesso!', 'webhook_success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao deletar webhook: {str(e)}', 'webhook_error')
    
    # Ação de criar novo webhook
    else:
        name = request.form.get('name')
        url = request.form.get('url')
        expiration_date = request.form.get('expiration_date')
        
        try:
            if not name or not url:
                flash('Nome e URL são obrigatórios!', 'webhook_error')
            elif Webhook.query.filter_by(name=name).first():
                flash('Já existe um webhook com este nome!', 'webhook_error')
            else:
                new_webhook = Webhook(
                    name=name,
                    url=url,
                    expiration_date=datetime.strptime(expiration_date, '%Y-%m-%d').date() if expiration_date else None,
                    created_by=user.email
                )
                db.session.add(new_webhook)
                db.session.commit()
                flash('Webhook criado com sucesso!', 'webhook_success')
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar webhook: {str(e)}', 'webhook_error')

    return redirect(url_for('view.notification'))


@view_bp.route('/notification/trigger', methods=['POST', 'GET'])
@login_required
def handle_trigger(user):
    if request.method == 'GET':
        return redirect(url_for('view.notification'))
    
    if 'authenticated' not in session:
      flash('Por favor, faça login para acessar esta página', 'error')
      return redirect(url_for('auth.login'))
  
    # Verifica se é ação de deletar trigger
    if 'delete_trigger_id' in request.form:
        trigger_id = request.form['delete_trigger_id']
        try:
            trigger = Trigger.query.get(trigger_id)
            if not trigger:
                flash('Trigger não encontrada!', 'trigger_error')
            elif trigger.created_by != user.email and not user.is_admin:
                flash('Não autorizado!', 'trigger_error')
            else:
                db.session.delete(trigger)
                db.session.commit()
                flash('Trigger deletada com sucesso!', 'trigger_success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao deletar trigger: {str(e)}', 'trigger_error')
    
    # Ação de criar nova trigger
    else:
        alert_types = request.form.getlist('alert_type')
        target_hosts = request.form.get('target_hosts')
        severity = request.form.get('severity')
        webhook_name = request.form.get('webhook')
        custom_message = request.form.get('custom_message')
        
        try:
            if not alert_types:
                flash('Selecione pelo menos um tipo de alerta!', 'trigger_error')
            elif not target_hosts:
                flash('Hosts alvo são obrigatórios!', 'trigger_error')
            elif not webhook_name:
                flash('Selecione um webhook!', 'trigger_error')
            else:
                webhook = Webhook.query.filter_by(name=webhook_name, created_by=user.email).first()
                if not webhook:
                    flash('Webhook não encontrado!', 'trigger_error')
                elif webhook.is_expired:
                    flash('O webhook selecionado está vencido! Atualize a data de expiração.', 'trigger_error')
                else:
                    new_trigger = Trigger(
                        alert_types=','.join(alert_types),
                        target_hosts=target_hosts,
                        severity=severity,
                        webhook_name=webhook_name,
                        custom_message=custom_message,
                        created_by=user.email
                    )
                    db.session.add(new_trigger)
                    db.session.commit()
                    flash('Trigger criada com sucesso!', 'trigger_success')
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar trigger: {str(e)}', 'trigger_error')
    
    return redirect(url_for('view.notification'))
