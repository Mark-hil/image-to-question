import os
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")

router = APIRouter()

@router.post("/images")
async def upload_images(files: List[UploadFile] = File(...)):
    saved_paths = []
    for file in files:
        filename = file.filename
        dest = os.path.join(UPLOAD_DIR, filename)
        content = await file.read()
        with open(dest, "wb") as f:
            f.write(content)
        saved_paths.append(dest)
    return {"uploaded": saved_paths}
