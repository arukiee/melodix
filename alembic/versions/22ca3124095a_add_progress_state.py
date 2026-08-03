"""add progress_state

Revision ID: 22ca3124095a
Revises: 05028df99758
Create Date: 2026-08-04 00:33:50.341217

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '22ca3124095a'
down_revision: Union[str, Sequence[str], None] = '05028df99758'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create progress_state table."""
    op.create_table(
        "progress_state",
        sa.Column("id", sa.String(36), primary_key=True, default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("lesson_id", sa.UUID(as_uuid=True), sa.ForeignKey("curriculum_lessons.id"), nullable=False, index=True),
        sa.Column("last_note_index", sa.Integer, nullable=False, server_default="0"),
        sa.Column("attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("confidence", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    """Drop progress_state table."""
    op.drop_table("progress_state")
