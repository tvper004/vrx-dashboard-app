#!/bin/bash

# Script para levantar vRx Dashboard App desde SSH en servidor Easypanel
# Servidor: 192.168.1.200

set -e

# Configuración
SERVER_IP="192.168.1.200"
SERVER_USER="rleon"
APP_NAME="vrx-dashboard"
APP_DIR="/opt/vrx-dashboard"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir mensajes
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
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
    print_error "No se puede conectar al servidor $SERVER_IP"
    exit 1
fi

print_status "Conexión al servidor verificada ✓"

print_step "2. Verificando Docker en el servidor..."

if ! run_remote "docker --version" > /dev/null 2>&1; then
    print_error "Docker no está instalado en el servidor"
    print_warning "Instalando Docker..."
    
    # Instalar Docker
    run_remote "
        apt-get update && \
        apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release && \
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg && \
        echo \"deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \$(lsb_release -cs) stable\" | tee /etc/apt/sources.list.d/docker.list > /dev/null && \
        apt-get update && \
        apt-get install -y docker-ce docker-ce-cli containerd.io && \
        systemctl enable docker && \
        systemctl start docker
    "
    
    print_status "Docker instalado ✓"
else
    print_status "Docker ya está instalado ✓"
fi

print_step "3. Verificando Docker Compose..."

if ! run_remote "docker-compose --version" > /dev/null 2>&1; then
    print_warning "Docker Compose no está instalado, instalando..."
    
    run_remote "
        curl -L \"https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose && \
        chmod +x /usr/local/bin/docker-compose && \
        ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    "
    
    print_status "Docker Compose instalado ✓"
else
    print_status "Docker Compose ya está instalado ✓"
fi

print_step "4. Creando directorio de la aplicación en el servidor..."

run_remote "mkdir -p $APP_DIR"
print_status "Directorio $APP_DIR creado ✓"

print_step "5. Copiando archivos de la aplicación..."

# Copiar archivos necesarios
copy_to_server "backend/" "$APP_DIR/"
copy_to_server "frontend/" "$APP_DIR/"
copy_to_server "database/" "$APP_DIR/"
copy_to_server "vRx-Report-Unicon/" "$APP_DIR/"
copy_to_server "Dockerfile" "$APP_DIR/"
copy_to_server "docker-compose.yml" "$APP_DIR/"
copy_to_server "easypanel-docker-compose.yml" "$APP_DIR/"
copy_to_server "nginx.conf" "$APP_DIR/"

print_status "Archivos copiados al servidor ✓"

print_step "6. Creando archivo de configuración para el servidor..."

# Crear archivo .env específico para el servidor
cat > server.env << 'EOF'
# Configuración para servidor Easypanel
POSTGRES_PASSWORD=vrx_secure_password_2024
FRONTEND_URL=http://192.168.1.200:8000
LOG_LEVEL=INFO
CORS_ORIGINS=http://192.168.1.200:8000,http://localhost:8000
API_HOST=0.0.0.0
API_PORT=8000
DATABASE_URL=postgresql://postgres:vrx_secure_password_2024@postgres:5432/vrx_dashboard
EOF

copy_to_server "server.env" "$APP_DIR/.env"

print_status "Archivo de configuración creado ✓"

print_step "7. Creando script de inicio en el servidor..."

# Crear script de inicio
cat > start-vrx-app.sh << 'EOF'
#!/bin/bash

# Script de inicio para vRx Dashboard App
cd /opt/vrx-dashboard

echo "🚀 Iniciando vRx Dashboard App..."

# Verificar que Docker esté ejecutándose
if ! systemctl is-active --quiet docker; then
    echo "Iniciando Docker..."
    systemctl start docker
fi

# Parar contenedores existentes si los hay
echo "Deteniendo contenedores existentes..."
docker-compose -f easypanel-docker-compose.yml down 2>/dev/null || true

# Construir y levantar servicios
echo "Construyendo imagen..."
docker-compose -f easypanel-docker-compose.yml build

echo "Iniciando servicios..."
docker-compose -f easypanel-docker-compose.yml up -d

# Esperar a que los servicios estén listos
echo "Esperando a que los servicios estén listos..."
sleep 30

# Verificar estado de los servicios
echo "Verificando estado de los servicios..."
docker-compose -f easypanel-docker-compose.yml ps

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

copy_to_server "start-vrx-app.sh" "$APP_DIR/"
run_remote "chmod +x $APP_DIR/start-vrx-app.sh"

print_status "Script de inicio creado ✓"

print_step "8. Creando script de parada..."

cat > stop-vrx-app.sh << 'EOF'
#!/bin/bash

# Script de parada para vRx Dashboard App
cd /opt/vrx-dashboard

echo "🛑 Deteniendo vRx Dashboard App..."

# Parar contenedores
docker-compose -f easypanel-docker-compose.yml down

echo "✅ Aplicación detenida"
EOF

copy_to_server "stop-vrx-app.sh" "$APP_DIR/"
run_remote "chmod +x $APP_DIR/stop-vrx-app.sh"

print_status "Script de parada creado ✓"

print_step "9. Creando script de monitoreo..."

cat > monitor-vrx-app.sh << 'EOF'
#!/bin/bash

# Script de monitoreo para vRx Dashboard App
cd /opt/vrx-dashboard

echo "📊 Estado de vRx Dashboard App"
echo "================================"

# Estado de contenedores
echo "🐳 Contenedores:"
docker-compose -f easypanel-docker-compose.yml ps

echo ""
echo "📈 Recursos:"
echo "CPU: $(docker stats --no-stream --format 'table {{.CPUPerc}}' vrx-dashboard-app 2>/dev/null | tail -1 || echo 'N/A')"
echo "RAM: $(docker stats --no-stream --format 'table {{.MemUsage}}' vrx-dashboard-app 2>/dev/null | tail -1 || echo 'N/A')"

echo ""
echo "🔍 Health Check:"
if curl -s -f http://localhost:8000/health > /dev/null; then
    echo "✅ Aplicación: OK"
else
    echo "❌ Aplicación: ERROR"
fi

echo ""
echo "📋 Logs recientes:"
docker-compose -f easypanel-docker-compose.yml logs --tail=10
EOF

copy_to_server "monitor-vrx-app.sh" "$APP_DIR/"
run_remote "chmod +x $APP_DIR/monitor-vrx-app.sh"

print_status "Script de monitoreo creado ✓"

print_step "10. Iniciando la aplicación..."

# Ejecutar script de inicio
run_remote "cd $APP_DIR && ./start-vrx-app.sh"

print_status "Aplicación iniciada ✓"

# Mostrar información final
echo ""
echo "🎉 ¡vRx Dashboard App desplegada exitosamente!"
echo ""
echo "📋 Información del despliegue:"
echo "├── Servidor: $SERVER_IP"
echo "├── Usuario: $SERVER_USER"
echo "├── Directorio: $APP_DIR"
echo "├── URL: http://$SERVER_IP:8000"
echo "└── API Docs: http://$SERVER_IP:8000/docs"
echo ""
echo "🚀 Comandos útiles:"
echo "├── Iniciar: ssh $SERVER_USER@$SERVER_IP 'cd $APP_DIR && ./start-vrx-app.sh'"
echo "├── Parar: ssh $SERVER_USER@$SERVER_IP 'cd $APP_DIR && ./stop-vrx-app.sh'"
echo "├── Monitorear: ssh $SERVER_USER@$SERVER_IP 'cd $APP_DIR && ./monitor-vrx-app.sh'"
echo "└── Ver logs: ssh $SERVER_USER@$SERVER_IP 'cd $APP_DIR && docker-compose logs -f'"
echo ""
echo "🔧 Configuración:"
echo "├── Contraseña BD: vrx_secure_password_2024"
echo "├── Puerto: 8000"
echo "└── Health Check: http://$SERVER_IP:8000/health"
echo ""

print_status "¡Despliegue completado exitosamente! 🎉"
