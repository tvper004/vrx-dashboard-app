# vRx Dashboard App

Una aplicación web completa para extraer datos de Vicarius vRx y visualizarlos en un dashboard interactivo similar a PowerBI.

## 🚀 Características

- **Extracción Automática**: Integra el script Python existente para extraer datos de la API de Vicarius
- **Dashboard Interactivo**: Visualizaciones dinámicas con gráficos tipo PowerBI
- **Base de Datos**: Almacenamiento persistente en PostgreSQL
- **API REST**: Backend FastAPI para manejar datos y extracciones
- **Frontend Moderno**: Interfaz React con Ant Design
- **Deployment Fácil**: Configurado para Easypanel y Docker

## 📊 Datos Visualizados

- **Endpoints**: Lista completa de assets con información del sistema operativo
- **Vulnerabilidades**: CVE, severidad, productos afectados y puntuaciones CVSS
- **Tareas**: Estado de automatizaciones y patches aplicados
- **Estadísticas**: Resúmenes por severidad, SO, estado de tareas

## 🛠️ Tecnologías

### Backend
- **FastAPI**: Framework web moderno y rápido
- **PostgreSQL**: Base de datos relacional
- **SQLAlchemy**: ORM para Python
- **Pandas**: Procesamiento de datos CSV

### Frontend
- **React 18**: Biblioteca de interfaz de usuario
- **Ant Design**: Componentes UI profesionales
- **Recharts**: Gráficos interactivos
- **Axios**: Cliente HTTP

### Infraestructura
- **Docker**: Containerización
- **Easypanel**: Plataforma de deployment
- **Nginx**: Servidor web y proxy

## 📋 Requisitos Previos

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Docker (opcional)
- API Key de Vicarius vRx

## 🚀 Instalación

### Opción 1: Easypanel (Recomendado)

1. **Subir el proyecto a Easypanel**:
   ```bash
   # Clonar o subir el directorio vRx-Dashboard-App
   ```

2. **Configurar en Easypanel**:
   - Crear nueva aplicación
   - Seleccionar "Custom Application"
   - Subir el código fuente
   - Configurar variables de entorno:
     ```
     DATABASE_URL=postgresql://postgres:password@postgres:5432/vrx_dashboard
     API_HOST=0.0.0.0
     API_PORT=8000
     ```

3. **Configurar Base de Datos**:
   - Crear servicio PostgreSQL
   - Ejecutar el script `database/schema.sql`

### Opción 2: Docker Compose

1. **Clonar el proyecto**:
   ```bash
   git clone <repository-url>
   cd vRx-Dashboard-App
   ```

2. **Ejecutar con Docker Compose**:
   ```bash
   docker-compose up -d
   ```

3. **Acceder a la aplicación**:
   - Frontend: http://localhost:8000
   - API: http://localhost:8000/docs

### Opción 3: Desarrollo Local

1. **Configurar Base de Datos**:
   ```bash
   # Instalar PostgreSQL
   # Crear base de datos
   createdb vrx_dashboard
   
   # Ejecutar esquema
   psql vrx_dashboard < database/schema.sql
   ```

2. **Configurar Backend**:
   ```bash
   cd backend
   pip install -r requirements.txt
   
   # Configurar variables de entorno
   cp env.example .env
   # Editar .env con tus configuraciones
   ```

3. **Configurar Frontend**:
   ```bash
   cd frontend
   npm install
   npm start
   ```

4. **Ejecutar Backend**:
   ```bash
   cd backend
   python main.py
   ```

## 🔧 Configuración

### Variables de Entorno

```bash
# Base de datos
DATABASE_URL=postgresql://postgres:password@localhost:5432/vrx_dashboard

# API
API_HOST=0.0.0.0
API_PORT=8000

# Frontend
FRONTEND_URL=http://localhost:3000

# Logging
LOG_LEVEL=INFO
```

### Configuración de Vicarius

Para extraer datos necesitas:
- **API Key**: Token de autenticación de Vicarius
- **Dashboard URL**: URL de tu instancia (ej: https://tu-instancia.vicarius.cloud)

## 📖 Uso

### 1. Primera Configuración

1. Accede a la aplicación web
2. Haz clic en "Extraer Datos"
3. Ingresa tu API Key y URL del dashboard de Vicarius
4. Haz clic en "Iniciar Extracción"

### 2. Explorar Datos

- **Resumen**: Vista general con estadísticas y gráficos
- **Vulnerabilidades**: Tabla filtrable de vulnerabilidades por severidad
- **Endpoints**: Lista de assets con filtros por sistema operativo
- **Tareas**: Estado de automatizaciones y patches

### 3. Actualizar Datos

- Haz clic en "Extraer Datos" para ejecutar una nueva extracción
- El estado se actualiza automáticamente
- Los datos se almacenan en la base de datos

## 🔄 Extracción de Datos

La aplicación utiliza el script Python existente (`VickyvRxReportCLI.py`) para extraer:

- **Endpoints**: Información de assets y sistemas operativos
- **Vulnerabilidades**: CVE, severidad, productos afectados
- **Patches**: Información de parches disponibles
- **Tareas**: Estado de automatizaciones
- **Grupos**: Agrupaciones de endpoints
- **Productos**: Versiones de software instalado

### Tipos de Extracción

- `--allreports`: Todos los reportes (recomendado)
- `--assetsreport`: Solo endpoints
- `--vulnerabilitiesreport`: Solo vulnerabilidades
- `--patchsreport`: Solo patches
- `--taskreport`: Solo tareas

## 📊 Visualizaciones

### Gráficos Disponibles

1. **Vulnerabilidades por Severidad**: Gráfico de pastel
2. **Endpoints por SO**: Gráfico de barras
3. **Estado de Tareas**: Gráfico de dona
4. **Estadísticas Generales**: Tarjetas con métricas

### Filtros Interactivos

- **Vulnerabilidades**: Por severidad y asset
- **Endpoints**: Por sistema operativo
- **Tareas**: Por estado y asset
- **Búsqueda**: Por nombre/hostname

## 🔧 Mantenimiento

### Logs

Los logs se almacenan en la tabla `extraction_logs`:
- Estado de extracciones
- Registros procesados
- Errores y mensajes

### Base de Datos

- **Limpieza**: Los datos se actualizan en cada extracción
- **Índices**: Optimizados para consultas rápidas
- **Backup**: Configurar respaldos regulares

### Actualizaciones

Para actualizar la aplicación:
1. Detener contenedores
2. Actualizar código
3. Reconstruir imágenes
4. Reiniciar servicios

## 🐛 Solución de Problemas

### Problemas Comunes

1. **Error de conexión a BD**:
   - Verificar DATABASE_URL
   - Comprobar que PostgreSQL esté ejecutándose

2. **Error en extracción**:
   - Verificar API Key de Vicarius
   - Comprobar URL del dashboard
   - Revisar logs en `/extraction-status`

3. **Frontend no carga**:
   - Verificar que el backend esté ejecutándose
   - Comprobar configuración de CORS

### Logs y Debugging

```bash
# Ver logs de la aplicación
docker-compose logs app

# Ver logs de base de datos
docker-compose logs postgres

# Acceder a la base de datos
docker-compose exec postgres psql -U postgres -d vrx_dashboard
```

## 📈 Rendimiento

### Optimizaciones

- **Índices de BD**: Para consultas rápidas
- **Paginación**: Tablas con límites de registros
- **Caché**: Datos estáticos servidos por Nginx
- **Rate Limiting**: Control de velocidad en extracciones

### Escalabilidad

- **Horizontal**: Múltiples instancias de la app
- **Vertical**: Más recursos para BD y app
- **CDN**: Para archivos estáticos

## 🔒 Seguridad

### Consideraciones

- **API Keys**: Almacenadas encriptadas en BD
- **HTTPS**: Usar certificados SSL en producción
- **CORS**: Configurar dominios específicos
- **Validación**: Entrada de datos validada

### Recomendaciones

- Cambiar contraseñas por defecto
- Usar variables de entorno para secretos
- Configurar firewall apropiado
- Mantener dependencias actualizadas

## 📞 Soporte

Para soporte técnico:
- Revisar logs de la aplicación
- Verificar configuración de variables de entorno
- Comprobar conectividad con Vicarius API
- Consultar documentación de Vicarius

## 📄 Licencia

MIT License - Ver archivo LICENSE para detalles.

## 🤝 Contribuciones

Las contribuciones son bienvenidas:
1. Fork el proyecto
2. Crear feature branch
3. Commit cambios
4. Push al branch
5. Crear Pull Request

---

**Desarrollado para facilitar la visualización y análisis de datos de seguridad de Vicarius vRx**
