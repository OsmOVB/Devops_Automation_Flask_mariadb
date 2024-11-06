#!/bin/bash
echo "Aguardando o banco de dados iniciar..."

while ! nc -z mariadb_container 3306; do
    echo "MariaDB não está disponível. Aguardando..."
    sleep 5
done

echo "MariaDB disponível. Iniciando a aplicação Flask."
exec flask run --host=0.0.0.0 --port=5000
