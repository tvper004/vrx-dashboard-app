# 🐳 Configuración para Easypanel - vRx Dashboard App

## 🚀 **RECOMENDACIÓN: Usar Dockerfile**

Para tu aplicación, **recomiendo usar Dockerfile** porque:

1. ✅ **Tienes una aplicación compleja** (Python + React + PostgreSQL)
2. ✅ **Necesitas control total** sobre el proceso de build
3. ✅ **Ya tienes el Dockerfile optimizado**
4. ✅ **Mejor rendimiento** en Easypanel

## 📋 **Archivos que Easypanel Considerará:**

### **Archivos Principales:**
- ✅ `Dockerfile` - **Archivo principal** (ya lo tienes)
- ✅ `Dockerfile.easypanel` - **Optimizado para Easypanel** (ya lo tienes)
- ✅ `docker-compose.yml` - Para desarrollo local
- ✅ `easypanel-docker-compose.yml` - **Para Easypanel** (ya lo tienes)

### **Archivos de Configuración:**
- ✅ `easypanel-config.yaml` - **Configuración específica** (ya lo tienes)
- ✅ `easypanel-env-example.txt` - **Variables de entorno** (ya lo tienes)

## 🔧 **Configuración en Easypanel**

### **Opción 1: Dockerfile (RECOMENDADA)**

1. **En Easypanel**:
   - **Tipo**: `Docker`
   - **Dockerfile**: `Dockerfile.easypanel` (usa el optimizado)
   - **Puerto**: `8000`
   - **Protocolo**: `HTTP`

2. **Variables de entorno**:
```bash
POSTGRES_PASSWORD=K67lkk7580*
FRONTEND_URL=https://tu-dominio.easypanel.host
LOG_LEVEL=INFO
CORS_ORIGINS=https://tu-dominio.easypanel.host
```

3. **Health Check**:
   - **Path**: `/health`
   - **Interval**: `30s`
   - **Timeout**: `10s`
   - **Retries**: `3`

### **Opción 2: Docker Compose (ALTERNATIVA)**

1. **En Easypanel**:
   - **Tipo**: `Docker Compose`
   - **Archivo**: `easypanel-docker-compose.yml`
   - **Puerto**: `8000`

## 🚀 **Pasos para Configurar en Easypanel**

### **Paso 1: Crear Nueva Aplicación**
1. **Ir a tu panel de Easypanel**
2. **Clic en "New Project"**
3. **Seleccionar "Docker"** (recomendado)

### **Paso 2: Conectar Repositorio**
1. **Conectar repositorio Git**:
   - URL: `https://github.com/tu-usuario/vrx-dashboard-app.git`
   - Rama: `main`
   - Directorio raíz: `/`

### **Paso 3: Configurar Build**
1. **Dockerfile**: `Dockerfile.easypanel`
2. **Context**: `/` (raíz del proyecto)
3. **Build Args**: (dejar vacío)

### **Paso 4: Configurar Variables de Entorno**
```bash
POSTGRES_PASSWORD=K67lkk7580*
FRONTEND_URL=https://tu-dominio.easypanel.host
LOG_LEVEL=INFO
CORS_ORIGINS=https://tu-dominio.easypanel.host
```

### **Paso 5: Configurar Puertos**
- **Puerto**: `8000`
- **Protocolo**: `HTTP`
- **Público**: `Sí`

### **Paso 6: Configurar Health Check**
- **Path**: `/health`
- **Interval**: `30s`
- **Timeout**: `10s`
- **Retries**: `3`

### **Paso 7: Deploy**
1. **Clic en "Deploy"**
2. **Esperar** construcción (5-10 minutos)
3. **Verificar logs** para asegurar éxito

## 🌐 **Acceso a la Aplicación**

Una vez desplegada, estará disponible en:
- **Dashboard**: `https://tu-dominio.easypanel.host`
- **API Docs**: `https://tu-dominio.easypanel.host/docs`
- **Health Check**: `https://tu-dominio.easypanel.host/health`

## 🔧 **Configuración de Uso**

Para usar la aplicación necesitas:
1. **API Key de Vicarius**: Tu token de autenticación
2. **URL del Dashboard**: URL de tu instancia Vicarius

## 📊 **Funcionalidades Disponibles**

- ✅ **Dashboard Interactivo** tipo PowerBI
- ✅ **Gráficos Dinámicos** (pie charts, barras, donas)
- ✅ **Tablas Filtrables** de vulnerabilidades y endpoints
- ✅ **Extracción Automática** de datos de Vicarius
- ✅ **API REST** completa
- ✅ **Base de Datos** PostgreSQL persistente

## 🛠️ **Solución de Problemas**

### Error: "Build failed"
- Verificar que el repositorio esté público
- Revisar logs de build en Easypanel
- Comprobar que `Dockerfile.easypanel` esté en la raíz

### Error: "Database connection failed"
- Verificar variable `POSTGRES_PASSWORD`
- Comprobar que PostgreSQL esté ejecutándose

### Error: "Health check failed"
- Verificar que la aplicación esté ejecutándose
- Comprobar logs de la aplicación

## 🎉 **¡Listo para Usar!**

Tu aplicación estará funcionando en la nube con:
- ✅ Escalabilidad automática
- ✅ Backup automático
- ✅ Monitoreo integrado
- ✅ SSL automático
- ✅ Dominio personalizado

---

## 🚀 **RESUMEN FINAL**

**Para Easypanel, usa:**

1. **Tipo**: `Docker`
2. **Dockerfile**: `Dockerfile.easypanel`
3. **Puerto**: `8000`
4. **Variables de entorno**: Las que tienes en `easypanel-env-example.txt`
5. **Health Check**: `/health`

**¡Tu dashboard de seguridad estará funcionando en la nube!** 🎉
