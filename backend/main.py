# vRx Dashboard App - Backend API
# FastAPI application for Vicarius data extraction and dashboard

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Request, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session, declarative_base
import pandas as pd
import os
import subprocess
import logging
from datetime import datetime
import time
from typing import List, Optional, Dict, Any
import asyncio
from contextlib import asynccontextmanager 
from fastapi.responses import StreamingResponse
import psycopg2
from psycopg2.extras import RealDictCursor
import io
import json
import uuid
import shutil

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Directorios ---
REPORTS_DIR = "/app/vRx-Report/reports"

# Configuración de base de datos
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    logger.error("FATAL: La variable de entorno DATABASE_URL no está configurada. La aplicación no puede iniciar.")
    import sys
    sys.exit(1)

# Crear engine de SQLAlchemy
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Almacenamiento en memoria para los logs de extracción en tiempo real
extraction_streams: Dict[str, List[str]] = {}

# Configuración de la aplicación FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting vRx Dashboard API...")
    os.makedirs(REPORTS_DIR, exist_ok=True)
    logger.info(f"Directorio de reportes asegurado en: {REPORTS_DIR}")
    
    # Reintentar conexión a la base de datos para manejar condiciones de carrera
    max_retries = 10
    retry_delay = 5  # segundos
    for attempt in range(max_retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection successful!")
            break  # Salir del bucle si la conexión es exitosa
        except Exception as e:
            logger.warning(f"Database connection failed (attempt {attempt + 1}/{max_retries}). Retrying in {retry_delay}s...")
            logger.debug(f"Error details: {e}")
            if attempt + 1 == max_retries:
                logger.error("Could not connect to the database after multiple retries. The application might not work correctly.")
            time.sleep(retry_delay)

    yield
    
    # Shutdown
    logger.info("Shutting down vRx Dashboard API...")

app = FastAPI(
    title="vRx Dashboard API",
    description="API para extracción de datos de Vicarius y dashboard interactivo",
    version="1.0.0",
    lifespan=lifespan
)

# Configuración de CORS
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar archivos estáticos del frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

# Dependency para obtener sesión de base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Modelo de datos para la petición de extracción
class ExtractionRequest(BaseModel):
    api_key: str
    dashboard_url: str
    extraction_type: str = "all"

# Rutas de la API

@app.get("/")
async def read_index():
    return FileResponse("static/index.html")

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
        extraction_id = str(uuid.uuid4())
        background_tasks.add_task(run_data_extraction, request.api_key, request.dashboard_url, request.extraction_type, extraction_id)
        
        return {
            "message": "Extracción de datos iniciada",
            "extraction_type": request.extraction_type,
            "timestamp": datetime.now().isoformat(),
            "extraction_id": extraction_id
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
            """ )).fetchone()
            
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
            """ )).fetchall()
            stats["vulnerabilities_by_severity"] = {row.sensitivity_level_name: row.count for row in result}
            
            # Endpoints por sistema operativo
            result = conn.execute(text("""
                SELECT operating_system, COUNT(*) as count 
                FROM endpoints 
                GROUP BY operating_system
            """ )).fetchall()
            stats["endpoints_by_os"] = {row.operating_system: row.count for row in result}
            
            # Tareas por estado
            result = conn.execute(text("""
                SELECT action_status, COUNT(*) as count 
                FROM endpoint_event_tasks 
                GROUP BY action_status
            """ )).fetchall()
            stats["tasks_by_status"] = {row.action_status: row.count for row in result}
            
            # Última actualización
            result = conn.execute(text("""
                SELECT MAX(updated_at) as last_update 
                FROM endpoints
            """ )).fetchone()
            stats["last_update"] = result.last_update.isoformat() if result and result.last_update else None
            
            return stats
            
    except Exception as e:
        logger.error(f"Error getting dashboard overview: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo datos: {str(e)}")

@app.get("/dashboard/groups")
async def get_groups():
    """Obtener una lista de todos los grupos de endpoints únicos."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT DISTINCT group_name FROM vulnerabilities WHERE group_name IS NOT NULL ORDER BY group_name")).fetchall()
            groups = [row.group_name for row in result]
            return groups
    except Exception as e:
        logger.error(f"Error getting groups: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo grupos")

@app.get("/dashboard/endpoint-status")
async def get_endpoint_status(groups: Optional[str] = None):
    """Obtener datos sobre el estado de los endpoints."""
    try:
        with engine.connect() as conn:
            group_list = groups.split(',') if groups else []
            
            # Gráfico de Status
            status_query = "SELECT status, sub_status, COUNT(*) as count FROM endpoints"
            params = {}
            if group_list:
                status_query += " WHERE hostname IN (SELECT DISTINCT asset FROM vulnerabilities WHERE group_name = ANY(:groups))"
                params["groups"] = group_list
            status_query += " GROUP BY status, sub_status"
            status_result = conn.execute(text(status_query), params).fetchall()

            # Tabla de Endpoints
            table_query = """
                SELECT 
                    e.hostname, e.status, e.sub_status,
                    COUNT(CASE WHEN v.sensitivity_level_name = 'Critical' THEN 1 END) as critical,
                    COUNT(CASE WHEN v.sensitivity_level_name = 'High' THEN 1 END) as high,
                    COUNT(CASE WHEN v.sensitivity_level_name = 'Low' THEN 1 END) as low,
                    COUNT(CASE WHEN v.sensitivity_level_name NOT IN ('Critical', 'High', 'Low') OR v.sensitivity_level_name IS NULL THEN 1 END) as na
                FROM endpoints e
                LEFT JOIN vulnerabilities v ON e.hostname = v.asset
            """
            if group_list:
                table_query += " WHERE e.hostname IN (SELECT DISTINCT asset FROM vulnerabilities WHERE group_name = ANY(:groups))"
            
            table_query += " GROUP BY e.hostname, e.status, e.sub_status ORDER BY e.hostname"
            table_result = conn.execute(text(table_query), params).fetchall()

            return {
                "status_chart": [{"name": f"{row.status or 'N/A'} ({row.sub_status or 'N/A'})", "value": row.count} for row in status_result],
                "endpoint_table": [dict(row._mapping) for row in table_result]
            }
    except Exception as e:
        logger.error(f"Error getting endpoint status: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo estado de endpoints")

@app.get("/dashboard/top-apps")
async def get_top_apps(groups: Optional[str] = None, remediated: bool = False):
    """Obtener top 15 aplicaciones por CVEs (remediados o no)."""
    try:
        with engine.connect() as conn:
            group_list = groups.split(',') if groups else []
            
            base_query = """
                SELECT 
                    v.product_name,
                    COUNT(v.id) as total_vulnerabilities,
                    COUNT(DISTINCT v.asset) as affected_endpoints,
                    COUNT(CASE WHEN v.sensitivity_level_name = 'Critical' THEN 1 END) as critical,
                    COUNT(CASE WHEN v.sensitivity_level_name = 'High' THEN 1 END) as high,
                    COUNT(CASE WHEN v.sensitivity_level_name = 'Low' THEN 1 END) as low,
                    COUNT(CASE WHEN v.sensitivity_level_name NOT IN ('Critical', 'High', 'Low') OR v.sensitivity_level_name IS NULL THEN 1 END) as na
                FROM vulnerabilities v
            """
            
            where_clauses = []
            params = {}

            if remediated:
                # Asumimos que una tarea de 'Patch Install' exitosa remedia la vulnerabilidad
                base_query += " JOIN endpoint_event_tasks t ON v.patch_id = t.path_or_product AND v.asset = t.asset"
                where_clauses.append("t.task_type = 'Patch Install' AND t.action_status = 'Succeeded'")

            if group_list:
                where_clauses.append("v.group_name = ANY(:groups)")
                params["groups"] = group_list

            if where_clauses:
                base_query += " WHERE " + " AND ".join(where_clauses)

            base_query += " GROUP BY v.product_name ORDER BY total_vulnerabilities DESC LIMIT 15"

            result = conn.execute(text(base_query), params).fetchall()

            chart_data = [{"name": row.product_name, "value": row.total_vulnerabilities} for row in result]
            table_data = [dict(row._mapping) for row in result]

            return {
                "chart_data": chart_data,
                "table_data": table_data
            }
    except Exception as e:
        logger.error(f"Error getting top apps: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo top de aplicaciones")

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

@app.post("/database/clear")
async def clear_database():
    """
    Limpia todas las tablas de datos de la base de datos.
    Esta es una operación destructiva y debe usarse con precaución.
    """
    tables_to_truncate = [
        "endpoints",
        "vulnerabilities",
        "endpoint_patches",
        "endpoint_event_tasks",
        "extraction_logs",
        "extraction_config"
    ]
    try:
        with engine.connect() as conn:
            for table in tables_to_truncate:
                # Usamos CASCADE para manejar dependencias de claves foráneas si las hubiera
                conn.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;"))
                logger.info(f"Tabla '{table}' truncada exitosamente.")
            conn.commit()
        
        return {"message": "Base de datos limpiada exitosamente."}
    except Exception as e:
        logger.error(f"Error limpiando la base de datos: {e}")
        raise HTTPException(status_code=500, detail=f"Error limpiando la base de datos: {str(e)}")

@app.get("/database/list-reports")
async def list_reports_in_server():
    """Lista los archivos CSV encontrados en el directorio de reportes del servidor."""
    try:
        if not os.path.exists(REPORTS_DIR):
            return {"message": "El directorio de reportes no existe.", "files": []}

        files_details = []
        for filename in os.listdir(REPORTS_DIR):
            if filename.endswith('.csv'):
                file_path = os.path.join(REPORTS_DIR, filename)
                try:
                    stats = os.stat(file_path)
                    files_details.append({
                        "filename": filename,
                        "size_bytes": stats.st_size,
                        "modified_at": datetime.fromtimestamp(stats.st_mtime).isoformat()
                    })
                except Exception as e:
                    logger.warning(f"No se pudo obtener detalles del archivo {filename}: {e}")
        
        return {"files": files_details}
    except Exception as e:
        logger.error(f"Error listando archivos de reportes: {e}")
        raise HTTPException(status_code=500, detail=f"Error listando archivos: {str(e)}")

@app.post("/database/upload-csvs")
async def upload_csvs(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...) ):
    """
    Permite subir archivos CSV al servidor y luego los procesa para cargarlos en la base de datos.
    """
    try:
        logger.info(f"Recibidos {len(files)} archivos para subir.")
        
        saved_files = []
        for file in files:
            # Validar tipo de archivo
            if not file.filename.endswith('.csv'):
                logger.warning(f"Archivo omitido: {file.filename} no es un archivo CSV.")
                continue
            
            dest_path = os.path.join(REPORTS_DIR, file.filename)
            
            # Guardar el archivo en el disco
            with open(dest_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            saved_files.append(file.filename)
            logger.info(f"Archivo '{file.filename}' guardado en '{dest_path}'")

        if not saved_files:
            raise HTTPException(status_code=400, detail="No se subieron archivos CSV válidos.")

        # Iniciar el procesamiento de los archivos CSV en segundo plano
        background_tasks.add_task(process_csv_files)
        
        return {
            "message": f"Archivos CSV subidos exitosamente: {', '.join(saved_files)}. El procesamiento ha comenzado en segundo plano."
        }
    except Exception as e:
        logger.error(f"Error subiendo archivos CSV: {e}")
        raise HTTPException(status_code=500, detail=f"Error subiendo archivos: {str(e)}")

@app.post("/database/load-csvs")
async def force_load_csvs(background_tasks: BackgroundTasks):
    """
    Fuerza la carga de los archivos CSV existentes en la base de datos.
    Útil si la extracción se completó pero la carga automática falló.
    """
    try:
        logger.info("Iniciando carga forzada de archivos CSV...")
        background_tasks.add_task(process_csv_files)
        return {"message": "Proceso de carga de CSVs iniciado en segundo plano."}
    except Exception as e:
        logger.error(f"Error al iniciar la carga forzada de CSVs: {e}")
        raise HTTPException(status_code=500, detail=f"Error al iniciar la carga forzada: {str(e)}")

@app.get("/stream-extraction-logs/{extraction_id}")
async def stream_extraction_logs(extraction_id: str):
    """
    Endpoint de Server-Sent Events (SSE) para transmitir logs de extracción en tiempo real.
    """
    async def event_generator():
        last_line_sent = 0
        heartbeat_counter = 0
        try:
            while True:
                if extraction_id in extraction_streams:
                    log_lines = extraction_streams[extraction_id]
                    if len(log_lines) > last_line_sent:
                        heartbeat_counter = 0 # Reiniciar contador porque hay datos
                        for i in range(last_line_sent, len(log_lines)):
                            line = log_lines[i]
                            yield f"data: {line}\n\n"
                            if line.startswith("__END__") or line.startswith("__ERROR__"):
                                if extraction_id in extraction_streams:
                                    del extraction_streams[extraction_id] # Limpiar memoria
                                return
                        last_line_sent = len(log_lines)
                
                await asyncio.sleep(1) # Esperar 1 segundo
                heartbeat_counter += 1

                # Enviar un "latido" cada 15 segundos de inactividad para mantener la conexión viva
                if heartbeat_counter >= 15:
                    yield ": heartbeat\n\n"
                    heartbeat_counter = 0

        except asyncio.CancelledError:
            logger.info(f"Cliente desconectado del stream {extraction_id}")
            if extraction_id in extraction_streams:
                del extraction_streams[extraction_id]

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Función para ejecutar la extracción de datos
async def run_data_extraction(api_key: str, dashboard_url: str, extraction_type: str, extraction_id: str):
    """Ejecutar extracción de datos usando el script Python existente"""
    # Timeout de seguridad para el script (1 hora)
    SCRIPT_TIMEOUT = 3600

    try:
        extraction_streams[extraction_id] = ["Iniciando proceso de extracción..."]
        # Registrar inicio de extracción
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO extraction_logs (extraction_type, status, started_at)
                VALUES (:extraction_type, :status, :started_at)
            """ ), {
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
        
        logger.info(f"Ejecutando comando: {' '.join(cmd)} con un timeout de {SCRIPT_TIMEOUT} segundos.")
        
        # Ejecutar el comando
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT, # Redirigir stderr a stdout
            cwd="/app/vRx-Report"
        )

        # Leer la salida en tiempo real
        while True:
            line_bytes = await process.stdout.readline()
            if not line_bytes:
                break
            line = line_bytes.decode('utf-8', errors='ignore').strip()
            
            # Enmascarar información sensible antes de enviarla al stream
            masked_line = line
            if line.strip().startswith("API Key:"):
                masked_line = "API Key: ****"
            if line.strip().startswith("Dashboard URL:"):
                masked_line = "Dashboard URL: ****"
            
            logger.info(f"[Script Salida] {masked_line}")
            extraction_streams[extraction_id].append(masked_line)

        await process.wait()

        if process.returncode == 0:
            extraction_streams[extraction_id].append("Procesando archivos CSV y cargando en la base de datos...")
            # Procesar archivos CSV y cargar en base de datos
            await process_csv_files()
            
            # Registrar éxito
            with engine.connect() as conn:
                conn.execute(text("""
                    UPDATE extraction_logs
                    SET status = :status, completed_at = :completed_at
                    WHERE id = (
                        SELECT id FROM extraction_logs
                        WHERE extraction_type = :extraction_type AND status = 'running'
                        ORDER BY created_at DESC LIMIT 1
                    )
                """ ), {
                    "status": "completed",
                    "completed_at": datetime.now(),
                    "extraction_type": extraction_type
                })
                conn.commit()
            
            extraction_streams[extraction_id].append("__END__")
            logger.info("Extracción completada exitosamente")
        else:
            error_message = f"El script de extracción finalizó con código de error {process.returncode}."
            # Registrar error
            with engine.connect() as conn:
                conn.execute(text("""
                    UPDATE extraction_logs
                    SET status = :status, error_message = :error_message, completed_at = :completed_at
                    WHERE id = (
                        SELECT id FROM extraction_logs
                        WHERE extraction_type = :extraction_type AND status = 'running'
                        ORDER BY created_at DESC LIMIT 1
                    )
                """ ), {
                    "status": "failed",
                    "error_message": error_message,
                    "completed_at": datetime.now(),
                    "extraction_type": extraction_type
                })
                conn.commit()
            
            extraction_streams[extraction_id].append(f"__ERROR__:{error_message}")
            logger.error(f"Error en extracción: {error_message}")
            
    except subprocess.TimeoutExpired as e:
        error_message = f"La extracción excedió el tiempo límite de {SCRIPT_TIMEOUT} segundos. Esto puede deberse a un gran volumen de datos o a un problema con la API de Vicarius. Revisa los logs para más detalles."
        logger.error(error_message)
        extraction_streams[extraction_id].append(f"__ERROR__:{error_message}")
        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE extraction_logs 
                SET status = :status, error_message = :error_message, completed_at = :completed_at
                WHERE id = (
                    SELECT id FROM extraction_logs
                    WHERE status = 'running' ORDER BY created_at DESC LIMIT 1
                )
            """ ), {"status": "failed", "error_message": error_message, "completed_at": datetime.now()})
            conn.commit()

    except Exception as e:
        logger.error(f"Error ejecutando extracción: {e}")
        
        # Registrar error
        extraction_streams[extraction_id].append(f"__ERROR__:Error inesperado en el servidor: {str(e)}")
        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE extraction_logs
                SET status = :status, error_message = :error_message, completed_at = :completed_at
                WHERE id = (
                    SELECT id FROM extraction_logs
                    WHERE extraction_type = :extraction_type AND status = 'running'
                    ORDER BY created_at DESC LIMIT 1
                )
            """ ), {
                "status": "failed",
                "error_message": str(e),
                "completed_at": datetime.now(),
                "extraction_type": extraction_type
            })
            conn.commit()

async def process_csv_files():
    """Procesar archivos CSV y cargar datos en base de datos"""
    try:
        # Procesar endpoints
        endpoints_file = os.path.join(REPORTS_DIR, "Endpoints.csv")
        if os.path.exists(endpoints_file):
            await load_endpoints_csv(endpoints_file)
        
        # Procesar vulnerabilidades
        vulnerabilities_file = os.path.join(REPORTS_DIR, "VulnerabilitiesND.csv")
        if os.path.exists(vulnerabilities_file):
            await load_vulnerabilities_csv(vulnerabilities_file)
        
        # Procesar patches
        patches_file = os.path.join(REPORTS_DIR, "EndpointPatchs.csv")
        if os.path.exists(patches_file):
            await load_patches_csv(patches_file)
        
        # Procesar tareas
        tasks_file = os.path.join(REPORTS_DIR, "EndpointsEventTask.csv")
        if os.path.exists(tasks_file):
            await load_tasks_csv(tasks_file)
        
        logger.info("Archivos CSV procesados exitosamente")
        
    except Exception as e:
        logger.error(f"Error procesando archivos CSV: {e}")
        raise

async def bulk_load_csv(file_path: str, table_name: str, columns: list, column_mapping: dict = None, timestamp_cols: list = None):
    """Carga datos desde un archivo CSV a una tabla usando el comando COPY de PostgreSQL."""
    try:
        try:
            # Intenta leer con UTF-8, manejando el BOM (Byte Order Mark) común en Windows
            df = pd.read_csv(file_path, usecols=columns, encoding='utf-8-sig', on_bad_lines='warn')
        except UnicodeDecodeError:
            logger.warning(f"La decodificación UTF-8 falló para {file_path}. Intentando con 'latin1'.")
            # Si falla, intenta con latin1, una codificación común para archivos de Windows
            df = pd.read_csv(file_path, usecols=columns, encoding='latin1', on_bad_lines='warn')

        # Convertir columnas de timestamp (Unix ms) a formato de fecha y hora
        if timestamp_cols:
            for col in timestamp_cols:
                if col in df.columns:
                    # errors='coerce' convierte valores no válidos en NaT (Not a Time), que se convierte en NULL
                    df[col] = pd.to_datetime(df[col], unit='ms', errors='coerce')

        db_columns = list(columns) # Copia de la lista de columnas
        if column_mapping:
            db_columns = [column_mapping.get(c, c) for c in columns]

        # Limpiar datos: reemplazar NaN por None (NULL en SQL) y manejar saltos de línea
        df = df.replace({pd.NA: None, pd.NaT: None})
        for col in df.select_dtypes(include=['object']).columns:
            # Aplicar reemplazo solo a los valores que son strings para evitar errores de tipo.
            df[col] = df[col].apply(
                lambda x: x.replace('\n', ' ').replace('\r', ' ') if isinstance(x, str) else x
            )

        with engine.connect() as conn:
            raw_conn = conn.connection
            with raw_conn.cursor() as cursor:
                # Vaciar la tabla antes de cargar nuevos datos
                logger.info(f"Truncando tabla '{table_name}' antes de la carga masiva.")
                cursor.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY;")
                
                # Preparar CSV en memoria
                output = io.StringIO()
                df.to_csv(output, sep='\t', header=False, index=False, na_rep='\\N')
                output.seek(0)
                
                # Ejecutar COPY
                cursor.copy_expert(
                    f"COPY {table_name} ({','.join(db_columns)}) FROM STDIN WITH (FORMAT csv, DELIMITER E'\t', NULL '\N')",
                    output
                )
            conn.commit()
        logger.info(f"Cargados {len(df)} registros en la tabla '{table_name}' exitosamente.")
    except Exception as e:
        logger.error(f"Error en la carga masiva para la tabla {table_name}: {e}")
        raise

async def load_endpoints_csv(file_path: str):
    """Cargar datos de endpoints desde CSV"""
    columns = [
        'ID', 'HOSTNAME', 'HASH', 'SO', 'VERSION', 'endpointUpdatedAt'
    ]
    timestamp_cols = ['endpointUpdatedAt']
    # Mapeo de nombres de columna del CSV a la Base de Datos
    column_mapping = {
        'ID': 'endpoint_id',
        'HOSTNAME': 'hostname',
        'HASH': 'hash',
        'SO': 'operating_system',
        'VERSION': 'version',
        'endpointUpdatedAt': 'endpoint_updated_at'
    }
    await bulk_load_csv(file_path, 'endpoints', columns, column_mapping, timestamp_cols)

async def load_vulnerabilities_csv(file_path: str):
    """Cargar datos de vulnerabilidades desde CSV"""
    columns = [
        'asset', 'assethash', 'group', 'productName', 'productRawEntryName',
        'sensitivityLevelName', 'cve', 'vulnerabilityid', 'patchid', 'patchName',
        'patchReleaseDate', 'createAt', 'updateAt', 'link', 'vulnerabilitySummary',
        'V3BaseScore', 'V3ExploitabilityLevel'
    ]
    timestamp_cols = ['patchReleaseDate', 'createAt', 'updateAt']
    column_mapping = {
        'assethash': 'asset_hash',
        'group': 'group_name',
        'productName': 'product_name',
        'productRawEntryName': 'product_raw_entry_name',
        'sensitivityLevelName': 'sensitivity_level_name',
        'vulnerabilityid': 'vulnerability_id',
        'patchid': 'patch_id',
        'patchName': 'patch_name',
        'patchReleaseDate': 'patch_release_date',
        'createAt': 'create_at',
        'updateAt': 'update_at',
        'vulnerabilitySummary': 'vulnerability_summary',
        'V3BaseScore': 'v3_base_score',
        'V3ExploitabilityLevel': 'v3_exploitability_level'
    }
    await bulk_load_csv(file_path, 'vulnerabilities', columns, column_mapping, timestamp_cols)

async def load_patches_csv(file_path: str):
    """Cargar datos de patches desde CSV"""
    columns = [
        'Asset', 'SO', 'PatchName', 'SeverityLevel', 
        'SeverityName', 'Description', 'PatchID'
    ]
    column_mapping = {
        'Asset': 'asset',
        'SO': 'operating_system',
        'PatchName': 'patch_name',
        'SeverityLevel': 'severity_level',
        'SeverityName': 'severity_name',
        'Description': 'description',
        'PatchID': 'patch_id'
    }
    await bulk_load_csv(file_path, 'endpoint_patches', columns, column_mapping)

async def load_tasks_csv(file_path: str):
    """Cargar datos de tareas desde CSV"""
    columns = [
        'Taskid', 'AutomationId', 'AutomationName', 'Asset', 'TaskType',
        'PublisherName', 'PathOrProduct', 'PathOrProductDesc',
        'ActionStatus', 'MessageStatus', 'Username', 'CreateAt', 'UpdateAt'
    ]
    timestamp_cols = ['CreateAt', 'UpdateAt']
    column_mapping = {
        'Taskid': 'task_id',
        'AutomationId': 'automation_id',
        'AutomationName': 'automation_name',
        'Asset': 'asset',
        'TaskType': 'task_type',
        'PublisherName': 'publisher_name',
        'PathOrProduct': 'path_or_product',
        'PathOrProductDesc': 'path_or_product_desc',
        'ActionStatus': 'action_status',
        'MessageStatus': 'message_status',
        'Username': 'username',
        'CreateAt': 'create_at',
        'UpdateAt': 'update_at'
    }
    await bulk_load_csv(file_path, 'endpoint_event_tasks', columns, column_mapping, timestamp_cols)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
