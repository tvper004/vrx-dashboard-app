# Instrucciones de Deployment en Easypanel

## 🚀 Guía Paso a Paso para Easypanel

### 1. Preparación del Proyecto

1. **Subir código a Git**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: vRx Dashboard App"
   git remote add origin <tu-repositorio-git>
   git push -u origin main
   ```

2. **Verificar estructura**:
   ```
   vRx-Dashboard-App/
   ├── backend/
   ├── frontend/
   ├── database/
   ├── vRx-Report-Unicon/
   ├── Dockerfile
   ├── docker-compose.yml
   ├── easypanel.json
   └── README.md
   ```

### 2. Configuración en Easypanel

#### Paso 1: Crear Nueva Aplicación
1. Accede a tu panel de Easypanel
2. Haz clic en "New Application"
3. Selecciona "Custom Application"

#### Paso 2: Configurar Repositorio
1. Conecta tu repositorio Git
2. Selecciona la rama principal (main/master)
3. Configura el directorio raíz como `/`

#### Paso 3: Configurar Build
- **Build Command**: `npm run build` (para el frontend)
- **Start Command**: `python backend/main.py`
- **Dockerfile**: Usar el Dockerfile incluido

#### Paso 4: Configurar Variables de Entorno
```
DATABASE_URL=postgresql://postgres:password@postgres:5432/vrx_dashboard
API_HOST=0.0.0.0
API_PORT=8000
FRONTEND_URL=https://tu-dominio.com
LOG_LEVEL=INFO
```

#### Paso 5: Configurar Base de Datos
1. Crear servicio PostgreSQL
2. Configurar variables:
   ```
   POSTGRES_DB=vrx_dashboard
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=password
   ```
3. Ejecutar script de inicialización:
   ```sql
   -- Ejecutar el contenido de database/schema.sql
   ```

#### Paso 6: Configurar Volúmenes
- **Nombre**: `reports`
- **Ruta**: `/app/vRx-Report-Unicon/reports`
- **Tipo**: Persistent Volume

#### Paso 7: Configurar Puertos
- **Puerto**: `8000`
- **Protocolo**: `HTTP`
- **Público**: Sí (si quieres acceso externo)

#### Paso 8: Configurar Health Check
- **Path**: `/health`
- **Interval**: `30s`
- **Timeout**: `10s`
- **Retries**: `3`

### 3. Configuración Avanzada

#### Variables de Entorno Adicionales
```bash
# Para producción
CORS_ORIGINS=https://tu-dominio.com,https://www.tu-dominio.com
LOG_LEVEL=WARNING
EXTRACTION_TIMEOUT=7200
MAX_CONCURRENT_EXTRACTIONS=2

# Para desarrollo
FRONTEND_URL=http://localhost:3000
LOG_LEVEL=DEBUG
```

#### Configuración de Recursos
- **CPU**: Mínimo 1 vCPU, recomendado 2 vCPU
- **RAM**: Mínimo 2GB, recomendado 4GB
- **Almacenamiento**: Mínimo 10GB para logs y datos

### 4. Verificación Post-Deployment

#### Verificar Aplicación
1. Accede a la URL de tu aplicación
2. Verifica que el dashboard cargue correctamente
3. Prueba la funcionalidad de extracción de datos

#### Verificar Base de Datos
```sql
-- Conectar a la base de datos
psql -h <host> -U postgres -d vrx_dashboard

-- Verificar tablas
\dt

-- Verificar datos
SELECT COUNT(*) FROM endpoints;
SELECT COUNT(*) FROM vulnerabilities;
```

#### Verificar Logs
1. Accede a los logs de la aplicación en Easypanel
2. Busca errores o advertencias
3. Verifica que las extracciones funcionen correctamente

### 5. Configuración de Dominio Personalizado

#### Configurar DNS
1. Crea un registro CNAME apuntando a tu aplicación Easypanel
2. Ejemplo: `dashboard.tu-dominio.com` → `tu-app.easypanel.com`

#### Configurar SSL
1. Easypanel maneja automáticamente los certificados SSL
2. Verifica que HTTPS esté habilitado

### 6. Monitoreo y Mantenimiento

#### Configurar Alertas
1. Configura alertas para:
   - Uso de CPU > 80%
   - Uso de RAM > 90%
   - Errores de aplicación
   - Fallos de health check

#### Backup de Base de Datos
1. Configura backups automáticos
2. Frecuencia recomendada: Diaria
3. Retención: 30 días

#### Actualizaciones
1. Para actualizar la aplicación:
   - Haz push de cambios a Git
   - Easypanel reconstruirá automáticamente
2. Para actualizar dependencias:
   - Actualiza requirements.txt
   - Haz commit y push

### 7. Solución de Problemas Comunes

#### Error: "Database connection failed"
- Verificar que PostgreSQL esté ejecutándose
- Verificar DATABASE_URL
- Verificar que el esquema se haya ejecutado

#### Error: "API Key invalid"
- Verificar que la API Key de Vicarius sea válida
- Verificar que la URL del dashboard sea correcta
- Verificar conectividad de red

#### Error: "Frontend not loading"
- Verificar que el build del frontend sea exitoso
- Verificar configuración de CORS
- Verificar que el backend esté ejecutándose

#### Error: "Extraction timeout"
- Aumentar EXTRACTION_TIMEOUT
- Verificar recursos disponibles (CPU/RAM)
- Verificar conectividad con API de Vicarius

### 8. Optimización de Rendimiento

#### Configuración de Recursos
- **CPU**: 2-4 vCPU para mejor rendimiento
- **RAM**: 4-8GB para datasets grandes
- **Almacenamiento**: SSD para mejor I/O

#### Configuración de Base de Datos
- Configurar índices adicionales si es necesario
- Configurar conexiones pool
- Monitorear queries lentas

#### Configuración de Caché
- Implementar caché Redis si es necesario
- Configurar TTL apropiado
- Monitorear hit rate

### 9. Seguridad

#### Configuración de Variables
- Nunca hardcodear API keys en el código
- Usar variables de entorno para secretos
- Rotar API keys regularmente

#### Configuración de CORS
- Limitar orígenes permitidos en producción
- No usar "*" en producción
- Configurar headers apropiados

#### Configuración de HTTPS
- Forzar HTTPS en producción
- Configurar HSTS headers
- Usar certificados válidos

### 10. Escalabilidad

#### Escalado Horizontal
- Configurar múltiples instancias
- Usar load balancer
- Configurar session affinity

#### Escalado Vertical
- Aumentar recursos según necesidad
- Monitorear métricas de uso
- Planificar capacidad

---

## 📞 Soporte

Si encuentras problemas durante el deployment:

1. **Revisar logs**: Siempre revisa los logs primero
2. **Verificar configuración**: Asegúrate de que todas las variables estén configuradas
3. **Probar localmente**: Usa Docker Compose para probar localmente
4. **Contactar soporte**: Si el problema persiste, contacta al soporte de Easypanel

## 🔗 Enlaces Útiles

- [Documentación de Easypanel](https://easypanel.io/docs)
- [Documentación de FastAPI](https://fastapi.tiangolo.com/)
- [Documentación de React](https://reactjs.org/docs)
- [Documentación de PostgreSQL](https://www.postgresql.org/docs/)
