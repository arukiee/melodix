"""persist analyzed-song practice session state

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
"""

from typing import Sequence, Union

from alembic import op
import app
import sqlalchemy as sa


revision: str = "b7c8d9e0f1a2"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "student_learning_states",
        sa.Column("practice_sessions", app.models.json_type.ConditionalJSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("student_learning_states", "practice_sessions")
