# 🚀 Guía de Uso con su root

## 📋 Comandos Disponibles

### Conectar al Servidor
```bash
ssh rleon@192.168.1.200
```

### Ir al Directorio de la Aplicación
```bash
cd /home/rleon/vrx-dashboard
```

### Comandos Rápidos
```bash
# Iniciar aplicación
./vrx-commands-su.sh start

# Ver estado
./vrx-commands-su.sh status

# Ver logs
./vrx-commands-su.sh logs

# Parar aplicación
./vrx-commands-su.sh stop

# Verificar health check
./vrx-commands-su.sh health
```

### Comandos Manuales con su root

#### Iniciar Aplicación
```bash
su root@192.168.1.200
# Ingresa la contraseña cuando se solicite
docker network create vrx-network 2>/dev/null || true
docker run -d --name vrx-postgres --network vrx-network -e POSTGRES_DB=vrx_dashboard -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=vrx_password_2024 -v postgres_data:/var/lib/postgresql/data -v $(pwd)/database/schema.sql:/docker-entrypoint-initdb.d/schema.sql -p 5432:5432 postgres:15-alpine
sleep 20
docker build -t vrx-dashboard-app .
docker run -d --name vrx-app --network vrx-network -e DATABASE_URL=postgresql://postgres:vrx_password_2024@vrx-postgres:5432/vrx_dashboard -e API_HOST=0.0.0.0 -e API_PORT=8000 -e FRONTEND_URL=http://192.168.1.200:8000 -e LOG_LEVEL=INFO -e CORS_ORIGINS=http://192.168.1.200:8000,http://localhost:8000 -v $(pwd)/vRx-Report-Unicon:/app/vRx-Report-Unicon -p 8000:8000 vrx-dashboard-app
```

#### Ver Estado
```bash
su root@192.168.1.200
docker ps
```

#### Ver Logs
```bash
su root@192.168.1.200
docker logs vrx-app -f
```

#### Parar Aplicación
```bash
su root@192.168.1.200
docker stop vrx-postgres vrx-app
docker rm vrx-postgres vrx-app
```

## 🌐 Acceso a la Aplicación

Una vez iniciada, la aplicación estará disponible en:
- **Dashboard**: http://192.168.1.200:8000
- **API Docs**: http://192.168.1.200:8000/docs
- **Health Check**: http://192.168.1.200:8000/health

## 🔧 Solución de Problemas

### Error: "permission denied"
Asegúrate de usar `su root@192.168.1.200` antes de ejecutar comandos Docker.

### Error: "port already in use"
```bash
su root@192.168.1.200
docker stop vrx-postgres vrx-app
```

### Error: "container not found"
```bash
su root@192.168.1.200
docker ps -a
```

## 📊 Monitoreo

### Ver Recursos
```bash
su root@192.168.1.200
docker stats
```

### Ver Logs en Tiempo Real
```bash
su root@192.168.1.200
docker logs vrx-app -f
```

### Verificar Health Check
```bash
curl http://192.168.1.200:8000/health
```

## 🎉 ¡Listo!

Tu aplicación estará funcionando en **http://192.168.1.200:8000**
