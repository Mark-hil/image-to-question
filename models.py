from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, Index, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func, text
from database import Base

class Question(Base):
    """Database model for storing questions."""
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    teacher_id = Column(String(100), nullable=True, index=True, comment="ID of the teacher who created the question")
    question_text = Column(Text, nullable=False, comment="The actual question text")
    answer_text = Column(Text, nullable=False, comment="The correct answer to the question")
    choices = Column(JSONB, nullable=True, comment="Multiple choice options (for MCQ type questions)")
    rationale = Column(Text, nullable=True, comment="Explanation or reasoning for the answer")
    qtype = Column(String(20), nullable=False, index=True, comment="Type of question: 'mcq', 'true_false', 'short_answer'")
    difficulty = Column(String(20), nullable=False, index=True, comment="Difficulty level: 'easy', 'medium', 'hard'")
    class_for = Column(String(100), nullable=True, index=True, comment="Target class/grade level")
    subject = Column(String(100), nullable=True, index=True, comment="Subject area of the question")
    metadata_ = Column('metadata', JSONB, nullable=True, comment="Additional metadata in JSON format")
    created_at = Column(DateTime(timezone=True), 
                       server_default=func.now(),
                       nullable=False,
                       comment="Timestamp when the question was created")
    updated_at = Column(DateTime(timezone=True),
                       server_default=text('CURRENT_TIMESTAMP'),
                       onupdate=func.now(),
                       nullable=False,
                       comment="Timestamp when the question was last updated")

    # Create indexes for common query patterns
    __table_args__ = (
        # Composite index for common filtering patterns
        Index('idx_question_teacher_type', 'teacher_id', 'qtype'),
        Index('idx_question_subject_difficulty', 'subject', 'difficulty'),
        # GIN index for JSONB columns to enable efficient querying
        Index('idx_metadata_gin', metadata_, postgresql_using='gin'),
        Index('idx_choices_gin', choices, postgresql_using='gin'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model instance to a dictionary."""
        return {
            'id': self.id,
            'teacher_id': self.teacher_id,
            'question_text': self.question_text,
            'answer_text': self.answer_text,
            'choices': self.choices,
            'rationale': self.rationale,
            'qtype': self.qtype,
            'difficulty': self.difficulty,
            'class_for': self.class_for,
            'subject': self.subject,
            'metadata': self.metadata_,  # Using the actual column name here
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if hasattr(self, 'updated_at') and self.updated_at else None
        }

    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<Question(id={self.id}, qtype='{self.qtype}', difficulty='{self.difficulty}')>"
