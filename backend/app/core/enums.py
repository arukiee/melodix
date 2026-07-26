"""Shared Enum definitions used throughout the project."""

from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"

class NotificationType(str, Enum):
    EMAIL = "email"
    INAPP = "inapp"
    PUSH = "push"

class RecommendationType(str, Enum):
    SONG = "song"
    LESSON = "lesson"
    PRACTICE = "practice"

class PracticeStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    REVIEWED = "reviewed"

class SearchType(str, Enum):
    TITLE = "title"
    COMPOSER = "composer"
    GENRE = "genre"
    TAG = "tag"
    NATURAL_LANGUAGE = "natural_language"

class LessonDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
