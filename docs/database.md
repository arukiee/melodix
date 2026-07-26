# Melodix Database Architecture

This document describes the complete Entity Relationship Diagram (ERD) and data model for the Melodix application, covering both the Version 1 entities and all future entities to ensure a scalable architecture.

## Entity Relationship Diagram (ERD)

```mermaid
erDiagram
    %% Core Entities (Version 1)
    USER {
        uuid id PK
        string email UK
        string password_hash "Nullable for OAuth"
        string full_name
        string avatar_url
        string role "STUDENT, TEACHER, ADMIN"
        string auth_provider "EMAIL, GOOGLE"
        boolean onboarding_completed
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    PROFILE {
        uuid id PK
        uuid user_id FK
        text bio
        string skill_level
        string preferred_instrument
        int daily_practice_goal
        jsonb preferred_genres
        jsonb learning_preferences
    }

    LESSON {
        uuid id PK
        uuid teacher_id FK
        string title
        text description
        string difficulty
        string genre
        int estimated_duration "minutes"
        string thumbnail_url
        string visibility "PUBLIC, PRIVATE"
        boolean is_published
        datetime created_at
        datetime updated_at
    }

    SONG {
        uuid id PK
        string title
        string composer
        string artist
        string genre
        string difficulty
        int bpm
        string key_signature
        string time_signature
        int duration "seconds"
        string source_type "MIDI, MUSICXML"
        string file_url
        string thumbnail_url
        datetime created_at
        datetime updated_at
    }

    LESSON_SONG {
        uuid lesson_id FK
        uuid song_id FK
        int display_order
    }

    %% Future Entities
    CLASS {
        uuid id PK
        uuid teacher_id FK
        string name
        string description
        string join_code UK
        datetime created_at
    }

    CLASS_MEMBER {
        uuid class_id FK
        uuid student_id FK
        datetime joined_at
    }

    ASSIGNMENT {
        uuid id PK
        uuid class_id FK "Nullable"
        uuid student_id FK "Nullable"
        uuid lesson_id FK
        uuid teacher_id FK
        datetime due_date
        datetime created_at
    }

    PRACTICE_SESSION {
        uuid id PK
        uuid student_id FK
        uuid song_id FK
        uuid assignment_id FK "Nullable"
        float accuracy_score
        float rhythm_score
        int duration_seconds
        datetime started_at
        datetime finished_at
    }

    AI_FEEDBACK {
        uuid id PK
        uuid practice_session_id FK
        text qualitative_feedback
        jsonb suggestions
        string generated_by_model
        datetime created_at
    }

    FRIENDSHIP {
        uuid user_id_1 FK
        uuid user_id_2 FK
        string status "PENDING, ACCEPTED"
        datetime created_at
    }

    NOTIFICATION {
        uuid id PK
        uuid user_id FK
        string type
        string message
        boolean is_read
        datetime created_at
    }

    %% Relationships
    USER ||--o| PROFILE : "has"
    USER ||--o{ LESSON : "creates"
    LESSON ||--o{ LESSON_SONG : "contains"
    SONG ||--o{ LESSON_SONG : "belongs_to"

    USER ||--o{ CLASS : "teaches"
    CLASS ||--o{ CLASS_MEMBER : "enrolls"
    USER ||--o{ CLASS_MEMBER : "joins"

    USER ||--o{ ASSIGNMENT : "assigns/receives"
    CLASS ||--o{ ASSIGNMENT : "receives"
    LESSON ||--o{ ASSIGNMENT : "is_assigned"

    USER ||--o{ PRACTICE_SESSION : "practices"
    SONG ||--o{ PRACTICE_SESSION : "is_practiced"
    ASSIGNMENT ||--o| PRACTICE_SESSION : "results_in"

    PRACTICE_SESSION ||--o| AI_FEEDBACK : "generates"

    USER ||--o{ FRIENDSHIP : "initiates/receives"
    USER ||--o{ NOTIFICATION : "receives"
```

## Schema Decisions
- **UUID Primary Keys**: All entities use UUIDv4 for scalability, security against enumeration attacks, and consistency across microservices/APIs.
- **Many-to-Many Relationships**: 
  - `LESSON_SONG`: A lesson can contain multiple songs (e.g., a warm-up exercise and a main piece), and a song can be featured in multiple lessons.
  - `CLASS_MEMBER`: Students can join multiple classes.
- **JSONB Fields**: PostgreSQL JSONB is used for arrays of strings (like `preferred_genres` and AI `suggestions`) to avoid unnecessary secondary tables for simple tags while retaining query capabilities.
