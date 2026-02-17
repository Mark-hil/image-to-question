from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, delete, update
from sqlalchemy.orm import selectinload
import json
from datetime import datetime

from database import get_db
from models import Question
from pydantic import BaseModel

router = APIRouter()

# Pydantic models for request/response
class QuestionUpdate(BaseModel):
    question_text: Optional[str] = None
    answer_text: Optional[str] = None
    choices: Optional[List[str]] = None
    rationale: Optional[str] = None
    difficulty: Optional[str] = None
    class_id: Optional[str] = None
    subject: Optional[str] = None

class QuestionResponse(BaseModel):
    id: int
    teacher_id: Optional[str]
    question_text: str
    answer_text: str
    choices: Optional[List[str]]
    rationale: Optional[str]
    qtype: str
    difficulty: str
    class_id: Optional[str]
    subject: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: Optional[str]
    updated_at: Optional[str]
    
    class Config:
        json_encoders = {
            # Handle datetime serialization if needed
        }

class QuestionListResponse(BaseModel):
    questions: List[QuestionResponse]
    total: int
    page: int
    size: int
    pages: int

class DeleteResponse(BaseModel):
    message: str
    deleted_count: int

class UpdateResponse(BaseModel):
    message: str
    question: QuestionResponse

@router.get("/questions/by-teacher/{teacher_id}", response_model=QuestionListResponse, summary="Get Questions by Teacher")
async def get_questions_by_teacher(
    teacher_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Questions per page"),
    db: AsyncSession = Depends(get_db)
):
    """
    👨‍🏫 **Get Questions by Teacher ID**
    
    Retrieve all questions created by a specific teacher.
    
    **Example:** `/api/questions/by-teacher/3`
    
    **Parameters:**
    - **teacher_id** (path): Teacher's unique identifier
    - **page**: Pagination page number (default: 1)
    - **size**: Questions per page (default: 10, max: 100)
    """
    return await get_questions(
        teacher_id=teacher_id,
        qtype=None,
        subject=None,
        class_id=None,
        difficulty=None,
        page=page,
        size=size,
        search=None,
        db=db
    )

@router.get("/questions/by-subject/{subject}", response_model=QuestionListResponse, summary="Get Questions by Subject")
async def get_questions_by_subject(
    subject: str,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Questions per page"),
    db: AsyncSession = Depends(get_db)
):
    """
    📖 **Get Questions by Subject**
    
    Retrieve all questions for a specific subject.
    
    **Examples:** 
    - `/api/questions/by-subject/english`
    - `/api/questions/by-subject/math`
    - `/api/questions/by-subject/science`
    
    **Parameters:**
    - **subject** (path): Subject name (english, math, science, etc.)
    - **page**: Pagination page number (default: 1)
    - **size**: Questions per page (default: 10, max: 100)
    """
    return await get_questions(
        teacher_id=None,
        qtype=None,
        subject=subject,
        class_id=None,
        difficulty=None,
        page=page,
        size=size,
        search=None,
        db=db
    )

@router.get("/questions/by-class/{class_id}", response_model=QuestionListResponse, summary="Get Questions by Class")
async def get_questions_by_class(
    class_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Questions per page"),
    db: AsyncSession = Depends(get_db)
):
    """
    🎓 **Get Questions by Class/Grade**
    
    Retrieve all questions for a specific class or grade level.
    
    **Examples:**
    - `/api/questions/by-class/3`
    - `/api/questions/by-class/5`
    - `/api/questions/by-class/grade-10`
    
    **Parameters:**
    - **class_id** (path): Class/grade identifier
    - **page**: Pagination page number (default: 1)
    - **size**: Questions per page (default: 10, max: 100)
    """
    return await get_questions(
        teacher_id=None,
        qtype=None,
        subject=None,
        class_id=class_id,
        difficulty=None,
        page=page,
        size=size,
        search=None,
        db=db
    )

@router.get("/questions/by-difficulty/{difficulty}", response_model=QuestionListResponse, summary="Get Questions by Difficulty")
async def get_questions_by_difficulty(
    difficulty: str,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Questions per page"),
    db: AsyncSession = Depends(get_db)
):
    """
    📊 **Get Questions by Difficulty Level**
    
    Retrieve all questions at a specific difficulty level.
    
    **Examples:**
    - `/api/questions/by-difficulty/easy`
    - `/api/questions/by-difficulty/medium`
    - `/api/questions/by-difficulty/hard`
    
    **Parameters:**
    - **difficulty** (path): Difficulty level - `easy`, `medium`, or `hard`
    - **page**: Pagination page number (default: 1)
    - **size**: Questions per page (default: 10, max: 100)
    """
    return await get_questions(
        teacher_id=None,
        qtype=None,
        subject=None,
        class_id=None,
        difficulty=difficulty,
        page=page,
        size=size,
        search=None,
        db=db
    )

@router.get("/questions/search", response_model=QuestionListResponse, summary="Search Questions")
async def search_questions(
    q: str = Query(..., description="Search query text"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Questions per page"),
    db: AsyncSession = Depends(get_db)
):
    """
    🔍 **Search Questions**
    
    Search for questions containing specific text in question or answer fields.
    
    **Example:** `/api/questions/search?q=hands`
    
    **Parameters:**
    - **q** (query): Search text to find in questions/answers
    - **page**: Pagination page number (default: 1)
    - **size**: Questions per page (default: 10, max: 100)
    
    **Searches through:**
    - Question text
    - Answer text
    """
    return await get_questions(
        teacher_id=None,
        qtype=None,
        subject=None,
        class_id=None,
        difficulty=None,
        page=page,
        size=size,
        search=q,
        db=db
    )

@router.get("/questions", response_model=QuestionListResponse, summary="List Questions with Filters")
async def get_questions(
    teacher_id: Optional[str] = Query(None, description="Filter by teacher ID who created the questions"),
    qtype: Optional[str] = Query(None, description="Filter by question type (mcq, true_false, short_answer)"),
    subject: Optional[str] = Query(None, description="Filter by subject (e.g., english, math, science)"),
    class_id: Optional[str] = Query(None, description="Filter by class/grade level (e.g., 3, 4, 5)"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty level (easy, medium, hard)"),
    page: int = Query(1, ge=1, description="Page number for pagination (starts from 1)"),
    size: int = Query(10, ge=1, le=100, description="Number of questions per page (max 100)"),
    search: Optional[str] = Query(None, description="Search text in question and answer fields"),
    db: AsyncSession = Depends(get_db)
):
    """
    **List Questions with Advanced Filtering**
    
    Use this endpoint to retrieve questions from the database with optional filters.
    
    **Common Use Cases:**
    - Get all questions: `/api/questions`
    - Get questions by teacher: `/api/questions?teacher_id=3`
    - Get questions by subject: `/api/questions?subject=english`
    - Get questions by class: `/api/questions?class_id=3`
    - Get questions by difficulty: `/api/questions?difficulty=easy`
    - Combine filters: `/api/questions?teacher_id=3&subject=english&class_id=3`
    - Search questions: `/api/questions?search=hands`
    
    **Filter Parameters:**
    - **teacher_id**: Questions created by specific teacher
    - **qtype**: Question type - `mcq`, `true_false`, or `short_answer`
    - **subject**: Subject area - `english`, `math`, `science`, etc.
    - **class_id**: Target class/grade - `1`, `2`, `3`, `4`, `5`, `6`, etc.
    - **difficulty**: Difficulty level - `easy`, `medium`, or `hard`
    - **search**: Text search in question and answer content
    - **page**: Pagination page number (default: 1)
    - **size**: Results per page (default: 10, max: 100)
    
    **Response includes:**
    - `questions`: Array of question objects
    - `total`: Total number of questions matching filters
    - `page`: Current page number
    - `size`: Questions per page
    - `pages`: Total number of pages
    """
    try:
        # Build query with filters
        stmt = select(Question)
        
        # Apply filters
        if teacher_id:
            stmt = stmt.where(Question.teacher_id == teacher_id)
        
        if qtype:
            stmt = stmt.where(Question.qtype == qtype)
        
        if subject:
            stmt = stmt.where(Question.subject.ilike(f"%{subject}%"))
        
        if class_id:
            stmt = stmt.where(Question.class_id == class_id)
        
        if difficulty:
            stmt = stmt.where(Question.difficulty == difficulty)
        
        if search:
            search_pattern = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Question.question_text.ilike(search_pattern),
                    Question.answer_text.ilike(search_pattern)
                )
            )
        
        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await db.execute(count_stmt)
        total = total_result.scalar()
        
        # Calculate pagination
        offset = (page - 1) * size
        pages = (total + size - 1) // size  # Ceiling division
        
        # Get paginated results
        stmt = stmt.offset(offset).limit(size)
        result = await db.execute(stmt)
        questions = result.scalars().all()
        
        # Convert to response format
        question_responses = []
        for q in questions:
            question_dict = q.to_dict()
            # Parse choices if it's a JSON string
            if isinstance(question_dict.get('choices'), str):
                try:
                    question_dict['choices'] = json.loads(question_dict['choices'])
                except:
                    question_dict['choices'] = []
            
            # Parse metadata if it's a JSON string
            if isinstance(question_dict.get('metadata'), str):
                try:
                    question_dict['metadata'] = json.loads(question_dict['metadata'])
                except:
                    question_dict['metadata'] = {}
            
            question_responses.append(QuestionResponse(**question_dict))
        
        return QuestionListResponse(
            questions=question_responses,
            total=total,
            page=page,
            size=size,
            pages=pages
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving questions: {str(e)}"
        )

@router.delete("/questions", response_model=DeleteResponse)
async def delete_questions(
    teacher_id: Optional[str] = Query(None, description="Filter by teacher ID"),
    qtype: Optional[str] = Query(None, description="Filter by question type"),
    subject: Optional[str] = Query(None, description="Filter by subject"),
    class_id: Optional[str] = Query(None, description="Filter by class/grade"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
    question_ids: Optional[str] = Query(None, description="Comma-separated question IDs to delete"),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete questions based on filters or specific IDs.
    
    You can either:
    1. Use filters to delete multiple questions matching criteria
    2. Use question_ids to delete specific questions by their IDs
    
    WARNING: This operation is irreversible!
    """
    try:
        # Build query
        stmt = select(Question)
        
        # If specific question IDs are provided, use those
        if question_ids:
            try:
                ids = [int(id.strip()) for id in question_ids.split(',')]
                stmt = stmt.where(Question.id.in_(ids))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid question IDs format. Use comma-separated integers."
                )
        else:
            # Apply filters
            if teacher_id:
                stmt = stmt.where(Question.teacher_id == teacher_id)
            
            if qtype:
                stmt = stmt.where(Question.qtype == qtype)
            
            if subject:
                stmt = stmt.where(Question.subject.ilike(f"%{subject}%"))
            
            if class_id:
                stmt = stmt.where(Question.class_id == class_id)
            
            if difficulty:
                stmt = stmt.where(Question.difficulty == difficulty)
        
        # Get count before deletion
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_result = await db.execute(count_stmt)
        count = count_result.scalar()
        
        if count == 0:
            return DeleteResponse(
                message="No questions found matching the criteria",
                deleted_count=0
            )
        
        # Perform deletion
        delete_stmt = delete(Question).where(Question.id.in_(
            select(Question.id).select_from(stmt.subquery())
        ))
        await db.execute(delete_stmt)
        await db.commit()
        
        return DeleteResponse(
            message=f"Successfully deleted {count} question(s)",
            deleted_count=count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting questions: {str(e)}"
        )

@router.put("/questions/{question_id}", response_model=UpdateResponse)
async def update_question(
    question_id: int,
    question_update: QuestionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a specific question by ID.
    
    Only provided fields will be updated. Other fields remain unchanged.
    """
    try:
        # Get the question
        stmt = select(Question).where(Question.id == question_id)
        result = await db.execute(stmt)
        question = result.scalar_one_or_none()
        
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Question with ID {question_id} not found"
            )
        
        # Update fields if provided
        update_data = question_update.dict(exclude_unset=True)
        
        if 'choices' in update_data and update_data['choices'] is not None:
            # Convert choices list to JSON
            update_data['choices'] = json.dumps(update_data['choices'])
        
        # Apply updates
        for field, value in update_data.items():
            if hasattr(question, field):
                setattr(question, field, value)
        
        # Update the updated_at timestamp
        question.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(question)
        
        # Convert to response format
        question_dict = question.to_dict()
        if isinstance(question_dict.get('choices'), str):
            try:
                question_dict['choices'] = json.loads(question_dict['choices'])
            except:
                question_dict['choices'] = []
        
        # Parse metadata if it's a JSON string
        if isinstance(question_dict.get('metadata'), str):
            try:
                question_dict['metadata'] = json.loads(question_dict['metadata'])
            except:
                question_dict['metadata'] = {}
        
        return UpdateResponse(
            message="Question updated successfully",
            question=QuestionResponse(**question_dict)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating question: {str(e)}"
        )

@router.get("/questions/{question_id}", response_model=QuestionResponse)
async def get_question(
    question_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific question by ID.
    """
    try:
        stmt = select(Question).where(Question.id == question_id)
        result = await db.execute(stmt)
        question = result.scalar_one_or_none()
        
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Question with ID {question_id} not found"
            )
        
        # Convert to response format
        question_dict = question.to_dict()
        if isinstance(question_dict.get('choices'), str):
            try:
                question_dict['choices'] = json.loads(question_dict['choices'])
            except:
                question_dict['choices'] = []
        
        # Parse metadata if it's a JSON string
        if isinstance(question_dict.get('metadata'), str):
            try:
                question_dict['metadata'] = json.loads(question_dict['metadata'])
            except:
                question_dict['metadata'] = {}
        
        return QuestionResponse(**question_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving question: {str(e)}"
        )

@router.delete("/questions/{question_id}", response_model=DeleteResponse)
async def delete_question(
    question_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a specific question by ID.
    
    WARNING: This operation is irreversible!
    """
    try:
        # Get the question first to check if it exists
        stmt = select(Question).where(Question.id == question_id)
        result = await db.execute(stmt)
        question = result.scalar_one_or_none()
        
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Question with ID {question_id} not found"
            )
        
        # Delete the question
        delete_stmt = delete(Question).where(Question.id == question_id)
        await db.execute(delete_stmt)
        await db.commit()
        
        return DeleteResponse(
            message=f"Question with ID {question_id} deleted successfully",
            deleted_count=1
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting question: {str(e)}"
        )
