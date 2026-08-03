"""create curriculum schema

Revision ID: 05028df99758
Revises: 
Create Date: 2026-08-03 03:57:27.917995

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '05028df99758'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema by creating curriculum tables."""
    # LearningPath table
    op.create_table(
        "learning_paths",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(300), nullable=False, unique=True, index=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("target_role", sa.String(50), nullable=False, server_default="STUDENT"),
        sa.Column("display_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_published", sa.Boolean, nullable=False, server_default=sa.text('1')),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )

    # CurriculumModule table
    op.create_table(
        "curriculum_modules",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column("path_id", sa.UUID(as_uuid=True), sa.ForeignKey("learning_paths.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(300), nullable=False, unique=True, index=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("display_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_unlocked_by_default", sa.Boolean, nullable=False, server_default=sa.text('0')),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # CurriculumUnit table
    op.create_table(
        "curriculum_units",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column("module_id", sa.UUID(as_uuid=True), sa.ForeignKey("curriculum_modules.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(300), nullable=False, index=True),
        sa.Column("display_order", sa.Integer, nullable=False, server_default="0"),
    )

    # CurriculumLesson table
    op.create_table(
        "curriculum_lessons",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column("unit_id", sa.UUID(as_uuid=True), sa.ForeignKey("curriculum_units.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(300), nullable=False, unique=True, index=True),
        sa.Column("learning_goal", sa.Text, nullable=True),
        sa.Column("estimated_time", sa.Integer, nullable=False, server_default="15"),
        sa.Column("difficulty", sa.String(50), nullable=False, server_default="BEGINNER"),
        sa.Column("required_skills", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("skills_taught", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("prerequisites", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("xp_reward", sa.Integer, nullable=False, server_default="100"),
        sa.Column("ai_coaching_enabled", sa.Boolean, nullable=False, server_default=sa.text('1')),
        sa.Column("teacher_assignable", sa.Boolean, nullable=False, server_default=sa.text('1')),
        sa.Column("display_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # CurriculumExercise table
    op.create_table(
        "curriculum_exercises",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column("lesson_id", sa.UUID(as_uuid=True), sa.ForeignKey("curriculum_lessons.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("exercise_type", sa.String(50), nullable=False, server_default="PRACTICE"),
        sa.Column("tempo_bpm", sa.Integer, nullable=False, server_default="80"),
        sa.Column("key_signature", sa.String(20), nullable=False, server_default="C Major"),
        sa.Column("midi_uri", sa.String(1024), nullable=True),
        sa.Column("display_order", sa.Integer, nullable=False, server_default="0"),
    )

    # CurriculumCheckpoint table
    op.create_table(
        "curriculum_checkpoints",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column("module_id", sa.UUID(as_uuid=True), sa.ForeignKey("curriculum_modules.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("pass_threshold_percentage", sa.Float, nullable=False, server_default="80.0"),
        sa.Column("unlocks_module_id", sa.UUID(as_uuid=True), nullable=True),
    )

def downgrade() -> None:
    """Drop curriculum tables in reverse order."""
    op.drop_table("curriculum_checkpoints")
    op.drop_table("curriculum_exercises")
    op.drop_table("curriculum_lessons")
    op.drop_table("curriculum_units")
    op.drop_table("curriculum_modules")
    op.drop_table("learning_paths")

