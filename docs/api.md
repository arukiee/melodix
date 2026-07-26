# Melodix API Design Contract

This document outlines the core REST API contract for the Melodix backend. It serves as the blueprint for our frontend integration and backend model design. All requests and responses use `application/json` unless otherwise specified.

## Authentication (`/api/auth`)

### `POST /auth/login`
Authenticates a user via email and password and returns a JWT token.
- **Request Body**: `{"email": "user@example.com", "password": "password123"}`
- **Response (200)**: `{"access_token": "eyJhb...", "token_type": "bearer"}`

### `POST /auth/google`
Authenticates or registers a user via a Google OAuth access token.
- **Request Body**: `{"google_token": "ya29.a0..."}`
- **Response (200)**: `{"access_token": "eyJhb...", "token_type": "bearer"}`

---

## Users & Profiles (`/api/users`)

### `GET /users/me`
Retrieves the currently authenticated user's details and active profile.
- **Headers**: `Authorization: Bearer <token>`
- **Response (200)**: 
  ```json
  {
    "id": "uuid",
    "email": "user@example.com",
    "name": "Alex",
    "avatar_url": "https://...",
    "active_role": "STUDENT"
  }
  ```

### `PATCH /users/profile`
Updates the user's profile information (e.g., onboarding data, bio).
- **Headers**: `Authorization: Bearer <token>`
- **Request Body**: `{"experience_level": "INTERMEDIATE", "bio": "Piano enthusiast"}`
- **Response (200)**: Updated user object.

---

## Lessons & Content (`/api/lessons`)

### `GET /lessons`
Retrieves a list of available lessons, optionally filtered by difficulty or instrument.
- **Query Params**: `?difficulty=BEGINNER&limit=10`
- **Response (200)**: 
  ```json
  [
    {
      "id": "uuid",
      "title": "Introduction to Scales",
      "difficulty": "BEGINNER",
      "duration_minutes": 15
    }
  ]
  ```

### `GET /lessons/{id}`
Retrieves detailed information and sheet music data for a specific lesson.
- **Response (200)**: Lesson details including `musicxml_url` or `midi_url`.

---

## Practice Engine (`/api/practice`)

### `POST /practice/start`
Initializes a new practice session for a specific song/lesson.
- **Headers**: `Authorization: Bearer <token>`
- **Request Body**: `{"lesson_id": "uuid"}`
- **Response (200)**: `{"session_id": "uuid", "started_at": "2026-07-26T10:00:00Z"}`

### `POST /practice/finish`
Submits the performance data at the end of a practice session to generate a score.
- **Headers**: `Authorization: Bearer <token>`
- **Request Body**: 
  ```json
  {
    "session_id": "uuid",
    "accuracy_score": 94.5,
    "rhythm_score": 88.0,
    "duration_seconds": 340
  }
  ```
- **Response (200)**: `{"final_score": 92, "xp_gained": 50}`

---

## Assignments (`/api/assignments`)

### `GET /assignments`
Retrieves all pending and completed assignments for the authenticated student.
- **Headers**: `Authorization: Bearer <token>`
- **Response (200)**: List of assignment objects.

### `POST /assignments`
(Teachers Only) Creates a new assignment for a class or specific student.
- **Headers**: `Authorization: Bearer <token>`
- **Request Body**: `{"student_id": "uuid", "lesson_id": "uuid", "due_date": "2026-08-01"}`
- **Response (201)**: Created assignment object.

---

## Social & Community (`/api/social`)

### `GET /leaderboard`
Retrieves the global or friends-only XP leaderboard.
- **Query Params**: `?type=GLOBAL` or `?type=FRIENDS`
- **Response (200)**: List of top-ranking user profiles.

### `GET /friends`
Retrieves the authenticated user's friend list and their current online/practice status.
- **Headers**: `Authorization: Bearer <token>`
- **Response (200)**: List of friend profiles with `status` (ONLINE, OFFLINE, PRACTICING).
