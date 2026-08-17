import asyncio
from app.core.database import SessionLocal
from app.models.song import Song
from app.models.user import User
from app.services.orchestrator.source_discovery import SourceDiscoveryService

async def main():
    db = SessionLocal()
    try:
        user = db.query(User).first()
        song = db.query(Song).first()
        if not user or not song:
            print("Missing user or song")
            return
            
        print(f"Running discovery for: {song.title} by {song.composer}")
        job_id = await SourceDiscoveryService.discover_and_analyze(song, user.id, db)
        print(f"Result job_id: {job_id}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
