from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from database import Base

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(String, nullable=True)
    question_text = Column(Text, nullable=False)
    answer_text = Column(Text, nullable=False)
    choices = Column(Text, nullable=True)  # Store as JSON string
    rationale = Column(Text, nullable=True)  # Explanation for the answer
    qtype = Column(String, nullable=False)  # 'mcq', 'true_false', 'short_answer'
    difficulty = Column(String, nullable=False)  # 'easy', 'medium', 'hard'
    metadata_ = Column('metadata', Text, nullable=True)  # Store additional question data as JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now())
