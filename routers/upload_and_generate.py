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
from services.qgen_service import generate_questions_from_content
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
            "class_id": request_data.get("class_id"),
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
    class_id: Optional[str] = None
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
    class_id: str = None,
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
        "class_id": class_id,
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
        
        # Process results and check for OCR failures
        processed_results = []
        ocr_errors = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_msg = f"OCR processing failed for file {i+1}: {str(result)}"
                ocr_errors.append(error_msg)
                logger.error(error_msg)
                continue
            if asyncio.isfuture(result) or asyncio.iscoroutine(result):
                result = await result
            if isinstance(result, dict):
                # Check if OCR extraction was successful
                text = result.get("text", "").strip()
                if not text or text.startswith("Error:") or "404" in text or "error" in text.lower():
                    error_msg = f"OCR extraction failed or returned error for file {i+1}: {text}"
                    ocr_errors.append(error_msg)
                    logger.error(error_msg)
                    continue
                processed_results.append(result)
        
        # If there are OCR errors, stop processing and return error
        if ocr_errors:
            error_msg = f"OCR processing failed: {'; '.join(ocr_errors)}"
            log_processing_metrics(
                stage="ocr_processing",
                status="failed",
                metrics=metrics,
                request_data=request_data,
                error=error_msg
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=error_msg
            )
        
        # If no valid results, stop processing
        if not processed_results:
            error_msg = "No valid text could be extracted from any uploaded files"
            log_processing_metrics(
                stage="ocr_processing",
                status="failed",
                metrics=metrics,
                request_data=request_data,
                error=error_msg
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=error_msg
            )
        
        # Generate questions for each image individually
        metrics.start_stage("question_generation")
        try:
            all_questions = []
            image_results = []
            
            for i, result in enumerate(processed_results):
                # Generate questions for this specific image
                image_text = str(result.get("text", ""))
                image_description = str(result.get("description", ""))
                
                if not image_text.strip():
                    logger.warning(f"No text extracted from image {i+1}, skipping question generation")
                    continue
                
                # Calculate questions per image (distribute total questions across images)
                questions_per_image = max(1, num_questions // len(processed_results))
                if i == len(processed_results) - 1:  # Last image gets remaining questions
                    questions_per_image = num_questions - (questions_per_image * (len(processed_results) - 1))
                
                logger.info(f"Generating {questions_per_image} questions for image {i+1}")
                
                questions = await asyncio.to_thread(
                    generate_questions_from_content,
                    text=image_text,
                    refined_text="",
                    description=image_description,
                    qtype=qtype,
                    difficulty=difficulty,
                    num_questions=questions_per_image,
                    class_id=class_id,
                    subject=subject
                )
                
                # Parse JSON string if needed
                if isinstance(questions, str):
                    try:
                        questions = json.loads(questions)
                    except json.JSONDecodeError:
                        import re
                        json_match = re.search(r'\[\s*\{.*\}\s*\]', questions, re.DOTALL)
                        if json_match:
                            questions = json.loads(json_match.group(0))
                        else:
                            error_msg = f"Failed to parse questions from model response for image {i+1}"
                            log_processing_metrics(
                                stage="question_generation",
                                status="failed",
                                metrics=metrics,
                                request_data=request_data,
                                error=error_msg
                            )
                            continue
                
                # Add image source information to each question
                for q in questions:
                    q["source_image"] = i + 1  # 1-based image index
                    q["source_file"] = result.get("file_path", f"image_{i+1}")
                    if image_description:
                        q["image_description"] = image_description
                
                all_questions.extend(questions)
                image_results.append({
                    "image_index": i + 1,
                    "file_path": result.get("file_path", f"image_{i+1}"),
                    "text_length": len(image_text),
                    "questions_generated": len(questions),
                    "questions": questions
                })
            
            questions = all_questions
            
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
                        class_id=class_id,
                        subject=subject,
                        metadata_=json.dumps({
                            "source_image": q.get("source_image", 0),
                            "source_file": q.get("source_file", ""),
                            "image_description": q.get("image_description", "")
                        })
                    )
                    db.add(db_question)
                    db_questions.append(db_question)
                
                db.commit()
                
                # Prepare response data with image organization
                response_data = []
                for q in db_questions:
                    # Get image source info from individual question metadata
                    metadata = json.loads(q.metadata_) if q.metadata_ else {}
                    
                    question_data = {
                        "id": q.id,
                        "question": q.question_text,
                        "answer": q.answer_text,
                        "choices": json.loads(q.choices) if q.choices else [],
                        "rationale": q.rationale,
                        "type": q.qtype,
                        "difficulty": q.difficulty,
                        "class_id": q.class_id,
                        "subject": q.subject,
                        "source_image": metadata.get("source_image", 0),
                        "source_file": metadata.get("source_file", ""),
                        # "image_description": metadata.get("image_description", "")
                    }
                    response_data.append(question_data)
                
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
                    "processing_metrics": metrics.get_metrics(),
                    # "image_summary": image_results
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
