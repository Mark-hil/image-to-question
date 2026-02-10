"""add_class_for_and_subject_to_questions

Revision ID: fe38474cceef
Revises: ed96411c8d70
Create Date: 2025-12-05 22:55:22.391525

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fe38474cceef'
down_revision: Union[str, Sequence[str], None] = 'ed96411c8d70'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
