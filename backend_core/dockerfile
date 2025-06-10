FROM mariadb:11

# Define variáveis de ambiente padrão(podem ser sobrescritas com -e no docker run)
ENV MYSQL_ROOT_PASSWORD=Devsecops2025 \
    MYSQL_DATABASE=siem_dev \
    MYSQL_USER=devsec \
    MYSQL_PASSWORD=Devsecops2025

# Diretório padrão do container onde scripts .sql e .sh são executados na inicialização
COPY ./initdb /docker-entrypoint-initdb.d/

# Exponha a porta padrão do MariaDB
EXPOSE 3306

