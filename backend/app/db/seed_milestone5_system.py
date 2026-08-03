import sys
import os
from sqlalchemy.orm import Session

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.core.database import SessionLocal
from app.models.song import Song

SONG_CURRICULUM_MAPPINGS = [
    {
        "title": "Minuet in G Major (BWV Anh. 114)",
        "educational_category": "Beginner Foundation",
        "learning_objectives": [
            "Master 3/4 dance meter pulse with emphasis on beat 1",
            "Execute smooth legato phrasing in RH melody",
            "Coordinate G-B-D LH bass line accompaniment"
        ],
        "skills_required": ["Treble Staff", "Bass Clef", "5-Finger Position"],
        "skills_reinforced": ["3/4 Meter", "Hands Together", "Baroque Articulation"],
        "prerequisite_lesson_slugs": ["minuet-in-g-section-a"],
        "mastery_threshold_percentage": 85.0,
        "ai_coaching_focus": {
            "primary_skills": ["Legato Phrasing", "3/4 Pulse"],
            "common_errors": ["Rushing measure 8 scalar run", "Uneven quarter-note rhythm"],
            "feedback_priorities": ["Timing", "Articulation"]
        },
        "teacher_notes": "Focus student on maintaining relaxed wrists during the scalar passages in measure 8."
    },
    {
        "title": "Für Elise (Bagatelle No. 25 in A Minor)",
        "educational_category": "Hand Independence",
        "learning_objectives": [
            "Execute E5-D#5 semitone chromatic shift with fingers 5-4",
            "Play smooth A-E-A left hand arpeggios without rushing"
        ],
        "skills_required": ["Chromatic Shift", "Arpeggio Motion"],
        "skills_reinforced": ["Hand Independence", "3/8 Meter"],
        "prerequisite_lesson_slugs": ["fur-elise-main-theme"],
        "mastery_threshold_percentage": 88.0,
        "ai_coaching_focus": {
            "primary_skills": ["Chromatic Precision", "Arpeggio Sweep"],
            "common_errors": ["Hesitation during finger 5-4 shift", "Heavy left-hand thumb on bass beat 1"],
            "feedback_priorities": ["Pitch Accuracy", "LH Voicing"]
        },
        "teacher_notes": "Keep left hand extremely quiet so the right hand melody floats above."
    },
    {
        "title": "Clair de Lune (Suite Bergamasque)",
        "educational_category": "Expression",
        "learning_objectives": [
            "Subdivide compound 9/8 meter into 3 steady beats of 3 notes",
            "Bring out top melody line in 3-part impressionist chords"
        ],
        "skills_required": ["Compound 9/8 Meter", "Db Major Scale", "Voicing"],
        "skills_reinforced": ["Coloristic Touch", "Dynamic Control", "Pianissimo"],
        "prerequisite_lesson_slugs": ["clair-de-lune-impressionist-textures"],
        "mastery_threshold_percentage": 90.0,
        "ai_coaching_focus": {
            "primary_skills": ["9/8 Subdivision", "Top-Note Voicing"],
            "common_errors": ["Rushing arpeggios in measure 14", "Harsh key attack on chordal entry"],
            "feedback_priorities": ["Dynamic Control", "Rubato Stability"]
        },
        "teacher_notes": "Use arm weight rather than finger impact for the delicate pianissimo openings."
    },
    {
        "title": "Gymnopédie No. 1",
        "educational_category": "Pedaling",
        "learning_objectives": [
            "Syncopated damper pedal timing on beat 2",
            "Lyrical melody projection over LH G-major waltz chords"
        ],
        "skills_required": ["Sustain Pedal", "Bass Clef Leaps"],
        "skills_reinforced": ["Pedal Timing", "Melodic Projection"],
        "prerequisite_lesson_slugs": ["beginner-recital-gymnopedie"],
        "mastery_threshold_percentage": 85.0,
        "ai_coaching_focus": {
            "primary_skills": ["Pedal Synchronization", "Melodic Legato"],
            "common_errors": ["Pedal blur on harmony change", "Clipping LH bass note"],
            "feedback_priorities": ["Pedal Timing", "Tone Quality"]
        },
        "teacher_notes": "Ensure pedal is cleared right as the new chord strikes."
    },
    {
        "title": "Ode to Joy (Symphony No. 9)",
        "educational_category": "Reading Practice",
        "learning_objectives": [
            "Maintain steady 4/4 meter at 100 bpm",
            "Read D Major scale degrees 1 through 5 in Treble Staff"
        ],
        "skills_required": ["Treble Staff Reading", "4/4 Meter"],
        "skills_reinforced": ["Rhythm Accuracy", "Sight Reading"],
        "prerequisite_lesson_slugs": ["ode-to-joy-hands-together"],
        "mastery_threshold_percentage": 85.0,
        "ai_coaching_focus": {
            "primary_skills": ["Sight Reading", "Rhythm Pulse"],
            "common_errors": ["Rushing quarter notes in measure 4", "Hesitating at measure 8 cadence"],
            "feedback_priorities": ["Rhythm Accuracy", "Steady Tempo"]
        },
        "teacher_notes": "Encourage counting out loud '1-2-3-4' during initial practice sessions."
    }
]

def seed_milestone5_system():
    db: Session = SessionLocal()
    try:
        count = 0
        for mapping in SONG_CURRICULUM_MAPPINGS:
            song = db.query(Song).filter(Song.title == mapping["title"]).first()
            if song:
                song.educational_category = mapping["educational_category"]
                song.learning_objectives = mapping["learning_objectives"]
                song.skills_required = mapping["skills_required"]
                song.skills_reinforced = mapping["skills_reinforced"]
                song.prerequisite_lesson_slugs = mapping["prerequisite_lesson_slugs"]
                song.mastery_threshold_percentage = mapping["mastery_threshold_percentage"]
                song.ai_coaching_focus = mapping["ai_coaching_focus"]
                song.teacher_notes = mapping["teacher_notes"]
                count += 1
        db.commit()
        print(f"Successfully mapped educational metadata onto {count} repertoire pieces.")
    except Exception as exc:
        db.rollback()
        print(f"Error seeding Milestone 5 mappings: {exc}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_milestone5_system()
