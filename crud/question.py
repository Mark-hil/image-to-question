from sqlalchemy.orm import Session
import models, schemas

def create_question(db: Session, q: schemas.QuestionCreate):
    db_q = models.Question(
        teacher_id=q.teacher_id,
        question_text=q.question_text,
        answer_text=q.answer_text,
        qtype=q.qtype,
        difficulty=q.difficulty,
        metadata_=q.metadata
    )
    db.add(db_q)
    db.commit()
    db.refresh(db_q)
    return db_q

def get_questions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Question).offset(skip).limit(limit).all()
