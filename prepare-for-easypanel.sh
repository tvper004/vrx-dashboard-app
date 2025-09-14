#!/bin/bash

# Script para preparar vRx Dashboard App para Easypanel
# Este script prepara todo para subir a Git y desplegar en Easypanel

set -e

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

print_step "1. Preparando archivos para Easypanel..."

# Crear archivo .gitignore
cat > .gitignore << 'EOF'
# Archivos de sistema
.DS_Store
Thumbs.db

# Archivos de entorno
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Logs
logs/
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Dependencias
node_modules/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
ENV/
env.bak/
venv.bak/

# Archivos de build
build/
dist/
*.egg-info/

# Archivos temporales
*.tmp
*.temp
.cache/

# Archivos de IDE
.vscode/
.idea/
*.swp
*.swo

# Archivos de Docker
.dockerignore

# Archivos de base de datos
*.db
*.sqlite
*.sqlite3

# Archivos de configuración local
server.env
local.env
EOF

print_status "Archivo .gitignore creado ✓"

# Crear archivo README específico para Easypanel
cat > README_EASYPANEL.md << 'EOF'
# vRx Dashboard App - Easypanel Deployment

## 🚀 Deployment en Easypanel

Esta aplicación está configurada para desplegarse fácilmente en Easypanel.

### 📋 Requisitos

- Cuenta de Easypanel
- Repositorio Git (GitHub/GitLab)
- API Key de Vicarius vRx

### 🚀 Deployment Rápido

1. **Subir a Git**:
   ```bash
   git add .
   git commit -m "vRx Dashboard App"
   git push origin main
   ```

2. **En Easypanel**:
   - Crear nueva aplicación
   - Seleccionar "Docker Compose"
   - Conectar repositorio Git
   - Usar `easypanel-docker-compose.yml`

3. **Configurar variables**:
   ```
   POSTGRES_PASSWORD=tu_password_seguro
   FRONTEND_URL=https://tu-dominio.easypanel.host
   LOG_LEVEL=INFO
   CORS_ORIGINS=https://tu-dominio.easypanel.host
   ```

4. **Deploy y listo!**

### 🌐 Acceso

- **Dashboard**: https://tu-dominio.easypanel.host
- **API Docs**: https://tu-dominio.easypanel.host/docs
- **Health Check**: https://tu-dominio.easypanel.host/health

### 📊 Funcionalidades

- Dashboard interactivo tipo PowerBI
- Extracción automática de datos de Vicarius
- Visualizaciones dinámicas
- API REST completa
- Base de datos PostgreSQL

### 🔧 Configuración

Para usar la aplicación necesitas:
- API Key de Vicarius
- URL del dashboard de Vicarius

### 📞 Soporte

Si encuentras problemas:
1. Revisar logs en Easypanel
2. Verificar variables de entorno
3. Comprobar conectividad con Vicarius API
EOF

print_status "README para Easypanel creado ✓"

# Crear archivo de configuración específico para Easypanel
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

print_status "Configuración de Easypanel creada ✓"

# Crear archivo de variables de entorno para Easypanel
cat > easypanel-env-example.txt << 'EOF'
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

print_status "Variables de entorno de ejemplo creadas ✓"

print_step "2. Preparando para Git..."

# Verificar si ya es un repositorio Git
if [ ! -d ".git" ]; then
    print_warning "Inicializando repositorio Git..."
    git init
    print_status "Repositorio Git inicializado ✓"
else
    print_status "Repositorio Git ya existe ✓"
fi

# Agregar todos los archivos
git add .

# Verificar estado
print_step "3. Verificando archivos para commit..."

echo "Archivos preparados para commit:"
git status --porcelain

print_step "4. Creando commit inicial..."

# Crear commit
git commit -m "vRx Dashboard App - Ready for Easypanel deployment

- Dashboard interactivo tipo PowerBI
- API REST con FastAPI
- Frontend React con visualizaciones
- Base de datos PostgreSQL
- Integración con Vicarius vRx
- Configuración para Easypanel
- Docker Compose incluido
- Health checks configurados
- Scripts de automatización"

print_status "Commit creado ✓"

print_step "5. Mostrando información para Easypanel..."

echo ""
echo "🎉 ¡Aplicación preparada para Easypanel!"
echo ""
echo "📋 Archivos creados:"
echo "├── .gitignore                    # Archivos a ignorar"
echo "├── README_EASYPANEL.md          # Documentación para Easypanel"
echo "├── easypanel-config.yaml        # Configuración de Easypanel"
echo "├── easypanel-env-example.txt    # Variables de entorno"
echo "└── easypanel-docker-compose.yml # Docker Compose para Easypanel"
echo ""
echo "🚀 Próximos pasos:"
echo "1. Subir a Git:"
echo "   git remote add origin https://github.com/tu-usuario/vrx-dashboard-app.git"
echo "   git push -u origin main"
echo ""
echo "2. En Easypanel:"
echo "   - Crear nueva aplicación"
echo "   - Seleccionar 'Docker Compose'"
echo "   - Conectar repositorio Git"
echo "   - Usar easypanel-docker-compose.yml"
echo "   - Configurar variables de easypanel-env-example.txt"
echo ""
echo "3. Deploy y listo!"
echo ""
echo "📖 Documentación completa en:"
echo "   - README_EASYPANEL.md"
echo "   - EASYPANEL_INTEGRATION_GUIDE.md"
echo ""

print_status "¡Preparación completada! 🎉"
