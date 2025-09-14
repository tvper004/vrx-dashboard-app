# vRx Dashboard App - Backend API
# FastAPI application for Vicarius data extraction and dashboard

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
import pandas as pd
import os
import subprocess
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import asyncio
from contextlib import asynccontextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
import json

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/vrx_dashboard")

# Crear engine de SQLAlchemy
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Configuración de la aplicación FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting vRx Dashboard API...")
    # Verificar conexión a base de datos
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down vRx Dashboard API...")

app = FastAPI(
    title="vRx Dashboard API",
    description="API para extracción de datos de Vicarius y dashboard interactivo",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency para obtener sesión de base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Modelos de datos (simplificados para la API)
class ExtractionConfig:
    def __init__(self, api_key: str, dashboard_url: str):
        self.api_key = api_key
        self.dashboard_url = dashboard_url

class ExtractionRequest:
    def __init__(self, api_key: str, dashboard_url: str, extraction_type: str = "all"):
        self.api_key = api_key
        self.dashboard_url = dashboard_url
        self.extraction_type = extraction_type

# Rutas de la API

@app.get("/")
async def root():
    return {"message": "vRx Dashboard API", "version": "1.0.0", "status": "running"}

@app.get("/health")
async def health_check():
    """Verificar estado de la aplicación y base de datos"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.post("/extract-data")
async def extract_data(request: ExtractionRequest, background_tasks: BackgroundTasks):
    """Iniciar extracción de datos en segundo plano"""
    try:
        # Validar parámetros
        if not request.api_key or not request.dashboard_url:
            raise HTTPException(status_code=400, detail="API key y dashboard URL son requeridos")
        
        # Guardar configuración en base de datos
        config_data = {
            "api_key": request.api_key,
            "dashboard_url": request.dashboard_url,
            "updated_at": datetime.now()
        }
        
        with engine.connect() as conn:
            # Insertar o actualizar configuración
            conn.execute(text("""
                INSERT INTO extraction_config (api_key, dashboard_url, updated_at)
                VALUES (:api_key, :dashboard_url, :updated_at)
                ON CONFLICT (id) DO UPDATE SET
                    api_key = EXCLUDED.api_key,
                    dashboard_url = EXCLUDED.dashboard_url,
                    updated_at = EXCLUDED.updated_at
            """), config_data)
            conn.commit()
        
        # Iniciar extracción en segundo plano
        background_tasks.add_task(run_data_extraction, request.api_key, request.dashboard_url, request.extraction_type)
        
        return {
            "message": "Extracción de datos iniciada",
            "extraction_type": request.extraction_type,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error starting data extraction: {e}")
        raise HTTPException(status_code=500, detail=f"Error iniciando extracción: {str(e)}")

@app.get("/extraction-status")
async def get_extraction_status():
    """Obtener estado de la última extracción"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT * FROM extraction_logs 
                ORDER BY created_at DESC 
                LIMIT 1
            """)).fetchone()
            
            if result:
                return {
                    "status": result.status,
                    "extraction_type": result.extraction_type,
                    "records_processed": result.records_processed,
                    "started_at": result.started_at.isoformat() if result.started_at else None,
                    "completed_at": result.completed_at.isoformat() if result.completed_at else None,
                    "error_message": result.error_message
                }
            else:
                return {"status": "no_extractions_found"}
                
    except Exception as e:
        logger.error(f"Error getting extraction status: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo estado: {str(e)}")

@app.get("/dashboard/overview")
async def get_dashboard_overview():
    """Obtener datos resumidos para el dashboard"""
    try:
        with engine.connect() as conn:
            # Estadísticas generales
            stats = {}
            
            # Total de endpoints
            result = conn.execute(text("SELECT COUNT(*) as count FROM endpoints")).fetchone()
            stats["total_endpoints"] = result.count if result else 0
            
            # Total de vulnerabilidades
            result = conn.execute(text("SELECT COUNT(*) as count FROM vulnerabilities")).fetchone()
            stats["total_vulnerabilities"] = result.count if result else 0
            
            # Vulnerabilidades por severidad
            result = conn.execute(text("""
                SELECT sensitivity_level_name, COUNT(*) as count 
                FROM vulnerabilities 
                GROUP BY sensitivity_level_name
            """)).fetchall()
            stats["vulnerabilities_by_severity"] = {row.sensitivity_level_name: row.count for row in result}
            
            # Endpoints por sistema operativo
            result = conn.execute(text("""
                SELECT operating_system, COUNT(*) as count 
                FROM endpoints 
                GROUP BY operating_system
            """)).fetchall()
            stats["endpoints_by_os"] = {row.operating_system: row.count for row in result}
            
            # Tareas por estado
            result = conn.execute(text("""
                SELECT action_status, COUNT(*) as count 
                FROM endpoint_event_tasks 
                GROUP BY action_status
            """)).fetchall()
            stats["tasks_by_status"] = {row.action_status: row.count for row in result}
            
            # Última actualización
            result = conn.execute(text("""
                SELECT MAX(updated_at) as last_update 
                FROM endpoints
            """)).fetchone()
            stats["last_update"] = result.last_update.isoformat() if result and result.last_update else None
            
            return stats
            
    except Exception as e:
        logger.error(f"Error getting dashboard overview: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo datos: {str(e)}")

@app.get("/dashboard/vulnerabilities")
async def get_vulnerabilities_data(
    limit: int = 100,
    offset: int = 0,
    severity: Optional[str] = None,
    asset: Optional[str] = None
):
    """Obtener datos de vulnerabilidades con filtros"""
    try:
        with engine.connect() as conn:
            query = "SELECT * FROM vulnerabilities WHERE 1=1"
            params = {}
            
            if severity:
                query += " AND sensitivity_level_name = :severity"
                params["severity"] = severity
                
            if asset:
                query += " AND asset ILIKE :asset"
                params["asset"] = f"%{asset}%"
            
            query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
            params["limit"] = limit
            params["offset"] = offset
            
            result = conn.execute(text(query), params).fetchall()
            
            vulnerabilities = []
            for row in result:
                vulnerabilities.append({
                    "id": row.id,
                    "asset": row.asset,
                    "cve": row.cve,
                    "severity": row.sensitivity_level_name,
                    "product_name": row.product_name,
                    "v3_base_score": float(row.v3_base_score) if row.v3_base_score else None,
                    "vulnerability_summary": row.vulnerability_summary,
                    "created_at": row.created_at.isoformat()
                })
            
            return {"vulnerabilities": vulnerabilities, "total": len(vulnerabilities)}
            
    except Exception as e:
        logger.error(f"Error getting vulnerabilities data: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo vulnerabilidades: {str(e)}")

@app.get("/dashboard/endpoints")
async def get_endpoints_data(
    limit: int = 100,
    offset: int = 0,
    os_filter: Optional[str] = None
):
    """Obtener datos de endpoints con filtros"""
    try:
        with engine.connect() as conn:
            query = "SELECT * FROM endpoints WHERE 1=1"
            params = {}
            
            if os_filter:
                query += " AND operating_system ILIKE :os_filter"
                params["os_filter"] = f"%{os_filter}%"
            
            query += " ORDER BY endpoint_updated_at DESC LIMIT :limit OFFSET :offset"
            params["limit"] = limit
            params["offset"] = offset
            
            result = conn.execute(text(query), params).fetchall()
            
            endpoints = []
            for row in result:
                endpoints.append({
                    "id": row.id,
                    "endpoint_id": row.endpoint_id,
                    "hostname": row.hostname,
                    "operating_system": row.operating_system,
                    "version": row.version,
                    "endpoint_updated_at": row.endpoint_updated_at.isoformat() if row.endpoint_updated_at else None,
                    "created_at": row.created_at.isoformat()
                })
            
            return {"endpoints": endpoints, "total": len(endpoints)}
            
    except Exception as e:
        logger.error(f"Error getting endpoints data: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo endpoints: {str(e)}")

@app.get("/dashboard/tasks")
async def get_tasks_data(
    limit: int = 100,
    offset: int = 0,
    status_filter: Optional[str] = None,
    asset_filter: Optional[str] = None
):
    """Obtener datos de tareas con filtros"""
    try:
        with engine.connect() as conn:
            query = "SELECT * FROM endpoint_event_tasks WHERE 1=1"
            params = {}
            
            if status_filter:
                query += " AND action_status = :status_filter"
                params["status_filter"] = status_filter
                
            if asset_filter:
                query += " AND asset ILIKE :asset_filter"
                params["asset_filter"] = f"%{asset_filter}%"
            
            query += " ORDER BY create_at DESC LIMIT :limit OFFSET :offset"
            params["limit"] = limit
            params["offset"] = offset
            
            result = conn.execute(text(query), params).fetchall()
            
            tasks = []
            for row in result:
                tasks.append({
                    "id": row.id,
                    "task_id": row.task_id,
                    "asset": row.asset,
                    "task_type": row.task_type,
                    "action_status": row.action_status,
                    "message_status": row.message_status,
                    "create_at": row.create_at.isoformat() if row.create_at else None,
                    "update_at": row.update_at.isoformat() if row.update_at else None
                })
            
            return {"tasks": tasks, "total": len(tasks)}
            
    except Exception as e:
        logger.error(f"Error getting tasks data: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo tareas: {str(e)}")

# Función para ejecutar la extracción de datos
async def run_data_extraction(api_key: str, dashboard_url: str, extraction_type: str):
    """Ejecutar extracción de datos usando el script Python existente"""
    try:
        # Registrar inicio de extracción
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO extraction_logs (extraction_type, status, started_at)
                VALUES (:extraction_type, :status, :started_at)
            """), {
                "extraction_type": extraction_type,
                "status": "running",
                "started_at": datetime.now()
            })
            conn.commit()
        
        # Ejecutar el script de extracción
        script_path = "/app/vRx-Report/VickyvRxReportCLI.py"
        
        cmd = [
            "python", script_path,
            "-k", api_key,
            "-d", dashboard_url,
            "--allreports" if extraction_type == "all" else f"--{extraction_type}report"
        ]
        
        logger.info(f"Ejecutando comando: {' '.join(cmd)}")
        
        # Ejecutar el comando
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd="/app/vRx-Report"
        )
        
        if process.returncode == 0:
            # Procesar archivos CSV y cargar en base de datos
            await process_csv_files()
            
            # Registrar éxito
            with engine.connect() as conn:
                conn.execute(text("""
                    UPDATE extraction_logs 
                    SET status = :status, completed_at = :completed_at
                    WHERE extraction_type = :extraction_type 
                    AND status = 'running'
                    ORDER BY created_at DESC LIMIT 1
                """), {
                    "status": "completed",
                    "completed_at": datetime.now(),
                    "extraction_type": extraction_type
                })
                conn.commit()
            
            logger.info("Extracción completada exitosamente")
        else:
            # Registrar error
            with engine.connect() as conn:
                conn.execute(text("""
                    UPDATE extraction_logs 
                    SET status = :status, error_message = :error_message, completed_at = :completed_at
                    WHERE extraction_type = :extraction_type 
                    AND status = 'running'
                    ORDER BY created_at DESC LIMIT 1
                """), {
                    "status": "failed",
                    "error_message": process.stderr,
                    "completed_at": datetime.now(),
                    "extraction_type": extraction_type
                })
                conn.commit()
            
            logger.error(f"Error en extracción: {process.stderr}")
            
    except Exception as e:
        logger.error(f"Error ejecutando extracción: {e}")
        
        # Registrar error
        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE extraction_logs 
                SET status = :status, error_message = :error_message, completed_at = :completed_at
                WHERE extraction_type = :extraction_type 
                AND status = 'running'
                ORDER BY created_at DESC LIMIT 1
            """), {
                "status": "failed",
                "error_message": str(e),
                "completed_at": datetime.now(),
                "extraction_type": extraction_type
            })
            conn.commit()

async def process_csv_files():
    """Procesar archivos CSV y cargar datos en base de datos"""
    try:
        reports_dir = "/app/vRx-Report/reports"
        
        # Procesar endpoints
        endpoints_file = os.path.join(reports_dir, "Endpoints.csv")
        if os.path.exists(endpoints_file):
            await load_endpoints_csv(endpoints_file)
        
        # Procesar vulnerabilidades
        vulnerabilities_file = os.path.join(reports_dir, "Vulnerabilities.csv")
        if os.path.exists(vulnerabilities_file):
            await load_vulnerabilities_csv(vulnerabilities_file)
        
        # Procesar patches
        patches_file = os.path.join(reports_dir, "EndpointPatchs.csv")
        if os.path.exists(patches_file):
            await load_patches_csv(patches_file)
        
        # Procesar tareas
        tasks_file = os.path.join(reports_dir, "EndpointsEventTask.csv")
        if os.path.exists(tasks_file):
            await load_tasks_csv(tasks_file)
        
        logger.info("Archivos CSV procesados exitosamente")
        
    except Exception as e:
        logger.error(f"Error procesando archivos CSV: {e}")
        raise

async def load_endpoints_csv(file_path: str):
    """Cargar datos de endpoints desde CSV"""
    try:
        df = pd.read_csv(file_path)
        
        with engine.connect() as conn:
            # Limpiar tabla existente
            conn.execute(text("DELETE FROM endpoints"))
            
            # Insertar nuevos datos
            for _, row in df.iterrows():
                conn.execute(text("""
                    INSERT INTO endpoints (endpoint_id, hostname, hash, operating_system, version, endpoint_updated_at)
                    VALUES (:endpoint_id, :hostname, :hash, :operating_system, :version, :endpoint_updated_at)
                """), {
                    "endpoint_id": int(row['ID']),
                    "hostname": row['HOSTNAME'],
                    "hash": row['HASH'],
                    "operating_system": row['SO'],
                    "version": row['VERSION'],
                    "endpoint_updated_at": datetime.fromtimestamp(int(row['endpointUpdatedAt']) / 1000) if pd.notna(row['endpointUpdatedAt']) else None
                })
            
            conn.commit()
            logger.info(f"Cargados {len(df)} endpoints")
            
    except Exception as e:
        logger.error(f"Error cargando endpoints: {e}")
        raise

async def load_vulnerabilities_csv(file_path: str):
    """Cargar datos de vulnerabilidades desde CSV"""
    try:
        df = pd.read_csv(file_path)
        
        with engine.connect() as conn:
            # Limpiar tabla existente
            conn.execute(text("DELETE FROM vulnerabilities"))
            
            # Insertar nuevos datos
            for _, row in df.iterrows():
                conn.execute(text("""
                    INSERT INTO vulnerabilities (
                        asset, asset_hash, group_name, product_name, product_raw_entry_name,
                        sensitivity_level_name, cve, vulnerability_id, patch_id, patch_name,
                        patch_release_date, create_at, update_at, link, vulnerability_summary,
                        v3_base_score, v3_exploitability_level
                    ) VALUES (
                        :asset, :asset_hash, :group_name, :product_name, :product_raw_entry_name,
                        :sensitivity_level_name, :cve, :vulnerability_id, :patch_id, :patch_name,
                        :patch_release_date, :create_at, :update_at, :link, :vulnerability_summary,
                        :v3_base_score, :v3_exploitability_level
                    )
                """), {
                    "asset": row['asset'],
                    "asset_hash": row['assethash'],
                    "group_name": row['group'],
                    "product_name": row['productName'],
                    "product_raw_entry_name": row['productRawEntryName'],
                    "sensitivity_level_name": row['sensitivityLevelName'],
                    "cve": row['cve'],
                    "vulnerability_id": int(row['vulnerabilityid']) if pd.notna(row['vulnerabilityid']) else None,
                    "patch_id": row['patchid'],
                    "patch_name": row['patchName'],
                    "patch_release_date": datetime.fromtimestamp(int(row['patchReleaseDate']) / 1000) if pd.notna(row['patchReleaseDate']) and row['patchReleaseDate'] != 'n\\a' else None,
                    "create_at": datetime.fromtimestamp(int(row['createAt']) / 1000) if pd.notna(row['createAt']) else None,
                    "update_at": datetime.fromtimestamp(int(row['updateAt']) / 1000) if pd.notna(row['updateAt']) else None,
                    "link": row['link'],
                    "vulnerability_summary": row['vulnerabilitySummary'],
                    "v3_base_score": float(row['V3BaseScore']) if pd.notna(row['V3BaseScore']) else None,
                    "v3_exploitability_level": float(row['V3ExploitabilityLevel']) if pd.notna(row['V3ExploitabilityLevel']) else None
                })
            
            conn.commit()
            logger.info(f"Cargadas {len(df)} vulnerabilidades")
            
    except Exception as e:
        logger.error(f"Error cargando vulnerabilidades: {e}")
        raise

async def load_patches_csv(file_path: str):
    """Cargar datos de patches desde CSV"""
    try:
        df = pd.read_csv(file_path)
        
        with engine.connect() as conn:
            # Limpiar tabla existente
            conn.execute(text("DELETE FROM endpoint_patches"))
            
            # Insertar nuevos datos
            for _, row in df.iterrows():
                conn.execute(text("""
                    INSERT INTO endpoint_patches (asset, operating_system, patch_name, severity_level, severity_name, description, patch_id)
                    VALUES (:asset, :operating_system, :patch_name, :severity_level, :severity_name, :description, :patch_id)
                """), {
                    "asset": row['Asset'],
                    "operating_system": row['SO'],
                    "patch_name": row['PatchName'],
                    "severity_level": row['SeverityLevel'],
                    "severity_name": row['SeverityName'],
                    "description": row['Description'],
                    "patch_id": row['PatchID']
                })
            
            conn.commit()
            logger.info(f"Cargados {len(df)} patches")
            
    except Exception as e:
        logger.error(f"Error cargando patches: {e}")
        raise

async def load_tasks_csv(file_path: str):
    """Cargar datos de tareas desde CSV"""
    try:
        df = pd.read_csv(file_path)
        
        with engine.connect() as conn:
            # Limpiar tabla existente
            conn.execute(text("DELETE FROM endpoint_event_tasks"))
            
            # Insertar nuevos datos
            for _, row in df.iterrows():
                conn.execute(text("""
                    INSERT INTO endpoint_event_tasks (
                        task_id, automation_id, automation_name, asset, task_type,
                        publisher_name, path_or_product, path_or_product_desc,
                        action_status, message_status, username, create_at, update_at
                    ) VALUES (
                        :task_id, :automation_id, :automation_name, :asset, :task_type,
                        :publisher_name, :path_or_product, :path_or_product_desc,
                        :action_status, :message_status, :username, :create_at, :update_at
                    )
                """), {
                    "task_id": int(row['Taskid']),
                    "automation_id": int(row['AutomationId']) if pd.notna(row['AutomationId']) else None,
                    "automation_name": row['AutomationName'],
                    "asset": row['Asset'],
                    "task_type": row['TaskType'],
                    "publisher_name": row['PublisherName'],
                    "path_or_product": row['PathOrProduct'],
                    "path_or_product_desc": row['PathOrProductDesc'],
                    "action_status": row['ActionStatus'],
                    "message_status": row['MessageStatus'],
                    "username": row['Username'],
                    "create_at": datetime.fromtimestamp(int(row['CreateAt']) / 1000) if pd.notna(row['CreateAt']) else None,
                    "update_at": datetime.fromtimestamp(int(row['UpdateAt']) / 1000) if pd.notna(row['UpdateAt']) else None
                })
            
            conn.commit()
            logger.info(f"Cargadas {len(df)} tareas")
            
    except Exception as e:
        logger.error(f"Error cargando tareas: {e}")
        raise

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
