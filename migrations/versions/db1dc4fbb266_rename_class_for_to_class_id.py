"""rename class_for to class_id

Revision ID: db1dc4fbb266
Revises: 248ad8b8d52c
Create Date: 2026-02-12 11:11:42.627052

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'db1dc4fbb266'
down_revision: Union[str, Sequence[str], None] = '248ad8b8d52c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: rename class_for column to class_id in questions table."""
    # Rename the column from class_for to class_id
    op.alter_column('questions', 'class_for', new_column_name='class_id')


def downgrade() -> None:
    """Downgrade schema: rename class_id column back to class_for in questions table."""
    # Rename the column back from class_id to class_for
    op.alter_column('questions', 'class_id', new_column_name='class_for')
