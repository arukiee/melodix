from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.song import Song
from app.models.user import User
from app.schemas.song import SongSchema, SongCreate, SongUpdate
from app.services.provider_ultimate_guitar import ultimate_guitar_provider
from app.services.provider_youtube import youtube_provider

router = APIRouter(prefix="/songs", tags=["songs"])

from app.schemas.search import SearchFilter, SearchResult
from app.services.search.search_engine import search_engine

@router.get("/search", response_model=List[SearchResult])
async def search_songs(
    q: str = Query(..., min_length=1), 
    difficulty: Optional[str] = None,
    genre: Optional[str] = None,
    instrument: Optional[str] = None,
    hasMidi: Optional[bool] = None,
    hasChords: Optional[bool] = None,
    beginnerFriendly: Optional[bool] = None,
    limit: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db)
):
    filters = SearchFilter(
        difficulty=difficulty,
        genre=genre,
        instrument=instrument,
        hasMidi=hasMidi,
        hasChords=hasChords,
        beginnerFriendly=beginnerFriendly,
        limit=limit
    )
    return await search_engine.search(query=q, filters=filters, db=db)

from pydantic import BaseModel

class SpotifySelectRequest(BaseModel):
    spotify_track_id: Optional[str] = None
    title: str
    artist: str
    album: Optional[str] = None
    duration_ms: Optional[int] = None
    album_art_url: Optional[str] = None

class SpotifySelectResponse(BaseModel):
    success: bool
    song_id: str
    processing_job_id: Optional[str] = None
    message: str

@router.post("/select", response_model=SpotifySelectResponse)
async def select_spotify_track(
    request: SpotifySelectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Check for existing song matching title and artist
    existing_song = (
        db.query(Song)
        .filter(
            Song.title.ilike(request.title.strip()),
            or_(Song.artist.ilike(request.artist.strip()), Song.composer.ilike(request.artist.strip()))
        )
        .first()
    )

    if existing_song:
        song = existing_song
        if request.album_art_url and not song.artwork_url:
            song.artwork_url = request.album_art_url
            song.thumbnail_url = request.album_art_url
            db.commit()
    else:
        import uuid
        song = Song(
            id=uuid.uuid4(),
            title=request.title.strip(),
            artist=request.artist.strip(),
            composer=request.artist.strip(),
            album=request.album.strip() if request.album else None,
            duration=int(request.duration_ms / 1000) if request.duration_ms else None,
            artwork_url=request.album_art_url,
            thumbnail_url=request.album_art_url,
            is_learnable=True,
        )
        db.add(song)
        db.commit()
        db.refresh(song)

    # Trigger backend audio discovery & processing pipeline server-side
    from app.services.orchestrator.source_discovery import SourceDiscoveryService
    job_id = None
    try:
        job_id = await SourceDiscoveryService.discover_and_analyze(
            song=song,
            user_id=current_user.id,
            db=db,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio source discovery failed: {str(e)}")

    return SpotifySelectResponse(
        success=True,
        song_id=str(song.id),
        processing_job_id=str(job_id) if job_id else None,
        message="Song selection completed and audio pipeline queued.",
    )


from pydantic import BaseModel
class ImportSearchRequest(BaseModel):
    id: str
    title: str
    artist: str
    provider: str
    youtube_id: str = ""   # video ID passed through for YouTube imports

from app.api.import_song import _run_pipeline
from app.schemas.import_schema import ImportCommitResponse

@router.post("/import_from_search", response_model=ImportCommitResponse)
async def import_from_search(
    request: ImportSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if request.provider == "Local Library":
        return ImportCommitResponse(
            success=True, song_id=request.id,
            message="Already in library."
        )
        
    provider = search_engine.get_provider(request.provider)
    if not provider:
        raise HTTPException(status_code=400, detail="Unknown provider")
        
    # Fetch raw data
    try:
        raw_data = await provider.get_raw_data(request.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch data: {str(e)}")
        
    # Run through the pipeline
    # Route to correct importer by setting specific file extensions based on the search provider
    if request.provider == "Ultimate Guitar":
        filename = "chords.ug"
    elif request.provider == "YouTube":
        filename = "youtube.yt"
    elif request.provider == "BitMidi":
        filename = "song.mid"
    else:
        filename = "download.mid"

    try:
        parsed, warnings, chords, expected_events, missions, measure_count = _run_pipeline(
            raw_data, filename
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")

    title = parsed.get("title") or request.title or "Imported Song"
    composer = parsed.get("composer") or request.artist or "Unknown"

    # Check for existing song
    existing = db.query(Song).filter(
        Song.title == title,
        Song.composer == composer
    ).first()

    if existing:
        existing.bpm = parsed.get("bpm", 60)
        existing.key_signature = parsed.get("key_signature")
        existing.time_signature = parsed.get("time_signature")
        existing.missions = missions
        existing.sections = parsed.get("sections", [])
        existing.steps = parsed.get("steps", [])
        existing.adaptive_thresholds = parsed.get("adaptive_thresholds", {})
        # Persist YouTube video ID so source discovery can download audio later
        if request.provider == "YouTube" and request.youtube_id:
            existing.file_url = f"https://www.youtube.com/watch?v={request.youtube_id}"
        db.commit()
        return ImportCommitResponse(
            success=True, song_id=str(existing.id),
            message=f"Updated existing song: {existing.title}"
        )

    new_song = Song(
        title=title,
        composer=composer,
        artist=request.artist,
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
        adaptive_thresholds=parsed.get("adaptive_thresholds", {}),
        # Store YouTube video URL so source discovery can download audio
        file_url=(
            f"https://www.youtube.com/watch?v={request.youtube_id}"
            if request.provider == "YouTube" and request.youtube_id
            else None
        ),
    )
    db.add(new_song)
    db.commit()
    db.refresh(new_song)

    return ImportCommitResponse(
        success=True, song_id=str(new_song.id),
        message=f"Successfully imported: {new_song.title}"
    )

from app.api.deps import get_optional_user
from app.models.discovery import SavedSong, SongLearningProgress, Classroom, ClassMembership, ClassSongAssignment
from app.schemas.song import (
    AutocompleteSuggestion,
    AssignSongRequest,
    ClassroomSchema,
    StartLearningRequest,
)
from app.services.discovery.catalog_search import search_catalog, autocomplete_catalog
from app.services.discovery.serialize import serialize_song, saved_song_ids
from app.services.music_engine.practice_session_service import progress_summary_for_song
from datetime import datetime, timezone


def _attach_learning_progress(payload: dict, db: Session, current_user: Optional[User]) -> dict:
    if not current_user:
        return payload
    song_id = payload.get("id")
    if not song_id:
        return payload
    payload.update(progress_summary_for_song(db, current_user.id, song_id if isinstance(song_id, UUID) else UUID(str(song_id))))
    return payload

@router.get("/catalog")
def catalog_search(
    q: Optional[str] = Query(None, description="Title and artist search"),
    difficulty: Optional[str] = None,
    genre: Optional[str] = None,
    mood: Optional[str] = None,
    tempo: Optional[str] = Query(None, description="slow, medium, fast, or min-max BPM"),
    language: Optional[str] = None,
    skill: Optional[str] = None,
    limit: int = Query(24, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    ids = saved_song_ids(db, current_user.id) if current_user else set()
    return search_catalog(
        db,
        q=q,
        difficulty=difficulty,
        genre=genre,
        mood=mood,
        tempo=tempo,
        language=language,
        skill=skill,
        limit=limit,
        saved_ids=ids,
    )


@router.get("/autocomplete", response_model=List[AutocompleteSuggestion])
def catalog_autocomplete(
    q: str = Query(..., min_length=1),
    limit: int = Query(8, ge=1, le=20),
    db: Session = Depends(get_db),
):
    return autocomplete_catalog(db, q, limit=limit)


@router.get("", response_model=List[SongSchema])
@router.get("/", response_model=List[SongSchema])
def list_songs(
    q: Optional[str] = Query(None, description="Search term for title, composer, or artist"),
    genre: Optional[str] = Query(None, description="Filter by genre"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty level"),
    mood: Optional[str] = Query(None),
    tempo: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    skill: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    ids = saved_song_ids(db, current_user.id) if current_user else set()
    songs = search_catalog(
        db,
        q=q,
        difficulty=difficulty,
        genre=genre,
        mood=mood,
        tempo=tempo,
        language=language,
        skill=skill,
        limit=100,
        saved_ids=ids,
    )
    return [_attach_learning_progress(item, db, current_user) for item in songs]

@router.get("/{song_id}", response_model=SongSchema)
def get_song(
    song_id: UUID,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    saved = False
    if current_user:
        saved = db.query(SavedSong).filter(
            SavedSong.user_id == current_user.id,
            SavedSong.song_id == song.id,
        ).first() is not None
    return _attach_learning_progress(serialize_song(song, saved=saved), db, current_user)

@router.post("/{song_id}/save")
def save_song(
    song_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    existing = db.query(SavedSong).filter(
        SavedSong.user_id == current_user.id, SavedSong.song_id == song_id
    ).first()
    if not existing:
        db.add(SavedSong(user_id=current_user.id, song_id=song_id))
        db.commit()
    return {"saved": True}


@router.delete("/{song_id}/save")
def unsave_song(
    song_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(SavedSong).filter(
        SavedSong.user_id == current_user.id, SavedSong.song_id == song_id
    ).first()
    if existing:
        db.delete(existing)
        db.commit()
    return {"saved": False}


@router.post("/{song_id}/start")
def start_learning(
    song_id: UUID,
    payload: StartLearningRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    arrangement = payload.arrangement if payload.arrangement in (song.available_arrangements or ["Easy", "Medium", "Hard"]) else "Easy"
    progress = db.query(SongLearningProgress).filter(
        SongLearningProgress.user_id == current_user.id,
        SongLearningProgress.song_id == song_id,
    ).first()
    if not progress:
        progress = SongLearningProgress(
            user_id=current_user.id,
            song_id=song_id,
            arrangement=arrangement,
            last_played_at=datetime.now(timezone.utc),
        )
        db.add(progress)
    else:
        progress.arrangement = arrangement
        progress.last_played_at = datetime.now(timezone.utc)
    db.commit()
    return {"song_id": str(song_id), "arrangement": arrangement}


@router.post("/{song_id}/assign")
def assign_song_to_class(
    song_id: UUID,
    payload: AssignSongRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if (current_user.role or "").upper() not in ("TEACHER", "ADMIN"):
        raise HTTPException(status_code=403, detail="Only teachers can assign songs")
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    classroom = None
    if payload.class_id:
        classroom = db.query(Classroom).filter(
            Classroom.id == payload.class_id,
            Classroom.teacher_id == current_user.id,
        ).first()
    if not classroom:
        name = (payload.class_name or "").strip() or "My Class"
        classroom = db.query(Classroom).filter(
            Classroom.teacher_id == current_user.id,
            Classroom.name == name,
        ).first()
        if not classroom:
            classroom = Classroom(name=name, teacher_id=current_user.id)
            db.add(classroom)
            db.flush()

    assignment = ClassSongAssignment(
        class_id=classroom.id,
        song_id=song_id,
        assigned_by=current_user.id,
    )
    db.add(assignment)
    db.commit()
    return {"assigned": True, "class_id": str(classroom.id), "class_name": classroom.name}


@router.post("/", response_model=SongSchema, status_code=status.HTTP_201_CREATED)
def create_song(song_in: SongCreate, db: Session = Depends(get_db)):
    tempo = song_in.tempo or song_in.bpm or 120
    artwork = song_in.artwork_url or song_in.thumbnail_url
    new_song = Song(
        title=song_in.title,
        composer=song_in.composer,
        artist=song_in.artist,
        album=song_in.album,
        genre=song_in.genre,
        mood=song_in.mood,
        language=song_in.language,
        difficulty=song_in.difficulty or "Beginner",
        bpm=tempo,
        tempo=tempo,
        key_signature=song_in.key_signature or "C Major",
        time_signature=song_in.time_signature or "4/4",
        duration=song_in.duration or 180,
        source_type=song_in.source_type or "MIDI",
        file_url=song_in.file_url,
        thumbnail_url=artwork,
        artwork_url=artwork,
        skills=song_in.skills or song_in.skills_required or [],
        available_arrangements=song_in.available_arrangements or ["Easy", "Medium", "Hard"],
        is_learnable=song_in.is_learnable if song_in.is_learnable is not None else True,
        educational_category=song_in.educational_category,
        learning_objectives=song_in.learning_objectives,
        skills_required=song_in.skills_required,
        skills_reinforced=song_in.skills_reinforced,
        prerequisite_lesson_slugs=song_in.prerequisite_lesson_slugs,
        mastery_threshold_percentage=song_in.mastery_threshold_percentage,
        ai_coaching_focus=song_in.ai_coaching_focus,
        teacher_notes=song_in.teacher_notes,
    )
    db.add(new_song)
    db.commit()
    db.refresh(new_song)
    return serialize_song(new_song)

@router.patch("/{song_id}", response_model=SongSchema)
def update_song(song_id: UUID, updates: SongUpdate, db: Session = Depends(get_db)):
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    update_data = updates.model_dump(exclude_unset=True)
    if "tempo" in update_data and "bpm" not in update_data:
        update_data["bpm"] = update_data["tempo"]
    for field, value in update_data.items():
        setattr(song, field, value)

    db.commit()
    db.refresh(song)
    return serialize_song(song)

@router.delete("/{song_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_song(song_id: UUID, db: Session = Depends(get_db)):
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    db.delete(song)
    db.commit()
    return None
