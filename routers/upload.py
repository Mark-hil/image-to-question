import os
from fastapi import APIRouter, UploadFile, File, status, Request
from utils.exceptions import AppError
from typing import List, Optional
import shutil
from pathlib import Path
from config import settings
import re


UPLOAD_DIR = settings.UPLOAD_DIR

# Create upload directory if it doesn't exist
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

router = APIRouter()

from utils.file import save_upload_file

@router.post("/files")
async def upload_files(
    request: Request,
    files: List[UploadFile] = File(..., description="List of files to upload. Images must be ≤3MB, PDFs must be ≤15MB.")
):
    """
    Handle both image and PDF uploads with size limits:
    - Images: Maximum 3MB
    - PDFs: Maximum 15MB
    """
    if not files:
        raise AppError(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="NO_FILES",
            message="No files provided"
        )
        
    # Check content length if available (pre-check before processing)
    content_length = request.headers.get('content-length')
    if content_length:
        content_length = int(content_length)
        if content_length > 16 * 1024 * 1024:  # 16MB (slightly more than max PDF size to be safe)
            raise AppError(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                error_code="REQUEST_TOO_LARGE",
                message="Total request size exceeds maximum allowed size"
            )
        
    saved_files = []
    errors = []
    
    for file in files:
        if not file.filename:
            errors.append("One or more files have no filename")
            continue
            
        try:
            file_path = await save_upload_file(
                file, 
                UPLOAD_DIR,
                max_image_size=3 * 1024 * 1024,  # 3MB
                max_pdf_size=15 * 1024 * 1024    # 15MB
            )
            saved_files.append({
                "filename": file.filename,
                "path": file_path,
                "size": os.path.getsize(file_path)
            })
        except AppError as e:
            errors.append(f"{file.filename}: {e.message}")
        except Exception as e:
            errors.append(f"{file.filename}: {str(e)}")
    
    # If there were any errors, include them in the response
    response = {
        "message": f"Successfully uploaded {len(saved_files)} file(s)",
        "saved_files": saved_files
    }
    
    if errors:
        response["errors"] = errors
        if not saved_files:  # If no files were saved, it's an error
            raise AppError(
                status_code=status.HTTP_400_BAD_REQUEST,
                error_code="UPLOAD_FAILED",
                message="Failed to upload files",
                details={"errors": errors}
            )
    
    return response
