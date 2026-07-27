import os
import logging
import sys
import uuid
import traceback
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from config import settings
from utils.exceptions import AppError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


UPLOAD_DIR = settings.UPLOAD_DIR
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Import after environment setup
from database import engine, Base, init_db
from routers import upload, generate, upload_and_generate, questions, tenant, billing

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events with better error handling"""
    logger.info("Starting application...")
    # logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Upload directory: {UPLOAD_DIR}")
    try:
        # Initialize database with timeout protection
        await asyncio.wait_for(init_db(), timeout=60)  # 60 second timeout
        logger.info("Database initialized successfully")
        
    except asyncio.TimeoutError:
        logger.error("Database initialization timed out after 60 seconds")
        logger.error("Please check your database connection and try again")
        # Don't raise - let the app start without database for debugging
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        logger.error(f"Database URL: {settings.DATABASE_URL[:50]}...")
        logger.error("Please check your database configuration")
        # Don't raise - let the app start without database for debugging
        
    logger.info("Application startup complete.")
    
    yield
    
    logger.info("Shutting down application...")
    # Clean up database connections
    try:
        await engine.dispose()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")

from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="AI Image-to-Question & Question Bank API",
    description="Multimodal Vision LLM & OCR Question Generation Platform. Free API access enabled.",
    version="1.0.0",
    lifespan=lifespan
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="AI Image-to-Question & Question Bank API",
        version="1.0.0",
        description="Multimodal OCR and AI Question Generation API. Free API Keys available at `/api/tenants/register`.",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "APIKeyHeader": {
            "type": "apiKey",
            "name": "X-API-Key",
            "in": "header",
            "description": "Enter your API Key (e.g., qg_live_...)"
        }
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Maximum file sizes in bytes
MAX_IMAGE_SIZE = 3 * 1024 * 1024  # 3 MB
MAX_PDF_SIZE = 15 * 1024 * 1024  # 15 MB

# Add CORS middleware - must be before other middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins like ["https://yourfrontend.com"]
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods including OPTIONS
    allow_headers=["*"],
    expose_headers=["*"],  # Expose all headers
    max_age=86400,  # Cache preflight for 24 hours
)

# Add middleware to handle OPTIONS method for all routes
@app.middleware("http")
async def options_middleware(request: Request, call_next):
    if request.method == "OPTIONS":
        response = JSONResponse(status_code=200, content={"message": "OK"})
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
        return response
    return await call_next(request)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    logger.info(f"Request: {request.method} {request.url} - ID: {request_id}")
    
    # Log request headers (be careful with sensitive data in production)
    logger.debug(f"Request headers: {dict(request.headers)}")
    
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"Request error: {str(e)}", exc_info=True)
        raise
    
    # Log response status and size
    response_headers = dict(response.headers)
    logger.info(
        f"Response: {request.method} {request.url} - "
        f"Status: {response.status_code} - "
        f"Size: {response_headers.get('content-length', '?')} bytes - "
        f"ID: {request_id}"
    )
    return response



@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details
        }
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    error_code = "API_ERROR"
    if exc.status_code == 404:
        error_code = "NOT_FOUND"
    elif exc.status_code == 401:
        error_code = "UNAUTHORIZED"
    elif exc.status_code == 403:
        error_code = "FORBIDDEN"
        
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": error_code,
            "message": str(exc.detail),
            "details": None
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    for error in exc.errors():
        if error["type"] == "request_too_large":
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={
                    "error_code": "FILE_TOO_LARGE",
                    "message": "File is too large. Images must be ≤3 MB and PDFs must be ≤15 MB.",
                    "details": None
                }
            )
            
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error_code": "VALIDATION_ERROR",
            "message": "Invalid request parameters",
            "details": exc.errors()
        }
    )

# Include routers with standardized prefixes
app.include_router(
    upload.router, 
    prefix="/api/upload", 
    tags=["Upload"]
)
app.include_router(
    generate.router, 
    prefix="/api/generate", 
    tags=["Generate"]
)
app.include_router(
    upload_and_generate.router, 
    prefix="/api/generate", 
    tags=["Generate"]
)
app.include_router(
    questions.router, 
    prefix="/api", 
    tags=["Questions"]
)
app.include_router(
    tenant.router,
    prefix="/api/tenants",
    tags=["Tenants & API Keys"]
)
app.include_router(
    billing.router,
    prefix="/api/billing",
    tags=["Billing & Payments (Paystack)"]
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint that doesn't fail completely if database is down"""
    health_status = {"status": "ok", "timestamp": str(datetime.now())}
    
    # Check database connection with timeout
    try:
        from sqlalchemy import text
        async with asyncio.wait_for(engine.connect(), timeout=5) as conn:
            await asyncio.wait_for(conn.execute(text("SELECT 1")), timeout=3)
            health_status["database"] = "connected"
    except asyncio.TimeoutError:
        health_status["database"] = "timeout"
        health_status["status"] = "degraded"
    except Exception as e:
        health_status["database"] = f"error: {str(e)[:100]}"
        health_status["status"] = "degraded"
        logger.warning(f"Health check database issue: {e}")
    
    # Check OCR service
    try:
        from services.ultimate_ocr_service import UltimateOCRService
        ocr_service = UltimateOCRService()
        health_status["ocr"] = "available"
    except Exception as e:
        health_status["ocr"] = f"error: {str(e)[:100]}"
        health_status["status"] = "degraded"
        logger.warning(f"Health check OCR issue: {e}")
    
    # Check question generation service
    try:
        from services.qgen_service import generate_questions_from_content
        health_status["question_generation"] = "available"
    except Exception as e:
        health_status["question_generation"] = f"error: {str(e)[:100]}"
        health_status["status"] = "degraded"
        logger.warning(f"Health check question generation issue: {e}")
    
    return health_status

@app.get("/")
async def root():
    return {"status": "ok", "message": "Question Generation API is running"}
