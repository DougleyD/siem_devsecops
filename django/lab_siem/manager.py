import socket

# Configurações do servidor
HOST = '0.0.0.0'  # Escuta em todas as interfaces
PORT = 9999       # Porta de comunicação

# Cria o socket
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    server_socket.bind((HOST, PORT))
    server_socket.listen()

    print(f"Servidor aguardando conexões em {HOST}:{PORT}...")
    conn, addr = server_socket.accept()
    with conn:

        # Recebe o nome do arquivo
        file_name = conn.recv(1024).decode('utf-8')
        print(f"Recebendo arquivo: {file_name}")

        # Recebe o arquivo em blocos de 1024 bytes
        with open(file_name, 'wb') as file:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                file.write(data)

        print(f"Arquivo {file_name} recebido com sucesso!")

""" COMUNICAÇÃO ENTRE SOCKETS

import socket
import json

# Configurações do socket
HOST = '0.0.0.0'  # Escuta em todas as interfaces
PORT = 9999      # Porta de comunicação

# Criar o socket e aguardar conexões
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as manager_socket:
    manager_socket.bind((HOST, PORT))
    manager_socket.listen()
    print(f"Aguardando conexões em {HOST}:{PORT}...")
    conn, addr = manager_socket.accept()
    with conn:
        print(f"Conexão estabelecida com {addr}")
        data = conn.recv(1024)  # Recebe os dados (ajuste o tamanho do buffer se necessário)
        json_data = data.decode('utf-8')  # Decodifica os bytes para string
        dados = json.loads(json_data)  # Converte o JSON para dicionário
        print("Dados recebidos:", dados)
"""

""" CONECTIVIDADE ENTRE HOSTS
from pythonping import ping

def status_ping(host):
    try:
        # Executa o PING com 4 pacotes
        resultado = ping(host, count=4, timeout=2)

        # Verifica se houve resposta
        if resultado.success():
            print(f"Host {host} está acessível.")
            print(resultado)
        else:
            print(f"Host {host} não está acessível.")
    except Exception as e:
        print(f"Erro ao tentar pingar {host}: {e}")

status_ping("192.168.31.134")"
"""