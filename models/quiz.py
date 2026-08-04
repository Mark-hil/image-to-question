import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, text
from database import Base

JSON_TYPE = JSON().with_variant(JSONB, 'postgresql')

class Quiz(Base):
    """Database model for saved Educator Quiz Banks."""
    __tablename__ = "quizzes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False, comment="Title or topic of the quiz bank")
    subject = Column(String(100), nullable=True, comment="Subject area e.g. Mathematics, Biology")
    class_id = Column(String(100), nullable=True, comment="Class or grade level e.g. Grade 10, Class 5A")
    original_file_name = Column(String(255), nullable=True, comment="Name of uploaded source file")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User")
    questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")

    def to_dict(self, include_questions: bool = True) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "subject": self.subject,
            "class_id": self.class_id,
            "original_file_name": self.original_file_name,
            "question_count": len(self.questions) if self.questions else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        if include_questions and self.questions:
            data["questions"] = [q.to_dict() for q in self.questions]
        return data

class QuizQuestion(Base):
    """Database model for individual questions contained inside a Quiz Bank."""
    __tablename__ = "quiz_questions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    quiz_id = Column(String(36), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    answer_text = Column(Text, nullable=False)
    choices = Column(JSON_TYPE, nullable=True, comment="List of choice strings")
    rationale = Column(Text, nullable=True)
    qtype = Column(String(20), nullable=False, default="mcq")
    difficulty = Column(String(20), nullable=False, default="medium")
    blooms_level = Column(String(30), nullable=True, default="Understand")
    class_id = Column(String(100), nullable=True, comment="Class or grade level")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    quiz = relationship("Quiz", back_populates="questions")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "quiz_id": self.quiz_id,
            "question_text": self.question_text,
            "question": self.question_text,
            "answer_text": self.answer_text,
            "answer": self.answer_text,
            "choices": self.choices or [],
            "rationale": self.rationale,
            "qtype": self.qtype,
            "type": self.qtype,
            "difficulty": self.difficulty,
            "blooms_level": self.blooms_level or "Understand",
            "class_id": self.class_id,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

