import os
import shutil
import json
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from pathlib import Path
from sqlalchemy.orm import Session
import asyncio
from pydantic import BaseModel

from database import get_db
from models import Question
from services import qgen_service
from .upload import ALLOWED_EXTENSIONS, save_upload_file
from .generate import process_image, process_pdf, get_file_extension

router = APIRouter()

class GenerateRequest(BaseModel):
    qtype: str
    difficulty: str
    teacher_id: str
    num_questions: int = 3
    class_for: Optional[str] = None
    subject: Optional[str] = None

def validate_file_extension(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@router.post("/upload-and-generate")
async def upload_and_generate(
    files: List[UploadFile] = File(...),
    qtype: str = "mcq",
    difficulty: str = "medium",
    teacher_id: str = None,
    num_questions: int = 3,
    class_for: str = None,
    subject: str = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Upload files and generate questions in one step.
    """
    # Validate files
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided"
        )
    
    # Process each file
    saved_files = []
    tasks = []
    
    try:
        # Ensure we have a list of files (handle single file case)
        if not isinstance(files, list):
            files = [files]
            
        # Save files and create processing tasks
        for file in files:
            if not file or not hasattr(file, 'filename') or not file.filename:
                continue
                
            if not validate_file_extension(file.filename):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File type not allowed: {file.filename}"
                )
            
            # Save the uploaded file
            file_path = await save_upload_file(file, "uploads")
            saved_files.append(file_path)
            
            # Create processing task based on file type
            ext = get_file_extension(file_path).lower()
            if ext == 'pdf':
                task = asyncio.create_task(process_pdf(file_path))
            else:
                task = asyncio.create_task(process_image(file_path))
            tasks.append(task)
        
        # Process all files concurrently with proper error handling
        results = []
        if tasks:
            try:
                # Wait for all tasks to complete
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process any exceptions that might have occurred
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        print(f"Error processing file {saved_files[i]}: {str(result)}")
                        continue
                    if asyncio.iscoroutine(result):
                        results[i] = await result
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error processing files: {str(e)}"
                )
        
        # Process results and combine content
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                continue
            if asyncio.isfuture(result) or asyncio.iscoroutine(result):
                result = await result
            if isinstance(result, dict):
                processed_results.append(result)
        
        # Combine all text and descriptions
        combined_text = "\n\n".join(
            str(r.get("text", "")) for r in processed_results
        )
        combined_descriptions = "\n\n".join(
            str(r.get("description", "")) for r in processed_results if r.get("description")
        )
        
        # Generate questions
        questions = await asyncio.to_thread(
            qgen_service.generate_questions_from_content,
            text=combined_text,
            refined_text="",
            description=combined_descriptions,
            qtype=qtype,
            difficulty=difficulty,
            num_questions=num_questions,
            class_for=class_for,
            subject=subject
        )
        
        # Parse the JSON string if needed
        if isinstance(questions, str):
            try:
                questions = json.loads(questions)
            except json.JSONDecodeError:
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
                teacher_id=teacher_id,
                question_text=q["question"],
                answer_text=q["answer"],
                choices=json.dumps(q.get("choices", [])),
                rationale=q.get("rationale", ""),
                qtype=qtype,
                difficulty=difficulty,
                class_for=class_for,
                subject=subject,
                metadata_=json.dumps({"source_files": saved_files})
            )
            db.add(db_question)
            db_questions.append(db_question)
        
        db.commit()
        
        # Prepare response
        response_data = [
            {
                "id": q.id,
                "question": q.question_text,
                "answer": q.answer_text,
                "choices": json.loads(q.choices) if q.choices else [],
                "rationale": q.rationale,
                "type": q.qtype,
                "difficulty": q.difficulty,
                "class_for": q.class_for,
                "subject": q.subject
            }
            for q in db_questions
        ]
        
        return {"questions": response_data, "saved_files": saved_files}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing request: {str(e)}"
        )
    finally:
        # Cleanup uploaded files if needed
        pass  # You might want to implement cleanup logic here

# Don't forget to include this router in your main FastAPI app
# from fastapi import FastAPI
# app = FastAPI()
# app.include_router(upload_and_generate.router, prefix="/api")
