# vRx Dashboard App - Backend API (Simplified for Manual Upload)

from fastapi import FastAPI, HTTPException, BackgroundTasks, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, text, Table, MetaData
import pandas as pd
import os
import logging
from datetime import datetime
import time
from typing import List, Optional
import asyncio
from contextlib import asynccontextmanager
import shutil
import sqlalchemy.exc

# --- Basic Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
REPORTS_DIR = "/app/vRx-Report/reports"

# --- Database Setup ---
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set.")
engine = create_engine(DATABASE_URL)

# --- FastAPI App Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting vRx Dashboard API...")
    os.makedirs(REPORTS_DIR, exist_ok=True)
    # Test database connection on startup
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection successful!")
    except Exception as e:
        logger.error(f"FATAL: Could not connect to the database on startup. Please check credentials and host. Error: {e}")
    yield
    logger.info("Shutting down vRx Dashboard API...")

# --- FastAPI App Initialization ---
app = FastAPI(
    title="vRx Dashboard API",
    description="API para dashboard interactivo con carga manual de CSV.",
    version="1.1.0-manual",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Static Files and Index ---
app.mount("/static", StaticFiles(directory="static"), name="static")
@app.get("/")
async def read_index():
    return FileResponse("static/index.html")

# --- API Endpoints ---

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
            table_result = conn.execute(text("""
                SELECT e.hostname, e.operating_system, COUNT(v.id) as total_vulnerabilities,
                       COUNT(CASE WHEN v.sensitivity_level_name = 'Critical' THEN 1 END) as critical,
                       COUNT(CASE WHEN v.sensitivity_level_name = 'High' THEN 1 END) as high,
                       COUNT(CASE WHEN v.sensitivity_level_name = 'Low' THEN 1 END) as low
                FROM endpoints e LEFT JOIN vulnerabilities v ON e.hostname = v.asset
                GROUP BY e.hostname, e.operating_system ORDER BY e.hostname
            """)).fetchall()
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

# --- Data Processing Logic ---

async def process_csv_files():
    logger.info("Iniciando el proceso de carga de datos de archivos CSV...")
    file_processors = {
        "Endpoints.csv": load_endpoints_csv,
        "VulnerabilitiesND.csv": load_vulnerabilities_csv,
        "EndpointPatchs.csv": load_patches_csv,
        "EndpointsEventTask.csv": load_tasks_csv
    }
    for filename, processor in file_processors.items():
        file_path = os.path.join(REPORTS_DIR, filename)
        if os.path.exists(file_path):
            await processor(file_path)
        else:
            logger.warning(f"No se encontró el archivo {filename}, se omitirá su procesamiento.")
    logger.info("Proceso de carga de datos finalizado.")

async def load_data_robustly(file_path: str, table_name: str, columns: list, column_mapping: dict, timestamp_cols: Optional[list] = None):
    logger.info(f"Iniciando carga robusta para la tabla '{table_name}' desde '{file_path}'")
    try:
        try:
            df = pd.read_csv(file_path, usecols=columns, encoding='utf-8-sig', on_bad_lines='warn')
        except UnicodeDecodeError:
            logger.warning(f"Decodificación UTF-8 falló para {file_path}. Intentando con 'latin1'.")
            df = pd.read_csv(file_path, usecols=columns, encoding='latin1', on_bad_lines='warn')

        df.rename(columns=column_mapping, inplace=True)
        
        if timestamp_cols:
            for col in timestamp_cols:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], unit='ms', errors='coerce')

        df.replace({pd.NaT: None}, inplace=True)

        with engine.connect() as conn:
            table = Table(table_name, MetaData(), autoload_with=conn)
            conn.execute(table.delete()) # Limpiar tabla antes de insertar
            records = df.to_dict(orient='records')
            
            successful_rows = 0
            failed_rows = 0

            for record in records:
                try:
                    # Limpiar NaNs que puedan quedar
                    clean_record = {k: v for k, v in record.items() if pd.notna(v)}
                    conn.execute(table.insert().values(**clean_record))
                    successful_rows += 1
                except (sqlalchemy.exc.IntegrityError, sqlalchemy.exc.DataError) as e:
                    logger.warning(f"Error al insertar fila en '{table_name}'. Saltando fila. Error: {e}. Fila: {record}")
                    failed_rows += 1
            conn.commit()
        logger.info(f"Carga para '{table_name}' completada. Filas exitosas: {successful_rows}, Filas fallidas: {failed_rows}")

    except Exception as e:
        logger.error(f"FALLO CRÍTICO en la carga para la tabla {table_name} desde {file_path}: {e}")
        # No re-lanzar la excepción para no detener el procesamiento de otros archivos

async def load_endpoints_csv(file_path: str):
    columns = ['ID', 'HOSTNAME', 'HASH', 'SO', 'VERSION', 'endpointUpdatedAt']
    column_mapping = {'ID': 'endpoint_id', 'HOSTNAME': 'hostname', 'HASH': 'hash', 'SO': 'operating_system', 'VERSION': 'version', 'endpointUpdatedAt': 'endpoint_updated_at'}
    await load_data_robustly(file_path, 'endpoints', columns, column_mapping, ['endpoint_updated_at'])

async def load_vulnerabilities_csv(file_path: str):
    columns = ['asset', 'assethash', 'group', 'productName', 'productRawEntryName', 'sensitivityLevelName', 'cve', 'vulnerabilityid', 'patchid', 'patchName', 'patchReleaseDate', 'createAt', 'updateAt', 'link', 'vulnerabilitySummary', 'V3BaseScore', 'V3ExploitabilityLevel']
    column_mapping = {'assethash': 'asset_hash', 'group': 'group_name', 'productName': 'product_name', 'productRawEntryName': 'product_raw_entry_name', 'sensitivityLevelName': 'sensitivity_level_name', 'vulnerabilityid': 'vulnerability_id', 'patchid': 'patch_id', 'patchName': 'patch_name', 'patchReleaseDate': 'patch_release_date', 'createAt': 'create_at', 'updateAt': 'update_at', 'vulnerabilitySummary': 'vulnerability_summary', 'V3BaseScore': 'v3_base_score', 'V3ExploitabilityLevel': 'v3_exploitability_level'}
    await load_data_robustly(file_path, 'vulnerabilities', columns, column_mapping, ['patch_release_date', 'create_at', 'update_at'])

async def load_patches_csv(file_path: str):
    columns = ['Asset', 'SO', 'PatchName', 'SeverityLevel', 'SeverityName', 'Description', 'PatchID']
    column_mapping = {'Asset': 'asset', 'SO': 'operating_system', 'PatchName': 'patch_name', 'SeverityLevel': 'severity_level', 'SeverityName': 'severity_name', 'Description': 'description', 'PatchID': 'patch_id'}
    await load_data_robustly(file_path, 'endpoint_patches', columns, column_mapping)

async def load_tasks_csv(file_path: str):
    columns = ['Taskid', 'AutomationId', 'AutomationName', 'Asset', 'TaskType', 'PublisherName', 'PathOrProduct', 'PathOrProductDesc', 'ActionStatus', 'MessageStatus', 'Username', 'CreateAt', 'UpdateAt']
    column_mapping = {'Taskid': 'task_id', 'AutomationId': 'automation_id', 'AutomationName': 'automation_name', 'Asset': 'asset', 'TaskType': 'task_type', 'PublisherName': 'publisher_name', 'PathOrProduct': 'path_or_product', 'PathOrProductDesc': 'path_or_product_desc', 'ActionStatus': 'action_status', 'MessageStatus': 'message_status', 'Username': 'username', 'CreateAt': 'create_at', 'UpdateAt': 'update_at'}
    await load_data_robustly(file_path, 'endpoint_event_tasks', columns, column_mapping, ['create_at', 'update_at'])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)