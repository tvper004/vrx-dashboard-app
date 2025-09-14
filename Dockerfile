# Dockerfile para vRx Dashboard App
FROM node:18-alpine AS frontend-builder

# Construir frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --only=production
COPY frontend/ ./
RUN npm run build

# Imagen final con Python y Node.js
FROM python:3.11-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos de Python existentes
COPY vRx-Report-Unicon/ ./vRx-Report-Unicon/

# Instalar dependencias de Python
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código del backend
COPY backend/ ./

# Copiar frontend construido
COPY --from=frontend-builder /app/frontend/build ./static

# Crear directorio para reports
RUN mkdir -p /app/vRx-Report-Unicon/reports

# Configurar variables de entorno
ENV PYTHONPATH=/app
ENV DATABASE_URL=postgresql://postgres:password@postgres:5432/vrx_dashboard
ENV API_HOST=0.0.0.0
ENV API_PORT=8000

# Exponer puerto
EXPOSE 8000

# Comando de inicio
CMD ["python", "main.py"]
