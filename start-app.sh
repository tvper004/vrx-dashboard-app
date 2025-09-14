#!/bin/bash

cd /home/rleon/vrx-dashboard

echo "🚀 Iniciando vRx Dashboard App..."

# Parar contenedores existentes
docker-compose down 2>/dev/null || true

# Construir y levantar
echo "Construyendo imagen..."
docker-compose build

echo "Iniciando servicios..."
docker-compose up -d

# Esperar
echo "Esperando servicios..."
sleep 30

# Verificar
echo "Verificando estado..."
docker-compose ps

echo "🎉 Aplicación iniciada!"
echo "🌐 Disponible en: http://192.168.1.200:8000"
