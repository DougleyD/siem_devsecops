from flask import Flask, request, jsonify
from datetime import datetime
from pymongo import MongoClient
import pika, json, os, traceback
import mysql.connector

app = Flask(__name__)

# ==== Configurações ====
MONGO_URI = "mongodb://devsec:Devsec2025@mongo:27017/siem?authSource=siem"
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "devsec")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "Devsecops2025")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "logs")

APPROVED_FILE = "approved_agents.json"
LOG_DIR = "logs"

os.makedirs(LOG_DIR, exist_ok=True)
if not os.path.exists(APPROVED_FILE):
    with open(APPROVED_FILE, "w") as fp:
        json.dump({}, fp)

# ==== MongoDB ====
mongo_collection = None
try:
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    mongo_db = mongo_client["siem"]
    mongo_db.command("ping")
    mongo_collection = mongo_db["logs"]
    print("[✔️] Conectado ao MongoDB e collection 'logs' selecionada.")
except Exception as e:
    print(f"[❌] Erro ao conectar ao MongoDB: {e}")

# ==== RabbitMQ ====
channel = None
try:
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        credentials=credentials,
        heartbeat=600,
        blocked_connection_timeout=300
    )
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
    print("[✔️] Conectado ao RabbitMQ.")
except Exception as e:
    print(f"[❌] Falha na conexão com RabbitMQ: {e}")

# ==== Utilitários ====
def load_agents(file):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_agents(data, file):
    try:
        with open(file, "w") as f:
            json.dump(data, f)
    except Exception as e:
        print(f"[❌] Erro ao salvar {file}: {e}")

def salvar_agente_mariadb(host_id, public_key, fernet_key, ip_agente):
    try:
        conn = mysql.connector.connect(
            host="siem_mariadb",
            user="devsec",
            password="Devsecops2025",
            database="siem_dev"
        )
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO agentes (
                identificador_host, chave_publica, chave_fernet, ip_agente, aprovado, criado_em
            )
            VALUES (%s, %s, %s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE
                chave_publica = VALUES(chave_publica),
                chave_fernet = VALUES(chave_fernet),
                ip_agente = VALUES(ip_agente),
                aprovado = 0
        """, (host_id, public_key, fernet_key, ip_agente, 0))
        conn.commit()
        cursor.close()
        conn.close()
        print(f"[✔️] Agente salvo no banco: {host_id} | IP: {ip_agente}")
    except Exception as e:
        print(f"[❌] Erro ao salvar no MariaDB: {e}")

# ==== Rotas Flask ====

@app.route("/validar", methods=["POST"])
def validar():
    data = request.get_json()
    host_id = data.get("host_id")
    public_key = data.get("public_key")
    fernet_key_criptografada = data.get("fernet_key_criptografada")
    ip_agente = data.get("ip_agente")

    print(f"[DEBUG] Recebido agente para validação: host_id={host_id}, ip={ip_agente}")

    if not host_id or not public_key or not fernet_key_criptografada:
        print("[❌] Dados ausentes no payload")
        return jsonify({"error": "Campos obrigatórios ausentes"}), 400

    approved = load_agents(APPROVED_FILE)
    if host_id in approved:
        print(f"[✔️] Agente já aprovado: {host_id}")
        return jsonify({"status": "aprovado"}), 200

    try:
        salvar_agente_mariadb(host_id, public_key, fernet_key_criptografada, ip_agente)
    except Exception as e:
        return jsonify({"error": "Erro ao salvar agente"}), 500

    return jsonify({"status": "pendente"}), 202

@app.route("/aprovar/<host_id>", methods=["POST"])
def aprovar(host_id):
    try:
        conn = mysql.connector.connect(
            host="siem_mariadb",
            user="devsec",
            password="Devsecops2025",
            database="siem_dev"
        )
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM agentes WHERE identificador_host = %s", (host_id,))
        result = cursor.fetchone()

        if not result:
            return jsonify({"error": "host_id não encontrado no banco"}), 404

        approved = load_agents(APPROVED_FILE)
        approved[host_id] = {
            "public_key": result["chave_publica"],
            "fernet_key_criptografada": result["chave_fernet"]
        }
        save_agents(approved, APPROVED_FILE)

        cursor.execute("UPDATE agentes SET aprovado = 1, aprovado_em = NOW() WHERE identificador_host = %s", (host_id,))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"status": f"{host_id} aprovado"}), 200

    except Exception as e:
        return jsonify({"error": f"Erro ao aprovar agente: {str(e)}"}), 500

@app.route("/log", methods=["POST"])
def receber_log():
    try:
        print("[DEBUG] Requisição recebida no /log")
        data = request.get_json(force=True)
        print(f"[DEBUG] Payload recebido: {data}")

        host_id = data.get("host_id")
        blob = data.get("blob")

        if not host_id or not blob:
            return jsonify({"error": "host_id ou blob ausente"}), 400

        approved = load_agents(APPROVED_FILE)
        if host_id not in approved:
            return jsonify({"error": "Agente não aprovado"}), 403

        now = datetime.now().isoformat()
        log_entry = {
            "timestamp": now,
            "host_id": host_id,
            "blob": blob
        }

        if mongo_collection is None:
            print("[❌] mongo_collection está None dentro do /log")
        else:
            try:
                print(f"[DEBUG] Gravando no Mongo: {log_entry}")
                result = mongo_collection.insert_one(log_entry)
                print(f"[✔️] Log gravado no Mongo com _id: {result.inserted_id}")
            except Exception as e:
                print(f"[❌] Erro ao gravar no MongoDB: {e}")

        if channel:
            try:
                log_to_rabbit = dict(log_entry)
                log_to_rabbit.pop("_id", None)
                channel.basic_publish(
                    exchange='',
                    routing_key=RABBITMQ_QUEUE,
                    body=json.dumps(log_to_rabbit),
                    properties=pika.BasicProperties(delivery_mode=2)
                )
            except Exception as e:
                print(f"[❌] Erro ao enviar para RabbitMQ: {e}")

        return jsonify({"status": "log recebido"}), 201

    except Exception as e:
        print(f"[❌] Erro geral no /log: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

