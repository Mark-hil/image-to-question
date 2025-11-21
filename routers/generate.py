import os
import sys
import json
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db
from services import ocr_service, vision_service, qgen_service
from models import Question  # Import directly from models
import crud
import schemas

router = APIRouter()

class GenerateRequest(BaseModel):
    file_paths: List[str]
    qtype: str
    difficulty: str
    teacher_id: str = None
    num_questions: int = 3
    

@router.post("/from-images")
async def generate_from_images(req: GenerateRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Validate files exist
    for p in req.file_paths:
        if not os.path.exists(p):
            raise HTTPException(status_code=400, detail=f"File not found: {p}")

    # Process images to extract text and descriptions
    accumulated_text = []
    accumulated_desc = []
    for p in req.file_paths:
        text = ocr_service.extract_text_from_path(p)
        desc = await vision_service.describe_image_stub(p)
        accumulated_text.append(text)
        accumulated_desc.append(desc)

    full_text = "\n\n".join(accumulated_text)
    full_desc = "\n\n".join(accumulated_desc)

    # Generate questions
    qgen_output = qgen_service.generate_questions_from_content(
        text=full_text,
        refined_text=full_text,
        description=full_desc,
        qtype=req.qtype,
        difficulty=req.difficulty,
        num_questions=req.num_questions
    )

    try:
        # Parse the questions
        questions = json.loads(qgen_output)
        
        # If we got an error message, return it
        if isinstance(questions, list) and len(questions) > 0 and "error" in questions[0]:
            raise HTTPException(status_code=400, detail=questions[0]["error"])
            
        # Save questions to database and prepare response
        created_questions = []
        for q in questions:
            # Create a new question in the database
            db_question = Question(
                teacher_id=req.teacher_id,
                question_text=q["question"],
                answer_text=q["answer"],
                choices=json.dumps(q.get("choices", [])),
                rationale=q.get("rationale", ""),
                qtype=req.qtype,
                difficulty=req.difficulty,
                metadata_=json.dumps(q)  # Store the full question data
            )
            db.add(db_question)
            db.commit()
            db.refresh(db_question)
            
            # Prepare response with all question data
            response_question = {
                "id": db_question.id,
                "question": db_question.question_text,
                "answer": db_question.answer_text,
                "qtype": db_question.qtype,
                "difficulty": db_question.difficulty
            }
            
            # Add choices and rationale if they exist
            if db_question.choices:
                response_question["choices"] = json.loads(db_question.choices)
            if db_question.rationale:
                response_question["rationale"] = db_question.rationale
                
            created_questions.append(response_question)
            
        return {"created": created_questions}
        
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse questions from the model: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating questions: {str(e)}"
        )
