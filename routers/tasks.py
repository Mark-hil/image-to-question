import os
import json
import uuid
import time
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends, BackgroundTasks, Query, Header
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database import async_session_maker, get_db
from models import Question
from services.qgen_service import generate_questions_from_content
from .generate import process_image, process_pdf
from utils.file import ALLOWED_EXTENSIONS, save_upload_file, get_file_extension, cleanup_files
from utils.exceptions import AppError
from utils.usage_limits import resolve_and_enforce_identity, deduct_usage, CallerIdentity, validate_question_count

router = APIRouter()
logger = logging.getLogger(__name__)

# Global in-memory task store for tracking background jobs
tasks_store: Dict[str, Dict[str, Any]] = {}

def validate_file_extension(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class AsyncGenerateResponse(BaseModel):
    task_id: str
    status: str
    progress: int
    stage: str
    message: str

async def run_async_generation_task(
    task_id: str,
    saved_files: List[str],
    qtype: str,
    difficulty: str,
    num_questions: int,
    class_id: Optional[str],
    subject: Optional[str],
    teacher_id: Optional[str],
    blooms_level: str = "all",
    page_range: str = "",
    caller_id: Optional[CallerIdentity] = None,
    mode: str = "exam"
):
    """Background worker function executing vision extractions, LLM generation, and DB storage."""
    try:
        logger.info(f"Starting background generation task {task_id}")
        tasks_store[task_id]["status"] = "processing"
        tasks_store[task_id]["progress"] = 15
        tasks_store[task_id]["stage"] = "Uploaded files validated. Starting Multimodal Vision LLM text extraction..."
        tasks_store[task_id]["updated_at"] = datetime.utcnow().isoformat()

        # Step 1: Process files via Vision / OCR
        tasks = []
        for file_path in saved_files:
            ext = get_file_extension(file_path).lower()
            if ext == 'pdf':
                tasks.append(process_pdf(file_path, page_range=page_range))
            else:
                tasks.append(process_image(file_path))

        ocr_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        tasks_store[task_id]["progress"] = 45
        tasks_store[task_id]["stage"] = "Text extraction complete. Analyzing content with Groq Vision LLM & Bloom's Taxonomy..."
        tasks_store[task_id]["updated_at"] = datetime.utcnow().isoformat()

        processed_results = []
        for i, res in enumerate(ocr_results):
            if isinstance(res, Exception):
                logger.error(f"Error in async task {task_id} OCR file {i}: {res}")
                continue
            if isinstance(res, dict) and res.get("text"):
                processed_results.append(res)

        if not processed_results:
            tasks_store[task_id]["status"] = "failed"
            tasks_store[task_id]["error"] = "No readable text could be extracted from uploaded files."
            tasks_store[task_id]["stage"] = "Failed during text extraction."
            tasks_store[task_id]["updated_at"] = datetime.utcnow().isoformat()
            return

        # Step 2: Generate Questions per image chunk
        all_questions = []
        total_sources = len(processed_results)

        for i, result in enumerate(processed_results):
            image_text = str(result.get("text", ""))
            image_description = str(result.get("description", ""))

            questions_per_image = max(1, num_questions // total_sources)
            if i == total_sources - 1:
                questions_per_image = num_questions - (questions_per_image * (total_sources - 1))

            prog_pct = 45 + int(35 * ((i + 1) / total_sources))
            tasks_store[task_id]["progress"] = min(80, prog_pct)
            tasks_store[task_id]["stage"] = f"Generating questions for document chunk {i + 1} of {total_sources} (Bloom's Taxonomy Classification)..."
            tasks_store[task_id]["updated_at"] = datetime.utcnow().isoformat()

            raw_questions = await asyncio.to_thread(
                generate_questions_from_content,
                text=image_text,
                refined_text="",
                description=image_description,
                qtype=qtype,
                difficulty=difficulty,
                num_questions=questions_per_image,
                class_id=class_id,
                subject=subject,
                blooms_level=blooms_level,
                mode=mode
            )

            if isinstance(raw_questions, str):
                try:
                    raw_questions = json.loads(raw_questions)
                except Exception:
                    raw_questions = []

            for q in raw_questions:
                q["source_image"] = i + 1
                q["source_file"] = result.get("file_path", f"file_{i+1}")
                if image_description:
                    q["image_description"] = image_description
                all_questions.append(q)

        tasks_store[task_id]["progress"] = 85
        tasks_store[task_id]["stage"] = "Questions generated and classified. Saving to PostgreSQL Database..."
        tasks_store[task_id]["updated_at"] = datetime.utcnow().isoformat()

        # Enforce strict question count ceiling
        all_questions = all_questions[:num_questions]

        # Step 3: Save to Database using fresh session
        response_data = []
        async with async_session_maker() as db:
            db_questions = []
            for q in all_questions:
                db_q = Question(
                    teacher_id=teacher_id,
                    question_text=q.get("question", "No question text"),
                    answer_text=q.get("answer", ""),
                    choices=json.dumps(q.get("choices", [])),
                    rationale=q.get("rationale", ""),
                    qtype=q.get("qtype") or (qtype.split(",")[0] if qtype else "mcq"),
                    difficulty=q.get("difficulty") or (difficulty.split(",")[0] if difficulty else "medium"),
                    blooms_level=q.get("blooms_level", "Understand"),
                    class_id=class_id,
                    subject=subject,
                    metadata_=json.dumps({
                        "source_image": q.get("source_image", 0),
                        "source_file": q.get("source_file", ""),
                        "image_description": q.get("image_description", "")
                    })
                )
                db.add(db_q)
                db_questions.append(db_q)

            await db.commit()

            for db_q in db_questions:
                metadata = json.loads(db_q.metadata_) if db_q.metadata_ else {}
                question_data = {
                    "id": db_q.id,
                    "question": db_q.question_text,
                    "question_text": db_q.question_text,
                    "answer": db_q.answer_text,
                    "answer_text": db_q.answer_text,
                    "choices": json.loads(db_q.choices) if db_q.choices else [],
                    "rationale": db_q.rationale,
                    "type": db_q.qtype,
                    "qtype": db_q.qtype,
                    "difficulty": db_q.difficulty,
                    "blooms_level": db_q.blooms_level or "Understand",
                    "class_id": db_q.class_id,
                    "subject": db_q.subject,
                    "source_image": metadata.get("source_image", 0),
                    "source_file": metadata.get("source_file", "")
                }
                response_data.append(question_data)

            # Deduct usage from caller quota pool
            usage_stats = None
            if caller_id:
                usage_stats = await deduct_usage(caller_id, db, questions_generated=len(db_questions))

        # Step 4: Mark Complete
        tasks_store[task_id]["status"] = "completed"
        tasks_store[task_id]["progress"] = 100
        tasks_store[task_id]["stage"] = "Generation complete! Question bank ready."
        tasks_store[task_id]["questions"] = response_data
        tasks_store[task_id]["usage"] = usage_stats
        tasks_store[task_id]["limit_hit_warning"] = usage_stats.get("limit_hit_warning") if usage_stats else None
        tasks_store[task_id]["updated_at"] = datetime.utcnow().isoformat()
        logger.info(f"Task {task_id} completed successfully with {len(response_data)} questions.")

    except Exception as e:
        logger.error(f"Error in background task {task_id}: {str(e)}", exc_info=True)
        tasks_store[task_id]["status"] = "failed"
        tasks_store[task_id]["error"] = str(e)
        tasks_store[task_id]["stage"] = f"Failed with error: {str(e)}"
        tasks_store[task_id]["updated_at"] = datetime.utcnow().isoformat()
    finally:
        # Extract & Discard: Clean up uploaded files immediately from disk
        cleanup_files(saved_files)


@router.post("/generate-async", response_model=AsyncGenerateResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_questions_async(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    qtype: Optional[str] = Form(None),
    qtype_query: Optional[str] = Query(None, alias="qtype"),
    difficulty: Optional[str] = Form(None),
    difficulty_query: Optional[str] = Query(None, alias="difficulty"),
    blooms_level: Optional[str] = Form(None),
    blooms_level_query: Optional[str] = Query(None, alias="blooms_level"),
    teacher_id: Optional[str] = Form(None),
    num_questions: Optional[int] = Form(None),
    num_questions_query: Optional[int] = Query(None, alias="num_questions"),
    class_id: Optional[str] = Form(None),
    subject: Optional[str] = Form(None),
    subject_query: Optional[str] = Query(None, alias="subject"),
    page_range: Optional[str] = Form(None),
    page_range_query: Optional[str] = Query(None, alias="page_range"),
    mode: Optional[str] = Form(None),
    mode_query: Optional[str] = Query(None, alias="mode"),
    x_api_key: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Initialize an asynchronous background task to extract text and generate questions.
    Ideal for large PDF documents or high-volume question generation (50+ questions).
    """
    qtype = qtype or qtype_query or "mcq"
    difficulty = difficulty or difficulty_query or "medium"
    blooms_level = blooms_level or blooms_level_query or "all"
    num_questions = num_questions or num_questions_query or 3
    subject = subject or subject_query or "General"
    page_range = page_range or page_range_query or ""
    mode = (mode or mode_query or "exam").lower()

    # Resolve caller identity and enforce usage limits & quotas
    caller_id = await resolve_and_enforce_identity(
        db=db,
        authorization=authorization,
        x_api_key=x_api_key,
        teacher_id=teacher_id
    )

    # Enforce tier-appropriate maximum questions per quiz
    num_questions = validate_question_count(caller_id, num_questions)

    if not files:
        raise AppError(status_code=400, error_code="NO_FILES", message="No files uploaded.")

    saved_files = []
    if not isinstance(files, list):
        files = [files]

    try:
        for file in files:
            if not file or not file.filename:
                continue
            if not validate_file_extension(file.filename):
                raise AppError(
                    status_code=400,
                    error_code="INVALID_FILE_TYPE",
                    message=f"File extension not allowed: {file.filename}"
                )
            file_path = await save_upload_file(file, "uploads")
            saved_files.append(file_path)

        if not saved_files:
            raise AppError(status_code=400, error_code="NO_VALID_FILES", message="No valid files saved.")

        task_id = str(uuid.uuid4())
        tasks_store[task_id] = {
            "task_id": task_id,
            "status": "queued",
            "progress": 5,
            "stage": "Task queued in background processing pipeline...",
            "questions": [],
            "error": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        # Dispatch background worker
        background_tasks.add_task(
            run_async_generation_task,
            task_id,
            saved_files,
            qtype,
            difficulty,
            num_questions,
            class_id,
            subject,
            teacher_id,
            blooms_level,
            page_range,
            caller_id,
            mode
        )
    except Exception:
        cleanup_files(saved_files)
        raise

    return {
        "task_id": task_id,
        "status": "queued",
        "progress": 5,
        "stage": "Task queued in background pipeline...",
        "message": "Async task accepted. Poll /api/tasks/status/{task_id} for progress updates."
    }


@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """
    Get the status, progress percentage, current stage message, and final result of an async generation task.
    """
    if task_id not in tasks_store:
        raise HTTPException(status_code=404, detail="Task ID not found or expired.")

    task_info = tasks_store[task_id]
    return {
        "task_id": task_info["task_id"],
        "status": task_info["status"],
        "progress": task_info["progress"],
        "stage": task_info["stage"],
        "questions": task_info.get("questions", []),
        "usage": task_info.get("usage"),
        "limit_hit_warning": task_info.get("limit_hit_warning"),
        "error": task_info.get("error"),
        "created_at": task_info["created_at"],
        "updated_at": task_info["updated_at"]
    }
