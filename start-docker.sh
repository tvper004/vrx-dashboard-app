#!/bin/bash

cd /home/rleon/vrx-dashboard

echo "🚀 Iniciando vRx Dashboard App con Docker..."

# Parar contenedores existentes
echo "Deteniendo contenedores existentes..."
docker stop vrx-postgres vrx-app 2>/dev/null || true
docker rm vrx-postgres vrx-app 2>/dev/null || true

# Crear red
echo "Creando red..."
docker network create vrx-network 2>/dev/null || true

# Iniciar PostgreSQL
echo "Iniciando PostgreSQL..."
docker run -d \
  --name vrx-postgres \
  --network vrx-network \
  -e POSTGRES_DB=vrx_dashboard \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=vrx_password_2024 \
  -v postgres_data:/var/lib/postgresql/data \
  -v $(pwd)/database/schema.sql:/docker-entrypoint-initdb.d/schema.sql \
  -p 5432:5432 \
  postgres:15-alpine

# Esperar a que PostgreSQL esté listo
echo "Esperando a que PostgreSQL esté listo..."
sleep 20

# Construir imagen de la aplicación
echo "Construyendo imagen de la aplicación..."
docker build -t vrx-dashboard-app .

# Iniciar aplicación
echo "Iniciando aplicación..."
docker run -d \
  --name vrx-app \
  --network vrx-network \
  -e DATABASE_URL=postgresql://postgres:vrx_password_2024@vrx-postgres:5432/vrx_dashboard \
  -e API_HOST=0.0.0.0 \
  -e API_PORT=8000 \
  -e FRONTEND_URL=http://192.168.1.200:8000 \
  -e LOG_LEVEL=INFO \
  -e CORS_ORIGINS=http://192.168.1.200:8000,http://localhost:8000 \
  -v $(pwd)/vRx-Report-Unicon:/app/vRx-Report-Unicon \
  -p 8000:8000 \
  vrx-dashboard-app

# Esperar a que la aplicación esté lista
echo "Esperando a que la aplicación esté lista..."
sleep 30

# Verificar estado
echo "Verificando estado de los contenedores..."
docker ps

# Verificar health check
echo "Verificando health check..."
for i in {1..10}; do
    if curl -s -f http://localhost:8000/health > /dev/null; then
        echo "✅ Aplicación funcionando correctamente"
        echo "🌐 Disponible en: http://192.168.1.200:8000"
        break
    else
        echo "⏳ Esperando aplicación... ($i/10)"
        sleep 10
    fi
done

echo "🎉 vRx Dashboard App iniciada exitosamente!"
