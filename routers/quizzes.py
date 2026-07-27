import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database import get_db
from models.user import User
from models.quiz import Quiz, QuizQuestion
from utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

class CreateQuestionInput(BaseModel):
    question_text: Optional[str] = None
    question: Optional[str] = None
    answer_text: Optional[str] = None
    answer: Optional[str] = None
    choices: Optional[List[str]] = None
    rationale: Optional[str] = None
    qtype: Optional[str] = "mcq"
    difficulty: Optional[str] = "medium"

class CreateQuizRequest(BaseModel):
    title: str
    subject: Optional[str] = "General"
    original_file_name: Optional[str] = None
    questions: List[CreateQuestionInput]

class UpdateQuestionInput(BaseModel):
    question_text: Optional[str] = None
    answer_text: Optional[str] = None
    choices: Optional[List[str]] = None
    rationale: Optional[str] = None
    difficulty: Optional[str] = None

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_quiz(
    body: CreateQuizRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Save a set of generated questions as a named Quiz Bank."""
    if not body.questions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quiz must contain at least 1 question."
        )

    new_quiz = Quiz(
        user_id=current_user.id,
        title=body.title,
        subject=body.subject or "General",
        original_file_name=body.original_file_name
    )
    db.add(new_quiz)
    await db.flush()

    quiz_questions = []
    for item in body.questions:
        q_text = item.question_text or item.question
        a_text = item.answer_text or item.answer
        if not q_text:
            continue
        q = QuizQuestion(
            quiz_id=new_quiz.id,
            question_text=q_text,
            answer_text=a_text or "",
            choices=item.choices,
            rationale=item.rationale,
            qtype=item.qtype or "mcq",
            difficulty=item.difficulty or "medium"
        )
        db.add(q)
        quiz_questions.append(q)

    await db.commit()

    # Re-fetch quiz with questions loaded
    res = await db.execute(
        select(Quiz).options(selectinload(Quiz.questions)).where(Quiz.id == new_quiz.id)
    )
    saved_quiz = res.scalar_one()

    return {"message": "Quiz saved successfully", "quiz": saved_quiz.to_dict(include_questions=True)}

@router.get("", status_code=status.HTTP_200_OK)
async def list_quizzes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all saved quiz banks for current user."""
    res = await db.execute(
        select(Quiz)
        .options(selectinload(Quiz.questions))
        .where(Quiz.user_id == current_user.id)
        .order_by(Quiz.created_at.desc())
    )
    quizzes = res.scalars().all()
    return {"quizzes": [q.to_dict(include_questions=True) for q in quizzes]}

@router.get("/{quiz_id}", status_code=status.HTTP_200_OK)
async def get_quiz(
    quiz_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve a single quiz bank with full question details."""
    res = await db.execute(
        select(Quiz)
        .options(selectinload(Quiz.questions))
        .where(Quiz.id == quiz_id, Quiz.user_id == current_user.id)
    )
    quiz = res.scalar_one_or_none()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    return {"quiz": quiz.to_dict(include_questions=True)}

@router.put("/{quiz_id}/questions/{q_id}", status_code=status.HTTP_200_OK)
async def update_question(
    quiz_id: str,
    q_id: str,
    body: UpdateQuestionInput,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a specific question inside a quiz bank."""
    # Ensure quiz belongs to user
    q_res = await db.execute(
        select(QuizQuestion)
        .join(Quiz)
        .where(QuizQuestion.id == q_id, QuizQuestion.quiz_id == quiz_id, Quiz.user_id == current_user.id)
    )
    q = q_res.scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    if body.question_text is not None:
        q.question_text = body.question_text
    if body.answer_text is not None:
        q.answer_text = body.answer_text
    if body.choices is not None:
        q.choices = body.choices
    if body.rationale is not None:
        q.rationale = body.rationale
    if body.difficulty is not None:
        q.difficulty = body.difficulty

    await db.commit()
    await db.refresh(q)
    return {"message": "Question updated successfully", "question": q.to_dict()}

@router.delete("/{quiz_id}", status_code=status.HTTP_200_OK)
async def delete_quiz(
    quiz_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a saved quiz bank."""
    res = await db.execute(
        select(Quiz).where(Quiz.id == quiz_id, Quiz.user_id == current_user.id)
    )
    quiz = res.scalar_one_or_none()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    await db.delete(quiz)
    await db.commit()
    return {"message": "Quiz deleted successfully"}

import urllib.parse
from fastapi.responses import Response
from services.export_service import ExportService

def make_download_response(content: Any, filename: str, media_type: str) -> Response:
    """Build HTTP Response with RFC 6266 / RFC 5987 compliant Content-Disposition header."""
    safe_ascii = "".join(c if c.isalnum() or c in "._-" else "_" for c in filename)
    encoded = urllib.parse.quote(filename)
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{safe_ascii}"; filename*=UTF-8\'\'{encoded}'
        }
    )

@router.get("/{quiz_id}/export/qti", status_code=status.HTTP_200_OK)
async def export_quiz_qti(
    quiz_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export quiz as Canvas QTI 2.1 zip package."""
    res = await db.execute(
        select(Quiz)
        .options(selectinload(Quiz.questions))
        .where(Quiz.id == quiz_id, Quiz.user_id == current_user.id)
    )
    quiz = res.scalar_one_or_none()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    questions_data = [q.to_dict() for q in quiz.questions]
    zip_bytes = ExportService.generate_canvas_qti_zip(quiz.title, questions_data)
    filename = f"{quiz.title.replace(' ', '_')}_qti.zip"
    return make_download_response(zip_bytes, filename, "application/zip")

@router.get("/{quiz_id}/export/text", status_code=status.HTTP_200_OK)
async def export_quiz_text(
    quiz_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export quiz as printable plain text with answer key."""
    res = await db.execute(
        select(Quiz)
        .options(selectinload(Quiz.questions))
        .where(Quiz.id == quiz_id, Quiz.user_id == current_user.id)
    )
    quiz = res.scalar_one_or_none()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    questions_data = [q.to_dict() for q in quiz.questions]
    text_content = ExportService.generate_printable_text(quiz.title, questions_data)
    filename = f"{quiz.title.replace(' ', '_')}.txt"
    return make_download_response(text_content, filename, "text/plain")

@router.get("/{quiz_id}/export/docx", status_code=status.HTTP_200_OK)
async def export_quiz_docx(
    quiz_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export quiz as Microsoft Word document (.docx)."""
    res = await db.execute(
        select(Quiz)
        .options(selectinload(Quiz.questions))
        .where(Quiz.id == quiz_id, Quiz.user_id == current_user.id)
    )
    quiz = res.scalar_one_or_none()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    questions_data = [q.to_dict() for q in quiz.questions]
    docx_bytes = ExportService.generate_docx(quiz.title, questions_data)
    filename = f"{quiz.title.replace(' ', '_')}.docx"
    return make_download_response(
        docx_bytes,
        filename,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

class DirectExportRequest(BaseModel):
    title: str
    export_format: str = "qti"  # "qti", "text", or "docx"
    questions: List[CreateQuestionInput]

@router.post("/export/direct", status_code=status.HTTP_200_OK)
async def export_direct(body: DirectExportRequest):
    """Directly export unsaved generated questions to Canvas QTI zip, printable text, or Word docx."""
    if not body.questions:
        raise HTTPException(status_code=400, detail="No questions provided for export.")

    questions_data = [q.model_dump() for q in body.questions]
    safe_title = body.title.replace(' ', '_')

    if body.export_format == "docx":
        docx_bytes = ExportService.generate_docx(body.title, questions_data)
        return make_download_response(
            docx_bytes,
            f"{safe_title}.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    elif body.export_format == "qti":
        zip_bytes = ExportService.generate_canvas_qti_zip(body.title, questions_data)
        return make_download_response(
            zip_bytes,
            f"{safe_title}_qti.zip",
            "application/zip"
        )
    else:
        text_content = ExportService.generate_printable_text(body.title, questions_data)
        return make_download_response(
            text_content,
            f"{safe_title}.txt",
            "text/plain"
        )


