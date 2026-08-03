import sys
import os
import uuid
from datetime import datetime
from sqlalchemy.orm import Session

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.core.database import SessionLocal
from app.models.curriculum import (
    LearningPath, CurriculumModule, CurriculumUnit, 
    CurriculumLesson, CurriculumExercise, CurriculumCheckpoint
)

# 7-Module Beginner Curriculum System
BEGINNER_CURRICULUM_SYSTEM = [
    {
        "module_title": "Module 1: Piano Foundations",
        "module_slug": "module-1-piano-foundations",
        "description": "Establish posture, hand shape, finger numbers 1-5, and locate Middle C.",
        "display_order": 1,
        "is_unlocked_by_default": True,
        "checkpoint_title": "Foundations Assessment",
        "units": [
            {
                "unit_title": "Unit 1.1: Keyboard Geography & Posture",
                "unit_slug": "unit-1-1-geography-posture",
                "lessons": [
                    {
                        "title": "Meet the Keyboard & 2-Black Key Groups",
                        "slug": "meet-the-keyboard",
                        "learning_goal": "Locate 2-black key patterns across the entire 88-key piano keyboard.",
                        "estimated_time": 10,
                        "difficulty": "BEGINNER",
                        "skills_taught": ["Keyboard Geography", "2-Black Key Recognition"],
                        "xp_reward": 100,
                        "exercises": [
                            {"title": "2-Black Key Press Drill", "exercise_type": "FINGER_EXERCISE", "tempo_bpm": 60, "key_signature": "C Major"}
                        ]
                    },
                    {
                        "title": "Ergonomic Posture & Curved Hand Shape",
                        "slug": "ergonomic-posture-hand-shape",
                        "learning_goal": "Maintain relaxed shoulders, level forearms, and bubble hand shape.",
                        "estimated_time": 10,
                        "difficulty": "BEGINNER",
                        "skills_taught": ["Posture", "Hand Shape"],
                        "xp_reward": 100,
                        "exercises": [
                            {"title": "Bubble Hand Shape Drop Drill", "exercise_type": "FINGER_EXERCISE", "tempo_bpm": 60, "key_signature": "C Major"}
                        ]
                    },
                    {
                        "title": "Finger Numbers 1 through 5",
                        "slug": "finger-numbers-1-to-5",
                        "learning_goal": "Instantly respond to finger numbers 1 (Thumb) through 5 (Pinky).",
                        "estimated_time": 12,
                        "difficulty": "BEGINNER",
                        "skills_taught": ["Finger Independence", "Finger Numbering"],
                        "xp_reward": 120,
                        "exercises": [
                            {"title": "Finger Number Tapping Exercise", "exercise_type": "RHYTHM_EXERCISE", "tempo_bpm": 70, "key_signature": "C Major"}
                        ]
                    },
                    {
                        "title": "Locating Middle C & C 5-Finger Position",
                        "slug": "locating-middle-c",
                        "learning_goal": "Find Middle C with right-hand finger 1 and place RH on C-D-E-F-G.",
                        "estimated_time": 15,
                        "difficulty": "BEGINNER",
                        "skills_taught": ["Middle C Identification", "5-Finger Position"],
                        "xp_reward": 150,
                        "exercises": [
                            {"title": "RH 5-Finger Scale Drill", "exercise_type": "SCALE_EXERCISE", "tempo_bpm": 76, "key_signature": "C Major"}
                        ]
                    }
                ]
            }
        ]
    },
    {
        "module_title": "Module 2: Reading Music & Staff Basics",
        "module_slug": "module-2-reading-music",
        "description": "Learn Grand Staff, Treble Clef, Bass Clef, and Line/Space note navigation.",
        "display_order": 2,
        "is_unlocked_by_default": False,
        "checkpoint_title": "Notation Reading Checkpoint",
        "units": [
            {
                "unit_title": "Unit 2.1: The Grand Staff",
                "unit_slug": "unit-2-1-grand-staff",
                "lessons": [
                    {
                        "title": "Treble Clef Notes (C4 to G4)",
                        "slug": "treble-clef-c4-to-g4",
                        "learning_goal": "Read and play Middle C, D, E, F, G on the Treble Staff.",
                        "estimated_time": 15,
                        "difficulty": "BEGINNER",
                        "skills_taught": ["Sight Reading", "Treble Staff"],
                        "xp_reward": 150,
                        "exercises": [
                            {"title": "Treble Staff Flashcard Drill", "exercise_type": "SIGHT_READING", "tempo_bpm": 80, "key_signature": "C Major"}
                        ]
                    },
                    {
                        "title": "Bass Clef Notes (C3 to G3)",
                        "slug": "bass-clef-c3-to-g3",
                        "learning_goal": "Read and play C3 to G3 on the Bass Staff using left-hand fingers 5-1.",
                        "estimated_time": 15,
                        "difficulty": "BEGINNER",
                        "skills_taught": ["Sight Reading", "Bass Staff"],
                        "xp_reward": 150,
                        "exercises": [
                            {"title": "Bass Clef Drone Drill", "exercise_type": "SIGHT_READING", "tempo_bpm": 80, "key_signature": "C Major"}
                        ]
                    }
                ]
            }
        ]
    },
    {
        "module_title": "Module 3: Rhythm & Time Signatures",
        "module_slug": "module-3-rhythm-time-signatures",
        "description": "Master Quarter, Half, Whole notes, and 4/4 vs 3/4 meter counting.",
        "display_order": 3,
        "is_unlocked_by_default": False,
        "checkpoint_title": "Rhythm Counting Checkpoint",
        "units": [
            {
                "unit_title": "Unit 3.1: Pulse & Note Values",
                "unit_slug": "unit-3-1-pulse-note-values",
                "lessons": [
                    {
                        "title": "Quarter Notes & Half Notes (1-2-3-4 Pulse)",
                        "slug": "quarter-half-notes-pulse",
                        "learning_goal": "Count steady quarter notes (1 beat) and half notes (2 beats) at 80 bpm.",
                        "estimated_time": 15,
                        "difficulty": "BEGINNER",
                        "skills_taught": ["Rhythm Counting", "Tempo Stability"],
                        "xp_reward": 150,
                        "exercises": [
                            {"title": "Metronome Clapping & Tapping Drill", "exercise_type": "RHYTHM_EXERCISE", "tempo_bpm": 80, "key_signature": "C Major"}
                        ]
                    },
                    {
                        "title": "Waltz Time: 3/4 Time Signature",
                        "slug": "waltz-time-3-4-signature",
                        "learning_goal": "Feel and count 3-beat measure pulse with strong emphasis on beat 1.",
                        "estimated_time": 18,
                        "difficulty": "BEGINNER",
                        "skills_taught": ["3/4 Meter", "Waltz Pulse"],
                        "xp_reward": 180,
                        "exercises": [
                            {"title": "3/4 Dance Pulse Exercise", "exercise_type": "RHYTHM_EXERCISE", "tempo_bpm": 96, "key_signature": "C Major"}
                        ]
                    }
                ]
            }
        ]
    },
    {
        "module_title": "Module 4: Playing with Both Hands",
        "module_slug": "module-4-both-hands-coordination",
        "description": "Combine left-hand accompaniment chords with right-hand melodies.",
        "display_order": 4,
        "is_unlocked_by_default": False,
        "checkpoint_title": "Hands Together Checkpoint",
        "units": [
            {
                "unit_title": "Unit 4.1: Parallel & Contrary Motion",
                "unit_slug": "unit-4-1-coordination",
                "lessons": [
                    {
                        "title": "C-Major Parallel Motion 5-Finger Scale",
                        "slug": "parallel-motion-5-finger-scale",
                        "learning_goal": "Play RH and LH C 5-finger scale simultaneously 1 octave apart.",
                        "estimated_time": 20,
                        "difficulty": "BEGINNER",
                        "skills_taught": ["Hand Coordination", "Parallel Motion"],
                        "xp_reward": 200,
                        "exercises": [
                            {"title": "Parallel Motion Scale Exercise", "exercise_type": "SCALE_EXERCISE", "tempo_bpm": 84, "key_signature": "C Major"}
                        ]
                    },
                    {
                        "title": "Left Hand Drone Bass Accompaniment",
                        "slug": "lh-drone-bass-accompaniment",
                        "learning_goal": "Sustain LH whole-note C & G drone chords while RH plays melody.",
                        "estimated_time": 20,
                        "difficulty": "BEGINNER",
                        "skills_taught": ["Accompaniment", "Drone Chords"],
                        "xp_reward": 200,
                        "exercises": [
                            {"title": "LH Drone & RH Melody Combination", "exercise_type": "CHORD_EXERCISE", "tempo_bpm": 76, "key_signature": "C Major"}
                        ]
                    }
                ]
            }
        ]
    },
    {
        "module_title": "Module 5: First Repertoire Integration",
        "module_slug": "module-5-repertoire-integration",
        "description": "Apply foundational skills to iconic beginner repertoire pieces.",
        "display_order": 5,
        "is_unlocked_by_default": False,
        "checkpoint_title": "Repertoire Mastery Checkpoint",
        "units": [
            {
                "unit_title": "Unit 5.1: Classical Beginner Masterpieces",
                "unit_slug": "unit-5-1-classical-masterpieces",
                "lessons": [
                    {
                        "title": "Ode to Joy (Complete Hands-Together Arrangement)",
                        "slug": "ode-to-joy-hands-together",
                        "learning_goal": "Perform Beethoven's Ode to Joy theme with RH melody and LH C-G bass.",
                        "estimated_time": 25,
                        "difficulty": "BEGINNER",
                        "skills_taught": ["Repertoire Performance", "Hands Together"],
                        "xp_reward": 250,
                        "exercises": [
                            {"title": "Ode to Joy Sectional Drill", "exercise_type": "REPERTOIRE", "tempo_bpm": 100, "key_signature": "D Major"}
                        ]
                    },
                    {
                        "title": "Minuet in G Major (Section A Legato Phrasing)",
                        "slug": "minuet-in-g-section-a",
                        "learning_goal": "Play Bach's Minuet in G Section A in 3/4 meter with smooth legato articulation.",
                        "estimated_time": 25,
                        "difficulty": "BEGINNER",
                        "skills_taught": ["Legato Phrasing", "Baroque Style"],
                        "xp_reward": 250,
                        "exercises": [
                            {"title": "Minuet in G Section A Practice", "exercise_type": "REPERTOIRE", "tempo_bpm": 110, "key_signature": "G Major"}
                        ]
                    }
                ]
            }
        ]
    },
    {
        "module_title": "Module 6: Dynamics & Touch",
        "module_slug": "module-6-dynamics-touch",
        "description": "Expressive touch control: Forte, Piano, Legato, and Staccato.",
        "display_order": 6,
        "is_unlocked_by_default": False,
        "checkpoint_title": "Dynamic Expression Checkpoint",
        "units": [
            {
                "unit_title": "Unit 6.1: Touch Control",
                "unit_slug": "unit-6-1-touch-control",
                "lessons": [
                    {
                        "title": "Forte vs Piano (Loud and Soft Key Attack)",
                        "slug": "forte-vs-piano-key-attack",
                        "learning_goal": "Control key depression velocity to produce contrasting forte (loud) and piano (soft) volume.",
                        "estimated_time": 20,
                        "difficulty": "BEGINNER",
                        "skills_taught": ["Dynamic Control", "Forte & Piano"],
                        "xp_reward": 200,
                        "exercises": [
                            {"title": "Dynamic Contrast Exercise", "exercise_type": "TEMPO_CONTROL", "tempo_bpm": 80, "key_signature": "C Major"}
                        ]
                    },
                    {
                        "title": "Legato vs Staccato Articulation",
                        "slug": "legato-vs-staccato-articulation",
                        "learning_goal": "Alternate smooth connected legato notes with crisp detached staccato notes.",
                        "estimated_time": 20,
                        "difficulty": "BEGINNER",
                        "skills_taught": ["Articulation", "Staccato & Legato"],
                        "xp_reward": 200,
                        "exercises": [
                            {"title": "Legato vs Staccato Touch Drill", "exercise_type": "FINGER_EXERCISE", "tempo_bpm": 84, "key_signature": "C Major"}
                        ]
                    }
                ]
            }
        ]
    },
    {
        "module_title": "Module 7: Pedaling & Final Beginner Assessment",
        "module_slug": "module-7-pedaling-final-assessment",
        "description": "Sustain pedal technique and comprehensive beginner milestone assessment.",
        "display_order": 7,
        "is_unlocked_by_default": False,
        "checkpoint_title": "Final Beginner Certification Checkpoint",
        "units": [
            {
                "unit_title": "Unit 7.1: Sustain Pedal & Graduation",
                "unit_slug": "unit-7-1-sustain-pedal",
                "lessons": [
                    {
                        "title": "Direct & Syncopated Pedaling Technique",
                        "slug": "direct-syncopated-pedaling",
                        "learning_goal": "Depress and release damper pedal synchronously with chord changes without blurring notes.",
                        "estimated_time": 25,
                        "difficulty": "BEGINNER",
                        "skills_taught": ["Sustain Pedal", "Pedal Timing"],
                        "xp_reward": 250,
                        "exercises": [
                            {"title": "Pedal Change Synchronization Drill", "exercise_type": "TEMPO_CONTROL", "tempo_bpm": 70, "key_signature": "D Major"}
                        ]
                    },
                    {
                        "title": "Comprehensive Beginner Recital (Gymnopédie No. 1)",
                        "slug": "beginner-recital-gymnopedie",
                        "learning_goal": "Perform Satie's Gymnopédie No. 1 applying 3/4 waltz rhythm, LH accompaniment leaps, and pedal.",
                        "estimated_time": 30,
                        "difficulty": "BEGINNER",
                        "skills_taught": ["Comprehensive Performance", "Pedaling & Phrasing"],
                        "xp_reward": 300,
                        "exercises": [
                            {"title": "Gymnopédie Full Performance Test", "exercise_type": "REPERTOIRE", "tempo_bpm": 76, "key_signature": "D Major"}
                        ]
                    }
                ]
            }
        ]
    }
]

def seed_beginner_curriculum_system():
    db: Session = SessionLocal()
    try:
        # Get or create path
        path = db.query(LearningPath).filter(LearningPath.slug == "beginner-piano-journey").first()
        if not path:
            path = LearningPath(
                title="Beginner Piano Journey",
                slug="beginner-piano-journey",
                description="Comprehensive 7-module beginner curriculum: posture, reading notes, rhythm, hands together, repertoire, dynamics, and pedaling.",
                target_role="STUDENT",
                display_order=1
            )
            db.add(path)
            db.flush()

        module_objs = []
        for mod_data in BEGINNER_CURRICULUM_SYSTEM:
            mod = db.query(CurriculumModule).filter(CurriculumModule.slug == mod_data["module_slug"]).first()
            if not mod:
                mod = CurriculumModule(
                    path_id=path.id,
                    title=mod_data["module_title"],
                    slug=mod_data["module_slug"],
                    description=mod_data["description"],
                    display_order=mod_data["display_order"],
                    is_unlocked_by_default=mod_data["is_unlocked_by_default"]
                )
                db.add(mod)
                db.flush()
            module_objs.append(mod)

        # Wire module checkpoints to unlock next module
        for i, mod in enumerate(module_objs):
            next_mod = module_objs[i + 1] if i + 1 < len(module_objs) else None
            chk = db.query(CurriculumCheckpoint).filter(CurriculumCheckpoint.module_id == mod.id).first()
            if not chk:
                chk = CurriculumCheckpoint(
                    module_id=mod.id,
                    title=BEGINNER_CURRICULUM_SYSTEM[i]["checkpoint_title"],
                    pass_threshold_percentage=80.0,
                    unlocks_module_id=next_mod.id if next_mod else None
                )
                db.add(chk)
                db.flush()

            # Process units & lessons
            for unit_data in BEGINNER_CURRICULUM_SYSTEM[i]["units"]:
                unit = db.query(CurriculumUnit).filter(CurriculumUnit.slug == unit_data["unit_slug"]).first()
                if not unit:
                    unit = CurriculumUnit(
                        module_id=mod.id,
                        title=unit_data["unit_title"],
                        slug=unit_data["unit_slug"],
                        display_order=1
                    )
                    db.add(unit)
                    db.flush()

                for order, les_data in enumerate(unit_data["lessons"], 1):
                    les = db.query(CurriculumLesson).filter(CurriculumLesson.slug == les_data["slug"]).first()
                    if not les:
                        les = CurriculumLesson(
                            unit_id=unit.id,
                            title=les_data["title"],
                            slug=les_data["slug"],
                            learning_goal=les_data["learning_goal"],
                            estimated_time=les_data["estimated_time"],
                            difficulty=les_data["difficulty"],
                            skills_taught=les_data["skills_taught"],
                            xp_reward=les_data["xp_reward"],
                            ai_coaching_enabled=True,
                            teacher_assignable=True,
                            display_order=order
                        )
                        db.add(les)
                        db.flush()

                    for ex_order, ex_data in enumerate(les_data["exercises"], 1):
                        ex = db.query(CurriculumExercise).filter(CurriculumExercise.lesson_id == les.id).first()
                        if not ex:
                            ex = CurriculumExercise(
                                lesson_id=les.id,
                                title=ex_data["title"],
                                exercise_type=ex_data["exercise_type"],
                                tempo_bpm=ex_data["tempo_bpm"],
                                key_signature=ex_data["key_signature"],
                                display_order=ex_order
                            )
                            db.add(ex)

        db.commit()
        print("Successfully seeded 7-Module Beginner Curriculum System in PostgreSQL.")
    except Exception as exc:
        db.rollback()
        print(f"Error seeding beginner curriculum system: {exc}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_beginner_curriculum_system()
