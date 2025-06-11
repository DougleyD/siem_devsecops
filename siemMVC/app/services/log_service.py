from pymongo import MongoClient
from cryptography.fernet import Fernet
from sqlalchemy.orm import Session
from siemMVC.app.models.agents import Agent
from app import db
import base64
import json
import os


def get_mongo_logs():
    client = MongoClient(os.getenv("MONGO_URI", "mongodb://devsec:Devsec2025@mongo:27017/siem?authSource=siem"))
    db_mongo = client["siem"]
    logs_collection = db_mongo["logs"]

    logs = []
    for doc in logs_collection.find().sort("timestamp", -1).limit(50):
        try:
            # Cada log vem criptografado e com um identificador_unico (host_id)
            host_id = doc.get("identificador_unico")
            encrypted_blob = doc.get("blob")

            if not host_id or not encrypted_blob:
                continue

            # Buscar agente no MariaDB
            agente: Agent = Agent.query.filter_by(identificador_unico=host_id, aprovado=True).first()
            if not agente:
                continue

            # Descriptografar blob com chave fernet
            fernet_key = agente.chave_fernet.encode()
            fernet = Fernet(fernet_key)
            decrypted_data = fernet.decrypt(encrypted_blob.encode()).decode()

            log_json = json.loads(decrypted_data)

            # Adicionar metadados extras se necessário
            logs.append({
                "timestamp": log_json.get("event", {}).get("timestamp", "N/A"),
                "id": log_json.get("event", {}).get("id", "N/A"),
                "agent_id": log_json.get("agent", {}).get("id", "N/A"),
                "hostname": log_json.get("agent", {}).get("hostname", "N/A"),
                "ip": log_json.get("agent", {}).get("ip", "N/A"),
                "description": log_json.get("event", {}).get("type", "N/A"),
                "category": log_json.get("event", {}).get("outcome", "N/A"),
                "full": log_json
            })

        except Exception as e:
            print(f"Erro ao processar log: {e}")
            continue

    return logs

