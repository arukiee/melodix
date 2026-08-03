import sys
import os
import uuid
from sqlalchemy.orm import Session

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.core.database import SessionLocal
from app.models.song import Song

SEED_SONGS = [
    {
        "title": "Clair de Lune",
        "composer": "Claude Debussy",
        "artist": "Claude Debussy",
        "genre": "Classical",
        "difficulty": "Advanced",
        "bpm": 66,
        "key_signature": "Db Major",
        "time_signature": "9/8",
        "duration": 300,
        "source_type": "MIDI",
        "file_url": "https://cdn.melodix.ai/songs/clair_de_lune.mid",
        "thumbnail_url": "https://cdn.melodix.ai/thumbnails/clair_de_lune.jpg"
    },
    {
        "title": "Für Elise",
        "composer": "Ludwig van Beethoven",
        "artist": "Ludwig van Beethoven",
        "genre": "Classical",
        "difficulty": "Intermediate",
        "bpm": 130,
        "key_signature": "A Minor",
        "time_signature": "3/8",
        "duration": 180,
        "source_type": "MIDI",
        "file_url": "https://cdn.melodix.ai/songs/fur_elise.mid",
        "thumbnail_url": "https://cdn.melodix.ai/thumbnails/fur_elise.jpg"
    },
    {
        "title": "Nocturne Op. 9 No. 2",
        "composer": "Frédéric Chopin",
        "artist": "Frédéric Chopin",
        "genre": "Classical",
        "difficulty": "Intermediate",
        "bpm": 120,
        "key_signature": "Eb Major",
        "time_signature": "12/8",
        "duration": 270,
        "source_type": "MIDI",
        "file_url": "https://cdn.melodix.ai/songs/nocturne_op9_no2.mid",
        "thumbnail_url": "https://cdn.melodix.ai/thumbnails/nocturne.jpg"
    },
    {
        "title": "Minuet in G Major",
        "composer": "J.S. Bach",
        "artist": "J.S. Bach",
        "genre": "Classical",
        "difficulty": "Beginner",
        "bpm": 110,
        "key_signature": "G Major",
        "time_signature": "3/4",
        "duration": 90,
        "source_type": "MIDI",
        "file_url": "https://cdn.melodix.ai/songs/minuet_in_g.mid",
        "thumbnail_url": "https://cdn.melodix.ai/thumbnails/minuet.jpg"
    },
    {
        "title": "Gymnopédie No. 1",
        "composer": "Erik Satie",
        "artist": "Erik Satie",
        "genre": "Impressionist",
        "difficulty": "Beginner",
        "bpm": 76,
        "key_signature": "D Major",
        "time_signature": "3/4",
        "duration": 200,
        "source_type": "MIDI",
        "file_url": "https://cdn.melodix.ai/songs/gymnopedie_no1.mid",
        "thumbnail_url": "https://cdn.melodix.ai/thumbnails/gymnopedie.jpg"
    }
]

def seed_songs():
    db: Session = SessionLocal()
    try:
        count = 0
        for song_data in SEED_SONGS:
            existing = db.query(Song).filter(Song.title == song_data["title"]).first()
            if not existing:
                song = Song(**song_data)
                db.add(song)
                count += 1
        db.commit()
        print(f"Successfully seeded {count} new catalog songs.")
    except Exception as exc:
        db.rollback()
        print(f"Error seeding songs: {exc}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_songs()
