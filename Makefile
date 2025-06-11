K8S_DIR := ./k8s

.PHONY: all apply delete status logs

all: apply

apply:
	@echo "🔧 Aplicando todos os manifests..."
	kubectl apply -R -f $(K8S_DIR)

delete:
	@echo "🗑️ Removendo todos os recursos..."
	kubectl delete -R -f $(K8S_DIR)

status:
	@echo "📦 Status dos pods:"
	kubectl get pods -o wide
	@echo "🌐 Serviços:"
	kubectl get svc -o wide

logs:
	@echo "📜 Logs do front:"
	kubectl logs -l app=siem-front

