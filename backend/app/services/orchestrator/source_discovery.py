import uuid
import hashlib
import logging
from typing import Optional
from sqlalchemy.orm import Session

from app.models.song import Song
from app.models.audio_asset import AudioAsset
from app.models.processing_job import ProcessingJob
from app.core.enums import AudioSourceType, ProcessingJobStage
from app.services.search.search_engine import search_engine

logger = logging.getLogger(__name__)

class SourceDiscoveryService:
    @staticmethod
    async def discover_and_analyze(song: Song, user_id: uuid.UUID, db: Session) -> Optional[uuid.UUID]:
        """
        Attempts to automatically discover a valid MIDI/Audio source for the song,
        download it, provision an AudioAsset, and start the processing pipeline.
        
        Returns the ProcessingJob ID if successful, else None.
        """
        import re
        
        # Clean title to remove "ft.", "-", "feat", brackets, etc. to get better BitMidi matches
        clean_title = re.sub(r'(?i)(\(.*?\)|\{.*?\}|\[.*?\]|ft\..*|feat\..*|-)', '', song.title).strip()
        query = f"{clean_title} {song.composer}".strip()
        logger.info(f"Source discovery searching for: {query} (Original: {song.title})")
        
        bitmidi = search_engine.get_provider("BitMidi")
        if not bitmidi:
            logger.error("BitMidi provider not registered.")
            return None
            
        from app.schemas.search import SearchFilter
        filters = SearchFilter(limit=1)
        results = await bitmidi.search(query, filters=filters, db=db)
        
        if not results:
            logger.info("No automatic source found.")
            return None
            
        best_match = results[0]
        logger.info(f"Found best match: {best_match.title} ({best_match.id})")
        
        # 2. Download the raw MIDI data
        try:
            raw_data = await bitmidi.get_raw_data(best_match.id)
            if not raw_data:
                return None
        except Exception as e:
            logger.error(f"Failed to fetch raw data from BitMidi: {e}")
            return None
            
        # 3. Create AudioAsset and ProcessingJob
        asset_id = uuid.uuid4()
        audio_format = "mid"
        file_hash = hashlib.sha256(raw_data).hexdigest()
        storage_path = f"audio/{asset_id}/original.{audio_format}"
        file_size = len(raw_data)
        
        # Check if already exists (deduplication)
        existing = db.query(AudioAsset).filter(
            AudioAsset.file_hash_sha256 == file_hash,
            AudioAsset.user_id == user_id,
        ).first()
        
        if existing:
            # Return existing job
            existing_job = db.query(ProcessingJob).filter(
                ProcessingJob.audio_asset_id == existing.id,
            ).order_by(ProcessingJob.created_at.desc()).first()
            if existing_job:
                # If it's stuck in QUEUED or FAILED, re-dispatch it
                if existing_job.status in [ProcessingJobStage.QUEUED.value, ProcessingJobStage.FAILED.value, 'queued', 'failed', 'QUEUED', 'FAILED']:
                    try:
                        from app.tasks.transcribe_audio import process_audio_pipeline
                        process_audio_pipeline.delay(str(existing_job.id))
                    except Exception as e:
                        logger.warning(f"Failed to re-dispatch celery task: {e}")
                return existing_job.id
                
        # Save to MinIO
        try:
            from app.storage.minio_service import minio_service
            minio_service.upload_bytes(storage_path, raw_data, content_type="audio/midi")
        except Exception as e:
            logger.error(f"Failed to save discovered source to MinIO: {e}")
            return None
            
        audio_asset = AudioAsset(
            id=asset_id,
            user_id=user_id,
            song_id=song.id,
            source_type=AudioSourceType.PUBLIC_DOMAIN.value,
            original_filename=f"{best_match.title}.{audio_format}",
            file_hash_sha256=file_hash,
            storage_path=storage_path,
            format=audio_format,
            file_size_bytes=file_size,
            is_valid=False,
        )
        db.add(audio_asset)
        
        job_id = uuid.uuid4()
        processing_job = ProcessingJob(
            id=job_id,
            audio_asset_id=asset_id,
            song_id=song.id,
            user_id=user_id,
            status=ProcessingJobStage.QUEUED.value,
            progress_percent=0,
            pipeline_version="1.0.0",
            stage_log=[],
        )
        db.add(processing_job)
        db.commit()
        
        # 4. Dispatch Celery Task
        try:
            from app.tasks.transcribe_audio import process_audio_pipeline
            process_audio_pipeline.delay(str(job_id))
        except Exception as e:
            logger.warning(f"Failed to dispatch celery task: {e}")
            
        return job_id
