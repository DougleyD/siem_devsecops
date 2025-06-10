import os
import sys
import time
import json
import gzip
import base64
import socket
import psutil
import hashlib
import requests
import subprocess
from datetime import datetime
from cryptography.fernet import Fernet
from collections import deque
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
import urllib.request

# ========== CHAVE PÚBLICA DO MANAGER (PEM hardcoded) ==========
MANAGER_PUBLIC_KEY_PEM = b"""
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAolQgLnTtcnxNNzx4CBmZ
Km97BKfWEuO0FZpDhjBYyvn7kD0hBV+HkKam0yCG58rJkhCQGxPMajlhVkTWjdRL
PKTpWXPAUQ1Sv1mB2cKQnZnFaWU8qcVI+qzKER+8qoIMYe7eUj0FB85lFUR1A/q0
T+i6bYri+u2Aqr1KR9AsaTpUByVM2pf4IdbDM75y8djdXzh4nfKJ3rCOFyQCVaZy
adSy49Z0GiAkBrCVMttDgtZEK5BvOuwubSrXwPRwAqoypZIKs7sOp6UcPNxzN0rN
Gs41K+N2uLiYNpZBhumFeXYmZ4eqiLe8cXtrg6eNmPoji9QC5QwtSdGcAOELPiBh
AwIDAQAB
-----END PUBLIC KEY-----
"""

# ========== CONFIGURAÇÃO ==========
INTERVAL = 30
MAX_BUFFER_SIZE = 50
AGENT_DIR = os.path.expanduser("~/.siem_agent")
KEY_FILE = os.path.join(AGENT_DIR, "fernet.key")
BUFFER_FILE = os.path.join(AGENT_DIR, "siem_buffer.json")
DEBUG_FILE = os.path.join(AGENT_DIR, "debug_payload.json")
CURSOR_FILE = os.path.join(AGENT_DIR, "last_cursor.txt")
LOG_FILE = os.path.join(AGENT_DIR, "agent.log")
ID_FILE = os.path.join(AGENT_DIR, "host_id")

LOG_FILTER_MODE = 'all'
FILTERS = {
    'all': [],
    'ssh': ['sshd', 'failed password', 'authentication failure'],
    'user': ['session opened', 'session closed', 'useradd', 'passwd', 'sudo', 'su'],
    'auth': ['pam_unix', 'authentication failure', 'failed password', 'sudo']
}

# ========== FUNÇÕES DE IDENTIDADE ==========
def gerar_host_id():
    if os.path.exists(ID_FILE):
        with open(ID_FILE) as f:
            return f.read().strip()

    def read_file(path):
        try:
            with open(path, "r") as f:
                return f.read().strip()
        except:
            return ""

    def get_disk_serial():
        try:
            result = subprocess.run(["lsblk", "-o", "NAME,SERIAL"], capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if any(d in line for d in ["sda", "nvme"]):
                    parts = line.split()
                    if len(parts) == 2:
                        return parts[1]
        except:
            pass
        return ""

    uuid = read_file("/sys/class/dmi/id/product_uuid")
    disk_serial = get_disk_serial()
    raw = f"{uuid}|{disk_serial}"
    host_id = hashlib.sha256(raw.encode()).hexdigest()
    with open(ID_FILE, "w") as f:
        f.write(host_id)
    return host_id

# ========== UTILITÁRIOS ==========
def setup_logging():
    os.makedirs(AGENT_DIR, mode=0o700, exist_ok=True)
    for f in [KEY_FILE, BUFFER_FILE, DEBUG_FILE, CURSOR_FILE, LOG_FILE, ID_FILE]:
        if os.path.exists(f):
            os.chmod(f, 0o600)

def log_message(msg, level="INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [{level}] {msg}")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] [{level}] {msg}\n")

def get_or_create_key():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
        return key
    with open(KEY_FILE, "rb") as f:
        return f.read()

# ========== COLETA ==========
def get_journal_logs():
    cursor = open(CURSOR_FILE).read().strip() if os.path.exists(CURSOR_FILE) else None
    cmd = ["journalctl", "--output", "json", "--no-pager"]
    cmd += ["--after-cursor", cursor] if cursor else ["--since", "5 minutes ago"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
    logs, last_cursor = [], None
    filters = FILTERS.get(LOG_FILTER_MODE, [])

    for line in lines:
        try:
            entry = json.loads(line)
            msg = entry.get("MESSAGE", "")
            ts = entry.get("__REALTIME_TIMESTAMP")
            iso_ts = datetime.fromtimestamp(int(ts)/1_000_000).isoformat() if ts and ts.isdigit() else None
            if not filters or any(term in msg.lower() for term in filters):
                logs.append({
                    "timestamp": iso_ts,
                    "host": entry.get("_HOSTNAME", socket.gethostname()),
                    "unit": entry.get("_SYSTEMD_UNIT", "unknown"),
                    "priority": entry.get("PRIORITY", 6),
                    "message": msg
                })
            last_cursor = entry.get("__CURSOR", last_cursor)
        except:
            continue
    if last_cursor:
        with open(CURSOR_FILE, "w") as f:
            f.write(last_cursor)
    return logs or ["-- No entries --"]

def get_system_metrics():
    return {
        "cpu": {
            "percent": psutil.cpu_percent(interval=1),
            "load_avg": os.getloadavg(),
            "cores": psutil.cpu_count(logical=False),
            "threads": psutil.cpu_count(logical=True)
        },
        "memory": psutil.virtual_memory()._asdict(),
        "disk": {
            "root": psutil.disk_usage('/')._asdict(),
            "total": psutil.disk_io_counters()._asdict()
        },
        "network": {
            "connections": len(psutil.net_connections()),
            "io": psutil.net_io_counters()._asdict()
        },
        "process_count": len(psutil.pids())
    }

# ========== ENVIO ==========
def build_payload():
    payload = {
        "timestamp": datetime.now().isoformat(),
        "hostname": socket.gethostname(),
        "ip_address": socket.gethostbyname(socket.gethostname()),
        "host_id": gerar_host_id(),
        "metrics": get_system_metrics(),
        "logs": {"journalctl": get_journal_logs()}
    }
    with open(DEBUG_FILE, "w") as f:
        json.dump(payload, f, indent=2)
    return payload

def encrypt_blob(data, fernet):
    json_data = json.dumps(data).encode('utf-8')
    compressed = gzip.compress(json_data)
    encrypted = fernet.encrypt(compressed)
    return base64.b64encode(encrypted).decode('utf-8')

def encrypt_fernet_key_with_rsa(key):
    public_key = serialization.load_pem_public_key(MANAGER_PUBLIC_KEY_PEM)
    encrypted = public_key.encrypt(
        key,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    )
    return base64.b64encode(encrypted).decode()

def post_to_validator(blob, url, host_id):
    try:
        res = requests.post(f"{url}/log", json={"host_id": host_id, "blob": blob}, timeout=10)
        if res.status_code in [200, 201]:
            log_message("Log enviado com sucesso")
            return True
        log_message(f"Erro ao enviar log: {res.status_code}", "ERROR")
    except Exception as e:
        log_message(f"Erro conexão validador: {e}", "ERROR")
    return False

def obter_ip_agente():
    try:
        # Tenta obter IP público de serviços confiáveis
        for url in ["https://api.ipify.org", "https://ifconfig.me/ip"]:
            try:
                with urllib.request.urlopen(url, timeout=5) as response:
                    ip_publico = response.read().decode().strip()
                    if ip_publico:
                        return ip_publico
            except Exception:
                continue
        raise Exception("Não foi possível obter IP público")
    except Exception as e:
        # Fallback para IP local
        try:
            return socket.gethostbyname(socket.gethostname())
        except:
            return "0.0.0.0"

def try_validar(url, host_id):
    try:
        pubkey = MANAGER_PUBLIC_KEY_PEM.decode()
        fernet_key = get_or_create_key()
        encrypted_fernet = encrypt_fernet_key_with_rsa(fernet_key)
        ip_agente = obter_ip_agente()
        payload = {
            "host_id": host_id,
            "public_key": pubkey,
            "fernet_key_criptografada": encrypted_fernet,
            "ip_agente": ip_agente
        }
        res = requests.post(f"{url}/validar", json=payload, timeout=10)
        if res.status_code in [200, 201]:
            log_message("Agente validado com sucesso")
            return True
        else:
            log_message(f"Validação pendente: {res.status_code}", "WARNING")
            return False
    except Exception as e:
        log_message(f"Erro na validação: {str(e)}", "CRITICAL")
        return False

# ========== LOOP PRINCIPAL ==========
def main():
    if len(sys.argv) != 2:
        print("Uso: python3 agent.py <IP_HOSPEDEIRO>")
        sys.exit(1)
    infra_ip = sys.argv[1]
    validator_url = f"http://{infra_ip}:7777"

    setup_logging()
    host_id = gerar_host_id()

    if not try_validar(validator_url, host_id):
        log_message("Abortando: agente não autorizado", "CRITICAL")
        return

    fernet = Fernet(get_or_create_key())
    buffer = load_buffer_from_disk()

    while True:
        try:
            payload = build_payload()
            blob = encrypt_blob(payload, fernet)
            buffer.append(blob)
            save_buffer_to_disk(buffer)
            while buffer:
                if post_to_validator(buffer[0], validator_url, host_id):
                    buffer.popleft()
                    save_buffer_to_disk(buffer)
                else:
                    break
            time.sleep(INTERVAL)
        except Exception as e:
            log_message(f"Erro geral no loop: {str(e)}", "ERROR")
            time.sleep(10)

def save_buffer_to_disk(buffer):
    with open(BUFFER_FILE, "w") as f:
        json.dump(list(buffer), f)

def load_buffer_from_disk():
    if os.path.exists(BUFFER_FILE):
        try:
            with open(BUFFER_FILE, "r") as f:
                return deque(json.load(f), maxlen=MAX_BUFFER_SIZE)
        except:
            pass
    return deque(maxlen=MAX_BUFFER_SIZE)

if __name__ == "__main__":
    main()
