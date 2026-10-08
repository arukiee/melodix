from __future__ import annotations

import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # Registers the complete metadata before create_all.
from app.core.database import Base
from app.models.audio_asset import AudioAsset
from app.models.discovery import SongLearningProgress
from app.models.processing_job import ProcessingJob
from app.models.song import Song
from app.models.student_progress import StudentLearningState
from app.models.transcription import Transcription
from app.models.transcription_note import TranscriptionNote
from app.models.user import User
from app.services.music_engine.practice_session_service import complete_job_mission, record_job_score, start_job_session


def test_job_practice_session_persists_and_resumes():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    user = User(id=uuid.uuid4(), email="learner@example.test", full_name="Learner")
    song = Song(id=uuid.uuid4(), title="Practice Song")
    asset = AudioAsset(
        id=uuid.uuid4(), user_id=user.id, song_id=song.id, original_filename="song.mid",
        file_hash_sha256="a" * 64, storage_path="audio/song.mid", format="mid", file_size_bytes=1,
    )
    job = ProcessingJob(id=uuid.uuid4(), audio_asset_id=asset.id, song_id=song.id, user_id=user.id)
    transcription = Transcription(
        id=uuid.uuid4(), processing_job_id=job.id, audio_asset_id=asset.id, song_id=song.id,
        model_version="test",
    )
    notes = [
        TranscriptionNote(transcription_id=transcription.id, sequence_index=index, midi_number=pitch,
                          note_name=name, start_time=index * 0.5, end_time=index * 0.5 + 0.4,
                          duration=0.4, velocity=80, confidence=1.0, validation_action="KEEP", hand="RIGHT")
        for index, (pitch, name) in enumerate([(60, "C4"), (64, "E4"), (67, "G4")])
    ]
    session.add_all([user, song, asset, job, transcription, *notes])
    session.commit()

    started = start_job_session(session, user.id, job.id)
    first = started["current_mission_id"]
    assert first
    assert started["overall_progress"] == 0

    advanced = complete_job_mission(session, user.id, job.id, first, score=0.92)
    assert advanced["overall_progress"] > 0
    assert advanced["current_mission_id"] != first

    resumed = start_job_session(session, user.id, job.id)
    assert resumed["current_mission_id"] == advanced["current_mission_id"]
    state = session.query(StudentLearningState).filter_by(user_id=user.id).one()
    assert first in state.practice_sessions[str(job.id)]["completed_mission_ids"]
    assert session.query(SongLearningProgress).filter_by(user_id=user.id, song_id=song.id).one().progress_percentage > 0


def test_segment_score_is_persisted_with_song_and_timing_metrics():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    user = User(id=uuid.uuid4(), email="scorer@example.test", full_name="Scorer")
    song = Song(id=uuid.uuid4(), title="Scored Song")
    asset = AudioAsset(id=uuid.uuid4(), user_id=user.id, song_id=song.id, original_filename="song.mid", file_hash_sha256="b" * 64, storage_path="audio/song.mid", format="mid", file_size_bytes=1)
    job = ProcessingJob(id=uuid.uuid4(), audio_asset_id=asset.id, song_id=song.id, user_id=user.id)
    transcription = Transcription(id=uuid.uuid4(), processing_job_id=job.id, audio_asset_id=asset.id, song_id=song.id, model_version="test")
    note = TranscriptionNote(transcription_id=transcription.id, sequence_index=0, midi_number=60, note_name="C4", start_time=0, end_time=0.4, duration=0.4, velocity=80, confidence=1, validation_action="KEEP", hand="RIGHT")
    session.add_all([user, song, asset, job, transcription, note])
    session.commit()

    curriculum = start_job_session(session, user.id, job.id)
    mission_id = curriculum["current_mission_id"]
    saved = record_job_score(session, user.id, job.id, mission_id, 0.9, 0.8, 0.85)

    assert saved["song_id"] == str(song.id)
    assert saved["pitch_accuracy"] == 0.9
    assert saved["timing_accuracy"] == 0.8
    assert saved["attempt"] == 1
