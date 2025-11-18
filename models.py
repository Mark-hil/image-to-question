from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from database import Base

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(String, nullable=True)
    question_text = Column(Text, nullable=False)
    answer_text = Column(Text, nullable=False)
    qtype = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)
    metadata_ = Column('metadata', Text, nullable=True)  # Using 'metadata' as the actual column name
    created_at = Column(DateTime(timezone=True), server_default=func.now())
