import sys
import os
import uuid
from sqlalchemy.orm import Session

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.core.database import SessionLocal
from app.models.curriculum import (
    LearningPath, CurriculumModule, CurriculumUnit, 
    CurriculumLesson, CurriculumExercise, CurriculumCheckpoint
)

def seed_curriculum_framework():
    db: Session = SessionLocal()
    try:
        # 1. Create Learning Path
        path = db.query(LearningPath).filter(LearningPath.slug == "beginner-piano-path").first()
        if not path:
            path = LearningPath(
                title="Beginner Piano Journey",
                slug="beginner-piano-path",
                description="Master piano posture, keyboard geography, finger independence, and simple melodies.",
                target_role="STUDENT",
                display_order=1
            )
            db.add(path)
            db.flush()

        # 2. Create Module 1
        mod1 = db.query(CurriculumModule).filter(CurriculumModule.slug == "module-1-foundations").first()
        if not mod1:
            mod1 = CurriculumModule(
                path_id=path.id,
                title="Module 1: Piano Foundations",
                slug="module-1-foundations",
                description="Posture, keyboard geography, finger numbers, and Middle C.",
                display_order=1,
                is_unlocked_by_default=True
            )
            db.add(mod1)
            db.flush()

        # 3. Create Module 2
        mod2 = db.query(CurriculumModule).filter(CurriculumModule.slug == "module-2-rhythm-reading").first()
        if not mod2:
            mod2 = CurriculumModule(
                path_id=path.id,
                title="Module 2: Rhythm & Treble Clef Reading",
                slug="module-2-rhythm-reading",
                description="Quarter notes, half notes, 4/4 meter, and reading treble staff.",
                display_order=2,
                is_unlocked_by_default=False
            )
            db.add(mod2)
            db.flush()

        # 4. Create Checkpoint for Module 1 unlocking Module 2
        chk1 = db.query(CurriculumCheckpoint).filter(CurriculumCheckpoint.module_id == mod1.id).first()
        if not chk1:
            chk1 = CurriculumCheckpoint(
                module_id=mod1.id,
                title="Module 1 Checkpoint Assessment",
                pass_threshold_percentage=80.0,
                unlocks_module_id=mod2.id
            )
            db.add(chk1)
            db.flush()

        # 5. Create Unit in Module 1
        unit1 = db.query(CurriculumUnit).filter(CurriculumUnit.slug == "unit-1-keyboard-setup").first()
        if not unit1:
            unit1 = CurriculumUnit(
                module_id=mod1.id,
                title="Unit 1: Getting Started at the Piano",
                slug="unit-1-keyboard-setup",
                display_order=1
            )
            db.add(unit1)
            db.flush()

        # 6. Create Lesson in Unit 1
        les1 = db.query(CurriculumLesson).filter(CurriculumLesson.slug == "lesson-1-meet-the-keyboard").first()
        if not les1:
            les1 = CurriculumLesson(
                unit_id=unit1.id,
                title="Meet the Keyboard & Middle C",
                slug="lesson-1-meet-the-keyboard",
                learning_goal="Locate Middle C using 2-black key groups and establish correct wrist posture.",
                estimated_time=10,
                difficulty="BEGINNER",
                required_skills=[],
                skills_taught=["Posture", "Middle C Identification"],
                prerequisites=[],
                xp_reward=100,
                ai_coaching_enabled=True,
                teacher_assignable=True,
                display_order=1
            )
            db.add(les1)
            db.flush()

        # 7. Create Exercise in Lesson 1
        ex1 = db.query(CurriculumExercise).filter(CurriculumExercise.lesson_id == les1.id).first()
        if not ex1:
            ex1 = CurriculumExercise(
                lesson_id=les1.id,
                title="Middle C Location Drill",
                exercise_type="PRACTICE",
                tempo_bpm=60,
                key_signature="C Major",
                display_order=1
            )
            db.add(ex1)

        db.commit()
        print("Successfully seeded Stage 3A Curriculum Engine framework models.")
    except Exception as exc:
        db.rollback()
        print(f"Error seeding framework: {exc}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_curriculum_framework()
