import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from fastapi import Depends

from app.core.database import get_db
from app.models.song import Song
from app.schemas.import_schema import (
    ImportPreviewResponse, ImportCommitResponse, ChordInfo, MissionInfo
)
from app.services.music_engine.importers.validator import ImportValidator
from app.services.music_engine.importers.musicxml_importer import MusicXMLImporter
from app.services.music_engine.importers.midi_importer import MIDIImporter
from app.services.music_engine.importers.chord_sheet_importer import ChordSheetImporter
from app.services.music_engine.importers.youtube_importer import YouTubeImporter
from app.services.music_engine.importers.chord_extractor import ChordExtractor
from app.services.music_engine.converters.timeline_builder import TimelineBuilder
from app.services.music_engine.converters.mission_builder import MissionBuilder

logger = logging.getLogger("melodix.import")

router = APIRouter(prefix="/api/v1/import", tags=["import"])

# Constants
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTENSIONS = {".xml", ".musicxml", ".mid", ".midi", ".ug", ".txt", ".yt", ".json"}


def _validate_upload(file_bytes: bytes, filename: str):
    """Validates file size and extension before pipeline processing."""
    # Extension check
    ext = ""
    if "." in filename:
        ext = "." + filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: '{ext}'. Accepted: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    # Size check
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        size_mb = len(file_bytes) / (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size_mb:.1f} MB). Maximum allowed: 5 MB."
        )

    # Empty file check
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")


def _run_pipeline(file_bytes: bytes, filename: str):
    """Runs the full import pipeline and returns the normalized result."""
    # 1. Choose importer based on extension
    if filename.endswith(".mid") or filename.endswith(".midi"):
        importer = MIDIImporter()
    elif filename.endswith(".ug") or filename.endswith(".txt"):
        importer = ChordSheetImporter()
    elif filename.endswith(".yt") or filename.endswith(".json"):
        importer = YouTubeImporter()
    else:
        importer = MusicXMLImporter()

    parsed = importer.parse(file_bytes)

    # 2. Validate
    warnings = ImportValidator.validate(parsed)

    # 3. Extract chords
    chords = ChordExtractor.extract_chords(parsed.get("notes", []))

    # 4. Build timeline
    expected_events = TimelineBuilder.build_expected_events(parsed)

    # 5. Generate missions
    missions = MissionBuilder.generate_missions(parsed)

    # 6. Count measures
    notes = parsed.get("notes", [])
    measure_count = max((n.get("measure", 0) for n in notes), default=0) + 1 if notes else 0

    return parsed, warnings, chords, expected_events, missions, measure_count


@router.post(
    "/preview",
    response_model=ImportPreviewResponse,
    summary="Preview a MusicXML or MIDI import",
    description="Uploads a MusicXML or MIDI file, runs the full import pipeline "
                "(validation, parsing, chord extraction, timeline building, mission generation), "
                "and returns a preview without persisting to the database.",
    responses={
        400: {"description": "File is empty or could not be parsed."},
        413: {"description": "File exceeds maximum size (5 MB)."},
        415: {"description": "Unsupported file type."},
    }
)
async def preview_import(file: UploadFile = File(...)):
    file_bytes = await file.read()
    filename = file.filename or "upload.xml"

    _validate_upload(file_bytes, filename)

    try:
        parsed, warnings, chords, expected_events, missions, measure_count = _run_pipeline(
            file_bytes, filename
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Import preview failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")

    return ImportPreviewResponse(
        title=parsed.get("title", "Unknown"),
        composer=parsed.get("composer", "Unknown"),
        key_signature=parsed.get("key_signature", "C Major"),
        time_signature=parsed.get("time_signature", "4/4"),
        bpm=parsed.get("bpm", 60),
        measure_count=measure_count,
        note_count=len(parsed.get("notes", [])),
        detected_chords=[
            ChordInfo(measure=c["measure"], pitches=c["pitches"], detected_chord=c["detected_chord"])
            for c in chords
        ],
        generated_missions=[
            MissionInfo(
                id=m["id"], title=m["title"], type=m["type"],
                bpm=m["bpm"], learningGoal=m["learningGoal"],
                xpReward=m["xpReward"],
                expectedNotes=m.get("expectedNotes", [])
            )
            for m in missions
        ],
        sections=parsed.get("sections", []),
        steps=parsed.get("steps", []),
        adaptive_thresholds=parsed.get("adaptive_thresholds", {}),
        validation_warnings=warnings,
        notes=parsed.get("notes", [])
    )


@router.post(
    "/commit",
    response_model=ImportCommitResponse,
    summary="Commit an imported song to the database",
    description="Uploads a MusicXML or MIDI file, runs the full import pipeline, "
                "and persists the normalized song to PostgreSQL. Blocks commit if "
                "critical validation errors are detected. Updates existing songs "
                "if title and composer match.",
    responses={
        400: {"description": "File is empty, corrupt, or has critical validation errors."},
        413: {"description": "File exceeds maximum size (5 MB)."},
        415: {"description": "Unsupported file type."},
    }
)
async def commit_import(file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_bytes = await file.read()
    filename = file.filename or "upload.xml"

    _validate_upload(file_bytes, filename)

    try:
        parsed, warnings, chords, expected_events, missions, measure_count = _run_pipeline(
            file_bytes, filename
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Import commit failed: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")

    # Block commit if there are critical validation errors
    critical = [w for w in warnings if "no parsed notes" in w.lower() or "missing" in w.lower()]
    if critical:
        return ImportCommitResponse(
            success=False, message=f"Import blocked: {'; '.join(critical)}"
        )

    # Check for existing song
    existing = db.query(Song).filter(
        Song.title == parsed.get("title"),
        Song.composer == parsed.get("composer")
    ).first()

    if existing:
        existing.bpm = parsed.get("bpm", 60)
        existing.key_signature = parsed.get("key_signature")
        existing.time_signature = parsed.get("time_signature")
        existing.missions = missions
        existing.sections = parsed.get("sections", [])
        existing.steps = parsed.get("steps", [])
        existing.adaptive_thresholds = parsed.get("adaptive_thresholds", {})
        db.commit()
        return ImportCommitResponse(
            success=True, song_id=str(existing.id),
            message=f"Updated existing song: {parsed['title']}"
        )

    new_song = Song(
        title=parsed.get("title", "Imported Song"),
        composer=parsed.get("composer", "Unknown"),
        difficulty="Level 1",
        bpm=parsed.get("bpm", 60),
        key_signature=parsed.get("key_signature"),
        time_signature=parsed.get("time_signature"),
        educational_category="Imported",
        learning_objectives=[],
        skills_required=[],
        skills_reinforced=[],
        prerequisite_lesson_slugs=[],
        missions=missions,
        sections=parsed.get("sections", []),
        steps=parsed.get("steps", []),
        adaptive_thresholds=parsed.get("adaptive_thresholds", {})
    )
    db.add(new_song)
    db.commit()
    db.refresh(new_song)

    return ImportCommitResponse(
        success=True, song_id=str(new_song.id),
        message=f"Successfully imported: {parsed['title']}"
    )
