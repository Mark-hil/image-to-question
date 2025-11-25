import os
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from typing import List
import shutil
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")

# Create upload directory if it doesn't exist
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

router = APIRouter()

# Allowed file extensions
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
ALLOWED_PDF_EXTENSIONS = {"pdf"}
ALLOWED_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS.union(ALLOWED_PDF_EXTENSIONS)

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

async def save_upload_file(upload_file: UploadFile, upload_dir: str) -> str:
    """Save an uploaded file and return its path"""
    if not allowed_file(upload_file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Create a secure filename
    filename = upload_file.filename
    file_path = os.path.join(upload_dir, filename)
    
    # Save the file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    
    return file_path

@router.post("/files")
async def upload_files(files: List[UploadFile] = File(...)):
    """Handle both image and PDF uploads"""
    saved_paths = []
    
    for file in files:
        try:
            file_path = await save_upload_file(file, UPLOAD_DIR)
            saved_paths.append(file_path)
        except HTTPException as e:
            # Re-raise HTTP exceptions
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing {file.filename}: {str(e)}"
            )
    
    return {"status": "success", "uploaded_files": saved_paths}
