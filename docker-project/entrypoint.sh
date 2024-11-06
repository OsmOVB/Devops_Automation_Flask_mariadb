#!/bin/bash
echo "Aguardando o banco de dados iniciar..."

# Tentativa de conexão com o MariaDB até estar disponível
while ! mysqladmin ping -h "mariadb" --silent; do
    echo "MariaDB não está disponível. Aguardando..."
    sleep 5
done

echo "MariaDB está disponível. Iniciando o Flask..."
exec "$@"
