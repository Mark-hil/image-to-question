"""add education_level and class_label with backfill

Revision ID: c4a89d10e5f2
Revises: db1dc4fbb266
Create Date: 2026-10-22 21:28:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column, select, update
from services.education.resolver import resolve_level_and_label


# revision identifiers, used by Alembic.
revision: str = 'c4a89d10e5f2'
down_revision: Union[str, Sequence[str], None] = 'db1dc4fbb266'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add columns to questions table
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'questions' in existing_tables:
        cols = [c['name'] for c in inspector.get_columns('questions')]
        if 'education_level' not in cols:
            op.add_column('questions', sa.Column('education_level', sa.String(32), nullable=True))
        if 'class_label' not in cols:
            op.add_column('questions', sa.Column('class_label', sa.String(100), nullable=True))
        
        # Create index if not exists
        indexes = [idx['name'] for idx in inspector.get_indexes('questions')]
        if 'idx_question_education_level' not in indexes:
            op.create_index('idx_question_education_level', 'questions', ['education_level'])

    if 'quizzes' in existing_tables:
        quiz_cols = [c['name'] for c in inspector.get_columns('quizzes')]
        if 'education_level' not in quiz_cols:
            op.add_column('quizzes', sa.Column('education_level', sa.String(32), nullable=True))
        if 'class_label' not in quiz_cols:
            op.add_column('quizzes', sa.Column('class_label', sa.String(100), nullable=True))

    if 'quiz_questions' in existing_tables:
        qq_cols = [c['name'] for c in inspector.get_columns('quiz_questions')]
        if 'education_level' not in qq_cols:
            op.add_column('quiz_questions', sa.Column('education_level', sa.String(32), nullable=True))
        if 'class_label' not in qq_cols:
            op.add_column('quiz_questions', sa.Column('class_label', sa.String(100), nullable=True))

    # 2. Backfill existing class_id data in questions table
    if 'questions' in existing_tables:
        questions_tbl = table(
            'questions',
            column('id', sa.Integer),
            column('class_id', sa.String),
            column('education_level', sa.String),
            column('class_label', sa.String)
        )
        results = conn.execute(select(questions_tbl.c.id, questions_tbl.c.class_id)).fetchall()
        for row in results:
            q_id = row[0]
            raw_class_id = row[1]
            if raw_class_id:
                level, label = resolve_level_and_label(raw_class_id)
                conn.execute(
                    update(questions_tbl)
                    .where(questions_tbl.c.id == q_id)
                    .values(
                        education_level=level.code if level else None,
                        class_label=label or raw_class_id
                    )
                )

    # 3. Backfill quizzes table
    if 'quizzes' in existing_tables:
        quizzes_tbl = table(
            'quizzes',
            column('id', sa.String),
            column('class_id', sa.String),
            column('education_level', sa.String),
            column('class_label', sa.String)
        )
        quiz_results = conn.execute(select(quizzes_tbl.c.id, quizzes_tbl.c.class_id)).fetchall()
        for qrow in quiz_results:
            quiz_id = qrow[0]
            raw_cid = qrow[1]
            if raw_cid:
                level, label = resolve_level_and_label(raw_cid)
                conn.execute(
                    update(quizzes_tbl)
                    .where(quizzes_tbl.c.id == quiz_id)
                    .values(
                        education_level=level.code if level else None,
                        class_label=label or raw_cid
                    )
                )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'questions' in existing_tables:
        indexes = [idx['name'] for idx in inspector.get_indexes('questions')]
        if 'idx_question_education_level' in indexes:
            op.drop_index('idx_question_education_level', table_name='questions')
        
        cols = [c['name'] for c in inspector.get_columns('questions')]
        if 'class_label' in cols:
            op.drop_column('questions', 'class_label')
        if 'education_level' in cols:
            op.drop_column('questions', 'education_level')

    if 'quizzes' in existing_tables:
        cols = [c['name'] for c in inspector.get_columns('quizzes')]
        if 'class_label' in cols:
            op.drop_column('quizzes', 'class_label')
        if 'education_level' in cols:
            op.drop_column('quizzes', 'education_level')

    if 'quiz_questions' in existing_tables:
        cols = [c['name'] for c in inspector.get_columns('quiz_questions')]
        if 'class_label' in cols:
            op.drop_column('quiz_questions', 'class_label')
        if 'education_level' in cols:
            op.drop_column('quiz_questions', 'education_level')
