"""create_song_educational_metadata_columns

Revision ID: 23f9a12e5d54
Revises: 4394dfc92b94
Create Date: 2026-08-02 22:16:54.630071

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '23f9a12e5d54'
down_revision: Union[str, Sequence[str], None] = '4394dfc92b94'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('songs', sa.Column('educational_category', sa.String(length=100), nullable=True))
    op.add_column('songs', sa.Column('learning_objectives', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('songs', sa.Column('skills_required', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('songs', sa.Column('skills_reinforced', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('songs', sa.Column('prerequisite_lesson_slugs', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('songs', sa.Column('mastery_threshold_percentage', sa.Float(), nullable=True))
    op.add_column('songs', sa.Column('ai_coaching_focus', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('songs', sa.Column('teacher_notes', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('songs', 'teacher_notes')
    op.drop_column('songs', 'ai_coaching_focus')
    op.drop_column('songs', 'mastery_threshold_percentage')
    op.drop_column('songs', 'prerequisite_lesson_slugs')
    op.drop_column('songs', 'skills_reinforced')
    op.drop_column('songs', 'skills_required')
    op.drop_column('songs', 'learning_objectives')
    op.drop_column('songs', 'educational_category')
