"""
Hand Assigner — assigns LEFT/RIGHT hand to transcribed notes.

V1: Threshold-based assignment.
  MIDI <= 60 (C4) → LEFT HAND
  MIDI > 60        → RIGHT HAND

V2 (future): Context-aware using pitch, time, density, chord structure,
and hand crossing detection.
"""

import logging
import uuid
from typing import Dict, Any

from sqlalchemy.orm import Session

from app.models.transcription_note import TranscriptionNote
from app.core.enums import HandAssignment

logger = logging.getLogger(__name__)

# C4 = MIDI 60, the traditional split point for piano
DEFAULT_SPLIT_POINT = 60


class HandAssigner:
    """
    Assigns LEFT/RIGHT hand to each TranscriptionNote.
    
    V1 uses a simple threshold rule:
      MIDI <= split_point → LEFT
      MIDI > split_point  → RIGHT
    """

    def __init__(self, split_point: int = DEFAULT_SPLIT_POINT):
        self.split_point = split_point

    def assign(
        self,
        transcription_id: str,
        db: Session,
        split_point: int | None = None,
    ) -> Dict[str, Any]:
        """
        Assign hands to all notes in a transcription.
        
        Returns:
            {
                "total": int,
                "left": int,
                "right": int,
                "split_point": int,
            }
        """
        sp = split_point or self.split_point

        notes = db.query(TranscriptionNote).filter(
            TranscriptionNote.transcription_id == uuid.UUID(transcription_id),
            TranscriptionNote.validation_action != "DISCARD",
        ).all()

        left_count = 0
        right_count = 0

        for note in notes:
            if note.midi_number <= sp:
                note.hand = HandAssignment.LEFT.value
                left_count += 1
            else:
                note.hand = HandAssignment.RIGHT.value
                right_count += 1

        db.commit()

        logger.info(
            f"Hand assignment for {transcription_id}: "
            f"{left_count} left, {right_count} right "
            f"(split at MIDI {sp} / {_midi_to_name(sp)})"
        )

        return {
            "total": left_count + right_count,
            "left": left_count,
            "right": right_count,
            "split_point": sp,
        }


def _midi_to_name(midi: int) -> str:
    names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    return f"{names[midi % 12]}{(midi // 12) - 1}"
