import os
import json
import logging
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.song import Song

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_songs")

def seed():
    session = SessionLocal()
    seed_file_path = os.path.join(os.path.dirname(__file__), "songs_seed.json")

    if not os.path.exists(seed_file_path):
        logger.error(f"Seeding template {seed_file_path} not found!")
        return

    with open(seed_file_path, "r") as f:
        data = json.load(f)

    for item in data:
        # Check if song exists based on Title and Composer
        existing = session.query(Song).filter(
            Song.title == item["title"],
            Song.composer == item["composer"]
        ).first()

        if existing:
            # Update fields
            existing.difficulty = item["difficulty"]
            existing.bpm = item["bpm"]
            existing.key_signature = item["key_signature"]
            existing.time_signature = item["time_signature"]
            existing.educational_category = item["educational_category"]
            existing.learning_objectives = item["learning_objectives"]
            existing.skills_required = item["skills_required"]
            existing.skills_reinforced = item["skills_reinforced"]
            existing.prerequisite_lesson_slugs = item["prerequisite_lesson_slugs"]
            existing.missions = item.get("missions", [])
            logger.info(f"Updated song: {item['title']} - {item['composer']}")
        else:
            # Create new
            new_song = Song(
                title=item["title"],
                composer=item["composer"],
                difficulty=item["difficulty"],
                bpm=item["bpm"],
                key_signature=item["key_signature"],
                time_signature=item["time_signature"],
                educational_category=item["educational_category"],
                learning_objectives=item["learning_objectives"],
                skills_required=item["skills_required"],
                skills_reinforced=item["skills_reinforced"],
                prerequisite_lesson_slugs=item["prerequisite_lesson_slugs"],
                missions=item.get("missions", [])
            )
            session.add(new_song)
            logger.info(f"Inserted song: {item['title']} - {item['composer']}")

    try:
        session.commit()
        logger.info("Song content seeding completed successfully.")
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to seed song database: {str(e)}")
    finally:
        session.close()

if __name__ == "__main__":
    seed()
