#!/bin/bash

set -e

echo "[✔] Instalando K3s..."
curl -sfL https://get.k3s.io | sh -

echo "[✔] Configurando kubectl para o usuário atual..."
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $USER:$USER ~/.kube/config

echo "[✔] Aguardando K3s inicializar..."
sleep 10
kubectl get nodes

echo "[✔] Criando namespaces e PVCs compartilhados..."
kubectl apply -f k8s/pvc.yaml

echo "[✔] Subindo componentes: MariaDB..."
kubectl apply -f k8s/mariadb/configmap.yaml
kubectl apply -f k8s/mariadb/pvc.yaml
kubectl apply -f k8s/mariadb/deployment.yaml
kubectl apply -f k8s/mariadb/service.yaml

echo "[✔] Subindo MongoDB e Mongo Express..."
kubectl apply -f k8s/mongo/pvc.yaml
kubectl apply -f k8s/mongo/deployment.yaml
kubectl apply -f k8s/mongo/service.yaml
kubectl apply -f k8s/mongo-express/deployment.yaml
kubectl apply -f k8s/mongo-express/service.yaml

echo "[✔] Subindo RabbitMQ..."
kubectl apply -f k8s/rabbitmq/deployment.yaml
kubectl apply -f k8s/rabbitmq/service.yaml

echo "[✔] Subindo Front-end..."
kubectl apply -f k8s/siem_front/deployment.yaml
kubectl apply -f k8s/siem_front/service.yaml

echo "[✔] Subindo Validador..."
kubectl apply -f k8s/validador/deployment.yaml
kubectl apply -f k8s/validador/service.yaml

echo "[✅] Deploy concluído com sucesso!"

echo ""
echo "[🌐] Acesse o sistema em: http://<IP-DO-HOST>:9000"

