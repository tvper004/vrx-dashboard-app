-- Script para arreglar el esquema de la base de datos
-- Este script debe ejecutarse en la base de datos PostgreSQL

-- Verificar y agregar columnas faltantes en la tabla endpoints
DO $$ 
BEGIN
    -- Agregar columna status si no existe
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'endpoints' AND column_name = 'status') THEN
        ALTER TABLE endpoints ADD COLUMN status VARCHAR(50);
        RAISE NOTICE 'Columna status agregada a la tabla endpoints';
    END IF;
    
    -- Agregar columna sub_status si no existe
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'endpoints' AND column_name = 'sub_status') THEN
        ALTER TABLE endpoints ADD COLUMN sub_status VARCHAR(50);
        RAISE NOTICE 'Columna sub_status agregada a la tabla endpoints';
    END IF;
END $$;

-- Verificar que las columnas existen
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'endpoints' 
ORDER BY ordinal_position;
