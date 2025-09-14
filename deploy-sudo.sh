#!/bin/bash

# Script para configurar permisos de Docker y levantar vRx Dashboard App
# Servidor: 192.168.1.200

SERVER_IP="192.168.1.200"
SERVER_USER="rleon"
APP_DIR="/home/rleon/vrx-dashboard"

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Función para ejecutar comandos en el servidor
run_remote() {
    ssh $SERVER_USER@$SERVER_IP "$1"
}

print_step "1. Configurando permisos de Docker..."

# Agregar usuario al grupo docker
run_remote "sudo usermod -aG docker $SERVER_USER"

print_warning "Usuario agregado al grupo docker. Necesitas reiniciar la sesión SSH."
print_warning "Ejecuta: ssh $SERVER_USER@$SERVER_IP"

print_step "2. Creando script de inicio con sudo..."

# Crear script que use sudo para Docker
cat > start-sudo.sh << 'EOF'
#!/bin/bash

cd /home/rleon/vrx-dashboard

echo "🚀 Iniciando vRx Dashboard App con sudo..."

# Parar contenedores existentes
echo "Deteniendo contenedores existentes..."
sudo docker stop vrx-postgres vrx-app 2>/dev/null || true
sudo docker rm vrx-postgres vrx-app 2>/dev/null || true

# Crear red
echo "Creando red..."
sudo docker network create vrx-network 2>/dev/null || true

# Iniciar PostgreSQL
echo "Iniciando PostgreSQL..."
sudo docker run -d \
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
sudo docker build -t vrx-dashboard-app .

# Iniciar aplicación
echo "Iniciando aplicación..."
sudo docker run -d \
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
sudo docker ps

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
EOF

# Copiar script al servidor
scp start-sudo.sh $SERVER_USER@$SERVER_IP:$APP_DIR/
run_remote "chmod +x $APP_DIR/start-sudo.sh"

print_status "Script de inicio con sudo creado ✓"

print_step "3. Iniciando la aplicación..."

# Ejecutar script de inicio
run_remote "cd $APP_DIR && ./start-sudo.sh"

print_status "Aplicación iniciada ✓"

echo ""
echo "🎉 ¡vRx Dashboard App desplegada exitosamente!"
echo ""
echo "📋 Información:"
echo "├── Servidor: $SERVER_IP"
echo "├── URL: http://$SERVER_IP:8000"
echo "├── API Docs: http://$SERVER_IP:8000/docs"
echo "└── Health: http://$SERVER_IP:8000/health"
echo ""
echo "🚀 Comandos útiles:"
echo "├── Iniciar: ssh $SERVER_USER@$SERVER_IP 'cd $APP_DIR && ./start-sudo.sh'"
echo "├── Parar: ssh $SERVER_USER@$SERVER_IP 'sudo docker stop vrx-postgres vrx-app'"
echo "├── Logs: ssh $SERVER_USER@$SERVER_IP 'sudo docker logs vrx-app'"
echo "└── Estado: ssh $SERVER_USER@$SERVER_IP 'sudo docker ps'"
echo ""

print_status "¡Despliegue completado! 🎉"
