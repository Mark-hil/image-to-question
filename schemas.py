from pydantic import BaseModel
from typing import Optional

class QuestionCreate(BaseModel):
    teacher_id: Optional[str]
    question_text: str
    answer_text: str
    qtype: str
    difficulty: str
    class_for: Optional[str] = None  # e.g., 'Grade 5', 'Class 10'
    subject: Optional[str] = None    # e.g., 'Math', 'Science', 'History'
    metadata: Optional[dict] = None

class QuestionOut(BaseModel):
    id: int
    teacher_id: Optional[str]
    question_text: str
    answer_text: str
    qtype: str
    difficulty: str
    class_for: Optional[str] = None
    subject: Optional[str] = None
    metadata: Optional[dict] = None

    class Config:
        from_attributes = True  # Replaces orm_mode in Pydantic v2
        # orm_mode = True  # Kept for backward compatibility
