"""Persisted practice sessions for curricula generated from processed songs or catalog songs.

The curriculum generator remains the single source of lesson content. This
service gives its generated objects stable identifiers and overlays each
student's saved progress without storing a second curriculum representation.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import uuid
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.models.discovery import SongLearningProgress
from app.models.processing_job import ProcessingJob
from app.models.song import Song
from app.models.student_progress import StudentLearningState
from app.services.music_engine.curriculum import LearningPlanGenerator
from app.services.music_engine.structure import MusicStructureEngine


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_id(target_id: uuid.UUID, kind: str, *parts: object) -> str:
    key = ":".join([str(target_id), kind, *(str(part) for part in parts)])
    return str(uuid.uuid5(uuid.NAMESPACE_URL, key))


def _stabilize_ids(curriculum: dict[str, Any], target_id: uuid.UUID, song_id: uuid.UUID | None = None) -> dict[str, Any]:
    """Make regenerated curriculum references stable across lesson resumes."""
    result = deepcopy(curriculum)
    result["lesson_id"] = str(target_id)
    result["processing_job_id"] = str(target_id)
    if song_id:
        result["song_id"] = str(song_id)
    event_ids: dict[str, str] = {}
    mission_ids: dict[str, str] = {}

    for level_index, level in enumerate(result.get("levels", [])):
        level["id"] = _stable_id(target_id, "level", level.get("levelNumber", level_index))
        for mission_index, mission in enumerate(level.get("missions", [])):
            old_id = mission.get("id", "")
            stable = _stable_id(target_id, "mission", level.get("levelNumber", level_index), mission_index)
            mission["id"] = stable
            if old_id:
                mission_ids[old_id] = stable
            for event_index, event in enumerate(mission.get("expectedEvents", [])):
                old_event_id = event.get("id", "")
                stable_event = _stable_id(target_id, "event", level.get("levelNumber", level_index), mission_index, event_index)
                event["id"] = stable_event
                if old_event_id:
                    event_ids[old_event_id] = stable_event

    for phrase_index, phrase in enumerate(result.get("phrases", [])):
        phrase["id"] = _stable_id(target_id, "phrase", phrase_index)
        for event_index, event in enumerate(phrase.get("expectedEvents", [])):
            old_event_id = event.get("id", "")
            stable_event = _stable_id(target_id, "phrase-event", phrase_index, event_index)
            event["id"] = stable_event
            if old_event_id:
                event_ids[old_event_id] = stable_event

    for phase_index, phase in enumerate(result.get("phases", [])):
        phase["id"] = _stable_id(target_id, "phase", phase_index)
        for mission_index, mission in enumerate(phase.get("missions", [])):
            old_id = mission.get("id", "")
            mission["id"] = mission_ids.get(old_id, _stable_id(target_id, "phase-mission", phase_index, mission_index))
            for event_index, event in enumerate(mission.get("expectedEvents", [])):
                old_event_id = event.get("id", "")
                event["id"] = event_ids.get(old_event_id, _stable_id(target_id, "phase-event", phase_index, mission_index, event_index))

    for syllable in result.get("lyricAlignment", {}).get("syllables", []):
        syllable["noteEventIds"] = [event_ids.get(event_id, event_id) for event_id in syllable.get("noteEventIds", [])]
    return result


def _missions(curriculum: dict[str, Any]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    return [
        (level, mission)
        for level in curriculum.get("levels", [])
        for mission in level.get("missions", [])
    ]


def _get_or_create_state(db: Session, user_id: uuid.UUID) -> StudentLearningState:
    state = db.query(StudentLearningState).filter(StudentLearningState.user_id == user_id).first()
    if state is None:
        state = StudentLearningState(user_id=user_id, practice_sessions={})
        db.add(state)
        db.flush()
    return state


def _session(state: StudentLearningState, job: ProcessingJob) -> dict[str, Any]:
    sessions = dict(state.practice_sessions or {})
    key = str(job.id)
    session = dict(sessions.get(key) or {})
    if not session:
        session = {
            "processing_job_id": key,
            "song_id": str(job.song_id) if job.song_id else None,
            "completed_mission_ids": [],
            "attempts": {},
            "mission_scores": {},
            "started_at": _now(),
        }
    sessions[key] = session
    state.practice_sessions = sessions
    return session


def _song_session(state: StudentLearningState, song: Song) -> dict[str, Any]:
    sessions = dict(state.practice_sessions or {})
    key = str(song.id)
    session = dict(sessions.get(key) or {})
    if not session:
        session = {
            "song_id": key,
            "processing_job_id": None,
            "completed_mission_ids": [],
            "attempts": {},
            "mission_scores": {},
            "started_at": _now(),
        }
    sessions[key] = session
    state.practice_sessions = sessions
    return session


def _persist_session(state: StudentLearningState, job: ProcessingJob, session: dict[str, Any]) -> None:
    """Reassign JSON so SQLAlchemy persists nested practice-session mutations."""
    sessions = dict(state.practice_sessions or {})
    sessions[str(job.id)] = dict(session)
    state.practice_sessions = sessions
    flag_modified(state, "practice_sessions")


def _persist_song_session(state: StudentLearningState, song: Song, session: dict[str, Any]) -> None:
    """Reassign JSON so SQLAlchemy persists nested practice-session mutations for a song."""
    sessions = dict(state.practice_sessions or {})
    sessions[str(song.id)] = dict(session)
    state.practice_sessions = sessions
    flag_modified(state, "practice_sessions")


def _latest_score(session: dict[str, Any] | None) -> dict[str, Any] | None:
    scores = list((session or {}).get("mission_scores") or {}.values())
    if not scores:
        return None
    return max(scores, key=lambda item: item.get("timestamp") or "")


def _record_performance_history(
    state: StudentLearningState, job: ProcessingJob, score: dict[str, Any]
) -> None:
    if not job.song_id:
        return
    _record_performance_history_for_song(state, job.song_id, score)


def _record_performance_history_for_song(
    state: StudentLearningState, song_id: uuid.UUID, score: dict[str, Any]
) -> None:
    history = dict(state.performance_history or {})
    song_key = str(song_id)
    by_difficulty = dict(history.get(song_key) or {})
    band = state.current_difficulty or "EASY"
    band_history = list(by_difficulty.get(band) or [])
    band_history.append(
        {
            "score": score.get("overall_score"),
            "pitch_accuracy": score.get("pitch_accuracy"),
            "timing_accuracy": score.get("timing_accuracy"),
            "mission_id": score.get("mission_id"),
            "attempt": score.get("attempt"),
            "date": score.get("timestamp") or _now(),
        }
    )
    by_difficulty[band] = band_history[-20:]
    history[song_key] = by_difficulty
    state.performance_history = history
    flag_modified(state, "performance_history")


def _save_song_summary(db: Session, user_id: uuid.UUID, job: ProcessingJob, progress: float, completed: bool) -> None:
    if not job.song_id:
        return
    _save_song_summary_by_id(db, user_id, job.song_id, progress, completed)


def _save_song_summary_by_id(db: Session, user_id: uuid.UUID, song_id: uuid.UUID, progress: float, completed: bool) -> None:
    summary = db.query(SongLearningProgress).filter(
        SongLearningProgress.user_id == user_id,
        SongLearningProgress.song_id == song_id,
    ).first()
    if summary is None:
        summary = SongLearningProgress(user_id=user_id, song_id=song_id)
        db.add(summary)
    summary.progress_percentage = progress
    summary.completed = completed
    summary.last_played_at = datetime.now(timezone.utc)


def apply_progress(curriculum: dict[str, Any], session: dict[str, Any]) -> dict[str, Any]:
    """Overlay saved state and expose one ordered next mission."""
    completed = set(session.get("completed_mission_ids") or [])
    scores = dict(session.get("mission_scores") or {})
    attempts = dict(session.get("attempts") or {})
    ordered = _missions(curriculum)
    next_index = next((index for index, (_, mission) in enumerate(ordered) if mission["id"] not in completed), len(ordered))
    for index, (level, mission) in enumerate(ordered):
        mission_id = mission["id"]
        saved = scores.get(mission_id) or {}
        if saved:
            mission["lastScore"] = saved
            mission["pitchAccuracy"] = saved.get("pitch_accuracy")
            mission["timingAccuracy"] = saved.get("timing_accuracy")
        mission["attempts"] = int(attempts.get(mission_id, 0))
        if mission_id in completed:
            mission["status"] = "completed"
            mission["progress"] = 100
        elif index == next_index:
            mission["status"] = "in_progress" if session.get("current_mission_id") == mission_id else "available"
            mission["progress"] = 0
            session["current_level_id"] = level["id"]
            session["current_mission_id"] = mission_id
        else:
            mission["status"] = "locked"
            mission["progress"] = 0
    progress = round((len(completed) / len(ordered)) * 100, 2) if ordered else 0.0
    curriculum["overall_progress"] = progress
    curriculum["current_mission_id"] = session.get("current_mission_id")
    curriculum["current_level_id"] = session.get("current_level_id")
    curriculum["completed_mission_ids"] = list(session.get("completed_mission_ids") or [])
    curriculum["mission_scores"] = scores
    curriculum["attempts"] = attempts
    return curriculum


def curriculum_for_job(db: Session, job_id: uuid.UUID) -> tuple[ProcessingJob, dict[str, Any]]:
    """Load canonical notes and invoke the existing curriculum engine once."""
    job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    if not job or not job.transcription:
        raise LookupError("Processed job or transcription not found")

    notes = [note for note in job.transcription.notes if note.validation_action != "DISCARD"]
    bpm = job.provenance.tempo_value if job.provenance and job.provenance.tempo_value else 100.0
    sections = MusicStructureEngine.analyze_structure(notes, bpm)
    curriculum = LearningPlanGenerator.generate_curriculum(sections, bpm)
    return job, _stabilize_ids(curriculum, job_id, song_id=job.song_id)


def _get_song_notes(db: Session, song: Song) -> list[Any]:
    """Retrieve canonical transcription notes if available, or generate from melody/chords."""
    job = (
        db.query(ProcessingJob)
        .filter(ProcessingJob.song_id == song.id)
        .order_by(ProcessingJob.created_at.desc())
        .first()
    )
    if job and job.transcription and job.transcription.notes:
        notes = [n for n in job.transcription.notes if getattr(n, "validation_action", None) != "DISCARD"]
        if notes:
            return notes

    from app.services.music_engine.transcription_service import midi_to_note_name
    bpm = float(song.bpm or 80.0)
    beat_dur = 60.0 / bpm

    notes_list: list[tuple[str, float, float]] = []
    if song.missions:
        for m in song.missions:
            if isinstance(m, dict) and m.get("expectedNotes"):
                for idx, note_name in enumerate(m["expectedNotes"]):
                    notes_list.append((str(note_name), idx * beat_dur, beat_dur))
                break

    if not notes_list:
        midi_nums = [60, 60, 67, 67, 69, 69, 67, 65, 65, 64, 64, 62, 62, 60]
        notes_list = [(midi_to_note_name(m), idx * beat_dur, beat_dur) for idx, m in enumerate(midi_nums)]

    class SimpleNote:
        def __init__(self, name: str, start: float, dur: float):
            self.note_name = name
            self.start_time = start
            self.end_time = start + dur
            self.duration = dur
            self.hand = "RIGHT"
            self.validation_action = "KEEP"

    return [SimpleNote(name, start, dur) for name, start, dur in notes_list]


def curriculum_for_song(db: Session, song_id: uuid.UUID) -> tuple[Song, dict[str, Any]]:
    """Build curriculum directly from a stored catalog song without requiring an ephemeral job ID."""
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise LookupError("Song not found")

    notes = _get_song_notes(db, song)
    bpm = float(song.bpm or 100.0)
    sections = MusicStructureEngine.analyze_structure(notes, bpm)
    curriculum = LearningPlanGenerator.generate_curriculum(sections, bpm)
    stabilized = _stabilize_ids(curriculum, song.id, song_id=song.id)
    return song, stabilized


def start_job_session(db: Session, user_id: uuid.UUID, job_id: uuid.UUID) -> dict[str, Any]:
    job, curriculum = curriculum_for_job(db, job_id)
    state = _get_or_create_state(db, user_id)
    session = _session(state, job)
    result = apply_progress(curriculum, session)
    session["updated_at"] = _now()
    _persist_session(state, job, session)
    _save_song_summary(db, user_id, job, result["overall_progress"], result["overall_progress"] >= 100)
    db.commit()
    return result


def complete_job_mission(
    db: Session, user_id: uuid.UUID, job_id: uuid.UUID, mission_id: str, score: float | None = None,
) -> dict[str, Any]:
    job, curriculum = curriculum_for_job(db, job_id)
    state = _get_or_create_state(db, user_id)
    session = _session(state, job)
    ordered = _missions(curriculum)
    ids = [mission["id"] for _, mission in ordered]
    if mission_id not in ids:
        raise ValueError("Mission does not belong to this processed song")
    completed = list(session.get("completed_mission_ids") or [])
    next_id = next((item for item in ids if item not in completed), None)
    if mission_id != next_id:
        raise ValueError("Complete the current available mission before advancing")
    completed.append(mission_id)
    session["completed_mission_ids"] = completed
    attempts = dict(session.get("attempts") or {})
    if mission_id not in attempts:
        attempts[mission_id] = 1
        session["attempts"] = attempts
    scores = dict(session.get("mission_scores") or {})
    existing = dict(scores.get(mission_id) or {})
    effective_score = score if score is not None else existing.get("overall_score", 100.0)
    scores[mission_id] = {
        **existing,
        "song_id": str(job.song_id) if job.song_id else None,
        "lesson_id": str(job.id),
        "phase_id": next(level["id"] for level, mission in ordered if mission["id"] == mission_id),
        "mission_id": mission_id,
        "attempt": attempts[mission_id],
        "overall_score": effective_score,
        "completed": True,
        "completion": True,
        "timestamp": _now(),
    }
    session["mission_scores"] = scores
    _record_performance_history(state, job, scores[mission_id])
    result = apply_progress(curriculum, session)
    session["updated_at"] = _now()
    _persist_session(state, job, session)
    _save_song_summary(db, user_id, job, result["overall_progress"], result["overall_progress"] >= 100)
    db.commit()
    return result


def record_job_score(
    db: Session, user_id: uuid.UUID, job_id: uuid.UUID, mission_id: str, pitch_accuracy: float, timing_accuracy: float, overall_score: float,
) -> dict[str, Any]:
    job, curriculum = curriculum_for_job(db, job_id)
    ordered = _missions(curriculum)
    if mission_id not in {mission["id"] for _, mission in ordered}:
        raise ValueError("Mission does not belong to this processed song")
    state = _get_or_create_state(db, user_id)
    session = _session(state, job)
    attempts = dict(session.get("attempts") or {})
    attempts[mission_id] = int(attempts.get(mission_id, 0)) + 1
    scores = dict(session.get("mission_scores") or {})
    completed = mission_id in set(session.get("completed_mission_ids") or [])
    scores[mission_id] = {
        "song_id": str(job.song_id) if job.song_id else None,
        "student_id": str(user_id),
        "lesson_id": str(job.id),
        "phase_id": next(level["id"] for level, mission in ordered if mission["id"] == mission_id),
        "mission_id": mission_id,
        "attempt": attempts[mission_id],
        "pitch_accuracy": round(pitch_accuracy, 4),
        "timing_accuracy": round(timing_accuracy, 4),
        "overall_score": round(overall_score, 4),
        "completion": completed,
        "completed": completed,
        "timestamp": _now(),
    }
    session["attempts"] = attempts
    session["mission_scores"] = scores
    session["updated_at"] = _now()
    _record_performance_history(state, job, scores[mission_id])
    result = apply_progress(curriculum, session)
    _persist_session(state, job, session)
    _save_song_summary(db, user_id, job, result["overall_progress"], result["overall_progress"] >= 100)
    db.commit()
    return scores[mission_id]


def start_song_session(db: Session, user_id: uuid.UUID, song_id: uuid.UUID) -> dict[str, Any]:
    """Start or resume practice for a catalog song."""
    song, curriculum = curriculum_for_song(db, song_id)
    state = _get_or_create_state(db, user_id)
    session = _song_session(state, song)
    result = apply_progress(curriculum, session)
    session["updated_at"] = _now()
    _persist_song_session(state, song, session)
    _save_song_summary_by_id(db, user_id, song.id, result["overall_progress"], result["overall_progress"] >= 100)
    db.commit()
    return result


def complete_song_mission(
    db: Session, user_id: uuid.UUID, song_id: uuid.UUID, mission_id: str, score: float | None = None,
) -> dict[str, Any]:
    """Advance mission status and store score for a catalog song practice session."""
    song, curriculum = curriculum_for_song(db, song_id)
    state = _get_or_create_state(db, user_id)
    session = _song_session(state, song)
    ordered = _missions(curriculum)
    ids = [mission["id"] for _, mission in ordered]
    if mission_id not in ids:
        raise ValueError("Mission does not belong to this song")
    completed = list(session.get("completed_mission_ids") or [])
    next_id = next((item for item in ids if item not in completed), None)
    if mission_id != next_id:
        raise ValueError("Complete the current available mission before advancing")
    completed.append(mission_id)
    session["completed_mission_ids"] = completed
    attempts = dict(session.get("attempts") or {})
    if mission_id not in attempts:
        attempts[mission_id] = 1
        session["attempts"] = attempts
    scores = dict(session.get("mission_scores") or {})
    existing = dict(scores.get(mission_id) or {})
    effective_score = score if score is not None else existing.get("overall_score", 100.0)
    scores[mission_id] = {
        **existing,
        "song_id": str(song.id),
        "lesson_id": str(song.id),
        "phase_id": next(level["id"] for level, mission in ordered if mission["id"] == mission_id),
        "mission_id": mission_id,
        "attempt": attempts[mission_id],
        "overall_score": effective_score,
        "completed": True,
        "completion": True,
        "timestamp": _now(),
    }
    session["mission_scores"] = scores
    _record_performance_history_for_song(state, song.id, scores[mission_id])
    result = apply_progress(curriculum, session)
    session["updated_at"] = _now()
    _persist_song_session(state, song, session)
    _save_song_summary_by_id(db, user_id, song.id, result["overall_progress"], result["overall_progress"] >= 100)
    db.commit()
    return result


def record_song_score(
    db: Session,
    user_id: uuid.UUID,
    song_id: uuid.UUID,
    mission_id: str,
    pitch_accuracy: float,
    timing_accuracy: float,
    overall_score: float,
) -> dict[str, Any]:
    """Persist segment score against song practice session."""
    song, curriculum = curriculum_for_song(db, song_id)
    ordered = _missions(curriculum)
    if mission_id not in {mission["id"] for _, mission in ordered}:
        raise ValueError("Mission does not belong to this song")
    state = _get_or_create_state(db, user_id)
    session = _song_session(state, song)
    attempts = dict(session.get("attempts") or {})
    attempts[mission_id] = int(attempts.get(mission_id, 0)) + 1
    scores = dict(session.get("mission_scores") or {})
    completed = mission_id in set(session.get("completed_mission_ids") or [])
    scores[mission_id] = {
        "song_id": str(song.id),
        "student_id": str(user_id),
        "lesson_id": str(song.id),
        "phase_id": next(level["id"] for level, mission in ordered if mission["id"] == mission_id),
        "mission_id": mission_id,
        "attempt": attempts[mission_id],
        "pitch_accuracy": round(pitch_accuracy, 4),
        "timing_accuracy": round(timing_accuracy, 4),
        "overall_score": round(overall_score, 4),
        "completion": completed,
        "completed": completed,
        "timestamp": _now(),
    }
    session["attempts"] = attempts
    session["mission_scores"] = scores
    session["updated_at"] = _now()
    _record_performance_history_for_song(state, song.id, scores[mission_id])
    result = apply_progress(curriculum, session)
    _persist_song_session(state, song, session)
    _save_song_summary_by_id(db, user_id, song.id, result["overall_progress"], result["overall_progress"] >= 100)
    db.commit()
    return scores[mission_id]


def progress_summary_for_song(db: Session, user_id: uuid.UUID, song_id: uuid.UUID) -> dict[str, Any]:
    """Song-level progress plus the latest persisted practice score, if any."""
    summary = db.query(SongLearningProgress).filter(
        SongLearningProgress.user_id == user_id,
        SongLearningProgress.song_id == song_id,
    ).first()
    state = db.query(StudentLearningState).filter(StudentLearningState.user_id == user_id).first()
    session = None
    if state:
        for item in (state.practice_sessions or {}).values():
            if item.get("song_id") == str(song_id):
                session = item
                break
    last_score = _latest_score(session)
    return {
        "progress_percentage": summary.progress_percentage if summary else 0.0,
        "completed": bool(summary.completed) if summary else False,
        "current_mission_id": (session or {}).get("current_mission_id"),
        "current_level_id": (session or {}).get("current_level_id"),
        "completed_mission_ids": list((session or {}).get("completed_mission_ids") or []),
        "last_score": last_score,
        "attempts": dict((session or {}).get("attempts") or {}),
    }
