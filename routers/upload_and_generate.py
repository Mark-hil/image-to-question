import os
import shutil
import json
import time
import logging
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from sqlalchemy.orm import Session
import asyncio
from pydantic import BaseModel
import traceback

from database import get_db
from models import Question
from services import qgen_service
from .generate import ALLOWED_EXTENSIONS, save_upload_file, process_image, process_pdf, get_file_extension

router = APIRouter()
logger = logging.getLogger(__name__)

class ProcessingMetrics:
    def __init__(self):
        self.start_time = time.time()
        self.metrics = {
            "total": 0,
            "file_processing": 0,
            "ocr_processing": 0,
            "question_generation": 0,
            "database_operations": 0,
            "stages": {}
        }
    
    def start_stage(self, stage_name: str):
        self.metrics["stages"][stage_name] = {
            "start": time.time(),
            "end": None,
            "duration": None
        }
        return self
    
    def end_stage(self, stage_name: str):
        if stage_name in self.metrics["stages"]:
            self.metrics["stages"][stage_name]["end"] = time.time()
            duration = self.metrics["stages"][stage_name]["end"] - self.metrics["stages"][stage_name]["start"]
            self.metrics["stages"][stage_name]["duration"] = duration
            self.metrics[f"{stage_name}_time"] = duration
        return self
    
    def get_metrics(self):
        self.metrics["total"] = time.time() - self.start_time
        return {
            **self.metrics,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "end_time": datetime.now().isoformat()
        }

def log_processing_metrics(
    stage: str,
    status: str,
    metrics: ProcessingMetrics,
    request_data: Dict[str, Any],
    error: Optional[str] = None,
    **extra
):
    """Helper function to log processing metrics in a structured format."""
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "stage": stage,
        "status": status,
        **metrics.get_metrics(),
        "request": {
            "qtype": request_data.get("qtype"),
            "difficulty": request_data.get("difficulty"),
            "num_questions": request_data.get("num_questions"),
            "class_for": request_data.get("class_for"),
            "subject": request_data.get("subject"),
            "file_count": len(request_data.get("files", [])),
            "teacher_id": request_data.get("teacher_id")
        },
        **extra
    }
    
    if error:
        log_data["error"] = error
        logger.error(json.dumps(log_data))
    else:
        logger.info(json.dumps(log_data))
    
    return log_data

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
    Upload files and generate questions in one step with detailed timing metrics.
    """
    metrics = ProcessingMetrics()
    request_data = {
        "qtype": qtype,
        "difficulty": difficulty,
        "num_questions": num_questions,
        "class_for": class_for,
        "subject": subject,
        "teacher_id": teacher_id,
        "files": files
    }
    
    try:
        # Validate files
        metrics.start_stage("validation")
        if not files:
            error_msg = "No files provided"
            log_processing_metrics(
                stage="validation",
                status="failed",
                metrics=metrics,
                request_data=request_data,
                error=error_msg
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        metrics.end_stage("validation")
        
        # Process files
        metrics.start_stage("file_processing")
        saved_files = []
        tasks = []
        
        # Ensure we have a list of files (handle single file case)
        if not isinstance(files, list):
            files = [files]
            
        # Save files and create processing tasks
        for file in files:
            if not file or not hasattr(file, 'filename') or not file.filename:
                continue
                
            if not validate_file_extension(file.filename):
                error_msg = f"File type not allowed: {file.filename}"
                log_processing_metrics(
                    stage="file_validation",
                    status="failed",
                    metrics=metrics,
                    request_data=request_data,
                    error=error_msg
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg
                )
            
            try:
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
                
            except Exception as e:
                error_msg = f"Error processing file {file.filename}: {str(e)}"
                logger.error(f"File processing error: {error_msg}\n{traceback.format_exc()}")
                continue
        
        metrics.end_stage("file_processing")
        log_processing_metrics(
            stage="file_processing",
            status="completed",
            metrics=metrics,
            request_data=request_data,
            files_processed=len(saved_files)
        )
        
        # Process files with OCR
        metrics.start_stage("ocr_processing")
        results = []
        if tasks:
            try:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                # Process any exceptions that might have occurred
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.error(f"Error in OCR processing task {i}: {str(result)}")
                        continue
                    if asyncio.iscoroutine(result):
                        results[i] = await result
            except Exception as e:
                error_msg = f"Error in OCR processing: {str(e)}"
                log_processing_metrics(
                    stage="ocr_processing",
                    status="failed",
                    metrics=metrics,
                    request_data=request_data,
                    error=error_msg
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=error_msg
                )
        
        metrics.end_stage("ocr_processing")
        log_processing_metrics(
            stage="ocr_processing",
            status="completed",
            metrics=metrics,
            request_data=request_data,
            files_processed=len([r for r in results if not isinstance(r, Exception)])
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
        metrics.start_stage("question_generation")
        try:
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
                        error_msg = "Failed to parse questions from the model response"
                        log_processing_metrics(
                            stage="question_generation",
                            status="failed",
                            metrics=metrics,
                            request_data=request_data,
                            error=error_msg
                        )
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=error_msg
                        )
            
            metrics.end_stage("question_generation")
            log_processing_metrics(
                stage="question_generation",
                status="completed",
                metrics=metrics,
                request_data=request_data,
                questions_generated=len(questions) if questions else 0
            )
            
            # Save questions to database
            metrics.start_stage("database_operations")
            db_questions = []
            try:
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
                        metadata_=json.dumps({
                            "source_files": saved_files,
                            "processing_metrics": metrics.get_metrics()
                        })
                    )
                    db.add(db_question)
                    db_questions.append(db_question)
                
                db.commit()
                
                # Prepare response data
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
                
                metrics.end_stage("database_operations")
                
                # Log successful completion
                log_processing_metrics(
                    stage="processing_complete",
                    status="success",
                    metrics=metrics,
                    request_data=request_data,
                    questions_saved=len(db_questions)
                )
                
                return {
                    "status": "success",
                    "questions": response_data,
                    "saved_files": saved_files,
                    "processing_metrics": metrics.get_metrics()
                }
                
            except Exception as e:
                db.rollback()
                error_msg = f"Database error: {str(e)}"
                log_processing_metrics(
                    stage="database_operations",
                    status="failed",
                    metrics=metrics,
                    request_data=request_data,
                    error=error_msg
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=error_msg
                )
                
        except Exception as e:
            error_msg = f"Error in question generation: {str(e)}"
            log_processing_metrics(
                stage="question_generation",
                status="failed",
                metrics=metrics,
                request_data=request_data,
                error=error_msg
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg
            )
            
    except HTTPException:
        # Re-raise HTTP exceptions as they are
        raise
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        log_processing_metrics(
            stage="unexpected_error",
            status="failed",
            metrics=metrics,
            request_data=request_data,
            error=error_msg,
            traceback=traceback.format_exc()
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )
        
    finally:
        # Cleanup resources if needed
        pass

# Don't forget to include this router in your main FastAPI app
# from fastapi import FastAPI
# app = FastAPI()
# app.include_router(upload_and_generate.router, prefix="/api")
