import os
import json
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session
from database import get_db
from services import ocr_service, vision_service, qgen_service
import crud, schemas

router = APIRouter()

class GenerateRequest(BaseModel):
    file_paths: List[str]
    qtype: str
    difficulty: str
    teacher_id: str = None

@router.post("/from-images")
async def generate_from_images(req: GenerateRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Validate files exist
    for p in req.file_paths:
        if not os.path.exists(p):
            raise HTTPException(status_code=400, detail=f"File not found: {p}")

    # Process synchronously (you can offload to background tasks or Celery)
    accumulated_text = []
    accumulated_desc = []
    for p in req.file_paths:
        text = ocr_service.extract_text_from_path(p)
        desc = await vision_service.describe_image_stub(p)
        accumulated_text.append(text)
        accumulated_desc.append(desc)

    full_text = "\n\n".join(accumulated_text)
    full_desc = "\n\n".join(accumulated_desc)

    qgen_output = qgen_service.generate_questions_from_content(full_text, full_desc, req.qtype, req.difficulty)

    # Try to parse qgen_output as JSON; if parsing fails, store raw
    try:
        parsed = json.loads(qgen_output)
    except Exception:
        # fallback: store as a single question with raw output
        parsed = [{"question": "(auto-generated) Please inspect output","answer": qgen_output}]

    created = []
    for item in parsed:
        qtext = item.get("question") or item.get("prompt") or str(item)
        ans = item.get("answer") or item.get("answers") or ""
        q = schemas.QuestionCreate(
            teacher_id=req.teacher_id,
            question_text=qtext,
            answer_text=ans,
            qtype=req.qtype,
            difficulty=req.difficulty,
            metadata=str(item)
        )
        db_q = crud.create_question(db, q)
        created.append(db_q)

    return {"created": [ {"id": c.id, "question": c.question_text} for c in created ] }
