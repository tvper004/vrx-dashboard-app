# 🎉 vRx Dashboard App - Lista para Usar con su root

## ✅ Resumen de lo Preparado

He preparado completamente tu aplicación para usar con `su root@192.168.1.200` en tu servidor Easypanel. Todo está listo para funcionar.

## 📋 Archivos Creados en el Servidor

En `/home/rleon/vrx-dashboard/` tienes:

- ✅ **`start-with-su.sh`** - Script de inicio que usa `su root`
- ✅ **`vrx-commands-su.sh`** - Comandos útiles para gestionar la app
- ✅ **`GUIA_USO_SU_ROOT.md`** - Guía completa de uso
- ✅ **`backend/`** - Código del API FastAPI
- ✅ **`frontend/`** - Código del dashboard React
- ✅ **`database/`** - Esquema de PostgreSQL
- ✅ **`vRx-Report-Unicon/`** - Tu código Python
- ✅ **`Dockerfile`** - Imagen Docker
- ✅ **`docker-compose.yml`** - Configuración Docker

## 🚀 Cómo Iniciar la Aplicación

### Opción 1: Desde tu Máquina Local
```bash
# Usar el script local
./vrx-local.sh start
```

### Opción 2: Conectando al Servidor
```bash
# Conectar al servidor
ssh rleon@192.168.1.200

# Ir al directorio
cd /home/rleon/vrx-dashboard

# Iniciar la aplicación
./vrx-commands-su.sh start
```

## 🔧 Comandos Disponibles

### Desde tu Máquina Local
```bash
./vrx-local.sh connect    # Conectar al servidor
./vrx-local.sh start      # Iniciar aplicación
./vrx-local.sh stop       # Parar aplicación
./vrx-local.sh status     # Ver estado
./vrx-local.sh logs       # Ver logs
./vrx-local.sh health     # Verificar health check
./vrx-local.sh update     # Actualizar aplicación
```

### Desde el Servidor
```bash
./vrx-commands-su.sh start      # Iniciar aplicación
./vrx-commands-su.sh stop       # Parar aplicación
./vrx-commands-su.sh status     # Ver estado
./vrx-commands-su.sh logs       # Ver logs
./vrx-commands-su.sh health     # Verificar health check
./vrx-commands-su.sh shell      # Acceder al contenedor
```

## 🌐 Acceso a la Aplicación

Una vez iniciada, la aplicación estará disponible en:

- **Dashboard**: http://192.168.1.200:8000
- **API Docs**: http://192.168.1.200:8000/docs
- **Health Check**: http://192.168.1.200:8000/health

## 🔑 Configuración de Credenciales

Para usar la aplicación necesitarás:

1. **API Key de Vicarius**: Tu token de autenticación
2. **URL del Dashboard**: URL de tu instancia (ej: https://tu-instancia.vicarius.cloud)

## 📊 Funcionalidades de la Aplicación

### Dashboard Interactivo
- ✅ Resumen general con estadísticas
- ✅ Gráficos tipo PowerBI (pie charts, barras, donas)
- ✅ Tablas filtrables de vulnerabilidades
- ✅ Lista de endpoints con filtros por SO
- ✅ Estado de tareas y automatizaciones

### Extracción de Datos
- ✅ Integra tu código Python existente
- ✅ Extracción automática con `--allreports`
- ✅ Procesamiento de archivos CSV
- ✅ Carga automática en base de datos

### API REST
- ✅ Endpoints para dashboard
- ✅ Extracción de datos en segundo plano
- ✅ Health checks
- ✅ Logs de monitoreo

## 🛠️ Solución de Problemas

### Error: "permission denied"
```bash
# Asegúrate de usar su root
su root@192.168.1.200
# Ingresa la contraseña cuando se solicite
```

### Error: "port already in use"
```bash
# Parar contenedores existentes
./vrx-commands-su.sh stop
```

### Error: "container not found"
```bash
# Ver todos los contenedores
su root@192.168.1.200
docker ps -a
```

### Error: "database connection failed"
```bash
# Verificar logs de PostgreSQL
su root@192.168.1.200
docker logs vrx-postgres
```

## 🔄 Actualizaciones

### Actualizar Código
```bash
# Desde tu máquina local
./vrx-local.sh update
```

### Actualizar Manualmente
```bash
# Copiar archivos
scp -r backend/ rleon@192.168.1.200:/home/rleon/vrx-dashboard/
scp -r frontend/ rleon@192.168.1.200:/home/rleon/vrx-dashboard/

# Reiniciar aplicación
ssh rleon@192.168.1.200 "cd /home/rleon/vrx-dashboard && ./vrx-commands-su.sh restart"
```

## 📈 Monitoreo

### Ver Recursos
```bash
su root@192.168.1.200
docker stats
```

### Ver Logs en Tiempo Real
```bash
./vrx-local.sh logs
```

### Verificar Health Check
```bash
curl http://192.168.1.200:8000/health
```

## 🎯 Próximos Pasos

1. **Iniciar la aplicación**:
   ```bash
   ./vrx-local.sh start
   ```

2. **Verificar que funciona**:
   ```bash
   ./vrx-local.sh health
   ```

3. **Acceder al dashboard**:
   Abrir http://192.168.1.200:8000 en tu navegador

4. **Configurar extracción**:
   - Hacer clic en "Extraer Datos"
   - Ingresar tu API Key de Vicarius
   - Ingresar URL del dashboard
   - Iniciar extracción

5. **Explorar datos**:
   - Ver resumen general
   - Filtrar vulnerabilidades por severidad
   - Explorar endpoints por sistema operativo
   - Revisar estado de tareas

## 🎉 ¡Listo para Usar!

Tu aplicación está completamente preparada y lista para funcionar. Solo necesitas:

1. Ejecutar `./vrx-local.sh start`
2. Acceder a http://192.168.1.200:8000
3. Configurar tus credenciales de Vicarius
4. ¡Disfrutar tu nuevo dashboard de seguridad!

**¡Tu dashboard tipo PowerBI para datos de Vicarius está listo!** 🚀
