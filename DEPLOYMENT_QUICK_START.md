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
