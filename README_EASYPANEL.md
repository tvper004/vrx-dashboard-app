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
