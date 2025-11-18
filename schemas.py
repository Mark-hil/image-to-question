from pydantic import BaseModel
from typing import Optional

class QuestionCreate(BaseModel):
    teacher_id: Optional[str]
    question_text: str
    answer_text: str
    qtype: str
    difficulty: str
    metadata: Optional[str] = None

class QuestionOut(BaseModel):
    id: int
    teacher_id: Optional[str]
    question_text: str
    answer_text: str
    qtype: str
    difficulty: str
    metadata: Optional[str] = None

    class Config:
        orm_mode = True
