# 🐳 Instalación en Easypanel usando Docker

## 📋 Guía Paso a Paso

### Paso 1: Preparar el Repositorio Git

1. **Inicializar repositorio Git** (si no lo has hecho):
```bash
cd /Users/rleon/Documents/ProyectoCursor/vRx-Dashboard-App
git init
git add .
git commit -m "Initial commit: vRx Dashboard App"
```

2. **Subir a GitHub/GitLab**:
```bash
git remote add origin https://github.com/tu-usuario/vrx-dashboard-app.git
git push -u origin main
```

### Paso 2: Configurar en Easypanel

#### Opción A: Docker Compose (Recomendado)

1. **Crear nueva aplicación en Easypanel**:
   - Ve a tu panel de Easypanel
   - Clic en "New Application"
   - Selecciona "Docker Compose"

2. **Configurar repositorio**:
   - Conecta tu repositorio Git
   - Selecciona la rama `main`
   - Directorio raíz: `/`

3. **Configurar variables de entorno**:
```bash
# Base de datos
POSTGRES_DB=vrx_dashboard
POSTGRES_USER=postgres
POSTGRES_PASSWORD=tu_password_seguro

# Aplicación
DATABASE_URL=postgresql://postgres:tu_password_seguro@postgres:5432/vrx_dashboard
API_HOST=0.0.0.0
API_PORT=8000
FRONTEND_URL=https://tu-dominio.easypanel.host
LOG_LEVEL=INFO
```

4. **Configurar puertos**:
   - Puerto: `8000`
   - Protocolo: `HTTP`
   - Público: `Sí`

#### Opción B: Dockerfile Individual

1. **Crear nueva aplicación**:
   - Selecciona "Custom Application"
   - Framework: "Docker"

2. **Configurar build**:
   - Dockerfile: Usar el Dockerfile incluido
   - Build context: `/`

3. **Configurar base de datos separada**:
   - Crear servicio PostgreSQL por separado
   - Configurar variables de conexión

### Paso 3: Configurar Base de Datos

1. **Crear servicio PostgreSQL**:
   - Imagen: `postgres:15-alpine`
   - Variables de entorno:
     ```
     POSTGRES_DB=vrx_dashboard
     POSTGRES_USER=postgres
     POSTGRES_PASSWORD=tu_password_seguro
     ```

2. **Inicializar esquema**:
   - Ejecutar el contenido de `database/schema.sql`
   - Puedes hacerlo desde la consola de PostgreSQL en Easypanel

### Paso 4: Configurar Volúmenes

1. **Volumen para reports**:
   - Nombre: `reports`
   - Ruta: `/app/vRx-Report-Unicon/reports`
   - Tipo: `Persistent Volume`

### Paso 5: Configurar Health Check

1. **Health check endpoint**:
   - Path: `/health`
   - Interval: `30s`
   - Timeout: `10s`
   - Retries: `3`

### Paso 6: Desplegar

1. **Hacer deploy**:
   - Clic en "Deploy"
   - Esperar a que se construya la imagen
   - Verificar que todos los servicios estén funcionando

2. **Verificar funcionamiento**:
   - Acceder a la URL de tu aplicación
   - Probar el endpoint `/health`
   - Verificar logs en Easypanel

## 🔧 Configuración Avanzada

### Variables de Entorno Adicionales

```bash
# Para producción
CORS_ORIGINS=https://tu-dominio.easypanel.host
LOG_LEVEL=WARNING
EXTRACTION_TIMEOUT=7200
MAX_CONCURRENT_EXTRACTIONS=2

# Para desarrollo
FRONTEND_URL=http://localhost:3000
LOG_LEVEL=DEBUG
```

### Configuración de Recursos

- **CPU**: Mínimo 1 vCPU, recomendado 2 vCPU
- **RAM**: Mínimo 2GB, recomendado 4GB
- **Almacenamiento**: Mínimo 10GB

### Configuración de Red

- **Puerto interno**: `8000`
- **Protocolo**: `HTTP`
- **Acceso público**: Habilitado

## 🚀 Comandos de Verificación

### Verificar Estado de la Aplicación

```bash
# Verificar health check
curl https://tu-dominio.easypanel.host/health

# Verificar API docs
curl https://tu-dominio.easypanel.host/docs

# Verificar base de datos
curl https://tu-dominio.easypanel.host/dashboard/overview
```

### Verificar Logs

1. **En Easypanel**:
   - Ve a la sección "Logs" de tu aplicación
   - Busca errores o advertencias
   - Verifica que las extracciones funcionen

2. **Desde terminal** (si tienes acceso SSH):
```bash
# Ver logs de la aplicación
docker logs vrx-dashboard-app

# Ver logs de la base de datos
docker logs vrx-postgres
```

## 🔍 Solución de Problemas

### Error: "Database connection failed"

**Solución**:
1. Verificar que PostgreSQL esté ejecutándose
2. Verificar DATABASE_URL en variables de entorno
3. Verificar que el esquema se haya ejecutado

```bash
# Verificar conexión a BD
docker exec -it vrx-postgres psql -U postgres -d vrx_dashboard -c "SELECT 1;"
```

### Error: "API Key invalid"

**Solución**:
1. Verificar que la API Key de Vicarius sea válida
2. Verificar que la URL del dashboard sea correcta
3. Probar conectividad desde la aplicación

### Error: "Frontend not loading"

**Solución**:
1. Verificar que el build del frontend sea exitoso
2. Verificar configuración de CORS
3. Verificar que el backend esté ejecutándose

### Error: "Extraction timeout"

**Solución**:
1. Aumentar EXTRACTION_TIMEOUT
2. Verificar recursos disponibles (CPU/RAM)
3. Verificar conectividad con API de Vicarius

## 📊 Monitoreo Post-Deployment

### Métricas a Monitorear

1. **CPU Usage**: Debe estar < 80%
2. **Memory Usage**: Debe estar < 90%
3. **Disk Usage**: Monitorear crecimiento
4. **Response Time**: < 2 segundos
5. **Error Rate**: < 1%

### Alertas Recomendadas

1. **Health Check Failures**: Configurar alertas
2. **High CPU/Memory**: > 80% por más de 5 minutos
3. **Database Connection Errors**: Cualquier fallo
4. **Extraction Failures**: Fallos en extracción de datos

## 🔄 Actualizaciones

### Actualizar la Aplicación

1. **Hacer cambios en el código**
2. **Commit y push a Git**:
```bash
git add .
git commit -m "Update: descripción del cambio"
git push origin main
```

3. **Easypanel reconstruirá automáticamente**
4. **Verificar que la nueva versión funcione**

### Actualizar Dependencias

1. **Backend**: Actualizar `backend/requirements.txt`
2. **Frontend**: Actualizar `frontend/package.json`
3. **Commit y push cambios**
4. **Easypanel reconstruirá con nuevas dependencias**

## 🛡️ Seguridad

### Configuración de Seguridad

1. **Variables de entorno**:
   - Nunca hardcodear API keys
   - Usar contraseñas seguras para PostgreSQL
   - Rotar API keys regularmente

2. **CORS**:
   - Limitar orígenes permitidos
   - No usar "*" en producción

3. **HTTPS**:
   - Easypanel maneja automáticamente SSL
   - Verificar que HTTPS esté habilitado

## 📞 Soporte

### Logs Importantes

- **Application Logs**: Errores de la aplicación
- **Database Logs**: Problemas de conexión
- **Build Logs**: Errores durante construcción
- **Deployment Logs**: Problemas de despliegue

### Contacto

Si encuentras problemas:
1. Revisar logs en Easypanel
2. Verificar configuración de variables
3. Probar localmente con Docker Compose
4. Contactar soporte de Easypanel si es necesario

---

## ✅ Checklist de Deployment

- [ ] Repositorio Git configurado
- [ ] Aplicación creada en Easypanel
- [ ] Variables de entorno configuradas
- [ ] Base de datos PostgreSQL creada
- [ ] Esquema de BD ejecutado
- [ ] Volúmenes configurados
- [ ] Health check configurado
- [ ] Puertos configurados
- [ ] Deploy ejecutado
- [ ] Aplicación funcionando
- [ ] Health check pasando
- [ ] Logs sin errores críticos
- [ ] Extracción de datos funcionando
- [ ] Dashboard cargando correctamente

¡Tu aplicación estará lista para usar! 🎉
