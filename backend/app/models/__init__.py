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
from app.models.discovery import (
    SavedSong,
    SongLearningProgress,
    Classroom,
    ClassMembership,
    ClassSongAssignment,
)

# Expose all models so Alembic metadata can discover them for migrations
from app.models.audio_asset import AudioAsset
from app.models.processing_job import ProcessingJob
from app.models.transcription import Transcription
from app.models.transcription_note import TranscriptionNote
from app.models.difficulty_variant import DifficultyVariant
from app.models.difficulty_note import DifficultyNote
from app.models.provenance import ProcessingProvenance
