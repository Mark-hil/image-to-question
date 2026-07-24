import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from sqlalchemy import or_, and_
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, status, UploadFile
from utils.exceptions import AppError
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

# Add the project root to Python path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from database import get_db
from services import vision_service, qgen_service, pdf_service, ultimate_ocr_service
from models import Question
import crud
import schemas

router = APIRouter()
logger = logging.getLogger(__name__)

from utils.file import ALLOWED_EXTENSIONS, get_file_extension

class GenerateRequest(BaseModel):
    file_paths: List[str] = Field(..., description="List of file paths to process")
    qtype: str = Field(..., description="Type of questions to generate (e.g., 'mcq', 'true_false')")
    difficulty: str = Field(..., description="Difficulty level (e.g., 'easy', 'medium', 'hard')")
    teacher_id: Optional[str] = Field(None, description="Optional teacher ID")
    num_questions: int = Field(3, ge=1, le=20, description="Number of questions to generate (1-20)")
    class_id: Optional[str] = Field(None, description="Class/grade level (e.g., 'Grade 5', 'Class 10')")
    subject: Optional[str] = Field(None, description="Subject of the questions (e.g., 'Math', 'Science')")

async def process_image(file_path: str) -> Dict[str, str]:
    """Process an image file and return extracted text and description"""
    try:
        # Use ultimate OCR service with severe error correction
        text = await ultimate_ocr_service.extract_text_from_path(file_path)
        
        # Check if OCR extraction was successful
        extracted_text = text.get("text", "").strip()
        if not extracted_text or extracted_text.startswith("Error:") or "404" in extracted_text or "error" in extracted_text.lower():
            raise ValueError(f"OCR extraction failed: {extracted_text}")
        
        # Get additional description if needed
        if hasattr(vision_service, 'describe_image') and asyncio.iscoroutinefunction(vision_service.describe_image):
            description_result = await vision_service.describe_image(file_path)
            description = description_result.get('description', text.get('description', ''))
        else:
            description = text.get('description', '')
        
        return {
            "text": extracted_text,
            "description": description,
            "file_path": file_path
        }
        
    except Exception as e:
        logger.error(f"Error processing image {file_path}: {str(e)}")
        raise AppError(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="IMAGE_PROCESSING_FAILED",
            message=f"Failed to process image: {str(e)}"
        )

async def process_pdf(file_path: str) -> Dict[str, str]:
    """Process a PDF file and return extracted text"""
    try:
        # Use ultimate OCR service with severe error correction
        text = await ultimate_ocr_service.extract_text_from_path(file_path)
        
        # Check if OCR extraction was successful
        extracted_text = text.get("text", "").strip()
        if not extracted_text or extracted_text.startswith("Error:") or "404" in extracted_text or "error" in extracted_text.lower():
            raise ValueError(f"OCR extraction failed: {extracted_text}")
        
        return {
            "text": extracted_text,
            "description": text.get('description', ''),
            "file_path": file_path
        }
        
    except Exception as e:
        logger.error(f"Error processing PDF {file_path}: {str(e)}")
        raise AppError(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="PDF_PROCESSING_FAILED",
            message=f"Failed to process PDF: {str(e)}"
        )

@router.post("/from-files")
async def generate_from_files(
    req: GenerateRequest, 
    background_tasks: BackgroundTasks, 
    db: AsyncSession = Depends(get_db)
):
    """
    Generate questions from uploaded files (images or PDFs)
    """
    try:
        # Validate files exist and have allowed extensions
        for file_path in req.file_paths:
            if not os.path.exists(file_path):
                raise AppError(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    error_code="FILE_NOT_FOUND",
                    message=f"File not found: {file_path}"
                )
            
            ext = get_file_extension(file_path)
            if ext not in ALLOWED_EXTENSIONS:
                raise AppError(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    error_code="INVALID_FILE_TYPE",
                    message=f"File type not allowed: {ext}"
                )
        
        # Process each file
        tasks = []
        for file_path in req.file_paths:
            ext = get_file_extension(file_path)
            if ext in {"png", "jpg", "jpeg", "gif"}:
                tasks.append(process_image(file_path))
            elif ext == "pdf":
                tasks.append(process_pdf(file_path))
        
        # Wait for all files to be processed
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check for any processing errors
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                file_path = req.file_paths[i]
                if isinstance(result, AppError) or isinstance(result, HTTPException):
                    raise result
                raise AppError(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    error_code="FILE_PROCESSING_ERROR",
                    message=f"Error processing file {file_path}: {str(result)}"
                )
        
        # Combine text and descriptions
        combined_text = "\n\n".join([r["text"] for r in results if r["text"]])
        combined_descriptions = "\n".join([r["description"] for r in results if r.get("description")])
        
        if not combined_text.strip():
            raise AppError(
                status_code=status.HTTP_400_BAD_REQUEST,
                error_code="NO_TEXT_EXTRACTED",
                message="No text could be extracted from the provided files"
            )
        
        # Generate questions
        questions = await asyncio.to_thread(
            qgen_service.generate_questions_from_content,
            text=combined_text,
            refined_text="",
            description=combined_descriptions,
            qtype=req.qtype,
            difficulty=req.difficulty,
            num_questions=req.num_questions,
            class_id=req.class_id,
            subject=req.subject
        )
        
        # Save questions to database
        response_questions = []
        for q in questions:
            db_question = Question(
                teacher_id=req.teacher_id,
                question_text=q["question"],
                answer_text=q["answer"],
                choices=json.dumps(q.get("choices", [])),
                rationale=q.get("rationale", ""),
                qtype=req.qtype,
                difficulty=req.difficulty,
                class_id=req.class_id,
                subject=req.subject,
                metadata_=json.dumps(q)
            )
            db.add(db_question)
            await db.commit()
            await db.refresh(db_question)
            
            question_data = {
                "id": db_question.id,
                "question": db_question.question_text,
                "answer": db_question.answer_text,
                "qtype": db_question.qtype,
                "difficulty": db_question.difficulty,
                "class_id": db_question.class_id,
                "subject": db_question.subject
            }
            if db_question.choices:
                question_data["choices"] = json.loads(db_question.choices)
            if db_question.rationale:
                question_data["rationale"] = db_question.rationale
            response_questions.append(question_data)
        
        return {"status": "success", "questions": response_questions}
    
    except (AppError, HTTPException):
        # Re-raise exceptions
        raise
    except Exception as e:
        await db.rollback()
        raise AppError(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="QUESTION_GENERATION_FAILED",
            message=f"Error generating questions: {str(e)}"
        )

