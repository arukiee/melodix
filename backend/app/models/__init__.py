from app.models.user import User
from app.models.profile import Profile
from app.models.lesson import Lesson, lesson_song
from app.models.song import Song
from app.models.lesson_progress import LessonProgress

# This file exposes all models so that Alembic can import them from a single place
# ensuring metadata is fully populated before generating migrations.
