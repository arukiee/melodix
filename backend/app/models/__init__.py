from app.models.user import User
from app.models.profile import Profile
from app.models.lesson import Lesson, lesson_song
from app.models.song import Song
from app.models.lesson_progress import LessonProgress
from app.models.social import FriendRequest, Friendship
from app.models.curriculum import (
    LearningPath, CurriculumModule, CurriculumUnit, 
    CurriculumLesson, CurriculumExercise, CurriculumCheckpoint
)
from app.models.student_progress import StudentLearningState

# Expose all models so Alembic metadata can discover them for migrations
