"""
Chord Detector — detects chords from simultaneous notes.
"""

import logging
import uuid
from typing import Dict, Any, List

from sqlalchemy.orm import Session

from app.models.transcription_note import TranscriptionNote

logger = logging.getLogger(__name__)


class ChordDetector:
    """
    Detects basic chords from groups of simultaneous notes.
    V1: Simple detection of simultaneous note groups (stub for actual chord naming).
    """

    def get_pitch_classes(self, notes: List[TranscriptionNote]) -> List[int]:
        """Convert MIDI notes to unique pitch classes (0-11)."""
        return list(set(n.midi_number % 12 for n in notes))

    def match_chord(self, root: int, pitch_classes: List[int]) -> tuple[str, float]:
        """Match pitch classes against chord templates for a given root."""
        templates = {
            "Maj": [0, 4, 7],
            "Min": [0, 3, 7],
            "Dim": [0, 3, 6],
            "Aug": [0, 4, 8],
            "Maj7": [0, 4, 7, 11],
            "Min7": [0, 3, 7, 10],
            "Dom7": [0, 4, 7, 10],
        }
        
        # Shift pitch classes so root is 0
        shifted = set((pc - root) % 12 for pc in pitch_classes)
        
        best_match = "Unknown"
        best_score = 0.0
        
        for name, template in templates.items():
            template_set = set(template)
            intersection = shifted.intersection(template_set)
            
            # Simple scoring: reward matches, penalize missing/extra notes
            score = len(intersection) / len(template_set) - (len(shifted - template_set) * 0.2)
            if score > best_score:
                best_score = score
                best_match = name
                
        return best_match, best_score

    def get_note_name(self, root: int) -> str:
        names = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
        return names[root]

    def detect(self, transcription_id: str, db: Session) -> Dict[str, Any]:
        """
        Detect chords in a transcription using pitch class matching.
        """
        trans_uuid = uuid.UUID(transcription_id)
        notes = db.query(TranscriptionNote).filter(
            TranscriptionNote.transcription_id == trans_uuid,
            TranscriptionNote.validation_action != "DISCARD",
        ).order_by(TranscriptionNote.start_time).all()

        if not notes:
            return {"chords_detected": 0, "chord_list": []}

        # Find simultaneous note groups (rough approximation of chords)
        chord_groups = []
        visited = set()
        
        for note in notes:
            if note.id in visited:
                continue
                
            group = [
                n for n in notes
                if n.id not in visited
                and abs(n.start_time - note.start_time) < 0.1 # 100ms window
            ]
            
            if len(group) >= 3:
                # Extract chord info
                pitch_classes = self.get_pitch_classes(group)
                
                # Assume lowest note is the root for simplicity (could be improved for inversions)
                sorted_group = sorted(group, key=lambda n: n.midi_number)
                bass_note = sorted_group[0].midi_number % 12
                
                chord_quality, score = self.match_chord(bass_note, pitch_classes)
                chord_name = f"{self.get_note_name(bass_note)}{chord_quality}"
                
                if score >= 0.6: # Minimum confidence
                    chord_groups.append({
                        "name": chord_name,
                        "time": sorted_group[0].start_time,
                        "confidence": score
                    })
                    
                for g in group:
                    visited.add(g.id)
            else:
                visited.add(note.id)

        logger.info(f"Chord detection for {transcription_id}: {len(chord_groups)} valid chords found")

        return {
            "chords_detected": len(chord_groups),
            "chord_list": chord_groups
        }
