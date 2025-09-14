#!/bin/bash

# Script de instalación para vRx Dashboard App
# Este script configura la aplicación para deployment en Easypanel

set -e

echo "🚀 Configurando vRx Dashboard App..."

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Verificar que estamos en el directorio correcto
if [ ! -f "easypanel.json" ]; then
    print_error "No se encontró easypanel.json. Ejecuta este script desde el directorio raíz del proyecto."
    exit 1
fi

print_status "Verificando estructura del proyecto..."

# Verificar archivos necesarios
required_files=(
    "backend/main.py"
    "backend/requirements.txt"
    "frontend/package.json"
    "database/schema.sql"
    "Dockerfile"
    "docker-compose.yml"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        print_error "Archivo requerido no encontrado: $file"
        exit 1
    fi
done

print_status "Estructura del proyecto verificada ✓"

# Crear directorio para el script Python existente si no existe
if [ ! -d "vRx-Report-Unicon" ]; then
    print_warning "Directorio vRx-Report-Unicon no encontrado."
    print_warning "Asegúrate de copiar tu código Python existente a este directorio."
    mkdir -p vRx-Report-Unicon
fi

# Crear directorio de reports
mkdir -p vRx-Report-Unicon/reports

print_status "Creando archivos de configuración..."

# Crear archivo .env para desarrollo local
cat > .env << EOF
# Configuración de desarrollo local
DATABASE_URL=postgresql://postgres:password@localhost:5432/vrx_dashboard
API_HOST=0.0.0.0
API_PORT=8000
FRONTEND_URL=http://localhost:3000
LOG_LEVEL=INFO
EOF

print_status "Archivo .env creado ✓"

# Crear script de inicialización de BD
cat > init-db.sh << 'EOF'
#!/bin/bash
# Script para inicializar la base de datos

echo "🗄️ Inicializando base de datos..."

# Esperar a que PostgreSQL esté listo
until pg_isready -h localhost -p 5432 -U postgres; do
    echo "Esperando a que PostgreSQL esté listo..."
    sleep 2
done

# Crear base de datos si no existe
createdb vrx_dashboard 2>/dev/null || echo "Base de datos ya existe"

# Ejecutar esquema
psql vrx_dashboard < database/schema.sql

echo "✅ Base de datos inicializada correctamente"
EOF

chmod +x init-db.sh

print_status "Script de inicialización de BD creado ✓"

# Crear script de deployment para Easypanel
cat > deploy-easypanel.sh << 'EOF'
#!/bin/bash
# Script para deployment en Easypanel

echo "🚀 Preparando aplicación para Easypanel..."

# Crear archivo de configuración de Easypanel
cat > easypanel-config.yaml << 'YAML'
name: vrx-dashboard
type: application
framework: fastapi
database: postgresql

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - 8000
    environment:
      DATABASE_URL: "postgresql://postgres:password@postgres:5432/vrx_dashboard"
      API_HOST: "0.0.0.0"
      API_PORT: "8000"
    volumes:
      - name: reports
        path: /app/vRx-Report-Unicon/reports
    healthcheck:
      path: /health
      interval: 30
      timeout: 10
      retries: 3

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: vrx_dashboard
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/schema.sql:/docker-entrypoint-initdb.d/schema.sql
YAML

echo "✅ Archivo de configuración de Easypanel creado"
echo "📋 Instrucciones para deployment:"
echo "1. Sube este proyecto a tu repositorio Git"
echo "2. En Easypanel, crea una nueva aplicación"
echo "3. Selecciona 'Custom Application'"
echo "4. Conecta tu repositorio Git"
echo "5. Usa el archivo easypanel-config.yaml como configuración"
echo "6. Configura las variables de entorno necesarias"
EOF

chmod +x deploy-easypanel.sh

print_status "Script de deployment creado ✓"

# Crear script de desarrollo local
cat > start-dev.sh << 'EOF'
#!/bin/bash
# Script para desarrollo local

echo "🔧 Iniciando entorno de desarrollo..."

# Verificar si Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no está instalado. Instálalo primero."
    exit 1
fi

# Verificar si Docker Compose está instalado
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose no está instalado. Instálalo primero."
    exit 1
fi

# Iniciar servicios
echo "🐳 Iniciando servicios con Docker Compose..."
docker-compose up -d

# Esperar a que los servicios estén listos
echo "⏳ Esperando a que los servicios estén listos..."
sleep 10

# Verificar estado de los servicios
echo "🔍 Verificando estado de los servicios..."
docker-compose ps

echo "✅ Servicios iniciados correctamente"
echo "🌐 Aplicación disponible en: http://localhost:8000"
echo "📊 API Docs disponible en: http://localhost:8000/docs"
echo "🗄️ Base de datos disponible en: localhost:5432"
EOF

chmod +x start-dev.sh

print_status "Script de desarrollo creado ✓"

# Crear script de parada
cat > stop-dev.sh << 'EOF'
#!/bin/bash
# Script para parar entorno de desarrollo

echo "🛑 Parando servicios..."

docker-compose down

echo "✅ Servicios parados correctamente"
EOF

chmod +x stop-dev.sh

print_status "Script de parada creado ✓"

# Crear archivo de configuración para el frontend
cat > frontend/.env << EOF
REACT_APP_API_URL=http://localhost:8000
EOF

print_status "Configuración del frontend creada ✓"

# Crear directorio de logs
mkdir -p logs

print_status "Directorio de logs creado ✓"

# Mostrar resumen
echo ""
echo "🎉 ¡Configuración completada!"
echo ""
echo "📁 Estructura del proyecto:"
echo "├── backend/          # API FastAPI"
echo "├── frontend/         # Aplicación React"
echo "├── database/         # Esquemas de BD"
echo "├── vRx-Report-Unicon/ # Script Python existente"
echo "├── logs/            # Archivos de log"
echo "└── scripts/         # Scripts de utilidad"
echo ""
echo "🚀 Comandos disponibles:"
echo "├── ./start-dev.sh      # Iniciar desarrollo local"
echo "├── ./stop-dev.sh        # Parar desarrollo local"
echo "├── ./init-db.sh         # Inicializar base de datos"
echo "└── ./deploy-easypanel.sh # Preparar para Easypanel"
echo ""
echo "📋 Próximos pasos:"
echo "1. Copia tu código Python existente a vRx-Report-Unicon/"
echo "2. Configura tus variables de entorno en .env"
echo "3. Ejecuta ./start-dev.sh para desarrollo local"
echo "4. O usa ./deploy-easypanel.sh para deployment en Easypanel"
echo ""
echo "🔗 URLs importantes:"
echo "├── Aplicación: http://localhost:8000"
echo "├── API Docs: http://localhost:8000/docs"
echo "└── Base de datos: localhost:5432"
echo ""

print_status "¡Configuración completada exitosamente! 🎉"
