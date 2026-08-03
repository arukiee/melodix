import sys
import os
from sqlalchemy.orm import Session

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.core.database import SessionLocal
from app.models.song import Song

# Genuine, educationally rich piano repertoire (35+ pieces across Beginner, Intermediate, and Advanced)
EXPANDED_SONG_CATALOG = [
    # --- BEGINNER REPERTOIRE ---
    {
        "title": "Minuet in G Major (BWV Anh. 114)",
        "composer": "J.S. Bach / Christian Petzold",
        "artist": "J.S. Bach",
        "genre": "Baroque",
        "difficulty": "Beginner",
        "bpm": 110,
        "key_signature": "G Major",
        "time_signature": "3/4",
        "duration": 105,
        "source_type": "MIDI",
        "file_url": "https://cdn.melodix.ai/songs/minuet_in_g.mid",
        "thumbnail_url": "https://images.unsplash.com/photo-1520523839897-bd0b52f945a0?w=600&auto=format&fit=crop"
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
        "thumbnail_url": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=600&auto=format&fit=crop"
    },
    {
        "title": "Ode to Joy (Symphony No. 9)",
        "composer": "Ludwig van Beethoven",
        "artist": "Ludwig van Beethoven",
        "genre": "Classical",
        "difficulty": "Beginner",
        "bpm": 100,
        "key_signature": "D Major",
        "time_signature": "4/4",
        "duration": 90,
        "source_type": "MIDI",
        "file_url": "https://cdn.melodix.ai/songs/ode_to_joy.mid",
        "thumbnail_url": "https://images.unsplash.com/photo-1507838153414-b4b713384a76?w=600&auto=format&fit=crop"
    },
    {
        "title": "Canon in D (Simple Arrangement)",
        "composer": "Johann Pachelbel",
        "artist": "Johann Pachelbel",
        "genre": "Baroque",
        "difficulty": "Beginner",
        "bpm": 80,
        "key_signature": "D Major",
        "time_signature": "4/4",
        "duration": 150,
        "source_type": "MIDI",
        "file_url": "https://cdn.melodix.ai/songs/canon_in_d_easy.mid",
        "thumbnail_url": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=600&auto=format&fit=crop"
    },
    {
        "title": "Twinkle, Twinkle, Little Star (Theme & Var 1)",
        "composer": "Traditional / W.A. Mozart",
        "artist": "W.A. Mozart",
        "genre": "Classical",
        "difficulty": "Beginner",
        "bpm": 108,
        "key_signature": "C Major",
        "time_signature": "2/4",
        "duration": 75,
        "source_type": "MIDI",
        "file_url": "https://cdn.melodix.ai/songs/twinkle_mozart.mid",
        "thumbnail_url": "https://images.unsplash.com/photo-1518609878373-06d740f60d8b?w=600&auto=format&fit=crop"
    },
    {
        "title": "Hanon Exercise No. 1 (5-Finger Independence)",
        "composer": "Charles-Louis Hanon",
        "artist": "Charles-Louis Hanon",
        "genre": "Etude",
        "difficulty": "Beginner",
        "bpm": 90,
        "key_signature": "C Major",
        "time_signature": "2/4",
        "duration": 120,
        "source_type": "MIDI",
        "file_url": "https://cdn.melodix.ai/songs/hanon_1.mid",
        "thumbnail_url": "https://images.unsplash.com/photo-1520523839897-bd0b52f945a0?w=600&auto=format&fit=crop"
    },
    {
        "title": "Musette in D Major (BWV Anh. 126)",
        "composer": "J.S. Bach",
        "artist": "J.S. Bach",
        "genre": "Baroque",
        "difficulty": "Beginner",
        "bpm": 120,
        "key_signature": "D Major",
        "time_signature": "2/4",
        "duration": 85,
        "source_type": "MIDI",
        "file_url": "https://cdn.melodix.ai/songs/musette_in_d.mid",
        "thumbnail_url": "https://images.unsplash.com/photo-1507838153414-b4b713384a76?w=600&auto=format&fit=crop"
    },
    {
        "title": "Sonatina in C Major (Op. 36 No. 1 - Allegro)",
        "composer": "Muzio Clementi",
        "artist": "Muzio Clementi",
        "genre": "Classical",
        "difficulty": "Beginner",
        "bpm": 124,
        "key_signature": "C Major",
        "time_signature": "2/2",
        "duration": 110,
        "source_type": "MUSICXML",
        "file_url": "https://cdn.melodix.ai/songs/clementi_op36_no1.xml",
        "thumbnail_url": "https://images.unsplash.com/photo-1518609878373-06d740f60d8b?w=600&auto=format&fit=crop"
    },
    {
        "title": "Arabesque (Op. 100 No. 2)",
        "composer": "Johann Friedrich Burgmüller",
        "artist": "Burgmüller",
        "genre": "Etude",
        "difficulty": "Beginner",
        "bpm": 132,
        "key_signature": "A Minor",
        "time_signature": "2/4",
        "duration": 80,
        "source_type": "MIDI",
        "file_url": "https://cdn.melodix.ai/songs/burgmuller_arabesque.mid",
        "thumbnail_url": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=600&auto=format&fit=crop"
    },
    {
        "title": "Spinning Song (Op. 14 No. 4)",
        "composer": "Albert Ellmenreich",
        "artist": "Ellmenreich",
        "genre": "Romantic",
        "difficulty": "Beginner",
        "bpm": 140,
        "key_signature": "F Major",
        "time_signature": "3/8",
        "duration": 95,
        "source_type": "MIDI",
        "file_url": "https://cdn.melodix.ai/songs/spinning_song.mid",
        "thumbnail_url": "https://images.unsplash.com/photo-1520523839897-bd0b52f945a0?w=600&auto=format&fit=crop"
    },
    {
        "title": "The Wild Rider (Op. 68 No. 8)",
        "composer": "Robert Schumann",
        "artist": "Robert Schumann",
        "genre": "Romantic",
        "difficulty": "Beginner",
        "bpm": 130,
        "key_signature": "A Minor",
        "time_signature": "6/8",
        "duration": 70,
        "source_type": "MIDI",
        "file_url": "https://cdn.melodix.ai/songs/schumann_wild_rider.mid",
        "thumbnail_url": "https://images.unsplash.com/photo-1507838153414-b4b713384a76?w=600&auto=format&fit=crop"
    },

    # --- INTERMEDIATE REPERTOIRE ---
    {
        "title": "Für Elise (Bagatelle No. 25 in A Minor)",
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
        "thumbnail_url": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=600&auto=format&fit=crop"
    },
    {
        "title": "Nocturne Op. 9 No. 2",
        "composer": "Frédéric Chopin",
        "artist": "Frédéric Chopin",
        "genre": "Romantic",
        "difficulty": "Intermediate",
        "bpm": 120,
        "key_signature": "Eb Major",
        "time_signature": "12/8",
        "duration": 270,
        "source_type": "MIDI",
        "file_url": "https://cdn.melodix.ai/songs/nocturne_op9_no2.mid",
        "thumbnail_url": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=600&auto=format&fit=crop"
    },
    {
        "title": "Prelude in C Major (Well-Tempered Clavier BWV 846)",
        "composer": "J.S. Bach",
        "artist": "J.S. Bach",
        "genre": "Baroque",
        "difficulty": "Intermediate",
        "bpm": 72,
        "key_signature": "C Major",
        "time_signature": "4/4",
        "duration": 130,
        "source_type": "MUSICXML",
        "file_url": "https://cdn.melodix.ai/songs/bach_wtc1_prelude1.xml",
        "thumbnail_url": "https://images.unsplash.com/photo-1520523839897-bd0b52f945a0?w=600&auto=format&fit=crop"
    },
    {
        "title": "Waltz in A Minor (B. 150)",
        "composer": "Frédéric Chopin",
        "artist": "Frédéric Chopin",
        "genre": "Romantic",
        "difficulty": "Intermediate",
        "bpm": 112,
        "key_signature": "A Minor",
        "time_signature": "3/4",
        "duration": 145,
        "source_type": "MIDI",
        "file_url": "https://cdn.melodix.ai/songs/chopin_waltz_a_minor.mid",
        "thumbnail_url": "https://images.unsplash.com/photo-1518609878373-06d740f60d8b?w=600&auto=format&fit=crop"
    },
    {
        "title": "Gnossienne No. 1",
        "composer": "Erik Satie",
        "artist": "Erik Satie",
        "genre": "Impressionist",
        "difficulty": "Intermediate",
        "bpm": 60,
        "key_signature": "F Minor",
        "time_signature": "Free Tempo",
        "duration": 210,
        "source_type": "MIDI",
        "file_url": "https://cdn.melodix.ai/songs/gnossienne_1.mid",
        "thumbnail_url": "https://images.unsplash.com/photo-1507838153414-b4b713384a76?w=600&auto=format&fit=crop"
    },
    {
        "title": "Turkish March (Rondo alla Turca K. 331)",
        "composer": "W.A. Mozart",
        "artist": "W.A. Mozart",
        "genre": "Classical",
        "difficulty": "Intermediate",
        "bpm": 128,
        "key_signature": "A Minor",
        "time_signature": "2/4",
        "duration": 205,
        "source_type": "MIDI",
        "file_url": "https://cdn.melodix.ai/songs/rondo_alla_turca.mid",
        "thumbnail_url": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=600&auto=format&fit=crop"
    },
    {
        "title": "Piano Sonata No. 16 in C Major ('Facile' K. 545)",
        "composer": "W.A. Mozart",
        "artist": "W.A. Mozart",
        "genre": "Classical",
        "difficulty": "Intermediate",
        "bpm": 132,
        "key_signature": "C Major",
        "time_signature": "4/4",
        "duration": 210,
        "source_type": "MIDI",
        "file_url": "https://cdn.melodix.ai/songs/mozart_k545.mid",
        "thumbnail_url": "https://images.unsplash.com/photo-1520523839897-bd0b52f945a0?w=600&auto=format&fit=crop"
    },
    {
        "title": "Moonlight Sonata (1st Movement - Adagio Sostenuto)",
        "composer": "Ludwig van Beethoven",
        "artist": "Ludwig van Beethoven",
        "genre": "Romantic",
        "difficulty": "Intermediate",
        "bpm": 60,
        "key_signature": "C# Minor",
        "time_signature": "4/4",
        "duration": 360,
        "source_type": "MIDI",
        "file_url": "https://cdn.melodix.ai/songs/moonlight_sonata_1st.mid",
        "thumbnail_url": "https://images.unsplash.com/photo-1507838153414-b4b713384a76?w=600&auto=format&fit=crop"
    },
    {
        "title": "The Entertainer (Ragtime Two-Step)",
        "composer": "Scott Joplin",
        "artist": "Scott Joplin",
        "genre": "Ragtime",
        "difficulty": "Intermediate",
        "bpm": 100,
        "key_signature": "C Major",
        "time_signature": "2/4",
        "duration": 230,
        "source_type": "MIDI",
        "file_url": "https://cdn.melodix.ai/songs/the_entertainer.mid",
        "thumbnail_url": "https://images.unsplash.com/photo-1518609878373-06d740f60d8b?w=600&auto=format&fit=crop"
    },
    {
        "title": "Prelude in E Minor (Op. 28 No. 4)",
        "composer": "Frédéric Chopin",
        "artist": "Frédéric Chopin",
        "genre": "Romantic",
        "difficulty": "Intermediate",
        "bpm": 50,
        "key_signature": "E Minor",
        "time_signature": "2/2",
        "duration": 140,
        "source_type": "MIDI",
        "file_url": "https://cdn.melodix.ai/songs/chopin_prelude_e_minor.mid",
        "thumbnail_url": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=600&auto=format&fit=crop"
    },
    {
        "title": "The Swan (Le Cygne from Carnival of the Animals)",
        "composer": "Camille Saint-Saëns",
        "artist": "Saint-Saëns",
        "genre": "Romantic",
        "difficulty": "Intermediate",
        "bpm": 68,
        "key_signature": "G Major",
        "time_signature": "6/4",
        "duration": 175,
        "source_type": "MIDI",
        "file_url": "https://cdn.melodix.ai/songs/saint_saens_swan.mid",
        "thumbnail_url": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=600&auto=format&fit=crop"
    },

    # --- ADVANCED REPERTOIRE ---
    {
        "title": "Clair de Lune (Suite Bergamasque)",
        "composer": "Claude Debussy",
        "artist": "Claude Debussy",
        "genre": "Impressionist",
        "difficulty": "Advanced",
        "bpm": 66,
        "key_signature": "Db Major",
        "time_signature": "9/8",
        "duration": 300,
        "source_type": "MIDI",
        "file_url": "https://cdn.melodix.ai/songs/clair_de_lune.mid",
        "thumbnail_url": "https://images.unsplash.com/photo-1520523839897-bd0b52f945a0?w=600&auto=format&fit=crop"
    },
    {
        "title": "Rêverie (L. 68)",
        "composer": "Claude Debussy",
        "artist": "Claude Debussy",
        "genre": "Impressionist",
        "difficulty": "Advanced",
        "bpm": 64,
        "key_signature": "F Major",
        "time_signature": "4/4",
        "duration": 260,
        "source_type": "MUSICXML",
        "file_url": "https://cdn.melodix.ai/songs/debussy_reverie.xml",
        "thumbnail_url": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=600&auto=format&fit=crop"
    },
    {
        "title": "Liebestraum No. 3 in Ab Major",
        "composer": "Franz Liszt",
        "artist": "Franz Liszt",
        "genre": "Romantic",
        "difficulty": "Advanced",
        "bpm": 72,
        "key_signature": "Ab Major",
        "time_signature": "6/4",
        "duration": 290,
        "source_type": "MIDI",
        "file_url": "https://cdn.melodix.ai/songs/liebestraum_3.mid",
        "thumbnail_url": "https://images.unsplash.com/photo-1507838153414-b4b713384a76?w=600&auto=format&fit=crop"
    },
    {
        "title": "Fantaisie-Impromptu in C# Minor (Op. 66)",
        "composer": "Frédéric Chopin",
        "artist": "Frédéric Chopin",
        "genre": "Romantic",
        "difficulty": "Advanced",
        "bpm": 160,
        "key_signature": "C# Minor",
        "time_signature": "4/4",
        "duration": 310,
        "source_type": "MIDI",
        "file_url": "https://cdn.melodix.ai/songs/fantaisie_impromptu.mid",
        "thumbnail_url": "https://images.unsplash.com/photo-1518609878373-06d740f60d8b?w=600&auto=format&fit=crop"
    },
    {
        "title": "La Campanella (Grandes Études de Paganini No. 3)",
        "composer": "Franz Liszt",
        "artist": "Franz Liszt",
        "genre": "Virtuoso Etude",
        "difficulty": "Advanced",
        "bpm": 136,
        "key_signature": "G# Minor",
        "time_signature": "6/8",
        "duration": 280,
        "source_type": "MIDI",
        "file_url": "https://cdn.melodix.ai/songs/la_campanella.mid",
        "thumbnail_url": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=600&auto=format&fit=crop"
    },
    {
        "title": "Maple Leaf Rag",
        "composer": "Scott Joplin",
        "artist": "Scott Joplin",
        "genre": "Ragtime",
        "difficulty": "Advanced",
        "bpm": 100,
        "key_signature": "Ab Major",
        "time_signature": "2/4",
        "duration": 190,
        "source_type": "MIDI",
        "file_url": "https://cdn.melodix.ai/songs/maple_leaf_rag.mid",
        "thumbnail_url": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=600&auto=format&fit=crop"
    },
    {
        "title": "Prelude in C# Minor (Op. 3 No. 2)",
        "composer": "Sergei Rachmaninoff",
        "artist": "Sergei Rachmaninoff",
        "genre": "Late Romantic",
        "difficulty": "Advanced",
        "bpm": 60,
        "key_signature": "C# Minor",
        "time_signature": "4/4",
        "duration": 240,
        "source_type": "MIDI",
        "file_url": "https://cdn.melodix.ai/songs/rachmaninoff_prelude_c_sharp_minor.mid",
        "thumbnail_url": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=600&auto=format&fit=crop"
    },
    {
        "title": "Consolation No. 3 in Db Major",
        "composer": "Franz Liszt",
        "artist": "Franz Liszt",
        "genre": "Romantic",
        "difficulty": "Advanced",
        "bpm": 60,
        "key_signature": "Db Major",
        "time_signature": "4/4",
        "duration": 250,
        "source_type": "MIDI",
        "file_url": "https://cdn.melodix.ai/songs/liszt_consolation_3.mid",
        "thumbnail_url": "https://images.unsplash.com/photo-1520523839897-bd0b52f945a0?w=600&auto=format&fit=crop"
    }
]

def seed_expanded_catalog():
    db: Session = SessionLocal()
    try:
        count = 0
        for song_data in EXPANDED_SONG_CATALOG:
            existing = db.query(Song).filter(Song.title == song_data["title"]).first()
            if not existing:
                song = Song(**song_data)
                db.add(song)
                count += 1
            else:
                for key, val in song_data.items():
                    setattr(existing, key, val)
        db.commit()
        print(f"Successfully seeded/updated {len(EXPANDED_SONG_CATALOG)} repertoire pieces ({count} new).")
    except Exception as exc:
        db.rollback()
        print(f"Error seeding catalog: {exc}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_expanded_catalog()
