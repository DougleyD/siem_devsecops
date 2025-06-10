from datetime import datetime
from flask import Blueprint, flash, redirect, render_template, request, session, url_for, send_file, current_app
from app.models.triggers import Trigger
from app.models.webhooks import Webhook
from app.services.auth_service import admin_required, login_required
import os
from app import db
   
view_bp = Blueprint('view', __name__)

@view_bp.route('/events', methods=['GET'])
@login_required
def events(user):
    if 'authenticated' not in session:
      flash('Por favor, faça login para acessar esta página', 'error')
      return redirect(url_for('auth.login'))
    return render_template('application/events.html', title='EventTrace | Event View', user=user)

@view_bp.route('/download', methods=['GET'])
@login_required
def download(user):
    if 'authenticated' not in session:
      flash('Por favor, faça login para acessar esta página', 'error')
      return redirect(url_for('auth.login'))
  
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
    
@view_bp.route('/manage', methods=['GET', 'POST'])
@login_required
@admin_required
def manage(user):
    if 'authenticated' not in session:
        flash('Por favor, faça login para acessar esta página', 'error')
        return redirect(url_for('auth.login'))
    
    # Dados mockados para exemplo (substitua por seus dados reais)
    approved_agents = [
        {
            'id': '00100',
            'notes': '8.5',
            'approval_timestamp': datetime(2023, 5, 15),
            'status': 'down',
            'collect_resources': True,
            'collect_system': True,
            'collect_auth': True,
            'collect_web': True
        },
        {
            'id': '00101',
            'notes': '7.2',
            'approval_timestamp': datetime(2023, 6, 1),
            'status': 'up',
            'collect_resources': True,
            'collect_system': False,
            'collect_auth': True,
            'collect_web': False
        }
    ]
    
    pending_agents = [
        {
            'id': '00200',
            'notes': None,
            'created_at': datetime(2023, 5, 28),
            'collect_resources': True,
            'collect_system': True,
            'collect_auth': False,
            'collect_web': True
        },
        {
            'id': '00201',
            'notes': None,
            'created_at': datetime(2023, 6, 10),
            'collect_resources': False,
            'collect_system': True,
            'collect_auth': True,
            'collect_web': False
        }
    ]
    
    if request.method == 'POST':
        # Processar o formulário de configuração
        agent_id = request.form.get('agent_id')
        nota = request.form.get('nota')
        collect_resources = 'collect_resources' in request.form
        collect_system = 'collect_system' in request.form
        collect_auth = 'collect_auth' in request.form
        collect_web = 'collect_web' in request.form
        
        # Atualizar os dados mockados (simulando banco de dados)
        for agent in approved_agents + pending_agents:
            if agent['id'] == agent_id:
                if nota:
                    agent['notes'] = nota
                agent['collect_resources'] = collect_resources
                agent['collect_system'] = collect_system
                agent['collect_auth'] = collect_auth
                agent['collect_web'] = collect_web
                flash('Configurações do agent atualizadas com sucesso!', 'success')
                break
        else:
            flash('Agent não encontrado!', 'error')
        
        return redirect(url_for('view.manage'))
    
    return render_template('application/manage.html', 
                         title='EventTrace | Manage Agent', 
                         user=user,
                         approved_agents=approved_agents,
                         pending_agents=pending_agents)

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