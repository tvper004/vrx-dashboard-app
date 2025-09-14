#!/bin/bash

# Script para levantar vRx Dashboard App usando su root
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

print_step "1. Creando script de inicio con su root..."

# Crear script que use su root
cat > start-with-su.sh << 'EOF'
#!/bin/bash

cd /home/rleon/vrx-dashboard

echo "🚀 Iniciando vRx Dashboard App con su root..."

# Parar contenedores existentes
echo "Deteniendo contenedores existentes..."
su root@192.168.1.200 -c "docker stop vrx-postgres vrx-app 2>/dev/null || true"
su root@192.168.1.200 -c "docker rm vrx-postgres vrx-app 2>/dev/null || true"

# Crear red
echo "Creando red..."
su root@192.168.1.200 -c "docker network create vrx-network 2>/dev/null || true"

# Iniciar PostgreSQL
echo "Iniciando PostgreSQL..."
su root@192.168.1.200 -c "docker run -d \
  --name vrx-postgres \
  --network vrx-network \
  -e POSTGRES_DB=vrx_dashboard \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=vrx_password_2024 \
  -v postgres_data:/var/lib/postgresql/data \
  -v $(pwd)/database/schema.sql:/docker-entrypoint-initdb.d/schema.sql \
  -p 5432:5432 \
  postgres:15-alpine"

# Esperar a que PostgreSQL esté listo
echo "Esperando a que PostgreSQL esté listo..."
sleep 20

# Construir imagen de la aplicación
echo "Construyendo imagen de la aplicación..."
su root@192.168.1.200 -c "docker build -t vrx-dashboard-app ."

# Iniciar aplicación
echo "Iniciando aplicación..."
su root@192.168.1.200 -c "docker run -d \
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
  vrx-dashboard-app"

# Esperar a que la aplicación esté lista
echo "Esperando a que la aplicación esté lista..."
sleep 30

# Verificar estado
echo "Verificando estado de los contenedores..."
su root@192.168.1.200 -c "docker ps"

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
scp start-with-su.sh $SERVER_USER@$SERVER_IP:$APP_DIR/
ssh $SERVER_USER@$SERVER_IP "chmod +x $APP_DIR/start-with-su.sh"

print_status "Script de inicio con su root creado ✓"

print_step "2. Creando script de comandos útiles..."

# Crear script de comandos útiles
cat > vrx-commands-su.sh << 'EOF'
#!/bin/bash

# Script de comandos para vRx Dashboard App usando su root
# Servidor: 192.168.1.200

APP_DIR="/home/rleon/vrx-dashboard"

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_help() {
    echo -e "${BLUE}vRx Dashboard App - Comandos con su root${NC}"
    echo ""
    echo "Uso: $0 [comando]"
    echo ""
    echo "Comandos disponibles:"
    echo "  start      - Iniciar la aplicación"
    echo "  stop       - Parar la aplicación"
    echo "  restart    - Reiniciar la aplicación"
    echo "  status     - Ver estado de la aplicación"
    echo "  logs       - Ver logs en tiempo real"
    echo "  health     - Verificar health check"
    echo "  shell      - Acceder al contenedor"
    echo "  help       - Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0 start"
    echo "  $0 logs"
    echo "  $0 status"
}

case "$1" in
    start)
        echo -e "${GREEN}🚀 Iniciando vRx Dashboard App...${NC}"
        cd $APP_DIR && ./start-with-su.sh
        ;;
    stop)
        echo -e "${YELLOW}🛑 Parando vRx Dashboard App...${NC}"
        su root@192.168.1.200 -c "docker stop vrx-postgres vrx-app"
        ;;
    restart)
        echo -e "${BLUE}🔄 Reiniciando vRx Dashboard App...${NC}"
        su root@192.168.1.200 -c "docker restart vrx-postgres vrx-app"
        ;;
    status)
        echo -e "${BLUE}📊 Estado de vRx Dashboard App${NC}"
        su root@192.168.1.200 -c "docker ps"
        ;;
    logs)
        echo -e "${BLUE}📋 Logs de vRx Dashboard App${NC}"
        echo "Presiona Ctrl+C para salir"
        su root@192.168.1.200 -c "docker logs vrx-app -f"
        ;;
    health)
        echo -e "${BLUE}🔍 Verificando health check...${NC}"
        if curl -s -f http://localhost:8000/health > /dev/null; then
            echo -e "${GREEN}✅ Aplicación funcionando correctamente${NC}"
        else
            echo -e "${RED}❌ Aplicación no responde${NC}"
        fi
        ;;
    shell)
        echo -e "${BLUE}🐚 Accediendo al contenedor...${NC}"
        su root@192.168.1.200 -c "docker exec -it vrx-app bash"
        ;;
    help|--help|-h)
        print_help
        ;;
    *)
        echo -e "${YELLOW}Comando no reconocido: $1${NC}"
        echo ""
        print_help
        exit 1
        ;;
esac
EOF

# Copiar script al servidor
scp vrx-commands-su.sh $SERVER_USER@$SERVER_IP:$APP_DIR/
ssh $SERVER_USER@$SERVER_IP "chmod +x $APP_DIR/vrx-commands-su.sh"

print_status "Script de comandos creado ✓"

print_step "3. Creando guía de uso..."

# Crear guía de uso
cat > GUIA_USO_SU_ROOT.md << 'EOF'
# 🚀 Guía de Uso con su root

## 📋 Comandos Disponibles

### Conectar al Servidor
```bash
ssh rleon@192.168.1.200
```

### Ir al Directorio de la Aplicación
```bash
cd /home/rleon/vrx-dashboard
```

### Comandos Rápidos
```bash
# Iniciar aplicación
./vrx-commands-su.sh start

# Ver estado
./vrx-commands-su.sh status

# Ver logs
./vrx-commands-su.sh logs

# Parar aplicación
./vrx-commands-su.sh stop

# Verificar health check
./vrx-commands-su.sh health
```

### Comandos Manuales con su root

#### Iniciar Aplicación
```bash
su root@192.168.1.200
# Ingresa la contraseña cuando se solicite
docker network create vrx-network 2>/dev/null || true
docker run -d --name vrx-postgres --network vrx-network -e POSTGRES_DB=vrx_dashboard -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=vrx_password_2024 -v postgres_data:/var/lib/postgresql/data -v $(pwd)/database/schema.sql:/docker-entrypoint-initdb.d/schema.sql -p 5432:5432 postgres:15-alpine
sleep 20
docker build -t vrx-dashboard-app .
docker run -d --name vrx-app --network vrx-network -e DATABASE_URL=postgresql://postgres:vrx_password_2024@vrx-postgres:5432/vrx_dashboard -e API_HOST=0.0.0.0 -e API_PORT=8000 -e FRONTEND_URL=http://192.168.1.200:8000 -e LOG_LEVEL=INFO -e CORS_ORIGINS=http://192.168.1.200:8000,http://localhost:8000 -v $(pwd)/vRx-Report-Unicon:/app/vRx-Report-Unicon -p 8000:8000 vrx-dashboard-app
```

#### Ver Estado
```bash
su root@192.168.1.200
docker ps
```

#### Ver Logs
```bash
su root@192.168.1.200
docker logs vrx-app -f
```

#### Parar Aplicación
```bash
su root@192.168.1.200
docker stop vrx-postgres vrx-app
docker rm vrx-postgres vrx-app
```

## 🌐 Acceso a la Aplicación

Una vez iniciada, la aplicación estará disponible en:
- **Dashboard**: http://192.168.1.200:8000
- **API Docs**: http://192.168.1.200:8000/docs
- **Health Check**: http://192.168.1.200:8000/health

## 🔧 Solución de Problemas

### Error: "permission denied"
Asegúrate de usar `su root@192.168.1.200` antes de ejecutar comandos Docker.

### Error: "port already in use"
```bash
su root@192.168.1.200
docker stop vrx-postgres vrx-app
```

### Error: "container not found"
```bash
su root@192.168.1.200
docker ps -a
```

## 📊 Monitoreo

### Ver Recursos
```bash
su root@192.168.1.200
docker stats
```

### Ver Logs en Tiempo Real
```bash
su root@192.168.1.200
docker logs vrx-app -f
```

### Verificar Health Check
```bash
curl http://192.168.1.200:8000/health
```

## 🎉 ¡Listo!

Tu aplicación estará funcionando en **http://192.168.1.200:8000**
EOF

print_status "Guía de uso creada ✓"

print_step "4. Mostrando información final..."

echo ""
echo "🎉 ¡Scripts creados exitosamente!"
echo ""
echo "📋 Archivos creados en el servidor:"
echo "├── start-with-su.sh      # Script de inicio con su root"
echo "├── vrx-commands-su.sh    # Comandos útiles"
echo "└── GUIA_USO_SU_ROOT.md   # Guía de uso"
echo ""
echo "🚀 Próximos pasos:"
echo "1. Conectar al servidor:"
echo "   ssh rleon@192.168.1.200"
echo ""
echo "2. Ir al directorio:"
echo "   cd /home/rleon/vrx-dashboard"
echo ""
echo "3. Iniciar la aplicación:"
echo "   ./vrx-commands-su.sh start"
echo ""
echo "4. Verificar estado:"
echo "   ./vrx-commands-su.sh status"
echo ""
echo "5. Acceder a la aplicación:"
echo "   http://192.168.1.200:8000"
echo ""
echo "📖 Para más información, consulta:"
echo "   cat GUIA_USO_SU_ROOT.md"
echo ""

print_status "¡Preparación completada! 🎉"
