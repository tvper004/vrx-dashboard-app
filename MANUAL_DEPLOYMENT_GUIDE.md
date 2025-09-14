# 🚀 Guía Manual para Levantar vRx Dashboard App en Easypanel

## 📋 Resumen de la Situación

He preparado todos los archivos necesarios en tu servidor `192.168.1.200`. Ahora necesitas ejecutar los comandos manualmente para levantar la aplicación.

## 🔧 Pasos Manuales

### Paso 1: Conectar al Servidor
```bash
ssh rleon@192.168.1.200
```

### Paso 2: Ir al Directorio de la Aplicación
```bash
cd /home/rleon/vrx-dashboard
```

### Paso 3: Verificar Archivos
```bash
ls -la
```
Deberías ver:
- `backend/` - Código del API
- `frontend/` - Código del dashboard
- `database/` - Esquema de base de datos
- `vRx-Report-Unicon/` - Tu código Python
- `Dockerfile` - Imagen Docker
- `docker-compose.yml` - Configuración Docker
- `start-sudo.sh` - Script de inicio

### Paso 4: Configurar Permisos de Docker

**Opción A: Agregar usuario al grupo docker**
```bash
sudo usermod -aG docker rleon
sudo systemctl restart docker
```

**Opción B: Usar sudo para Docker**
```bash
# Verificar que sudo funciona
sudo docker --version
```

### Paso 5: Levantar la Aplicación

**Opción A: Con Docker Compose (si está instalado)**
```bash
# Parar contenedores existentes
docker-compose down 2>/dev/null || true

# Construir y levantar
docker-compose build
docker-compose up -d

# Verificar estado
docker-compose ps
```

**Opción B: Con Docker directamente**
```bash
# Parar contenedores existentes
sudo docker stop vrx-postgres vrx-app 2>/dev/null || true
sudo docker rm vrx-postgres vrx-app 2>/dev/null || true

# Crear red
sudo docker network create vrx-network 2>/dev/null || true

# Iniciar PostgreSQL
sudo docker run -d \
  --name vrx-postgres \
  --network vrx-network \
  -e POSTGRES_DB=vrx_dashboard \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=vrx_password_2024 \
  -v postgres_data:/var/lib/postgresql/data \
  -v $(pwd)/database/schema.sql:/docker-entrypoint-initdb.d/schema.sql \
  -p 5432:5432 \
  postgres:15-alpine

# Esperar 20 segundos
sleep 20

# Construir imagen de la aplicación
sudo docker build -t vrx-dashboard-app .

# Iniciar aplicación
sudo docker run -d \
  --name vrx-app \
  --network vrx-network \
  -e DATABASE_URL=postgresql://postgres:vrx_password_2024@vrx-postgres:5432/vrx_dashboard \
  -e API_HOST=0.0.0.0 \
  -e API_PORT=8000 \
  -e FRONTEND_URL=http://192.168.1.200:8000 \
  -e LOG_LEVEL=INFO \
  -e CORS_ORIGINS=http://192.168.1.200:8000,http://localhost:8000 \
  -v $(pwd)/vRx-Report-Unicon:/app/vRx-Report-Unicon \
  -p 8000:8000 \
  vrx-dashboard-app

# Verificar estado
sudo docker ps
```

### Paso 6: Verificar que Funciona

**Verificar contenedores:**
```bash
sudo docker ps
```

**Verificar logs:**
```bash
sudo docker logs vrx-app
sudo docker logs vrx-postgres
```

**Verificar health check:**
```bash
curl http://localhost:8000/health
```

**Verificar aplicación:**
```bash
curl http://localhost:8000/dashboard/overview
```

## 🌐 Acceso a la Aplicación

Una vez que esté funcionando, puedes acceder a:

- **Dashboard**: http://192.168.1.200:8000
- **API Docs**: http://192.168.1.200:8000/docs
- **Health Check**: http://192.168.1.200:8000/health

## 🔧 Comandos Útiles

### Iniciar Aplicación
```bash
cd /home/rleon/vrx-dashboard
sudo docker-compose up -d
```

### Parar Aplicación
```bash
sudo docker-compose down
# o
sudo docker stop vrx-postgres vrx-app
```

### Ver Logs
```bash
sudo docker logs vrx-app -f
sudo docker logs vrx-postgres -f
```

### Ver Estado
```bash
sudo docker ps
sudo docker-compose ps
```

### Reiniciar Aplicación
```bash
sudo docker-compose restart
```

## 🐛 Solución de Problemas

### Error: "permission denied"
```bash
# Agregar usuario al grupo docker
sudo usermod -aG docker rleon
# Cerrar sesión SSH y volver a conectar
exit
ssh rleon@192.168.1.200
```

### Error: "docker-compose not found"
```bash
# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Error: "port already in use"
```bash
# Ver qué está usando el puerto
sudo netstat -tulpn | grep :8000
# Parar proceso o cambiar puerto
```

### Error: "database connection failed"
```bash
# Verificar que PostgreSQL esté ejecutándose
sudo docker logs vrx-postgres
# Verificar conectividad
sudo docker exec vrx-postgres pg_isready -U postgres
```

## 📊 Monitoreo

### Ver Recursos
```bash
sudo docker stats
```

### Ver Logs en Tiempo Real
```bash
sudo docker logs vrx-app -f
```

### Verificar Health Check
```bash
curl -s http://localhost:8000/health | jq .
```

## 🔄 Actualizaciones

### Actualizar Código
```bash
# Desde tu máquina local
scp -r backend/ rleon@192.168.1.200:/home/rleon/vrx-dashboard/
scp -r frontend/ rleon@192.168.1.200:/home/rleon/vrx-dashboard/

# En el servidor
cd /home/rleon/vrx-dashboard
sudo docker-compose build
sudo docker-compose up -d
```

### Actualizar Base de Datos
```bash
# Ejecutar migraciones si las hay
sudo docker exec vrx-postgres psql -U postgres -d vrx_dashboard -f /docker-entrypoint-initdb.d/schema.sql
```

## 🎉 ¡Listo!

Una vez que ejecutes estos comandos, tu aplicación estará funcionando en:

**http://192.168.1.200:8000**

La aplicación incluye:
- ✅ Dashboard interactivo tipo PowerBI
- ✅ API REST completa
- ✅ Base de datos PostgreSQL
- ✅ Integración con tu código Python existente
- ✅ Health checks y monitoreo

¡Disfruta tu nuevo dashboard de seguridad! 🚀
