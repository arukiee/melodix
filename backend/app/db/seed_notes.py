"""
Seeding script for Melodix canonical melody transcriptions and notes.
Seeds real, playable note sequences for core piano pieces so practice mode works end-to-end.
"""

import uuid
import hashlib
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.song import Song
from app.models.audio_asset import AudioAsset
from app.models.processing_job import ProcessingJob, ProcessingJobStage
from app.models.transcription import Transcription
from app.models.transcription_note import TranscriptionNote
from app.models.provenance import ProcessingProvenance

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

def midi_to_name(midi: int) -> str:
    """Convert MIDI number (e.g. 60) to pitch name with octave (e.g. 'C4')."""
    octave = (midi // 12) - 1
    return f"{NOTE_NAMES[midi % 12]}{octave}"

SONG_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "title": "Twinkle Twinkle Little Star",
        "artist": "Jane Taylor",
        "composer": "Wolfgang Amadeus Mozart",
        "genre": "Traditional",
        "difficulty": "Beginner",
        "bpm": 80,
        "notes": [60, 60, 67, 67, 69, 69, 67, 65, 65, 64, 64, 62, 62, 60],
        "note_duration": 0.5,
    },
    {
        "title": "Ode to Joy",
        "artist": "Ludwig van Beethoven",
        "composer": "Ludwig van Beethoven",
        "genre": "Classical",
        "difficulty": "Beginner",
        "bpm": 120,
        "notes": [64, 64, 65, 67, 67, 65, 64, 62, 60, 60, 62, 64, 64, 62, 62, 60],
        "note_duration": 0.5,
    },
    {
        "title": "Moonlight Sonata",
        "artist": "Ludwig van Beethoven",
        "composer": "Ludwig van Beethoven",
        "genre": "Classical",
        "difficulty": "Intermediate",
        "bpm": 54,
        "notes": [56, 56, 56, 56, 56, 56, 56, 56, 56, 56, 56, 56, 61, 59, 61, 64],
        "note_duration": 0.5,
    },
    {
        "title": "Fur Elise",
        "artist": "Ludwig van Beethoven",
        "composer": "Ludwig van Beethoven",
        "genre": "Classical",
        "difficulty": "Beginner",
        "bpm": 60,
        "notes": [76, 75, 76, 75, 76, 71, 74, 72, 69],
        "note_duration": 0.5,
    },
    {
        "title": "Prelude in C Major",
        "artist": "Johann Sebastian Bach",
        "composer": "Johann Sebastian Bach",
        "genre": "Classical",
        "difficulty": "Beginner",
        "bpm": 110,
        "notes": [60, 64, 67, 72, 76, 60, 64, 67, 72, 76],
        "note_duration": 0.5,
    },
]

def seed_transcriptions_and_notes(db: Session):
    # Ensure all tables exist
    Base.metadata.create_all(bind=engine)

    # 1. Get or create a default user for ownership
    user = db.query(User).first()
    if not user:
        user = User(
            id=uuid.uuid4(),
            email="admin@melodix.com",
            full_name="Admin",
            role="ADMIN",
            auth_provider="EMAIL",
            onboarding_completed=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    print(f"Using user {user.email} (ID: {user.id}) for seeding.")

    seeded_summary = []

    for song_def in SONG_DEFINITIONS:
        title = song_def["title"]
        midi_notes = song_def["notes"]
        note_dur = song_def["note_duration"]
        total_duration = len(midi_notes) * note_dur

        # 2. Find or create the song
        song = db.query(Song).filter(Song.title.ilike(f"%{title}%")).first()
        if not song:
            song = Song(
                id=uuid.uuid4(),
                title=title,
                artist=song_def["artist"],
                composer=song_def["composer"],
                genre=song_def["genre"],
                difficulty=song_def["difficulty"],
                bpm=song_def["bpm"],
                duration=int(total_duration),
                source_type="MIDI",
                is_learnable=True,
            )
            db.add(song)
            db.commit()
            db.refresh(song)
            print(f"[+] Created song: {song.title} (ID: {song.id})")
        else:
            print(f"[*] Found existing song: {song.title} (ID: {song.id})")

        # 3. Find or create AudioAsset
        slug = title.lower().replace(" ", "_").replace("'", "")
        file_hash = hashlib.sha256(slug.encode("utf-8")).hexdigest()
        
        audio_asset = db.query(AudioAsset).filter(
            AudioAsset.song_id == song.id,
            AudioAsset.format == 'mid'
        ).first()

        if not audio_asset:
            audio_asset = AudioAsset(
                id=uuid.uuid4(),
                user_id=user.id,
                song_id=song.id,
                source_type="USER_MIDI",
                original_filename=f"{slug}.mid",
                file_hash_sha256=file_hash,
                storage_path=f"midi/{slug}.mid",
                format="mid",
                duration_seconds=total_duration,
                file_size_bytes=len(midi_notes) * 32,
                is_valid=True,
            )
            db.add(audio_asset)
            db.commit()
            db.refresh(audio_asset)
            print(f"    -> Created AudioAsset: {audio_asset.id}")
        else:
            audio_asset.is_valid = True
            audio_asset.duration_seconds = total_duration
            db.commit()

        # 4. Find or create completed ProcessingJob
        processing_job = db.query(ProcessingJob).filter(
            ProcessingJob.audio_asset_id == audio_asset.id
        ).first()

        if not processing_job:
            processing_job = ProcessingJob(
                id=uuid.uuid4(),
                audio_asset_id=audio_asset.id,
                song_id=song.id,
                user_id=user.id,
                status=ProcessingJobStage.COMPLETED.value,
                progress_percent=100,
                pipeline_version="1.0.0",
                stage_log=[
                    {"stage": "validating", "result": "valid"},
                    {"stage": "transcribing", "result": "seeded_melody"},
                    {"stage": "completed", "result": "success"}
                ],
            )
            db.add(processing_job)
            db.commit()
            db.refresh(processing_job)
            print(f"    -> Created ProcessingJob: {processing_job.id}")
        else:
            processing_job.status = ProcessingJobStage.COMPLETED.value
            processing_job.progress_percent = 100
            db.commit()

        # 5. Find or create ProcessingProvenance
        provenance = db.query(ProcessingProvenance).filter(
            ProcessingProvenance.processing_job_id == processing_job.id
        ).first()

        if not provenance:
            provenance = ProcessingProvenance(
                id=uuid.uuid4(),
                processing_job_id=processing_job.id,
                song_id=song.id,
                audio_asset_id=audio_asset.id,
                pipeline_version="1.0.0",
                source_type="MIDI",
                file_hash=audio_asset.file_hash_sha256,
                audio_duration=total_duration,
                transcription_model="seeded_melody",
                transcription_model_version="1.0",
                tempo_value=float(song.bpm or 100.0),
                note_count=len(midi_notes),
            )
            db.add(provenance)
            db.commit()
            db.refresh(provenance)
            print(f"    -> Created ProcessingProvenance: {provenance.id}")

        # 6. Find or create Transcription
        transcription = db.query(Transcription).filter(
            Transcription.processing_job_id == processing_job.id
        ).first()

        if not transcription:
            transcription = Transcription(
                id=uuid.uuid4(),
                processing_job_id=processing_job.id,
                audio_asset_id=audio_asset.id,
                song_id=song.id,
                model_name="seeded_melody",
                model_version="1.0",
                note_count=len(midi_notes),
                duration_seconds=total_duration,
                processing_time_ms=50,
            )
            db.add(transcription)
            db.commit()
            db.refresh(transcription)
            print(f"    -> Created Transcription: {transcription.id}")
        else:
            transcription.note_count = len(midi_notes)
            transcription.duration_seconds = total_duration
            db.commit()

        # Link transcription to provenance
        provenance.transcription_id = transcription.id
        db.commit()

        # 7. Create/Replace TranscriptionNote records
        # Delete existing notes for this transcription to avoid duplication
        db.query(TranscriptionNote).filter(
            TranscriptionNote.transcription_id == transcription.id
        ).delete()

        created_notes = []
        for idx, midi in enumerate(midi_notes):
            start_t = idx * note_dur
            end_t = (idx + 1) * note_dur
            pitch_name = midi_to_name(midi)
            measure_num = (idx // 4) + 1
            beat_pos = float((idx % 4) + 1)

            note_row = TranscriptionNote(
                transcription_id=transcription.id,
                sequence_index=idx,
                midi_number=midi,
                note_name=pitch_name,
                start_time=start_t,
                end_time=end_t,
                duration=note_dur,
                velocity=80,
                confidence=1.0,
                is_validated=True,
                validation_action="KEEP",
                validation_reason="Seeded canonical melody note",
                hand="RIGHT",
                measure_number=measure_num,
                beat_position=beat_pos,
            )
            db.add(note_row)
            created_notes.append(f"{pitch_name} (MIDI {midi}) @ {start_t:.1f}s")

        db.commit()
        print(f"    -> Seeded {len(created_notes)} TranscriptionNotes: {', '.join(created_notes[:4])}...")
        seeded_summary.append({
            "song": song.title,
            "song_id": str(song.id),
            "job_id": str(processing_job.id),
            "note_count": len(created_notes),
            "notes": [midi_to_name(m) for m in midi_notes]
        })

    print("\n========================================================")
    print("Seeding completed successfully!")
    for s in seeded_summary:
        print(f" • {s['song']} (Job ID: {s['job_id']}) -> {s['note_count']} notes: {' '.join(s['notes'])}")
    print("========================================================\n")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_transcriptions_and_notes(db)
    finally:
        db.close()
