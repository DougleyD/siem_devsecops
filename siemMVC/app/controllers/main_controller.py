from flask import Blueprint, flash, redirect, render_template, session, url_for, request, jsonify
from app.services.auth_service import admin_required, login_required
from app import db
from siemMVC.app.models.agents import Agent
from datetime import datetime
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
import base64
import os
import requests

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def root():
    return redirect(url_for('auth.login'))

@main_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard(user):
    return render_template('application/dashboard.html', title='EventTrace | Dashboard', user=user)

@main_bp.route('/manage', methods=['GET'])
@login_required
@admin_required
def manage_agents(user):
    if 'authenticated' not in session:
        flash('Por favor, faça login para acessar esta página', 'error')
        return redirect(url_for('auth.login'))
    
    approved_agents = Agent.query.filter_by(aprovado=True).all()
    pending_agents = Agent.query.filter_by(aprovado=False).all()
    return render_template('application/manage.html', title='EventTrace | Manage Agent', user=user,
                           approved_agents=approved_agents, pending_agents=pending_agents)

@main_bp.route('/update_agent', methods=['POST'])
@login_required
@admin_required
def update_agent(user):
    if 'authenticated' not in session:
        flash('Por favor, faça login para acessar esta página', 'error')
        return redirect(url_for('auth.login'))
    
    agent_id = request.form.get('agent_id')
    notes = request.form.get('notes')
    collect_resources = request.form.get('collect_resources') == 'on'
    collect_system = request.form.get('collect_system') == 'on'
    collect_auth = request.form.get('collect_auth') == 'on'
    collect_web = request.form.get('collect_web') == 'on'

    agent = Agent.query.get(agent_id)
    if not agent:
        flash('Agente não encontrado', 'error')
        return redirect(url_for('main.manage'))
    
    try:
        agent.notes = notes
        agent.collect_resources = collect_resources
        agent.collect_system = collect_system
        agent.collect_auth = collect_auth
        agent.collect_web = collect_web
        
        db.session.commit()
        flash('Configurações do agente atualizadas com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar agente: {str(e)}', 'error')
    
    return redirect(url_for('main.manage'))

@main_bp.route('/autorizar', methods=['POST'])
@login_required
@admin_required
def autorizar_agente(user):
    data = request.get_json()
    host_id = data.get("host_id")

    if not host_id:
        return redirect(url_for('main.manage'))

    agente = Agent.query.filter_by(identificador_host=host_id, aprovado=False).first()
    if not agente:
        return redirect(url_for('main.manage'))

    # Envia POST para o validador
    try:
        url_validador = f"http://siem_validador:5000/aprovar/{host_id}"
        res = requests.post(url_validador, timeout=10)
        if res.status_code != 200:
            return redirect(url_for('main.manage'))
    except Exception as e:
        return redirect(url_for('main.manage'))

    # Marca como aprovado
    agente.aprovado = True
    agente.aprovado_em = datetime.utcnow()
    db.session.commit()

    return redirect(url_for('main.manage'))

@main_bp.route('/rejeitar', methods=['POST'])
@login_required
@admin_required
def rejeitar_agente(user):
    data = request.get_json()
    host_id = data.get("host_id")

    if not host_id:
        return redirect(url_for('main.manage'))

    agente = Agent.query.filter_by(identificador_host=host_id, aprovado=False).first()
    if not agente:
        return redirect(url_for('main.manage'))

    db.session.delete(agente)
    db.session.commit()

    return redirect(url_for('main.manage'))

@main_bp.route('/bloquear', methods=['POST'])
@login_required
@admin_required
def bloquear(user):
    agent_id = request.form.get("agent_id")

    if not agent_id:
        flash('ID do agente ausente', 'error')
        return redirect(url_for('main.manage'))

    agente = Agent.query.filter_by(id=agent_id, aprovado=True).first()
    if not agente:
        flash('Agente não encontrado ou já bloqueado', 'error')
        return redirect(url_for('main.manage'))

    agente.aprovado = False
    db.session.commit()
    flash('Agente bloqueado com sucesso!', 'success')

    return redirect(url_for('main.manage'))