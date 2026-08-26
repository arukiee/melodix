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
    limit: int = Query(10, ge=1, le=10),
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
    
    results = await search_engine.search(query=q, filters=filters, db=db)
    return results

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

@router.get("", response_model=List[SongSchema])
@router.get("/", response_model=List[SongSchema])
def list_songs(
    q: Optional[str] = Query(None, description="Search term for title, composer, or artist"),
    genre: Optional[str] = Query(None, description="Filter by genre"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty level"),
    db: Session = Depends(get_db)
):
    query = db.query(Song)
    
    if q and q.strip():
        search_term = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Song.title.ilike(search_term),
                Song.composer.ilike(search_term),
                Song.artist.ilike(search_term),
                Song.genre.ilike(search_term)
            )
        )

    if genre and genre.strip():
        query = query.filter(Song.genre.ilike(genre.strip()))

    if difficulty and difficulty.strip():
        query = query.filter(Song.difficulty.ilike(difficulty.strip()))

    return query.order_by(Song.title.asc()).all()

@router.get("/{song_id}", response_model=SongSchema)
def get_song(song_id: UUID, db: Session = Depends(get_db)):
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    return song

@router.post("/", response_model=SongSchema, status_code=status.HTTP_201_CREATED)
def create_song(song_in: SongCreate, db: Session = Depends(get_db)):
    new_song = Song(
        title=song_in.title,
        composer=song_in.composer,
        artist=song_in.artist,
        genre=song_in.genre,
        difficulty=song_in.difficulty or "Beginner",
        bpm=song_in.bpm or 120,
        key_signature=song_in.key_signature or "C Major",
        time_signature=song_in.time_signature or "4/4",
        duration=song_in.duration or 180,
        source_type=song_in.source_type or "MIDI",
        file_url=song_in.file_url,
        thumbnail_url=song_in.thumbnail_url
    )
    db.add(new_song)
    db.commit()
    db.refresh(new_song)
    return new_song

@router.patch("/{song_id}", response_model=SongSchema)
def update_song(song_id: UUID, updates: SongUpdate, db: Session = Depends(get_db)):
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(song, field, value)

    db.commit()
    db.refresh(song)
    return song

@router.delete("/{song_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_song(song_id: UUID, db: Session = Depends(get_db)):
    song = db.query(Song).filter(Song.id == song_id).first()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    db.delete(song)
    db.commit()
    return None
