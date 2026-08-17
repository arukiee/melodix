"""
Source Manager — manages legal musical sources and routes to appropriate analysis engine.
"""

import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.audio_asset import AudioAsset

logger = logging.getLogger(__name__)

class SourceManager:
    """
    Manages legal musical sources and orchestrates the routing:
    - If MIDI exists: direct parsing -> canonical notes
    - If Audio exists: Basic Pitch -> canonical notes
    - If neither: error / request upload
    """
    
    def validate_source(self, source_type: str) -> bool:
        """Check if a source type is permitted."""
        permitted = ["USER_UPLOAD", "USER_MIDI", "PUBLIC_DOMAIN", "LICENSED"]
        return source_type in permitted

    def resolve_source(self, song_id: str, db: Session) -> Dict[str, Any]:
        """
        Finds the best available source for a given song.
        Prefers MIDI over Audio.
        """
        # Look for MIDI first
        midi_asset = db.query(AudioAsset).filter(
            AudioAsset.song_id == song_id,
            AudioAsset.format == 'mid',
            AudioAsset.is_valid == True
        ).first()

        if midi_asset:
            return {
                "source_type": "MIDI",
                "asset_id": str(midi_asset.id),
                "path": midi_asset.storage_path,
                "requires_ml_transcription": False
            }

        # Look for Audio
        audio_asset = db.query(AudioAsset).filter(
            AudioAsset.song_id == song_id,
            AudioAsset.format.in_(['wav', 'mp3', 'flac']),
            AudioAsset.is_valid == True
        ).first()

        if audio_asset:
            return {
                "source_type": "AUDIO",
                "asset_id": str(audio_asset.id),
                "path": audio_asset.storage_path,
                "requires_ml_transcription": True
            }

        return {
            "source_type": "NONE",
            "asset_id": None,
            "path": None,
            "requires_ml_transcription": False
        }
