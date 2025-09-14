#!/bin/bash

# Script para crear un ZIP con todos los archivos necesarios para subir a Git
# Este ZIP contendrá todos los archivos que Easypanel necesita

set -e

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

print_step "Creando ZIP con todos los archivos para subir a Git..."

# Crear directorio temporal
TEMP_DIR="vrx-dashboard-upload"
ZIP_NAME="vRx-Dashboard-App-Complete.zip"

# Limpiar directorio temporal si existe
if [ -d "$TEMP_DIR" ]; then
    rm -rf "$TEMP_DIR"
fi

# Crear directorio temporal
mkdir -p "$TEMP_DIR"

print_step "Copiando archivos esenciales..."

# Copiar directorios principales
cp -r backend "$TEMP_DIR/"
cp -r frontend "$TEMP_DIR/"
cp -r database "$TEMP_DIR/"
cp -r vRx-Report "$TEMP_DIR/"

# Copiar archivos de configuración
cp Dockerfile "$TEMP_DIR/"
cp Dockerfile.easypanel "$TEMP_DIR/"
cp docker-compose.yml "$TEMP_DIR/"
cp easypanel-docker-compose.yml "$TEMP_DIR/"
cp easypanel-config.yaml "$TEMP_DIR/"
cp easypanel-env-example.txt "$TEMP_DIR/"
cp easypanel.json "$TEMP_DIR/"

# Copiar archivos de documentación
cp README.md "$TEMP_DIR/"
cp README_EASYPANEL.md "$TEMP_DIR/"
cp CONFIGURACION_EASYPANEL.md "$TEMP_DIR/"
cp INSTRUCCIONES_SUBIR_MANUAL.md "$TEMP_DIR/"

# Copiar archivos de configuración adicionales
cp .gitignore "$TEMP_DIR/"
cp .dockerignore "$TEMP_DIR/"

print_step "Verificando estructura..."

# Verificar que los directorios principales estén presentes
required_dirs=("backend" "frontend" "database" "vRx-Report")
for dir in "${required_dirs[@]}"; do
    if [ -d "$TEMP_DIR/$dir" ]; then
        print_status "Directorio $dir copiado correctamente"
    else
        print_error "Directorio $dir no encontrado"
        exit 1
    fi
done

# Verificar archivos principales
required_files=(
    "Dockerfile"
    "Dockerfile.easypanel"
    "docker-compose.yml"
    "easypanel-docker-compose.yml"
    "easypanel-config.yaml"
    "easypanel-env-example.txt"
)

for file in "${required_files[@]}"; do
    if [ -f "$TEMP_DIR/$file" ]; then
        print_status "Archivo $file copiado correctamente"
    else
        print_error "Archivo $file no encontrado"
        exit 1
    fi
done

print_step "Creando archivo ZIP..."

# Crear ZIP
cd "$TEMP_DIR"
zip -r "../$ZIP_NAME" . -x "*.DS_Store" "*.git*"
cd ..

# Limpiar directorio temporal
rm -rf "$TEMP_DIR"

print_step "Verificando ZIP creado..."

if [ -f "$ZIP_NAME" ]; then
    print_status "ZIP creado exitosamente: $ZIP_NAME"
    zip_size=$(du -sh "$ZIP_NAME" | cut -f1)
    echo "Tamaño del ZIP: $zip_size"
else
    print_error "Error al crear ZIP"
    exit 1
fi

print_step "Verificando contenido del ZIP..."

# Verificar contenido del ZIP
zip_content=$(unzip -l "$ZIP_NAME" | grep -E "(backend|frontend|database|vRx-Report|Dockerfile)" | wc -l)
echo "Archivos importantes en el ZIP: $zip_content"

echo ""
echo "🎉 ¡ZIP creado exitosamente!"
echo ""
echo "📋 Contenido del ZIP:"
echo "├── 📁 backend/                    # API FastAPI"
echo "├── 📁 frontend/                   # Dashboard React"
echo "├── 📁 database/                  # Esquemas de BD"
echo "├── 📁 vRx-Report/                # Tu código Python"
echo "├── 🐳 Dockerfile                 # Imagen Docker"
echo "├── 🐳 Dockerfile.easypanel        # Optimizado para Easypanel"
echo "├── 🐳 docker-compose.yml         # Orquestación local"
echo "├── ⚙️ easypanel-docker-compose.yml # Docker Compose para Easypanel"
echo "├── ⚙️ easypanel-config.yaml       # Configuración de Easypanel"
echo "├── ⚙️ easypanel-env-example.txt   # Variables de entorno"
echo "├── 📖 README_EASYPANEL.md        # Documentación para Easypanel"
echo "└── 📖 CONFIGURACION_EASYPANEL.md # Configuración específica"
echo ""
echo "🚀 Próximos pasos:"
echo "1. Subir el archivo $ZIP_NAME a GitHub/GitLab"
echo "2. Extraer el ZIP en el repositorio"
echo "3. Configurar en Easypanel usando Dockerfile.easypanel"
echo "4. Configurar variables de entorno"
echo "5. Deploy y listo!"
echo ""
echo "📁 Archivo listo: $ZIP_NAME"
echo ""

print_status "¡ZIP listo para subir! 🎉"
