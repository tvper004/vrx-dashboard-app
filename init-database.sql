-- Script de inicialización para Easypanel
-- Este script se ejecuta automáticamente al crear la base de datos

-- Crear base de datos si no existe
SELECT 'CREATE DATABASE vrx_dashboard'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'vrx_dashboard')\gexec

-- Conectar a la base de datos
\c vrx_dashboard;

-- Ejecutar el esquema principal
\i /docker-entrypoint-initdb.d/schema.sql

-- Verificar que las tablas se crearon correctamente
\dt

-- Mostrar mensaje de éxito
SELECT 'Base de datos vrx_dashboard inicializada correctamente' as status;
