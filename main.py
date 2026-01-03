import os
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os

load_dotenv()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

from database import engine, Base
from routers import upload, generate, upload_and_generate

# create DB tables (simple approach for prototype)
Base.metadata.create_all(bind=engine)

# Maximum file sizes in bytes
MAX_IMAGE_SIZE = 3 * 1024 * 1024  # 3 MB
MAX_PDF_SIZE = 15 * 1024 * 1024  # 15 MB

app = FastAPI(
    title="Question Generation Backend",
    # Set default request body size limit (slightly larger than our max file size)
    max_upload_size=MAX_PDF_SIZE + (1 * 1024 * 1024)  # 16 MB to be safe
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/")
async def root():
    return {"status": "ok"}
