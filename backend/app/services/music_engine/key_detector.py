"""
Key Detector — determines the key signature of a song.
"""

import logging
import uuid
from typing import Dict, Any, List

from sqlalchemy.orm import Session
from app.models.transcription_note import TranscriptionNote

logger = logging.getLogger(__name__)

class KeyDetector:
    """
    Detects the key signature of a song using a simplified Krumhansl-Schmuckler key-finding algorithm.
    It builds a profile of the pitch classes (total duration of each pitch class)
    and correlates it with standard major and minor profiles.
    """

    def __init__(self):
        # Krumhansl-Kessler profiles
        self.major_profile = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
        self.minor_profile = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
        self.pitch_names = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]

    def _correlation(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate Pearson correlation coefficient between two vectors."""
        if len(vec1) != len(vec2) or len(vec1) == 0:
            return 0.0
            
        mean1 = sum(vec1) / len(vec1)
        mean2 = sum(vec2) / len(vec2)
        
        num = sum((x - mean1) * (y - mean2) for x, y in zip(vec1, vec2))
        den1 = sum((x - mean1)**2 for x in vec1)
        den2 = sum((y - mean2)**2 for y in vec2)
        
        if den1 == 0 or den2 == 0:
            return 0.0
            
        return num / ((den1 * den2) ** 0.5)

    def detect(self, transcription_id: str, db: Session) -> Dict[str, Any]:
        """
        Detect the key of a transcription.
        """
        trans_uuid = uuid.UUID(transcription_id)
        notes = db.query(TranscriptionNote).filter(
            TranscriptionNote.transcription_id == trans_uuid,
            TranscriptionNote.validation_action != "DISCARD",
        ).all()

        if not notes:
            return {"key": "Unknown", "confidence": 0.0}

        # Build pitch class duration profile
        pitch_durations = [0.0] * 12
        for note in notes:
            pc = note.midi_number % 12
            pitch_durations[pc] += note.duration

        best_key = "Unknown"
        best_correlation = -1.0

        # Test all 12 major and 12 minor keys
        for root in range(12):
            # Shift the profile so 'root' is at index 0
            shifted_durations = pitch_durations[root:] + pitch_durations[:root]
            
            # Test Major
            r_maj = self._correlation(shifted_durations, self.major_profile)
            if r_maj > best_correlation:
                best_correlation = r_maj
                best_key = f"{self.pitch_names[root]} Major"
                
            # Test Minor
            r_min = self._correlation(shifted_durations, self.minor_profile)
            if r_min > best_correlation:
                best_correlation = r_min
                best_key = f"{self.pitch_names[root]} Minor"

        # Normalize correlation roughly to a 0-1 confidence score (r is usually between -1 and 1)
        # Realistically, a good match is > 0.6
        confidence = max(0.0, best_correlation)

        logger.info(f"Key detection for {transcription_id}: {best_key} (conf: {confidence:.2f})")

        return {
            "key": best_key,
            "confidence": round(confidence, 4),
            "method": "krumhansl-schmuckler"
        }
