import os
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Request
from typing import List, Optional
import shutil
from pathlib import Path
from dotenv import load_dotenv
import re

load_dotenv()
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")

# Create upload directory if it doesn't exist
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

router = APIRouter()

# Allowed file extensions
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
ALLOWED_PDF_EXTENSIONS = {"pdf"}
ALLOWED_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS.union(ALLOWED_PDF_EXTENSIONS)

def get_file_extension(filename: str) -> str:
    """Extract and return the file extension in lowercase"""
    return Path(filename).suffix.lower().lstrip('.')

def allowed_file(filename: str) -> bool:
    """Check if the file has an allowed extension"""
    return get_file_extension(filename) in ALLOWED_EXTENSIONS

def is_image(filename: str) -> bool:
    """Check if the file is an image based on its extension"""
    return get_file_extension(filename) in ALLOWED_IMAGE_EXTENSIONS

def is_pdf(filename: str) -> bool:
    """Check if the file is a PDF based on its extension"""
    return get_file_extension(filename) in ALLOWED_PDF_EXTENSIONS

async def save_upload_file(upload_file: UploadFile, upload_dir: str, max_image_size: int = 3 * 1024 * 1024, max_pdf_size: int = 15 * 1024 * 1024) -> str:
    """
    Save an uploaded file and return its path
    
    Args:
        upload_file: The uploaded file
        upload_dir: Directory to save the file
        max_image_size: Maximum allowed image size in bytes (default: 3MB)
        max_pdf_size: Maximum allowed PDF size in bytes (default: 15MB)
        
    Returns:
        str: Path to the saved file
        
    Raises:
        HTTPException: If file type is not allowed or size exceeds limits
    """
    if not upload_file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
        
    if not allowed_file(upload_file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
        
    # Read file content to check size
    content = await upload_file.read()
    file_size = len(content)
    
    # Check file size based on type
    if is_image(upload_file.filename) and file_size > max_image_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image file is too large. Maximum size is {max_image_size // (1024 * 1024)}MB"
        )
    elif is_pdf(upload_file.filename) and file_size > max_pdf_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"PDF file is too large. Maximum size is {max_pdf_size // (1024 * 1024)}MB"
        )
        
    # Reset file pointer after reading
    await upload_file.seek(0)
    
    try:
        # Create a secure filename
        filename = Path(upload_file.filename).name
        file_path = os.path.join(upload_dir, filename)
        
        # Save the file using the content we already read
        with open(file_path, "wb") as buffer:
            buffer.write(content)
            
        return file_path
        
    except Exception as e:
        # Clean up partially written file if it exists
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
                
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving file: {str(e)}"
        )

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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided"
        )
        
    # Check content length if available (pre-check before processing)
    content_length = request.headers.get('content-length')
    if content_length:
        content_length = int(content_length)
        if content_length > 16 * 1024 * 1024:  # 16MB (slightly more than max PDF size to be safe)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Total request size exceeds maximum allowed size"
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
        except HTTPException as e:
            errors.append(f"{file.filename}: {e.detail}")
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Failed to upload files", "errors": errors}
            )
    
    return response
