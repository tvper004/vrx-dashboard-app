-- Esquema de base de datos para vRx Dashboard App
-- Base de datos PostgreSQL para almacenar datos de Vicarius

-- Tabla de endpoints/assets
CREATE TABLE IF NOT EXISTS endpoints (
    id SERIAL PRIMARY KEY,
    endpoint_id BIGINT UNIQUE NOT NULL,
    hostname VARCHAR(255) NOT NULL,
    hash VARCHAR(255),
    operating_system VARCHAR(255),
    version VARCHAR(100),
    endpoint_updated_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de grupos de endpoints
CREATE TABLE IF NOT EXISTS endpoint_groups (
    id SERIAL PRIMARY KEY,
    group_name VARCHAR(255) NOT NULL,
    assets TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de vulnerabilidades
CREATE TABLE IF NOT EXISTS vulnerabilities (
    id SERIAL PRIMARY KEY,
    asset VARCHAR(255),
    asset_hash VARCHAR(255),
    group_name VARCHAR(255),
    product_name VARCHAR(255),
    product_raw_entry_name VARCHAR(500),
    sensitivity_level_name VARCHAR(100),
    cve VARCHAR(50),
    vulnerability_id BIGINT,
    patch_id VARCHAR(100),
    patch_name VARCHAR(500),
    patch_release_date TIMESTAMP,
    create_at TIMESTAMP,
    update_at TIMESTAMP,
    link TEXT,
    vulnerability_summary TEXT,
    v3_base_score DECIMAL(5,2),
    v3_exploitability_level DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de patches por endpoint
CREATE TABLE IF NOT EXISTS endpoint_patches (
    id SERIAL PRIMARY KEY,
    asset VARCHAR(255),
    operating_system VARCHAR(255),
    patch_name VARCHAR(500),
    severity_level VARCHAR(100),
    severity_name VARCHAR(100),
    description TEXT,
    patch_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de conteo de patches por endpoint
CREATE TABLE IF NOT EXISTS endpoint_patch_counts (
    id SERIAL PRIMARY KEY,
    asset VARCHAR(255),
    total_patches INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de eventos de tareas
CREATE TABLE IF NOT EXISTS endpoint_event_tasks (
    id SERIAL PRIMARY KEY,
    task_id BIGINT UNIQUE NOT NULL,
    automation_id BIGINT,
    automation_name VARCHAR(255),
    asset VARCHAR(255),
    task_type VARCHAR(255),
    publisher_name VARCHAR(255),
    path_or_product VARCHAR(500),
    path_or_product_desc TEXT,
    action_status VARCHAR(100),
    message_status TEXT,
    username VARCHAR(255),
    create_at TIMESTAMP,
    update_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de productos y versiones
CREATE TABLE IF NOT EXISTS endpoint_products (
    id SERIAL PRIMARY KEY,
    asset VARCHAR(255),
    product_name VARCHAR(255),
    product_raw_entry_name VARCHAR(500),
    product_version VARCHAR(100),
    publisher_name VARCHAR(255),
    operating_system_family_name VARCHAR(255),
    endpoint_id BIGINT,
    product_id BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de incidentes de vulnerabilidades
CREATE TABLE IF NOT EXISTS incident_vulnerabilities (
    id SERIAL PRIMARY KEY,
    asset_id BIGINT,
    asset VARCHAR(255),
    cve VARCHAR(50),
    severity VARCHAR(100),
    event_type VARCHAR(100),
    publisher VARCHAR(255),
    app_or_so VARCHAR(255),
    threat_level_id INTEGER,
    vul_v3_exploit_level DECIMAL(5,2),
    vul_v3_base_score DECIMAL(5,2),
    patch_id VARCHAR(100),
    vul_summary TEXT,
    event_created_at TIMESTAMP,
    event_updated_at TIMESTAMP,
    mitigated_event_detection_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de tiempo de mitigación
CREATE TABLE IF NOT EXISTS mitigation_time (
    id SERIAL PRIMARY KEY,
    asset VARCHAR(255),
    cve VARCHAR(50),
    detection_date TIMESTAMP,
    mitigation_date TIMESTAMP,
    mitigation_time_hours DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de configuración de extracción
CREATE TABLE IF NOT EXISTS extraction_config (
    id SERIAL PRIMARY KEY,
    api_key VARCHAR(500),
    dashboard_url VARCHAR(500),
    last_endpoints BIGINT DEFAULT 0,
    last_endpoints_event_task BIGINT DEFAULT 0,
    min_date_incident_event_vulnerabilities BIGINT DEFAULT 0,
    last_product_versions BIGINT DEFAULT 0,
    last_patchs_endpoint BIGINT DEFAULT 0,
    last_incident_event_vulnerabilities BIGINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de logs de extracción
CREATE TABLE IF NOT EXISTS extraction_logs (
    id SERIAL PRIMARY KEY,
    extraction_type VARCHAR(100),
    status VARCHAR(50),
    records_processed INTEGER,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para mejorar el rendimiento
CREATE INDEX IF NOT EXISTS idx_endpoints_hostname ON endpoints(hostname);
CREATE INDEX IF NOT EXISTS idx_endpoints_os ON endpoints(operating_system);
CREATE INDEX IF NOT EXISTS idx_vulnerabilities_cve ON vulnerabilities(cve);
CREATE INDEX IF NOT EXISTS idx_vulnerabilities_asset ON vulnerabilities(asset);
CREATE INDEX IF NOT EXISTS idx_vulnerabilities_severity ON vulnerabilities(sensitivity_level_name);
CREATE INDEX IF NOT EXISTS idx_patches_asset ON endpoint_patches(asset);
CREATE INDEX IF NOT EXISTS idx_event_tasks_asset ON endpoint_event_tasks(asset);
CREATE INDEX IF NOT EXISTS idx_event_tasks_status ON endpoint_event_tasks(action_status);
CREATE INDEX IF NOT EXISTS idx_incident_vuln_asset ON incident_vulnerabilities(asset);
CREATE INDEX IF NOT EXISTS idx_incident_vuln_cve ON incident_vulnerabilities(cve);

-- Función para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers para actualizar updated_at
CREATE TRIGGER update_endpoints_updated_at BEFORE UPDATE ON endpoints FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_endpoint_groups_updated_at BEFORE UPDATE ON endpoint_groups FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_vulnerabilities_updated_at BEFORE UPDATE ON vulnerabilities FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_endpoint_patches_updated_at BEFORE UPDATE ON endpoint_patches FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_endpoint_patch_counts_updated_at BEFORE UPDATE ON endpoint_patch_counts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_endpoint_event_tasks_updated_at BEFORE UPDATE ON endpoint_event_tasks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_endpoint_products_updated_at BEFORE UPDATE ON endpoint_products FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_incident_vulnerabilities_updated_at BEFORE UPDATE ON incident_vulnerabilities FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_mitigation_time_updated_at BEFORE UPDATE ON mitigation_time FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_extraction_config_updated_at BEFORE UPDATE ON extraction_config FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
