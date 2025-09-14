# 🎯 Pasos Específicos para Integrar en Easypanel

## ✅ Lo que ya tienes preparado

Tu aplicación está **100% lista** para Easypanel. He creado todos los archivos necesarios:

- ✅ **Repositorio Git** inicializado
- ✅ **Commit inicial** creado
- ✅ **Configuración de Easypanel** lista
- ✅ **Docker Compose** optimizado
- ✅ **Variables de entorno** preparadas
- ✅ **Documentación** completa

## 🚀 Pasos para Integrar en Easypanel

### Paso 1: Subir a GitHub/GitLab

```bash
# Crear repositorio en GitHub/GitLab primero, luego:
git remote add origin https://github.com/tu-usuario/vrx-dashboard-app.git
git push -u origin main
```

### Paso 2: En Easypanel Web

1. **Abrir navegador** y ir a tu panel de Easypanel
2. **Iniciar sesión** con tus credenciales
3. **Ir a "Projects"** o "Aplicaciones"
4. **Clic en "New Project"**

### Paso 3: Configurar Aplicación

1. **Seleccionar "Docker Compose"**
2. **Conectar repositorio Git**:
   - URL: `https://github.com/tu-usuario/vrx-dashboard-app.git`
   - Rama: `main`
   - Directorio raíz: `/`

### Paso 4: Configurar Variables de Entorno

En la sección "Environment Variables", agregar:

```bash
POSTGRES_PASSWORD=tu_password_seguro_aqui
FRONTEND_URL=https://tu-dominio.easypanel.host
LOG_LEVEL=INFO
CORS_ORIGINS=https://tu-dominio.easypanel.host
```

### Paso 5: Configurar Puertos

- **Puerto**: `8000`
- **Protocolo**: `HTTP`
- **Público**: `Sí`

### Paso 6: Configurar Health Check

- **Path**: `/health`
- **Interval**: `30s`
- **Timeout**: `10s`
- **Retries**: `3`

### Paso 7: Deploy

1. **Clic en "Deploy"**
2. **Esperar** construcción (5-10 minutos)
3. **Verificar logs** para asegurar éxito

## 🌐 Acceso a la Aplicación

Una vez desplegada, estará disponible en:
- **Dashboard**: `https://tu-dominio.easypanel.host`
- **API Docs**: `https://tu-dominio.easypanel.host/docs`
- **Health Check**: `https://tu-dominio.easypanel.host/health`

## 🔧 Configuración de Uso

Para usar la aplicación necesitas:

1. **API Key de Vicarius**: Tu token de autenticación
2. **URL del Dashboard**: URL de tu instancia Vicarius

## 📊 Funcionalidades Disponibles

- ✅ **Dashboard Interactivo** tipo PowerBI
- ✅ **Gráficos Dinámicos** (pie charts, barras, donas)
- ✅ **Tablas Filtrables** de vulnerabilidades y endpoints
- ✅ **Extracción Automática** de datos de Vicarius
- ✅ **API REST** completa
- ✅ **Base de Datos** PostgreSQL persistente

## 🛠️ Solución de Problemas

### Error: "Build failed"
- Verificar que el repositorio esté público
- Revisar logs de build en Easypanel

### Error: "Database connection failed"
- Verificar variable `POSTGRES_PASSWORD`
- Comprobar que PostgreSQL esté ejecutándose

### Error: "Health check failed"
- Verificar que la aplicación esté ejecutándose
- Comprobar logs de la aplicación

## 🔄 Actualizaciones

Para actualizar la aplicación:
1. Hacer cambios en tu código local
2. Commit y push a Git
3. Easypanel reconstruirá automáticamente

## 🎉 ¡Listo!

Tu aplicación estará funcionando en la nube con:
- ✅ Escalabilidad automática
- ✅ Backup automático
- ✅ Monitoreo integrado
- ✅ SSL automático
- ✅ Dominio personalizado

**¡Tu dashboard de seguridad estará disponible 24/7 en la nube!** 🚀
