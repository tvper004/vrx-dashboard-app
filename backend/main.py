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

# Configuração de base de datos
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
    
    max_retries = 10
    retry_delay = 5
    for attempt in range(max_retries):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection successful!")
            break
        except Exception as e:
            logger.warning(f"Database connection failed (attempt {attempt + 1}/{max_retries}). Retrying in {retry_delay}s...")
            if attempt + 1 == max_retries:
                logger.error("Could not connect to the database after multiple retries.")
            time.sleep(retry_delay)

    yield
    
    logger.info("Shutting down vRx Dashboard API...")

app = FastAPI(
    title="vRx Dashboard API",
    description="API para extracción de datos de Vicarius y dashboard interactivo",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Rutas de la API

@app.get("/")
async def read_index():
    return FileResponse("static/index.html")

@app.post("/extract-data")
async def extract_data(request: ExtractionRequest, background_tasks: BackgroundTasks):
    if not request.api_key or not request.dashboard_url:
        raise HTTPException(status_code=400, detail="API key y dashboard URL son requeridos")
    extraction_id = str(uuid.uuid4())
    background_tasks.add_task(run_data_extraction, request.api_key, request.dashboard_url, request.extraction_type, extraction_id)
    return {"message": "Extracción de datos iniciada", "extraction_id": extraction_id}

@app.get("/dashboard/overview")
async def get_dashboard_overview():
    try:
        with engine.connect() as conn:
            stats = {}
            stats["total_endpoints"] = conn.execute(text("SELECT COUNT(*) FROM endpoints")).scalar_one_or_none() or 0
            stats["total_vulnerabilities"] = conn.execute(text("SELECT COUNT(*) FROM vulnerabilities")).scalar_one_or_none() or 0
            
            vulns_by_severity = conn.execute(text("SELECT sensitivity_level_name, COUNT(*) as count FROM vulnerabilities GROUP BY sensitivity_level_name")).fetchall()
            stats["vulnerabilities_by_severity"] = {row.sensitivity_level_name: row.count for row in vulns_by_severity}

            endpoints_by_os = conn.execute(text("SELECT operating_system, COUNT(*) as count FROM endpoints GROUP BY operating_system")).fetchall()
            stats["endpoints_by_os"] = {row.operating_system: row.count for row in endpoints_by_os}

            tasks_by_status = conn.execute(text("SELECT action_status, COUNT(*) as count FROM endpoint_event_tasks GROUP BY action_status")).fetchall()
            stats["tasks_by_status"] = {row.action_status: row.count for row in tasks_by_status}

            last_update = conn.execute(text("SELECT MAX(endpoint_updated_at) FROM endpoints")).scalar_one_or_none()
            stats["last_update"] = last_update.isoformat() if last_update else None
            
            return stats
    except Exception as e:
        logger.error(f"Error getting dashboard overview: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo datos del resumen: {str(e)}")

@app.get("/dashboard/endpoint-status")
async def get_endpoint_status():
    try:
        with engine.connect() as conn:
            status_result = conn.execute(text("SELECT operating_system, COUNT(*) as count FROM endpoints GROUP BY operating_system")).fetchall()
            table_result = conn.execute(text("
                SELECT 
                    e.hostname, e.operating_system,
                    COUNT(v.id) as total_vulnerabilities,
                    COUNT(CASE WHEN v.sensitivity_level_name = 'Critical' THEN 1 END) as critical,
                    COUNT(CASE WHEN v.sensitivity_level_name = 'High' THEN 1 END) as high,
                    COUNT(CASE WHEN v.sensitivity_level_name = 'Low' THEN 1 END) as low
                FROM endpoints e
                LEFT JOIN vulnerabilities v ON e.hostname = v.asset
                GROUP BY e.hostname, e.operating_system ORDER BY e.hostname
            ")).fetchall()

            return {
                "status_chart": [{"name": row.operating_system or 'N/A', "value": row.count} for row in status_result],
                "endpoint_table": [dict(row._mapping) for row in table_result]
            }
    except Exception as e:
        logger.error(f"Error getting endpoint status: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo estado de endpoints")

@app.get("/database/list-reports")
async def list_reports_in_server():
    try:
        if not os.path.exists(REPORTS_DIR):
            return {"files": []}
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
                except Exception:
                    pass
        return {"files": sorted(files_details, key=lambda x: x['filename'])}
    except Exception as e:
        logger.error(f"Error listando archivos de reportes: {e}")
        raise HTTPException(status_code=500, detail=f"Error listando archivos: {str(e)}")

@app.post("/database/upload-csvs")
async def upload_csvs(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...) ):
    saved_files = []
    for file in files:
        if file.filename.endswith('.csv'):
            dest_path = os.path.join(REPORTS_DIR, file.filename)
            with open(dest_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_files.append(file.filename)
    if not saved_files:
        raise HTTPException(status_code=400, detail="No se subieron archivos CSV válidos.")
    background_tasks.add_task(process_csv_files)
    return {"message": f"Archivos CSV subidos exitosamente: {', '.join(saved_files)}. El procesamiento ha comenzado."}

async def run_data_extraction(api_key: str, dashboard_url: str, extraction_type: str, extraction_id: str):
    try:
        extraction_streams[extraction_id] = ["Iniciando proceso de extracción..."]
        cmd = ["python", "/app/vRx-Report/VickyvRxReportCLI.py", "-k", api_key, "-d", dashboard_url, "--allreports"]
        logger.info(f"Ejecutando comando: {' '.join(cmd)}")
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd="/app/vRx-Report"
        )

        while True:
            line_bytes = await process.stdout.readline()
            if not line_bytes:
                break
            line = line_bytes.decode('utf-8', errors='ignore').strip()
            extraction_streams[extraction_id].append(line)

        await process.wait()

        if process.returncode == 0:
            extraction_streams[extraction_id].append("Procesando archivos CSV y cargando en la base de datos...")
            await process_csv_files()
            extraction_streams[extraction_id].append("__END__")
            logger.info("Extracción completada exitosamente")
        else:
            error_message = f"El script de extracción finalizó con código de error {process.returncode}."
            extraction_streams[extraction_id].append(f"__ERROR__:{error_message}")
            logger.error(f"Error en extracción: {error_message}")

    except Exception as e:
        logger.error(f"Error ejecutando extracción: {e}")
        extraction_streams[extraction_id].append(f"__ERROR__:Error inesperado en el servidor: {str(e)}")

async def process_csv_files():
    file_processors = {
        "Endpoints.csv": load_endpoints_csv,
        "VulnerabilitiesND.csv": load_vulnerabilities_csv,
        "EndpointPatchs.csv": load_patches_csv,
        "EndpointsEventTask.csv": load_tasks_csv
    }
    for filename, processor in file_processors.items():
        file_path = os.path.join(REPORTS_DIR, filename)
        if os.path.exists(file_path):
            try:
                await processor(file_path)
            except Exception as e:
                logger.error(f"Error procesando el archivo {filename}: {e}")
        else:
            logger.warning(f"No se encontró el archivo {filename}, se omitirá su procesamiento.")

async def bulk_load_csv(file_path: str, table_name: str, columns: list, column_mapping: dict = None, timestamp_cols: list = None):
    try:
        try:
            df = pd.read_csv(file_path, usecols=columns, encoding='utf-8-sig', on_bad_lines='warn')
        except UnicodeDecodeError:
            logger.warning(f"La decodificación UTF-8 falló para {file_path}. Intentando con 'latin1'.")
            df = pd.read_csv(file_path, usecols=columns, encoding='latin1', on_bad_lines='warn')

        if column_mapping:
            df.rename(columns=column_mapping, inplace=True)
        
        db_columns = list(df.columns)

        if timestamp_cols:
            for col in timestamp_cols:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], unit='ms', errors='coerce')

        df = df.replace({pd.NA: None, pd.NaT: None})
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].apply(lambda x: x.replace('\n', ' ').replace('\r', ' ') if isinstance(x, str) else x)

        with engine.connect() as conn:
            with conn.connection.cursor() as cursor:
                cursor.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE;")
                output = io.StringIO()
                df.to_csv(output, sep='\t', header=False, index=False, na_rep='\\N')
                output.seek(0)
                cursor.copy_expert(f"COPY {table_name} ({','.join(db_columns)}) FROM STDIN WITH (FORMAT csv, DELIMITER E'\t', NULL '\N')", output)
            conn.commit()
        logger.info(f"Cargados {len(df)} registros en la tabla '{table_name}' exitosamente.")
    except Exception as e:
        logger.error(f"Error en la carga masiva para la tabla {table_name} desde {file_path}: {e}")
        raise

async def load_endpoints_csv(file_path: str):
    columns = ['ID', 'HOSTNAME', 'HASH', 'SO', 'VERSION', 'endpointUpdatedAt']
    column_mapping = {'ID': 'endpoint_id', 'HOSTNAME': 'hostname', 'HASH': 'hash', 'SO': 'operating_system', 'VERSION': 'version', 'endpointUpdatedAt': 'endpoint_updated_at'}
    await bulk_load_csv(file_path, 'endpoints', columns, column_mapping, ['endpoint_updated_at'])

async def load_vulnerabilities_csv(file_path: str):
    columns = ['asset', 'assethash', 'group', 'productName', 'productRawEntryName', 'sensitivityLevelName', 'cve', 'vulnerabilityid', 'patchid', 'patchName', 'patchReleaseDate', 'createAt', 'updateAt', 'link', 'vulnerabilitySummary', 'V3BaseScore', 'V3ExploitabilityLevel']
    column_mapping = {'assethash': 'asset_hash', 'group': 'group_name', 'productName': 'product_name', 'productRawEntryName': 'product_raw_entry_name', 'sensitivityLevelName': 'sensitivity_level_name', 'vulnerabilityid': 'vulnerability_id', 'patchid': 'patch_id', 'patchName': 'patch_name', 'patchReleaseDate': 'patch_release_date', 'createAt': 'create_at', 'updateAt': 'update_at', 'vulnerabilitySummary': 'vulnerability_summary', 'V3BaseScore': 'v3_base_score', 'V3ExploitabilityLevel': 'v3_exploitability_level'}
    await bulk_load_csv(file_path, 'vulnerabilities', columns, column_mapping, ['patch_release_date', 'create_at', 'update_at'])

async def load_patches_csv(file_path: str):
    columns = ['Asset', 'SO', 'PatchName', 'SeverityLevel', 'SeverityName', 'Description', 'PatchID']
    column_mapping = {'Asset': 'asset', 'SO': 'operating_system', 'PatchName': 'patch_name', 'SeverityLevel': 'severity_level', 'SeverityName': 'severity_name', 'Description': 'description', 'PatchID': 'patch_id'}
    await bulk_load_csv(file_path, 'endpoint_patches', columns, column_mapping)

async def load_tasks_csv(file_path: str):
    columns = ['Taskid', 'AutomationId', 'AutomationName', 'Asset', 'TaskType', 'PublisherName', 'PathOrProduct', 'PathOrProductDesc', 'ActionStatus', 'MessageStatus', 'Username', 'CreateAt', 'UpdateAt']
    column_mapping = {'Taskid': 'task_id', 'AutomationId': 'automation_id', 'AutomationName': 'automation_name', 'Asset': 'asset', 'TaskType': 'task_type', 'PublisherName': 'publisher_name', 'PathOrProduct': 'path_or_product', 'PathOrProductDesc': 'path_or_product_desc', 'ActionStatus': 'action_status', 'MessageStatus': 'message_status', 'Username': 'username', 'CreateAt': 'create_at', 'UpdateAt': 'update_at'}
    await bulk_load_csv(file_path, 'endpoint_event_tasks', columns, column_mapping, ['create_at', 'update_at'])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
