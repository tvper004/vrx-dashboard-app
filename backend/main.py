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
    version="1.3.0-manual",
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

@app.get("/health")
async def health_check():
    return {"status": "healthy", "mode": "manual_upload"}

@app.get("/extraction-status")
async def get_extraction_status():
    return {"status": "manual_mode", "message": "API running in manual upload mode."}

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

@app.get("/dashboard/top-apps")
async def get_top_apps(groups: Optional[str] = None, remediated: bool = False):
    try:
        with engine.connect() as conn:
            base_query = """
                SELECT v.product_name, COUNT(v.id) as total_vulnerabilities, COUNT(DISTINCT v.asset) as affected_endpoints,
                       COUNT(CASE WHEN v.sensitivity_level_name = 'Critical' THEN 1 END) as critical,
                       COUNT(CASE WHEN v.sensitivity_level_name = 'High' THEN 1 END) as high,
                       COUNT(CASE WHEN v.sensitivity_level_name = 'Low' THEN 1 END) as low
                FROM vulnerabilities v
            """
            where_clauses = []
            params = {}
            if remediated:
                base_query += " JOIN endpoint_event_tasks t ON v.patch_id = t.path_or_product AND v.asset = t.asset"
                where_clauses.append("t.task_type = 'Patch Install' AND t.action_status = 'Succeeded'")
            if groups:
                group_list = groups.split(',')
                where_clauses.append("v.group_name = ANY(:groups)")
                params["groups"] = group_list
            if where_clauses:
                base_query += " WHERE " + " AND ".join(where_clauses)
            base_query += " GROUP BY v.product_name ORDER BY total_vulnerabilities DESC LIMIT 15"
            result = conn.execute(text(base_query), params).fetchall()
            chart_data = [{"name": row.product_name, "value": row.total_vulnerabilities} for row in result]
            table_data = [dict(row._mapping) for row in result]
            return {"chart_data": chart_data, "table_data": table_data}
    except Exception as e:
        logger.error(f"Error getting top apps: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo top de aplicaciones")

@app.get("/dashboard/remediation-comparison")
async def get_remediation_comparison(start_date: str, end_date: str):
    """
    Returns the count of resolved vulnerabilities within a specified date range.
    Resolved vulnerabilities are defined as successful patch installations.
    """
    logger.info(f"Solicitud de comparación de remediación para fechas: {start_date} a {end_date}")
    try:
        with engine.connect() as conn:
            # Convert date strings to datetime objects for comparison
            # Assuming YYYY-MM-DD format from frontend
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")

            query = text("""
                SELECT COUNT(DISTINCT asset || '-' || path_or_product) as resolved_vulnerabilities_count
                FROM endpoint_event_tasks
                WHERE task_type = 'Patch Install'
                AND action_status = 'Succeeded'
                AND create_at BETWEEN :start_dt AND :end_dt
            """)
            result = conn.execute(query, {"start_dt": start_dt, "end_dt": end_dt}).scalar_one_or_none()
            return {"resolved_vulnerabilities": result or 0}
    except Exception as e:
        logger.error(f"Error getting remediation comparison data: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo datos de comparación de remediación: {str(e)}")

@app.get("/dashboard/vulnerabilities")
async def get_vulnerabilities_data(limit: int = 100, offset: int = 0, severity: Optional[str] = None, asset: Optional[str] = None):
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
            total_query = query.replace("SELECT *", "SELECT COUNT(*)")
            total = conn.execute(text(total_query), params).scalar_one()
            query += " ORDER BY v3_base_score DESC, create_at DESC LIMIT :limit OFFSET :offset"
            params["limit"] = limit
            params["offset"] = offset
            result = conn.execute(text(query), params).fetchall()
            return {"data": [dict(row._mapping) for row in result], "total": total}
    except Exception as e:
        logger.error(f"Error getting vulnerabilities data: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo vulnerabilidades: {str(e)}")

@app.get("/dashboard/endpoints")
async def get_endpoints_data(limit: int = 100, offset: int = 0, os_filter: Optional[str] = None, hostname_filter: Optional[str] = None):
    try:
        with engine.connect() as conn:
            query = "SELECT * FROM endpoints WHERE 1=1"
            params = {}
            if os_filter:
                query += " AND operating_system ILIKE :os_filter"
                params["os_filter"] = f"%{os_filter}%"
            if hostname_filter:
                query += " AND hostname ILIKE :hostname_filter"
                params["hostname_filter"] = f"%{hostname_filter}%"
            total_query = query.replace("SELECT *", "SELECT COUNT(*)")
            total = conn.execute(text(total_query), params).scalar_one()
            query += " ORDER BY endpoint_updated_at DESC LIMIT :limit OFFSET :offset"
            params["limit"] = limit
            params["offset"] = offset
            result = conn.execute(text(query), params).fetchall()
            return {"data": [dict(row._mapping) for row in result], "total": total}
    except Exception as e:
        logger.error(f"Error getting endpoints data: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo endpoints: {str(e)}")

@app.get("/dashboard/tasks")
async def get_tasks_data(limit: int = 100, offset: int = 0, status_filter: Optional[str] = None, asset_filter: Optional[str] = None):
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
            total_query = query.replace("SELECT *", "SELECT COUNT(*)")
            total = conn.execute(text(total_query), params).scalar_one()
            query += " ORDER BY create_at DESC LIMIT :limit OFFSET :offset"
            params["limit"] = limit
            params["offset"] = offset
            result = conn.execute(text(query), params).fetchall()
            return {"data": [dict(row._mapping) for row in result], "total": total}
    except Exception as e:
        logger.error(f"Error getting tasks data: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo tareas: {str(e)}")

@app.get("/database/list-reports")
async def list_reports_in_server():
    try:
        if not os.path.exists(REPORTS_DIR):
            return {"files": []}
        files_details = []
        for filename in os.listdir(REPORTS_DIR):
            if filename.endswith(".csv"):
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
        return {"files": sorted(files_details, key=lambda x: x["filename"])}
    except Exception as e:
        logger.error(f"Error listando archivos de reportes: {e}")
        raise HTTPException(status_code=500, detail=f"Error listando archivos: {str(e)}")

@app.post("/database/upload-csvs")
async def upload_csvs(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...) ):
    saved_files = []
    for file in files:
        if file.filename.endswith(".csv"):
            dest_path = os.path.join(REPORTS_DIR, file.filename)
            with open(dest_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_files.append(file.filename)
    if not saved_files:
        raise HTTPException(status_code=400, detail="No se subieron archivos CSV válidos.")
    
    try:
        background_tasks.add_task(process_csv_files)
        return {"message": f"Archivos CSV subidos exitosamente: {', '.join(saved_files)}. El procesamiento ha comenzado."}
    except Exception as e:
        logger.error(f"Error al iniciar el procesamiento de CSV: {e}")
        raise HTTPException(status_code=500, detail=f"Error al iniciar el procesamiento de archivos: {str(e)}")

@app.post("/api/database/reload")
async def reload_database_from_disk(background_tasks: BackgroundTasks):
    """
    Re-triggers the processing of CSV files already present on the server disk.
    """
    logger.info("Solicitud para recargar la base de datos desde el disco recibida.")
    try:
        # Check if the directory and at least one target file exist before starting
        if not os.path.exists(REPORTS_DIR) or not any(f in os.listdir(REPORTS_DIR) for f in ["Endpoints.csv", "VulnerabilitiesND.csv"]):
             raise HTTPException(status_code=404, detail=f"El directorio de reportes ({REPORTS_DIR}) o los archivos CSV principales no se encontraron en el servidor.")
        
        background_tasks.add_task(process_csv_files)
        return {"message": "El proceso de recarga de la base de datos ha comenzado en segundo plano."}
    except Exception as e:
        logger.error(f"No se pudo iniciar la recarga de la base de datos: {e}")
        # If it's an HTTPException from our check, re-raise it
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"No se pudo iniciar el proceso de recarga: {str(e)}")

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
                    clean_record = {k: v for k, v in record.items() if pd.notna(v)}
                    conn.execute(table.insert().values(**clean_record))
                    successful_rows += 1
                except (sqlalchemy.exc.IntegrityError, sqlalchemy.exc.DataError) as e:
                    logger.warning(f"Error al insertar fila en '{table_name}'. Saltando fila. Error: {e}. Fila: {record}")
                    failed_rows += 1
            conn.commit()
        if job_id and reload_jobs.get(job_id):
            reload_jobs[job_id]['log'] += f"  - Carga para '{table_name}' completada. Filas exitosas: {successful_rows}, fallidas: {failed_rows}\n"
        logger.info(f"{log_prefix}Carga para '{table_name}' completada. Filas exitosas: {successful_rows}, Filas fallidas: {failed_rows}")

    except Exception as e:
        error_msg = f"FALLO CRÍTICO en la carga para la tabla {table_name} desde {file_path}: {e}"
        if job_id and reload_jobs.get(job_id):
            reload_jobs[job_id]['log'] += f"ERROR: {error_msg}\n"
            reload_jobs[job_id]['status'] = "failed"
        logger.error(f"{log_prefix}{error_msg}")
        raise  # Re-raise exception to stop the whole process

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