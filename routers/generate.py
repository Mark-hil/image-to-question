import os
import sys
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from database import get_db
from services import ocr_service, vision_service, qgen_service, pdf_service
from models import Question
import crud
import schemas

router = APIRouter()

# Allowed file extensions
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf"}

def get_file_extension(file_path: str) -> str:
    """Get the file extension in lowercase"""
    return Path(file_path).suffix.lower().lstrip('.')

class GenerateRequest(BaseModel):
    file_paths: List[str] = Field(..., description="List of file paths to process")
    qtype: str = Field(..., description="Type of questions to generate (e.g., 'mcq', 'true_false')")
    difficulty: str = Field(..., description="Difficulty level (e.g., 'easy', 'medium', 'hard')")
    teacher_id: Optional[str] = Field(None, description="Optional teacher ID")
    num_questions: int = Field(3, ge=1, le=20, description="Number of questions to generate (1-20)")

async def process_image(file_path: str) -> Dict[str, str]:
    """Process an image file and return extracted text and description"""
    try:
        # Check if the functions are async or not and call them appropriately
        if hasattr(ocr_service, 'extract_text') and asyncio.iscoroutinefunction(ocr_service.extract_text):
            text = await ocr_service.extract_text(file_path)
        elif hasattr(ocr_service, 'extract_text_from_path'):
            text = await asyncio.to_thread(ocr_service.extract_text_from_path, file_path)
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No valid OCR function found"
            )
            
        if hasattr(vision_service, 'describe_image') and asyncio.iscoroutinefunction(vision_service.describe_image):
            description = await vision_service.describe_image(file_path)
        elif hasattr(vision_service, 'describe_image_stub'):
            description = await asyncio.to_thread(vision_service.describe_image_stub, file_path)
        else:
            description = ""
            
        return {"text": text, "description": description, "type": "image"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing image {file_path}: {str(e)}"
        )

async def process_pdf(file_path: str) -> Dict[str, str]:
    """Process a PDF file and return extracted text"""
    try:
        # Extract text directly from PDF using a thread pool executor
        text = await asyncio.to_thread(
            pdf_service.PDFService.extract_text_from_pdf, 
            file_path
        )
        return {"text": text, "description": "", "type": "pdf"}
    except Exception as e:
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
    # Validate files exist and have allowed extensions
    for file_path in req.file_paths:
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {file_path}"
            )
        
        ext = get_file_extension(file_path)
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed: {file_path}. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )

    # Process files based on their type
    tasks = []
    for file_path in req.file_paths:
        ext = get_file_extension(file_path)
        if ext == 'pdf':
            tasks.append(process_pdf(file_path))
        else:
            tasks.append(process_image(file_path))
    
    # Process all files concurrently and gather results
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results and ensure we have the actual values, not coroutines
    processed_results = []
    for result in results:
        if isinstance(result, Exception):
            continue  # Skip failed tasks
        if asyncio.isfuture(result) or asyncio.iscoroutine(result):
            result = await result  # Await any coroutines
        if isinstance(result, dict):
            processed_results.append(result)
    
    # Combine all text and descriptions
    combined_text = "\n\n".join(
        str(r.get("text", "")) for r in processed_results
    )
    combined_descriptions = "\n\n".join(
        str(r.get("description", "")) for r in processed_results if r.get("description")
    )

    # Generate questions from combined content
    try:
        # Run synchronous function in a thread pool
        questions = await asyncio.to_thread(
            qgen_service.generate_questions_from_content,
            text=combined_text,
            refined_text="",
            description=combined_descriptions,
            qtype=req.qtype,
            difficulty=req.difficulty,
            num_questions=req.num_questions
        )
        
        # Parse the JSON string if needed
        if isinstance(questions, str):
            try:
                questions = json.loads(questions)
            except json.JSONDecodeError:
                # If parsing fails, try to extract JSON from the string
                import re
                json_match = re.search(r'\[\s*\{.*\}\s*\]', questions, re.DOTALL)
                if json_match:
                    questions = json.loads(json_match.group(0))
                else:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to parse questions from the model response"
                    )

        # Save questions to database
        db_questions = []
        for q in questions:
            db_question = Question(
                teacher_id=req.teacher_id,
                question_text=q["question"],
                answer_text=q["answer"],
                choices=json.dumps(q.get("choices", [])),
                rationale=q.get("rationale", ""),
                qtype=req.qtype,
                difficulty=req.difficulty,
                metadata_=json.dumps(q)
            )
            db.add(db_question)
            db_questions.append(db_question)
        
        db.commit()
        
        # Prepare response
        response_questions = []
        for q in db_questions:
            question_data = {
                "id": q.id,
                "question": q.question_text,
                "answer": q.answer_text,
                "qtype": q.qtype,
                "difficulty": q.difficulty
            }
            if q.choices:
                question_data["choices"] = json.loads(q.choices)
            if q.rationale:
                question_data["rationale"] = q.rationale
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
    
    # JSON decode error handling is now part of the main try-except block
