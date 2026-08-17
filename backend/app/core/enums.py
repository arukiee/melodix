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

class AudioSourceType(str, Enum):
    USER_UPLOAD = "USER_UPLOAD"
    USER_MIDI = "USER_MIDI"
    PUBLIC_DOMAIN = "PUBLIC_DOMAIN"
    LICENSED = "LICENSED"

class ProcessingJobStage(str, Enum):
    QUEUED = "QUEUED"
    VALIDATING = "VALIDATING"
    PREPROCESSING = "PREPROCESSING"
    TRANSCRIBING = "TRANSCRIBING"
    VALIDATING_NOTES = "VALIDATING_NOTES"
    ANALYZING_RHYTHM = "ANALYZING_RHYTHM"
    ANALYZING_CHORDS = "ANALYZING_CHORDS"
    ASSIGNING_HANDS = "ASSIGNING_HANDS"
    COMPUTING_DIFFICULTY = "COMPUTING_DIFFICULTY"
    CREATING_LESSON = "CREATING_LESSON"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class DifficultyLevel(str, Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
    EXPERT = "EXPERT"

class HandAssignment(str, Enum):
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    UNASSIGNED = "UNASSIGNED"

class ValidationAction(str, Enum):
    KEEP = "KEEP"
    MERGE = "MERGE"
    DISCARD = "DISCARD"
    FLAG = "FLAG"
