import os
from pathlib import Path
from fastapi import UploadFile, status
from utils.exceptions import AppError

# Allowed file extensions
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
ALLOWED_PDF_EXTENSIONS = {"pdf"}
ALLOWED_PPTX_EXTENSIONS = {"pptx", "ppt"}
ALLOWED_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS.union(ALLOWED_PDF_EXTENSIONS).union(ALLOWED_PPTX_EXTENSIONS)

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

def is_pptx(filename: str) -> bool:
    """Check if the file is a PowerPoint presentation based on its extension"""
    return get_file_extension(filename) in ALLOWED_PPTX_EXTENSIONS

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
        raise AppError(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="NO_FILE_PROVIDED",
            message="No file provided"
        )
        
    if not allowed_file(upload_file.filename):
        raise AppError(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="INVALID_FILE_TYPE",
            message=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
        
    # Read file content to check size
    content = await upload_file.read()
    file_size = len(content)
    
    # Check file size based on type
    if is_image(upload_file.filename) and file_size > max_image_size:
        raise AppError(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            error_code="FILE_TOO_LARGE",
            message=f"Image file is too large. Maximum size is {max_image_size // (1024 * 1024)}MB"
        )
    elif is_pdf(upload_file.filename) and file_size > max_pdf_size:
        raise AppError(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            error_code="FILE_TOO_LARGE",
            message=f"PDF file is too large. Maximum size is {max_pdf_size // (1024 * 1024)}MB"
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
                
        raise AppError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="FILE_SAVE_ERROR",
            message=f"Error saving file: {str(e)}"
        )
