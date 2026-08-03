"""add core domain tables and embeddings

Revision ID: f994f8a9dc9e
Revises: 22ca3124095a
Create Date: 2026-08-04 00:44:09.876318

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f994f8a9dc9e'
down_revision: Union[str, Sequence[str], None] = '22ca3124095a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create core domain tables and embedding columns."""
    # Ensure clean start: drop tables if they exist
    op.execute('DROP TABLE IF EXISTS roles')
    op.execute('DROP TABLE IF EXISTS user_roles')
    op.execute('DROP TABLE IF EXISTS songs')
    # Roles
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(20), unique=True, nullable=False),
    )
    # Association table user_roles
    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role_id", sa.Integer, sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    )
    # Lesson content (one-to-one with curriculum_lessons)
    op.create_table(
        "lesson_contents",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("lesson_id", sa.UUID(as_uuid=True), sa.ForeignKey("curriculum_lessons.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("content", sa.JSON, nullable=False),
    )
    # Practice sessions
    op.create_table(
        "practice_sessions",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("lesson_id", sa.UUID(as_uuid=True), sa.ForeignKey("curriculum_lessons.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("song_id", sa.UUID(as_uuid=True), sa.ForeignKey("songs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="IN_PROGRESS"),
        sa.Column("audio_recording_uri", sa.String, nullable=True),
        # Metrics
        sa.Column("accuracy", sa.Float, nullable=True),
        sa.Column("tempo", sa.Float, nullable=True),
        sa.Column("average_latency", sa.Float, nullable=True),
        sa.Column("pitch_score", sa.Float, nullable=True),
        sa.Column("rhythm_score", sa.Float, nullable=True),
        sa.Column("expression_score", sa.Float, nullable=True),
        sa.Column("duration", sa.Float, nullable=True),
        sa.Column("mistake_count", sa.Integer, nullable=True),
        sa.Column("completion_percentage", sa.Float, nullable=True),
        sa.Column("notes_played", sa.Integer, nullable=True),
        sa.Column("notes_expected", sa.Integer, nullable=True),
        sa.Column("correct_notes", sa.Integer, nullable=True),
        sa.Column("analysis_json", sa.JSON, nullable=True),
        sa.Column("practice_embedding", sa.JSON, nullable=True),
    )
    # Create songs table with required columns
    op.create_table(
        "songs",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column("instrument", sa.String(50), nullable=True),
        sa.Column("difficulty", sa.Enum("BEGINNER", "INTERMEDIATE", "ADVANCED", name="songdifficulty"), nullable=True),
        sa.Column("genre", sa.String(100), nullable=True),
        sa.Column("audio_file_uri", sa.String, nullable=True),
        sa.Column("song_embedding", sa.JSON, nullable=True),
    )
    # Add embedding to curriculum_lessons (lesson_embedding)
    op.add_column("curriculum_lessons", sa.Column("lesson_embedding", sa.JSON, nullable=True))

def downgrade() -> None:
    """Drop core domain tables and columns."""
    # Revert song extensions
    op.drop_column("curriculum_lessons", "lesson_embedding")
    op.drop_column("songs", "song_embedding")
    op.drop_column("songs", "genre")
    op.drop_column("songs", "difficulty")
    op.drop_column("songs", "instrument")
    op.drop_column("songs", "audio_file_uri")
    # Drop practice_sessions
    op.drop_table("practice_sessions")
    # Drop lesson_contents
    op.drop_table("lesson_contents")
    # Drop association and roles
    op.drop_table("user_roles")
    # Drop tables if they exist during downgrade
    op.drop_table("songs")
    op.drop_table("roles")




