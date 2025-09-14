#!/bin/bash

# Script simplificado para levantar vRx Dashboard App desde SSH
# Servidor: 192.168.1.200

SERVER_IP="192.168.1.200"
SERVER_USER="rleon"
APP_DIR="/home/rleon/vrx-dashboard"

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Función para ejecutar comandos en el servidor
run_remote() {
    ssh $SERVER_USER@$SERVER_IP "$1"
}

# Función para copiar archivos al servidor
copy_to_server() {
    scp -r "$1" $SERVER_USER@$SERVER_IP:"$2"
}

print_step "1. Verificando conexión al servidor..."

if ! ssh -o ConnectTimeout=10 $SERVER_USER@$SERVER_IP "echo 'Conexión OK'" > /dev/null 2>&1; then
    echo "❌ No se puede conectar al servidor $SERVER_IP"
    exit 1
fi

print_status "Conexión al servidor verificada ✓"

print_step "2. Creando directorio de la aplicación..."

run_remote "mkdir -p $APP_DIR"
print_status "Directorio $APP_DIR creado ✓"

print_step "3. Copiando archivos de la aplicación..."

# Copiar archivos necesarios
copy_to_server "backend/" "$APP_DIR/"
copy_to_server "frontend/" "$APP_DIR/"
copy_to_server "database/" "$APP_DIR/"
copy_to_server "vRx-Report-Unicon/" "$APP_DIR/"
copy_to_server "Dockerfile" "$APP_DIR/"
copy_to_server "docker-compose.yml" "$APP_DIR/"

print_status "Archivos copiados al servidor ✓"

print_step "4. Creando archivo de configuración..."

# Crear archivo .env
cat > server.env << 'EOF'
POSTGRES_PASSWORD=vrx_password_2024
FRONTEND_URL=http://192.168.1.200:8000
LOG_LEVEL=INFO
CORS_ORIGINS=http://192.168.1.200:8000,http://localhost:8000
API_HOST=0.0.0.0
API_PORT=8000
DATABASE_URL=postgresql://postgres:vrx_password_2024@postgres:5432/vrx_dashboard
EOF

copy_to_server "server.env" "$APP_DIR/.env"

print_status "Archivo de configuración creado ✓"

print_step "5. Creando script de inicio simple..."

# Crear script de inicio simple
cat > start-app.sh << 'EOF'
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
EOF

copy_to_server "start-app.sh" "$APP_DIR/"
run_remote "chmod +x $APP_DIR/start-app.sh"

print_status "Script de inicio creado ✓"

print_step "6. Iniciando la aplicación..."

# Ejecutar script de inicio
run_remote "cd $APP_DIR && ./start-app.sh"

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
echo "├── Iniciar: ssh $SERVER_USER@$SERVER_IP 'cd $APP_DIR && ./start-app.sh'"
echo "├── Parar: ssh $SERVER_USER@$SERVER_IP 'cd $APP_DIR && docker-compose down'"
echo "├── Logs: ssh $SERVER_USER@$SERVER_IP 'cd $APP_DIR && docker-compose logs -f'"
echo "└── Estado: ssh $SERVER_USER@$SERVER_IP 'cd $APP_DIR && docker-compose ps'"
echo ""

print_status "¡Despliegue completado! 🎉"
