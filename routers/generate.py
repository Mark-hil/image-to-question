import os
import sys
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from sqlalchemy import or_, and_
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, status, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# Add the project root to Python path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from database import get_db
from services import vision_service, qgen_service, pdf_service, ultimate_ocr_service
from models import Question
import crud
import schemas

router = APIRouter(prefix="/api", tags=["questions"])

# Allowed file extensions
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf"}

def get_file_extension(file_path: str) -> str:
    """Get the file extension in lowercase"""
    return Path(file_path).suffix.lower().lstrip('.')

def allowed_file(filename: str) -> bool:
    """Check if the file has an allowed extension"""
    return get_file_extension(filename) in ALLOWED_EXTENSIONS

def is_image(filename: str) -> bool:
    """Check if the file is an image based on its extension"""
    return get_file_extension(filename) in {"png", "jpg", "jpeg", "gif"}

def is_pdf(filename: str) -> bool:
    """Check if the file is a PDF based on its extension"""
    return get_file_extension(filename) in {"pdf"}

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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving file: {str(e)}"
        )

class GenerateRequest(BaseModel):
    file_paths: List[str] = Field(..., description="List of file paths to process")
    qtype: str = Field(..., description="Type of questions to generate (e.g., 'mcq', 'true_false')")
    difficulty: str = Field(..., description="Difficulty level (e.g., 'easy', 'medium', 'hard')")
    teacher_id: Optional[str] = Field(None, description="Optional teacher ID")
    num_questions: int = Field(3, ge=1, le=20, description="Number of questions to generate (1-20)")
    class_for: Optional[str] = Field(None, description="Class/grade level (e.g., 'Grade 5', 'Class 10')")
    subject: Optional[str] = Field(None, description="Subject of the questions (e.g., 'Math', 'Science')")

async def process_image(file_path: str) -> Dict[str, str]:
    """Process an image file and return extracted text and description"""
    try:
        # Use ultimate OCR service with severe error correction
        text = await ultimate_ocr_service.extract_text_from_path(file_path)
        
        # Get additional description if needed
        if hasattr(vision_service, 'describe_image') and asyncio.iscoroutinefunction(vision_service.describe_image):
            description_result = await vision_service.describe_image(file_path)
            description = description_result.get('description', text.get('description', ''))
        else:
            description = text.get('description', '')
        
        return {
            "text": text.get("text", ""),
            "description": description,
            "file_path": file_path
        }
        
    except Exception as e:
        logger.error(f"Error processing image {file_path}: {str(e)}")
        return {
            "text": "",
            "description": f"Error processing image: {str(e)}",
            "file_path": file_path
        }

async def process_pdf(file_path: str) -> Dict[str, str]:
    """Process a PDF file and return extracted text"""
    try:
        # Use ultimate OCR service with severe error correction
        text = await ultimate_ocr_service.extract_text_from_path(file_path)
        
        return {
            "text": text.get("text", ""),
            "description": text.get('description', ''),
            "file_path": file_path
        }
        
    except Exception as e:
        logger.error(f"Error processing PDF {file_path}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing PDF {file_path}: {str(e)}"
        )

@router.post("/from-files")
async def generate_from_files(
    req: GenerateRequest, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db)
):
    """
    Generate questions from uploaded files (images or PDFs)
    """
    try:
        # Validate files exist and have allowed extensions
        for file_path in req.file_paths:
            if not os.path.exists(file_path):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File not found: {file_path}"
                )
            
            ext = get_file_extension(file_path)
            if ext not in ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File type not allowed: {ext}"
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
                if isinstance(result, HTTPException):
                    raise result
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error processing file {file_path}: {str(result)}"
                )
        
        # Combine text and descriptions
        combined_text = "\n\n".join([r["text"] for r in results if r["text"]])
        combined_descriptions = "\n".join([r["description"] for r in results if r.get("description")])
        
        if not combined_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No text could be extracted from the provided files"
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
            class_for=req.class_for,
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
                class_for=req.class_for,
                subject=req.subject,
                metadata_=json.dumps(q)
            )
            db.add(db_question)
            db.commit()
            db.refresh(db_question)
            
            question_data = {
                "id": db_question.id,
                "question": db_question.question_text,
                "answer": db_question.answer_text,
                "qtype": db_question.qtype,
                "difficulty": db_question.difficulty,
                "class_for": db_question.class_for,
                "subject": db_question.subject
            }
            if db_question.choices:
                question_data["choices"] = json.loads(db_question.choices)
            if db_question.rationale:
                question_data["rationale"] = db_question.rationale
            response_questions.append(question_data)
        
        return {"status": "success", "questions": response_questions}
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating questions: {str(e)}"
        )



class QuestionFilter(BaseModel):
    """Filter options for question retrieval"""
    class_for: Optional[Union[str, List[str]]] = None
    subject: Optional[Union[str, List[str]]] = None
    qtype: Optional[Union[str, List[str]]] = None
    difficulty: Optional[Union[str, List[str]]] = None
    teacher_id: Optional[Union[str, List[str]]] = None
    search: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    has_image: Optional[bool] = None
    has_choices: Optional[bool] = None


class QuestionPagination(BaseModel):
    """Pagination options"""
    skip: int = 0
    limit: int = 20
    order_by: str = "created_at"
    order: str = "desc"  # 'asc' or 'desc'


@router.get("/questions/", response_model=Dict[str, Any])
async def get_questions(
    filters: QuestionFilter = Depends(),
    pagination: QuestionPagination = Depends(),
    db: Session = Depends(get_db)
):
    """
    Retrieve questions with advanced filtering, searching, and pagination.
    
    Example queries:
    - /api/questions/?subject=Math&class_for=Grade%205
    - /api/questions/?search=capital%20of%20france
    - /api/questions/?qtype=mcq&difficulty=easy&order_by=created_at&order=desc
    """
    try:
        from sqlalchemy import desc, asc, func
        
        # Start building the query
        query = db.query(Question)
        
        # Apply filters
        if filters.class_for:
            if isinstance(filters.class_for, list):
                query = query.filter(Question.class_for.in_(filters.class_for))
            else:
                query = query.filter(Question.class_for == filters.class_for)
    
        if filters.subject:
            if isinstance(filters.subject, list):
                query = query.filter(Question.subject.in_(filters.subject))
            else:
                query = query.filter(Question.subject.ilike(f"%{filters.subject}%"))
        
        if filters.qtype:
            if isinstance(filters.qtype, list):
                query = query.filter(Question.qtype.in_(filters.qtype))
            else:
                query = query.filter(Question.qtype == filters.qtype)
        
        if filters.difficulty:
            if isinstance(filters.difficulty, list):
                query = query.filter(Question.difficulty.in_(filters.difficulty))
            else:
                query = query.filter(Question.difficulty == filters.difficulty)
        
        if filters.teacher_id:
            if isinstance(filters.teacher_id, list):
                query = query.filter(Question.teacher_id.in_(filters.teacher_id))
            else:
                query = query.filter(Question.teacher_id == filters.teacher_id)
        
        # Text search across question and answer
        if filters.search:
            search = f"%{filters.search}%"
            query = query.filter(
                or_(
                    Question.question_text.ilike(search),
                    Question.answer_text.ilike(search),
                    Question.rationale.ilike(search)
                )
            )
        
        # Date range filters
        if filters.created_after:
            query = query.filter(Question.created_at >= filters.created_after)
        if filters.created_before:
            query = query.filter(Question.created_at <= filters.created_before)
        
        # Special filters
        if filters.has_image is not None:
            if filters.has_image:
                query = query.filter(Question.metadata_.contains('"source_files":'))
            else:
                query = query.filter(~Question.metadata_.contains('"source_files":'))
        
        if filters.has_choices is not None:
            if filters.has_choices:
                query = query.filter(Question.choices != None)  # noqa: E711
            else:
                query = query.filter(Question.choices == None)  # noqa: E711
        
        # Get total count before pagination
        total = query.count()
        
        # Apply ordering
        order_column = getattr(Question, pagination.order_by, Question.created_at)
        if pagination.order.lower() == 'desc':
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(asc(order_column))
        
        # Apply pagination
        questions = query.offset(pagination.skip).limit(pagination.limit).all()
        
        # Prepare response
        response_questions = []
        for q in questions:
            question_data = {
                "id": q.id,
                "question": q.question_text,
                "answer": q.answer_text,
                "qtype": q.qtype,
                "difficulty": q.difficulty,
                "class_for": q.class_for,
                "subject": q.subject,
                "created_at": q.created_at.isoformat() if q.created_at else None
            }
            
            # Add choices if they exist
            if q.choices:
                try:
                    question_data["choices"] = json.loads(q.choices)
                except json.JSONDecodeError:
                    question_data["choices"] = []
            
            # Add rationale if it exists
            if q.rationale:
                question_data["rationale"] = q.rationale
            
            # Add metadata if it exists
            if q.metadata_:
                try:
                    question_data["metadata"] = json.loads(q.metadata_)
                except json.JSONDecodeError:
                    question_data["metadata"] = {}
            
            response_questions.append(question_data)
        
        return {
            "status": "success",
            "data": response_questions,
            "pagination": {
                "total": total,
                "returned": len(response_questions),
                "offset": pagination.skip,
                "limit": pagination.limit,
                "has_more": (pagination.skip + len(response_questions)) < total
            }
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating questions: {str(e)}"
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving questions: {str(e)}"
        )
