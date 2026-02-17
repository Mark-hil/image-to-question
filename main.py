import os
import logging
import sys
import uuid
import traceback
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Import after environment setup
from database import engine, Base, init_db
from routers import upload, generate, upload_and_generate, questions

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events with better error handling"""
    logger.info("Starting application...")
    try:
        # Initialize database with timeout protection
        await asyncio.wait_for(init_db(), timeout=60)  # 60 second timeout
        logger.info("✅ Database initialized successfully")
        
        # Log successful startup
        logger.info("🚀 Application started successfully")
        yield
        
    except asyncio.TimeoutError:
        logger.error("❌ Database initialization timed out after 60 seconds")
        logger.error("Please check your database connection and try again")
        # Don't raise - let the app start without database for debugging
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        logger.error(f"Database URL: {os.getenv('DATABASE_URL', 'Not set')[:50]}...")
        logger.error("Please check your database configuration")
        # Don't raise - let the app start without database for debugging
        
    finally:
        logger.info("Shutting down application...")
        # Clean up database connections
        try:
            await engine.dispose()
            logger.info("✅ Database connections closed")
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")

app = FastAPI(lifespan=lifespan)

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

# Add startup event to log configuration
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up application...")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"Upload directory: {UPLOAD_DIR}")
    
    # Test database connection
    try:
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        logger.info("✅ Database connection successful")
    except Exception as e:
        logger.error("❌ Database connection failed")
        logger.error(str(e))
        raise

# Add shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down application...")
# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    logger.info(f"Request: {request.method} {request.url} - ID: {request_id}")
    
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"Request error: {str(e)}", exc_info=True)
        raise
    
    response_headers = dict(response.headers)
    logger.info(
        f"Response: {request.method} {request.url} - "
        f"Status: {response.status_code} - "
        f"Size: {response_headers.get('content-length', '?')} bytes - "
        f"ID: {request_id}"
    )
    return response

# Exception handler for file size validation
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Check if the error is related to file size
    for error in exc.errors():
        if error["type"] == "request_too_large":
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"detail": "File is too large. Images must be ≤3 MB and PDFs must be ≤15 MB."}
            )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )

# Include routers with file size limits
app.include_router(
    upload.router, 
    prefix="/upload", 
    tags=["upload"]
)
app.include_router(
    generate.router, 
    prefix="/generate", 
    tags=["generate"]
)
app.include_router(
    upload_and_generate.router, 
    prefix="/api", 
    tags=["combined"]
)
app.include_router(
    questions.router, 
    prefix="/api", 
    tags=["questions"]
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint that doesn't fail completely if database is down"""
    health_status = {"status": "ok", "timestamp": str(datetime.now())}
    
    # Check database connection with timeout
    try:
        async with asyncio.wait_for(engine.connect(), timeout=5):
            await asyncio.wait_for(engine.execute("SELECT 1"), timeout=3)
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
