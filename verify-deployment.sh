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
