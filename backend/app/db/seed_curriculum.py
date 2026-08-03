import sys
import os
import uuid
from datetime import datetime
from sqlalchemy.orm import Session

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.core.database import SessionLocal
from app.models.lesson import Lesson
from app.models.song import Song

CURRICULUM_LESSONS = [
    # --- BEGINNER PATH ---
    {
        "title": "Keyboard Foundations & Middle C",
        "slug": "keyboard-foundations-middle-c",
        "description": "Learn key names, posture, octave orientation, and locate Middle C with right hand 1st finger.",
        "category": "Basics",
        "difficulty": "BEGINNER",
        "genre": "Classical",
        "estimated_duration": 10,
        "display_order": 1,
        "objectives": [
            {"id": "obj-1", "title": "Locate Middle C", "description": "Identify Middle C relative to 2-black key groups."},
            {"id": "obj-2", "title": "Proper Posture", "description": "Maintain curved fingers and relaxed wrists."}
        ],
        "is_published": True
    },
    {
        "title": "Five-Finger Position & Right Hand Melody",
        "slug": "five-finger-position-rh-melody",
        "description": "Master C-D-E-F-G 5-finger position, finger numbers 1 through 5, and play your first right-hand melody.",
        "category": "Finger Technique",
        "difficulty": "BEGINNER",
        "genre": "Classical",
        "estimated_duration": 15,
        "display_order": 2,
        "objectives": [
            {"id": "obj-1", "title": "Finger Independence", "description": "Play fingers 1-5 without collapsing knuckles."},
            {"id": "obj-2", "title": "Quarter & Half Notes", "description": "Keep steady 4/4 meter at 60 bpm."}
        ],
        "is_published": True
    },
    {
        "title": "Left Hand Bass Lines & Coordination",
        "slug": "lh-bass-lines-coordination",
        "description": "Introduce Bass Clef, C-G left hand position, and simple drone bass accompaniment.",
        "category": "Coordination",
        "difficulty": "BEGINNER",
        "genre": "Classical",
        "estimated_duration": 20,
        "display_order": 3,
        "objectives": [
            {"id": "obj-1", "title": "Bass Clef Reading", "description": "Identify C3 and G3 in Bass Clef."},
            {"id": "obj-2", "title": "Hand Coordination", "description": "Play LH whole notes while RH plays 5-note melody."}
        ],
        "is_published": True
    },
    {
        "title": "Minuet in G Major – Section A",
        "slug": "minuet-in-g-major-section-a",
        "description": "Learn J.S. Bach's iconic Minuet in G Major in 3/4 time with legato phrasing.",
        "category": "Repertoire",
        "difficulty": "BEGINNER",
        "genre": "Baroque",
        "estimated_duration": 20,
        "display_order": 4,
        "objectives": [
            {"id": "obj-1", "title": "3/4 Dance Meter", "description": "Count 1-2-3 pulse with emphasis on beat 1."},
            {"id": "obj-2", "title": "Hands Together Part 1", "description": "Combine RH melody with LH G-B-D accompaniment."}
        ],
        "is_published": True
    },

    # --- INTERMEDIATE PATH ---
    {
        "title": "Major Scale Fingerings & Thumb Tucks",
        "slug": "major-scale-fingerings-thumb-tucks",
        "description": "Master C Major and G Major 1-octave scales with smooth thumb-under tucks.",
        "category": "Technical Drills",
        "difficulty": "INTERMEDIATE",
        "genre": "Classical",
        "estimated_duration": 20,
        "display_order": 5,
        "objectives": [
            {"id": "obj-1", "title": "Thumb Under Tuck", "description": "Pass finger 1 under finger 3 smoothly."},
            {"id": "obj-2", "title": "Scale Evenness", "description": "Maintain equal tone volume across all 8 scale degrees."}
        ],
        "is_published": True
    },
    {
        "title": "Für Elise – Main Theme & Arpeggios",
        "slug": "fur-elise-main-theme",
        "description": "Study Beethoven's classic in 3/8 time featuring alternating E-D# motifs and A minor arpeggios.",
        "category": "Repertoire",
        "difficulty": "INTERMEDIATE",
        "genre": "Romantic",
        "estimated_duration": 30,
        "display_order": 6,
        "objectives": [
            {"id": "obj-1", "title": "Chromatic Alternation", "description": "Execute E5-D#5 semitone shift with finger 5-4."},
            {"id": "obj-2", "title": "Left Hand Arpeggio Sweep", "description": "Play A-E-A broken chords smoothly."}
        ],
        "is_published": True
    },
    {
        "title": "Nocturne Op. 9 No. 2 – Rubato Phrasing",
        "slug": "nocturne-op9-no2-rubato",
        "description": "Explore Chopin's bel canto melody over Eb major waltz bass with expressive rubato timing.",
        "category": "Expression",
        "difficulty": "INTERMEDIATE",
        "genre": "Romantic",
        "estimated_duration": 30,
        "display_order": 7,
        "objectives": [
            {"id": "obj-1", "title": "Bel Canto Line", "description": "Project RH melody over soft LH accompaniment."},
            {"id": "obj-2", "title": "Expressive Rubato", "description": "Apply subtle tempo fluctuation at cadences."}
        ],
        "is_published": True
    },

    # --- ADVANCED PATH ---
    {
        "title": "Clair de Lune – Impressionist Textures & 9/8 Meter",
        "slug": "clair-de-lune-impressionist-textures",
        "description": "Master Debussy's masterpiece in Db Major with complex 9/8 compound meter and delicate pianissimo touch.",
        "category": "Advanced Repertoire",
        "difficulty": "ADVANCED",
        "genre": "Impressionist",
        "estimated_duration": 45,
        "display_order": 8,
        "objectives": [
            {"id": "obj-1", "title": "Compound 9/8 Meter", "description": "Subdivide 9 beats per measure into 3 groups of 3."},
            {"id": "obj-2", "title": "Coloristic Voicing", "description": "Bring out top melody notes within dense 3-part chords."}
        ],
        "is_published": True
    },
    {
        "title": "Polyphonic Sight Reading & Counterpoint",
        "slug": "polyphonic-sight-reading-counterpoint",
        "description": "Independent voice leading in J.S. Bach 3-part Inventions with subjects and countersubjects.",
        "category": "Masterclass",
        "difficulty": "ADVANCED",
        "genre": "Baroque",
        "estimated_duration": 40,
        "display_order": 9,
        "objectives": [
            {"id": "obj-1", "title": "Subject Projection", "description": "Highlight subject entries in soprano, alto, or bass."},
            {"id": "obj-2", "title": "Polyphonic Articulation", "description": "Execute staccato countersubject against legato main subject."}
        ],
        "is_published": True
    }
]

def seed_curriculum():
    db: Session = SessionLocal()
    try:
        count = 0
        now = datetime.utcnow()
        for item in CURRICULUM_LESSONS:
            existing = db.query(Lesson).filter(Lesson.slug == item["slug"]).first()
            if not existing:
                lesson = Lesson(
                    title=item["title"],
                    slug=item["slug"],
                    description=item["description"],
                    category=item["category"],
                    difficulty=item["difficulty"],
                    genre=item["genre"],
                    estimated_duration=item["estimated_duration"],
                    display_order=item["display_order"],
                    objectives=item["objectives"],
                    is_published=item["is_published"],
                    published_at=now
                )
                db.add(lesson)
                count += 1
        db.commit()
        print(f"Successfully seeded {count} structured curriculum lessons.")
    except Exception as exc:
        db.rollback()
        print(f"Error seeding curriculum: {exc}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_curriculum()
