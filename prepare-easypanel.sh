#!/bin/bash

# Script para preparar deployment en Easypanel usando Docker
# Este script configura la aplicación específicamente para Easypanel

set -e

echo "🐳 Preparando vRx Dashboard App para Easypanel..."

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

# Verificar que estamos en el directorio correcto
if [ ! -f "Dockerfile" ]; then
    print_error "No se encontró Dockerfile. Ejecuta este script desde el directorio raíz del proyecto."
    exit 1
fi

print_step "1. Verificando estructura del proyecto..."

# Verificar archivos necesarios
required_files=(
    "backend/main.py"
    "backend/requirements.txt"
    "frontend/package.json"
    "database/schema.sql"
    "Dockerfile"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        print_error "Archivo requerido no encontrado: $file"
        exit 1
    fi
done

print_status "Estructura del proyecto verificada ✓"

print_step "2. Creando configuración específica para Easypanel..."

# Crear archivo de configuración para Easypanel
cat > easypanel-config.yaml << 'EOF'
# Configuración para Easypanel
name: vrx-dashboard
type: docker-compose
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: vrx_dashboard
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/schema.sql:/docker-entrypoint-initdb.d/schema.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 30s
      timeout: 10s
      retries: 3

  app:
    build: .
    environment:
      DATABASE_URL: postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/vrx_dashboard
      API_HOST: 0.0.0.0
      API_PORT: 8000
      FRONTEND_URL: ${FRONTEND_URL}
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
      CORS_ORIGINS: ${CORS_ORIGINS:-*}
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - reports_data:/app/vRx-Report-Unicon/reports
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

volumes:
  postgres_data:
  reports_data:
EOF

print_status "Archivo de configuración de Easypanel creado ✓"

# Crear archivo de variables de entorno para Easypanel
cat > easypanel-env.txt << 'EOF'
# Variables de entorno para Easypanel
# Copia estas variables en la configuración de Easypanel

# Base de datos
POSTGRES_PASSWORD=tu_password_seguro_aqui

# Aplicación
FRONTEND_URL=https://tu-dominio.easypanel.host
LOG_LEVEL=INFO
CORS_ORIGINS=https://tu-dominio.easypanel.host

# Opcional: Para desarrollo
# LOG_LEVEL=DEBUG
# CORS_ORIGINS=http://localhost:3000,https://tu-dominio.easypanel.host
EOF

print_status "Archivo de variables de entorno creado ✓"

print_step "3. Creando script de inicialización de base de datos..."

# Crear script para inicializar la base de datos
cat > init-database.sql << 'EOF'
-- Script de inicialización para Easypanel
-- Este script se ejecuta automáticamente al crear la base de datos

-- Crear base de datos si no existe
SELECT 'CREATE DATABASE vrx_dashboard'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'vrx_dashboard')\gexec

-- Conectar a la base de datos
\c vrx_dashboard;

-- Ejecutar el esquema principal
\i /docker-entrypoint-initdb.d/schema.sql

-- Verificar que las tablas se crearon correctamente
\dt

-- Mostrar mensaje de éxito
SELECT 'Base de datos vrx_dashboard inicializada correctamente' as status;
EOF

print_status "Script de inicialización de BD creado ✓"

print_step "4. Creando archivo de configuración de Docker optimizado..."

# Crear Dockerfile optimizado para Easypanel
cat > Dockerfile.easypanel << 'EOF'
# Dockerfile optimizado para Easypanel
FROM node:18-alpine AS frontend-builder

# Construir frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --only=production
COPY frontend/ ./
RUN npm run build

# Imagen final con Python
FROM python:3.11-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos de Python existentes
COPY vRx-Report-Unicon/ ./vRx-Report-Unicon/

# Instalar dependencias de Python
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código del backend
COPY backend/ ./

# Copiar frontend construido
COPY --from=frontend-builder /app/frontend/build ./static

# Crear directorio para reports
RUN mkdir -p /app/vRx-Report-Unicon/reports

# Configurar variables de entorno
ENV PYTHONPATH=/app
ENV API_HOST=0.0.0.0
ENV API_PORT=8000

# Exponer puerto
EXPOSE 8000

# Comando de inicio
CMD ["python", "main.py"]
EOF

print_status "Dockerfile optimizado creado ✓"

print_step "5. Creando script de verificación..."

# Crear script para verificar el deployment
cat > verify-deployment.sh << 'EOF'
#!/bin/bash

# Script para verificar que el deployment en Easypanel funciona correctamente

echo "🔍 Verificando deployment en Easypanel..."

# URL de tu aplicación (reemplaza con tu URL real)
APP_URL=${APP_URL:-"https://tu-dominio.easypanel.host"}

# Función para verificar endpoint
check_endpoint() {
    local endpoint=$1
    local description=$2
    
    echo "Verificando $description..."
    if curl -s -f "$APP_URL$endpoint" > /dev/null; then
        echo "✅ $description: OK"
        return 0
    else
        echo "❌ $description: FAILED"
        return 1
    fi
}

# Verificar endpoints
check_endpoint "/health" "Health Check"
check_endpoint "/docs" "API Documentation"
check_endpoint "/dashboard/overview" "Dashboard Overview"

echo "🎉 Verificación completada!"
EOF

chmod +x verify-deployment.sh

print_status "Script de verificación creado ✓"

print_step "6. Creando documentación de deployment..."

# Crear guía rápida de deployment
cat > DEPLOYMENT_QUICK_START.md << 'EOF'
# 🚀 Deployment Rápido en Easypanel

## Pasos para Deploy

### 1. Preparar Repositorio
```bash
git add .
git commit -m "Prepare for Easypanel deployment"
git push origin main
```

### 2. Configurar en Easypanel
1. Crear nueva aplicación
2. Seleccionar "Docker Compose"
3. Conectar repositorio Git
4. Usar archivo `easypanel-docker-compose.yml`

### 3. Configurar Variables de Entorno
Copiar variables del archivo `easypanel-env.txt`:
- POSTGRES_PASSWORD
- FRONTEND_URL
- LOG_LEVEL
- CORS_ORIGINS

### 4. Configurar Puertos
- Puerto: 8000
- Protocolo: HTTP
- Público: Sí

### 5. Configurar Health Check
- Path: /health
- Interval: 30s
- Timeout: 10s
- Retries: 3

### 6. Deploy
1. Clic en "Deploy"
2. Esperar construcción
3. Verificar logs
4. Probar aplicación

## Verificación Post-Deploy

```bash
# Ejecutar script de verificación
./verify-deployment.sh
```

## URLs Importantes
- Aplicación: https://tu-dominio.easypanel.host
- API Docs: https://tu-dominio.easypanel.host/docs
- Health Check: https://tu-dominio.easypanel.host/health

## Solución de Problemas
- Revisar logs en Easypanel
- Verificar variables de entorno
- Comprobar conectividad de BD
- Verificar health checks
EOF

print_status "Documentación de deployment creada ✓"

print_step "7. Creando archivo .dockerignore..."

# Crear .dockerignore para optimizar build
cat > .dockerignore << 'EOF'
# Archivos a ignorar en Docker build
node_modules
npm-debug.log
.git
.gitignore
README.md
.env
.env.local
.env.development.local
.env.test.local
.env.production.local
.DS_Store
*.log
logs/
*.pid
*.seed
*.pid.lock
coverage/
.nyc_output/
.cache/
dist/
build/
EOF

print_status "Archivo .dockerignore creado ✓"

# Mostrar resumen
echo ""
echo "🎉 ¡Preparación para Easypanel completada!"
echo ""
echo "📁 Archivos creados:"
echo "├── easypanel-config.yaml      # Configuración de Easypanel"
echo "├── easypanel-env.txt          # Variables de entorno"
echo "├── easypanel-docker-compose.yml # Docker Compose para Easypanel"
echo "├── init-database.sql          # Script de inicialización BD"
echo "├── Dockerfile.easypanel       # Dockerfile optimizado"
echo "├── verify-deployment.sh       # Script de verificación"
echo "├── DEPLOYMENT_QUICK_START.md  # Guía rápida"
echo "└── .dockerignore              # Optimización Docker"
echo ""
echo "🚀 Próximos pasos:"
echo "1. Subir código a Git:"
echo "   git add ."
echo "   git commit -m 'Prepare for Easypanel deployment'"
echo "   git push origin main"
echo ""
echo "2. En Easypanel:"
echo "   - Crear nueva aplicación"
echo "   - Seleccionar 'Docker Compose'"
echo "   - Conectar repositorio Git"
echo "   - Usar easypanel-docker-compose.yml"
echo "   - Configurar variables de easypanel-env.txt"
echo ""
echo "3. Deploy y verificar:"
echo "   - Hacer deploy"
echo "   - Ejecutar ./verify-deployment.sh"
echo "   - Probar la aplicación"
echo ""
echo "📖 Documentación completa en:"
echo "   - DEPLOYMENT_QUICK_START.md"
echo "   - EASYPANEL_DOCKER_GUIDE.md"
echo ""

print_status "¡Preparación completada exitosamente! 🎉"
