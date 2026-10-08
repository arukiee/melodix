"""add song discovery catalog fields and tables

Revision ID: a1b2c3d4e5f6
Revises: 62f879a6c3de
Create Date: 2026-08-27 04:45:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import app


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "62f879a6c3de"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.add_column("songs", sa.Column("album", sa.String(length=255), nullable=True))
    op.add_column("songs", sa.Column("mood", sa.String(length=100), nullable=True))
    op.add_column("songs", sa.Column("language", sa.String(length=80), nullable=True))
    op.add_column("songs", sa.Column("tempo", sa.Integer(), nullable=True))
    op.add_column("songs", sa.Column("artwork_url", sa.String(length=1024), nullable=True))
    op.add_column("songs", sa.Column("skills", app.models.json_type.ConditionalJSON(), nullable=True))
    op.add_column("songs", sa.Column("available_arrangements", app.models.json_type.ConditionalJSON(), nullable=True))
    op.add_column("songs", sa.Column("is_learnable", sa.Boolean(), nullable=True))
    op.add_column("songs", sa.Column("embedding", app.models.json_type.ConditionalVector(dim=768), nullable=True))
    op.create_index("ix_songs_artist", "songs", ["artist"], unique=False)
    op.create_index("ix_songs_genre", "songs", ["genre"], unique=False)
    op.create_index("ix_songs_mood", "songs", ["mood"], unique=False)
    op.create_index("ix_songs_language", "songs", ["language"], unique=False)
    op.create_index("ix_songs_tempo", "songs", ["tempo"], unique=False)
    op.create_index("ix_songs_is_learnable", "songs", ["is_learnable"], unique=False)

    op.create_table(
        "saved_songs",
        sa.Column("id", app.models.json_type.ConditionalUUID(), nullable=False),
        sa.Column("user_id", app.models.json_type.ConditionalUUID(), nullable=False),
        sa.Column("song_id", app.models.json_type.ConditionalUUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["song_id"], ["songs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "song_id", name="uq_saved_song_user"),
    )
    op.create_index(op.f("ix_saved_songs_song_id"), "saved_songs", ["song_id"], unique=False)
    op.create_index(op.f("ix_saved_songs_user_id"), "saved_songs", ["user_id"], unique=False)

    op.create_table(
        "song_learning_progress",
        sa.Column("id", app.models.json_type.ConditionalUUID(), nullable=False),
        sa.Column("user_id", app.models.json_type.ConditionalUUID(), nullable=False),
        sa.Column("song_id", app.models.json_type.ConditionalUUID(), nullable=False),
        sa.Column("arrangement", sa.String(length=20), nullable=True),
        sa.Column("progress_percentage", sa.Float(), nullable=True),
        sa.Column("completed", sa.Boolean(), nullable=True),
        sa.Column("last_played_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["song_id"], ["songs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "song_id", name="uq_song_learning_user"),
    )
    op.create_index(op.f("ix_song_learning_progress_last_played_at"), "song_learning_progress", ["last_played_at"], unique=False)
    op.create_index(op.f("ix_song_learning_progress_song_id"), "song_learning_progress", ["song_id"], unique=False)
    op.create_index(op.f("ix_song_learning_progress_user_id"), "song_learning_progress", ["user_id"], unique=False)

    op.create_table(
        "classrooms",
        sa.Column("id", app.models.json_type.ConditionalUUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("teacher_id", app.models.json_type.ConditionalUUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_classrooms_teacher_id"), "classrooms", ["teacher_id"], unique=False)

    op.create_table(
        "class_memberships",
        sa.Column("id", app.models.json_type.ConditionalUUID(), nullable=False),
        sa.Column("class_id", app.models.json_type.ConditionalUUID(), nullable=False),
        sa.Column("user_id", app.models.json_type.ConditionalUUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["class_id"], ["classrooms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("class_id", "user_id", name="uq_class_member"),
    )
    op.create_index(op.f("ix_class_memberships_class_id"), "class_memberships", ["class_id"], unique=False)
    op.create_index(op.f("ix_class_memberships_user_id"), "class_memberships", ["user_id"], unique=False)

    op.create_table(
        "class_song_assignments",
        sa.Column("id", app.models.json_type.ConditionalUUID(), nullable=False),
        sa.Column("class_id", app.models.json_type.ConditionalUUID(), nullable=False),
        sa.Column("song_id", app.models.json_type.ConditionalUUID(), nullable=False),
        sa.Column("assigned_by", app.models.json_type.ConditionalUUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["assigned_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["class_id"], ["classrooms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["song_id"], ["songs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_class_song_assignments_class_id"), "class_song_assignments", ["class_id"], unique=False)
    op.create_index(op.f("ix_class_song_assignments_created_at"), "class_song_assignments", ["created_at"], unique=False)
    op.create_index(op.f("ix_class_song_assignments_song_id"), "class_song_assignments", ["song_id"], unique=False)

    if bind.dialect.name == "postgresql":
        op.execute(
            """
            UPDATE songs
            SET tempo = COALESCE(tempo, bpm),
                artwork_url = COALESCE(artwork_url, thumbnail_url),
                is_learnable = COALESCE(is_learnable, TRUE),
                available_arrangements = COALESCE(available_arrangements, '["Easy","Medium","Hard"]'::jsonb)
            """
        )


def downgrade() -> None:
    op.drop_table("class_song_assignments")
    op.drop_table("class_memberships")
    op.drop_table("classrooms")
    op.drop_table("song_learning_progress")
    op.drop_table("saved_songs")
    op.drop_index("ix_songs_is_learnable", table_name="songs")
    op.drop_index("ix_songs_tempo", table_name="songs")
    op.drop_index("ix_songs_language", table_name="songs")
    op.drop_index("ix_songs_mood", table_name="songs")
    op.drop_index("ix_songs_genre", table_name="songs")
    op.drop_index("ix_songs_artist", table_name="songs")
    op.drop_column("songs", "embedding")
    op.drop_column("songs", "is_learnable")
    op.drop_column("songs", "available_arrangements")
    op.drop_column("songs", "skills")
    op.drop_column("songs", "artwork_url")
    op.drop_column("songs", "tempo")
    op.drop_column("songs", "language")
    op.drop_column("songs", "mood")
    op.drop_column("songs", "album")
