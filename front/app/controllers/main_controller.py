from flask import Blueprint, redirect, render_template, url_for, request, jsonify
from app.services.auth_service import login_required
from app import db
from app.models.agente import Agente
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
def manage_agents(user):
    aprovados = Agente.query.filter_by(aprovado=True).all()
    pendentes = Agente.query.filter_by(aprovado=False).all()
    return render_template('application/manage.html', title='EventTrace | Agentes', user=user,
                           aprovados=aprovados, pendentes=pendentes)

@main_bp.route('/autorizar', methods=['POST'])
@login_required
def autorizar_agente(user):
    data = request.get_json()
    host_id = data.get("host_id")

    if not host_id:
        return jsonify({"error": "host_id ausente"}), 400

    agente = Agente.query.filter_by(identificador_host=host_id, aprovado=False).first()
    if not agente:
        return jsonify({"error": "Agente não encontrado ou já aprovado"}), 404

    # Envia POST para o validador
    try:
        url_validador = f"http://siem_validador:5000/aprovar/{host_id}"
        res = requests.post(url_validador, timeout=10)
        if res.status_code != 200:
            return jsonify({"error": f"Validador respondeu com erro: {res.status_code}"}), 502
    except Exception as e:
        return jsonify({"error": f"Falha ao contactar validador: {str(e)}"}), 500

    # Marca como aprovado
    agente.aprovado = True
    agente.aprovado_em = datetime.utcnow()
    db.session.commit()

    return jsonify({"status": "Agente aprovado com sucesso"}), 200

@main_bp.route('/rejeitar', methods=['POST'])
@login_required
def rejeitar_agente(user):
    data = request.get_json()
    host_id = data.get("host_id")

    if not host_id:
        return jsonify({"error": "host_id ausente"}), 400

    agente = Agente.query.filter_by(identificador_host=host_id, aprovado=False).first()
    if not agente:
        return jsonify({"error": "Agente não encontrado ou já aprovado"}), 404

    db.session.delete(agente)
    db.session.commit()

    return jsonify({"status": "Agente rejeitado e removido com sucesso"}), 200

