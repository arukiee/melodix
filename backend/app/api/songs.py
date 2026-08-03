from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.core.database import get_db
from app.models.song import Song
from app.schemas.song import SongSchema, SongCreate, SongUpdate

router = APIRouter(prefix="/songs", tags=["songs"])

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
