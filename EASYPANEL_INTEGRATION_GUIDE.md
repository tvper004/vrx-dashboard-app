# 🚀 Integrar vRx Dashboard en Easypanel - Guía Completa

## 📋 Pasos para Integrar en Easypanel

### Paso 1: Preparar el Repositorio Git

Primero necesitas subir tu código a un repositorio Git:

```bash
# En tu máquina local
cd /Users/rleon/Documents/ProyectoCursor/vRx-Dashboard-App

# Inicializar Git (si no lo has hecho)
git init
git add .
git commit -m "vRx Dashboard App - Ready for Easypanel"

# Subir a GitHub/GitLab
git remote add origin https://github.com/tu-usuario/vrx-dashboard-app.git
git push -u origin main
```

### Paso 2: Acceder a Easypanel Web

1. **Abrir navegador** y ir a tu panel de Easypanel
2. **Iniciar sesión** con tus credenciales
3. **Ir a la sección "Projects"** o "Aplicaciones"

### Paso 3: Crear Nueva Aplicación

1. **Clic en "New Project"** o "New Application"
2. **Seleccionar tipo de aplicación**:
   - **Opción A**: "Docker Compose" (recomendado)
   - **Opción B**: "Custom Application"

### Paso 4: Configurar Repositorio

1. **Conectar repositorio Git**:
   - Seleccionar "Git Repository"
   - Ingresar URL de tu repositorio
   - Seleccionar rama `main`

2. **Configurar directorio raíz**: `/`

### Paso 5: Configurar Variables de Entorno

En la sección "Environment Variables", agregar:

```bash
# Base de datos
POSTGRES_PASSWORD=tu_password_seguro_aqui

# Aplicación
FRONTEND_URL=https://tu-dominio.easypanel.host
LOG_LEVEL=INFO
CORS_ORIGINS=https://tu-dominio.easypanel.host

# Opcional
EXTRACTION_TIMEOUT=7200
MAX_CONCURRENT_EXTRACTIONS=2
```

### Paso 6: Configurar Puertos

1. **Puerto**: `8000`
2. **Protocolo**: `HTTP`
3. **Público**: `Sí` (para acceso externo)

### Paso 7: Configurar Health Check

1. **Path**: `/health`
2. **Interval**: `30s`
3. **Timeout**: `10s`
4. **Retries**: `3`

### Paso 8: Configurar Volúmenes

1. **Nombre**: `reports`
2. **Ruta**: `/app/vRx-Report-Unicon/reports`
3. **Tipo**: `Persistent Volume`

### Paso 9: Deploy

1. **Clic en "Deploy"**
2. **Esperar** a que se construya la imagen
3. **Verificar logs** para asegurar que no hay errores

## 🔧 Configuración Específica para Easypanel

### Opción A: Docker Compose (Recomendado)

Usar el archivo `easypanel-docker-compose.yml` que ya creamos:

```yaml
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
```

### Opción B: Custom Application

Si prefieres usar "Custom Application":

1. **Framework**: `Docker`
2. **Dockerfile**: Usar el Dockerfile incluido
3. **Build context**: `/`
4. **Start command**: `python backend/main.py`

## 📊 Configuración de Recursos

### Recursos Recomendados

- **CPU**: 2 vCPU
- **RAM**: 4GB
- **Almacenamiento**: 20GB

### Configuración de Red

- **Puerto interno**: `8000`
- **Protocolo**: `HTTP`
- **Acceso público**: Habilitado

## 🔍 Verificación Post-Deployment

### Verificar Estado

1. **En Easypanel**:
   - Ir a la sección "Logs"
   - Verificar que no hay errores
   - Comprobar que los servicios estén ejecutándose

2. **Desde navegador**:
   - Acceder a la URL de tu aplicación
   - Verificar que el dashboard carga
   - Probar el health check

### URLs Importantes

- **Aplicación**: `https://tu-dominio.easypanel.host`
- **API Docs**: `https://tu-dominio.easypanel.host/docs`
- **Health Check**: `https://tu-dominio.easypanel.host/health`

## 🛠️ Solución de Problemas

### Error: "Build failed"

1. **Verificar Dockerfile**: Asegurar que sea válido
2. **Verificar dependencias**: Comprobar requirements.txt
3. **Revisar logs de build**: En Easypanel

### Error: "Database connection failed"

1. **Verificar variables de entorno**: POSTGRES_PASSWORD
2. **Verificar que PostgreSQL esté ejecutándose**
3. **Revisar logs de la base de datos**

### Error: "Port already in use"

1. **Cambiar puerto** en la configuración
2. **Verificar que no haya conflictos**

### Error: "Health check failed"

1. **Verificar que la aplicación esté ejecutándose**
2. **Comprobar que el endpoint /health funcione**
3. **Revisar logs de la aplicación**

## 🔄 Actualizaciones

### Actualizar Código

1. **Hacer cambios** en tu código local
2. **Commit y push** a Git:
   ```bash
   git add .
   git commit -m "Update: descripción del cambio"
   git push origin main
   ```
3. **Easypanel reconstruirá automáticamente**

### Actualizar Variables de Entorno

1. **En Easypanel**: Ir a configuración de la aplicación
2. **Modificar variables** de entorno
3. **Reiniciar aplicación**

## 📈 Monitoreo

### Métricas en Easypanel

1. **CPU Usage**: Debe estar < 80%
2. **Memory Usage**: Debe estar < 90%
3. **Disk Usage**: Monitorear crecimiento
4. **Response Time**: < 2 segundos

### Alertas Recomendadas

1. **Health Check Failures**
2. **High CPU/Memory Usage**
3. **Database Connection Errors**
4. **Application Crashes**

## 🎯 Checklist de Deployment

- [ ] Repositorio Git configurado
- [ ] Aplicación creada en Easypanel
- [ ] Repositorio conectado
- [ ] Variables de entorno configuradas
- [ ] Puertos configurados
- [ ] Health check configurado
- [ ] Volúmenes configurados
- [ ] Deploy ejecutado
- [ ] Aplicación funcionando
- [ ] Health check pasando
- [ ] Logs sin errores críticos
- [ ] Dashboard accesible
- [ ] API Docs funcionando

## 🎉 ¡Listo!

Una vez completados estos pasos, tu aplicación estará integrada en Easypanel y disponible para usar.

**¡Tu dashboard de seguridad estará funcionando en la nube!** 🚀
