FROM python:3.13.4-bookworm

ENV DEBIAN_FRONTEND=noninteractive

# Instala pacotes do sistema + Node.js 18.x para Snyk
RUN apt-get update && apt-get install -y \
    curl \
    git \
    gcc \
    libffi-dev \
    libssl-dev \
    libpq-dev \
    mariadb-client \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Define diretório da aplicação
WORKDIR /app
COPY . .

# Garante que o diretório raiz da aplicação esteja no PYTHONPATH
ENV PYTHONPATH=/app

# Instala as dependências do Python
RUN pip install --upgrade pip \
 && pip install -r requirements.txt \
 && pip install pytest

# Instala o Snyk CLI globalmente
RUN npm install -g snyk

# Expõe a porta usada pelo Flask
EXPOSE 5000

# Comando para iniciar a aplicação
CMD ["python", "run.py"]

