# Configuración para vRx Dashboard App Backend
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Config:
    """Configuración de la aplicación"""
    
    # Base de datos
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/vrx_dashboard")
    
    # API
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    
    # Frontend
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Configuración de extracción
    EXTRACTION_TIMEOUT = int(os.getenv("EXTRACTION_TIMEOUT", "3600"))  # 1 hora
    MAX_CONCURRENT_EXTRACTIONS = int(os.getenv("MAX_CONCURRENT_EXTRACTIONS", "1"))
    
    # Configuración de archivos
    REPORTS_DIR = os.getenv("REPORTS_DIR", "/app/vRx-Report/reports")
    SCRIPT_DIR = os.getenv("SCRIPT_DIR", "/app/vRx-Report")
    
    # Configuración de CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
    
    # Configuración de paginación
    DEFAULT_PAGE_SIZE = int(os.getenv("DEFAULT_PAGE_SIZE", "100"))
    MAX_PAGE_SIZE = int(os.getenv("MAX_PAGE_SIZE", "1000"))
    
    # Configuración de caché
    CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))  # 5 minutos
    
    @classmethod
    def validate(cls):
        """Validar configuración"""
        required_vars = [
            "DATABASE_URL",
            "API_HOST",
            "API_PORT"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Variables de entorno requeridas faltantes: {', '.join(missing_vars)}")
        
        return True

# Instancia de configuración
config = Config()
