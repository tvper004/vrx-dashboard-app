#!/bin/bash

# Script para validar que todo esté correcto antes de subir a Git
# Verifica estructura, archivos y configuraciones

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

print_step "1. Verificando estructura de directorios..."

# Verificar directorios principales
required_dirs=("backend" "frontend" "database" "vRx-Report")
for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        print_status "Directorio $dir existe"
    else
        print_error "Directorio $dir no encontrado"
        exit 1
    fi
done

print_step "2. Verificando archivos principales..."

# Verificar archivos principales
required_files=(
    "backend/main.py"
    "backend/requirements.txt"
    "frontend/package.json"
    "frontend/src/App.js"
    "database/schema.sql"
    "vRx-Report/VickyvRxReportCLI.py"
    "Dockerfile"
    "docker-compose.yml"
    "easypanel-docker-compose.yml"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        print_status "Archivo $file existe"
    else
        print_error "Archivo $file no encontrado"
        exit 1
    fi
done

print_step "3. Verificando configuración de Docker..."

# Verificar Dockerfile
if grep -q "vRx-Report" Dockerfile; then
    print_status "Dockerfile usa vRx-Report correctamente"
else
    print_error "Dockerfile no usa vRx-Report"
    exit 1
fi

# Verificar docker-compose.yml
if grep -q "vRx-Report" docker-compose.yml; then
    print_status "docker-compose.yml usa vRx-Report correctamente"
else
    print_error "docker-compose.yml no usa vRx-Report"
    exit 1
fi

# Verificar easypanel-docker-compose.yml
if grep -q "vRx-Report" easypanel-docker-compose.yml; then
    print_status "easypanel-docker-compose.yml usa vRx-Report correctamente"
else
    print_error "easypanel-docker-compose.yml no usa vRx-Report"
    exit 1
fi

print_step "4. Verificando configuración del backend..."

# Verificar que el backend use vRx-Report
if grep -q "vRx-Report" backend/main.py; then
    print_status "Backend usa vRx-Report correctamente"
else
    print_error "Backend no usa vRx-Report"
    exit 1
fi

if grep -q "vRx-Report" backend/config.py; then
    print_status "Config.py usa vRx-Report correctamente"
else
    print_error "Config.py no usa vRx-Report"
    exit 1
fi

print_step "5. Verificando archivos de configuración..."

# Verificar que no queden referencias a vRx-Report-Unicon
if grep -r "vRx-Report-Unicon" . --exclude-dir=.git --exclude="*.md" > /dev/null 2>&1; then
    print_warning "Aún hay referencias a vRx-Report-Unicon en archivos de configuración"
    echo "Archivos con referencias:"
    grep -r "vRx-Report-Unicon" . --exclude-dir=.git --exclude="*.md" | cut -d: -f1 | sort | uniq
else
    print_status "No hay referencias a vRx-Report-Unicon en archivos de configuración"
fi

print_step "6. Verificando estructura de vRx-Report..."

# Verificar contenido de vRx-Report
if [ -f "vRx-Report/VickyvRxReportCLI.py" ]; then
    print_status "VickyvRxReportCLI.py existe en vRx-Report"
else
    print_error "VickyvRxReportCLI.py no existe en vRx-Report"
    exit 1
fi

if [ -d "vRx-Report/reports" ]; then
    print_status "Directorio reports existe en vRx-Report"
else
    print_warning "Directorio reports no existe en vRx-Report, creándolo..."
    mkdir -p vRx-Report/reports
    print_status "Directorio reports creado"
fi

print_step "7. Verificando archivos de Easypanel..."

# Verificar archivos específicos de Easypanel
easypanel_files=(
    "easypanel-docker-compose.yml"
    "easypanel-config.yaml"
    "easypanel-env-example.txt"
    "README_EASYPANEL.md"
)

for file in "${easypanel_files[@]}"; do
    if [ -f "$file" ]; then
        print_status "Archivo $file existe"
    else
        print_error "Archivo $file no encontrado"
        exit 1
    fi
done

print_step "8. Verificando .gitignore..."

if [ -f ".gitignore" ]; then
    print_status ".gitignore existe"
    if grep -q "\.env" .gitignore; then
        print_status ".gitignore incluye .env"
    else
        print_warning ".gitignore no incluye .env"
    fi
else
    print_error ".gitignore no existe"
    exit 1
fi

print_step "9. Verificando tamaño del proyecto..."

# Verificar tamaño del proyecto
project_size=$(du -sh . | cut -f1)
echo "Tamaño del proyecto: $project_size"

# Verificar archivos grandes
large_files=$(find . -type f -size +10M -not -path "./.git/*" 2>/dev/null || true)
if [ -n "$large_files" ]; then
    print_warning "Archivos grandes encontrados:"
    echo "$large_files"
else
    print_status "No hay archivos grandes"
fi

print_step "10. Verificando permisos..."

# Verificar permisos de archivos ejecutables
executable_files=$(find . -type f -executable -not -path "./.git/*" 2>/dev/null || true)
if [ -n "$executable_files" ]; then
    print_status "Archivos ejecutables encontrados:"
    echo "$executable_files"
else
    print_warning "No hay archivos ejecutables"
fi

print_step "11. Verificando dependencias..."

# Verificar requirements.txt
if [ -f "backend/requirements.txt" ]; then
    print_status "requirements.txt existe"
    if grep -q "fastapi" backend/requirements.txt; then
        print_status "FastAPI incluido en requirements.txt"
    else
        print_error "FastAPI no incluido en requirements.txt"
        exit 1
    fi
else
    print_error "requirements.txt no existe"
    exit 1
fi

# Verificar package.json
if [ -f "frontend/package.json" ]; then
    print_status "package.json existe"
    if grep -q "react" frontend/package.json; then
        print_status "React incluido en package.json"
    else
        print_error "React no incluido en package.json"
        exit 1
    fi
else
    print_error "package.json no existe"
    exit 1
fi

print_step "12. Verificando configuración de base de datos..."

# Verificar schema.sql
if [ -f "database/schema.sql" ]; then
    print_status "schema.sql existe"
    if grep -q "CREATE TABLE" database/schema.sql; then
        print_status "schema.sql contiene tablas"
    else
        print_error "schema.sql no contiene tablas"
        exit 1
    fi
else
    print_error "schema.sql no existe"
    exit 1
fi

echo ""
echo "🎉 ¡Validación completada exitosamente!"
echo ""
echo "📋 Resumen de la validación:"
echo "├── ✅ Estructura de directorios correcta"
echo "├── ✅ Archivos principales presentes"
echo "├── ✅ Configuración de Docker correcta"
echo "├── ✅ Backend configurado correctamente"
echo "├── ✅ Archivos de Easypanel preparados"
echo "├── ✅ Dependencias verificadas"
echo "├── ✅ Base de datos configurada"
echo "└── ✅ Proyecto listo para subir"
echo ""
echo "🚀 El proyecto está listo para subir a Git y desplegar en Easypanel!"
echo ""
echo "📖 Próximos pasos:"
echo "1. Crear repositorio en GitHub/GitLab"
echo "2. Subir la carpeta completa manualmente"
echo "3. Configurar en Easypanel usando easypanel-docker-compose.yml"
echo "4. Configurar variables de entorno"
echo "5. Deploy y listo!"
echo ""

print_status "¡Validación exitosa! 🎉"
