"""add missing song fields (album, artwork_url, mood, etc.)

Revision ID: a8d29f01e123
Revises: f994f8a9dc9e
Create Date: 2026-09-22 02:05:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a8d29f01e123'
down_revision: Union[str, Sequence[str], None] = 'f994f8a9dc9e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column("songs", sa.Column("album", sa.String(255), nullable=True))
    op.add_column("songs", sa.Column("mood", sa.String(100), nullable=True))
    op.add_column("songs", sa.Column("language", sa.String(80), nullable=True))
    op.add_column("songs", sa.Column("artwork_url", sa.String(1024), nullable=True))
    op.add_column("songs", sa.Column("skills", sa.JSON(), nullable=True))
    op.add_column("songs", sa.Column("available_arrangements", sa.JSON(), nullable=True))
    op.add_column("songs", sa.Column("is_learnable", sa.Boolean(), server_default=sa.text("true"), nullable=True))
    op.add_column("songs", sa.Column("tempo", sa.Integer(), nullable=True))
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    op.execute("ALTER TABLE songs ADD COLUMN IF NOT EXISTS embedding vector(768);")

def downgrade() -> None:
    op.drop_column("songs", "embedding")
    op.drop_column("songs", "tempo")
    op.drop_column("songs", "is_learnable")
    op.drop_column("songs", "available_arrangements")
    op.drop_column("songs", "skills")
    op.drop_column("songs", "artwork_url")
    op.drop_column("songs", "language")
    op.drop_column("songs", "mood")
    op.drop_column("songs", "album")

