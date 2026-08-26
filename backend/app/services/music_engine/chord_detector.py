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

    def match_chord(self, root: int, pitch_classes: List[int], bass_note: int) -> tuple[str, float]:
        """
        Match pitch classes against chord templates for a given root.
        Supports inversions (e.g., C/E if bass_note != root).
        """
        templates = {
            "Major": ([0, 4, 7], ""),
            "Minor": ([0, 3, 7], "m"),
            "Diminished": ([0, 3, 6], "dim"),
            "Augmented": ([0, 4, 8], "aug"),
            "Sus2": ([0, 2, 7], "sus2"),
            "Sus4": ([0, 5, 7], "sus4"),
            "Major7": ([0, 4, 7, 11], "Maj7"),
            "Minor7": ([0, 3, 7, 10], "m7"),
            "Dominant7": ([0, 4, 7, 10], "7"),
            "Diminished7": ([0, 3, 6, 9], "dim7"),
            "HalfDiminished7": ([0, 3, 6, 10], "m7b5"),
            "Major6": ([0, 4, 7, 9], "6"),
            "Minor6": ([0, 3, 7, 9], "m6"),
        }
        
        # Shift pitch classes so root is 0
        shifted = set((pc - root) % 12 for pc in pitch_classes)
        
        best_match = "Unknown"
        best_score = 0.0
        
        for name, (template, suffix) in templates.items():
            template_set = set(template)
            intersection = shifted.intersection(template_set)
            extra = shifted - template_set
            
            # Require at least 3 matching notes for full chord
            if len(intersection) < 3:
                continue

            score = (len(intersection) / len(template_set)) - (len(extra) * 0.2)
            if score > best_score:
                best_score = score
                root_name = self.get_note_name(root)
                label = f"{root_name}{suffix}" if suffix or root_name else name
                if root != bass_note:
                    bass_name = self.get_note_name(bass_note)
                    label += f"/{bass_name}"
                best_match = label

        return best_match, best_score

    def get_note_name(self, root: int) -> str:
        names = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
        return names[root % 12]

    def detect(self, transcription_id: str, db: Session) -> Dict[str, Any]:
        """
        Detect chords in a transcription using pitch class matching and inversion handling.
        """
        trans_uuid = uuid.UUID(transcription_id)
        notes = db.query(TranscriptionNote).filter(
            TranscriptionNote.transcription_id == trans_uuid,
            TranscriptionNote.validation_action != "DISCARD",
        ).order_by(TranscriptionNote.start_time).all()

        if not notes:
            return {"chords_detected": 0, "chord_list": []}

        # Find simultaneous note groups (within 100ms window)
        chord_groups = []
        visited = set()
        
        for note in notes:
            if note.id in visited:
                continue
                
            group = [
                n for n in notes
                if n.id not in visited
                and abs(n.start_time - note.start_time) < 0.1  # 100ms window
            ]
            
            if len(group) >= 3:
                pitch_classes = self.get_pitch_classes(group)
                sorted_group = sorted(group, key=lambda n: n.midi_number)
                bass_note = sorted_group[0].midi_number % 12
                
                # Check all candidate root pitch classes in the group
                best_chord = "Unknown"
                max_score = 0.0
                
                for candidate_root in pitch_classes:
                    chord_name, score = self.match_chord(candidate_root, pitch_classes, bass_note)
                    if score > max_score:
                        max_score = score
                        best_chord = chord_name
                
                if max_score >= 0.70:  # Enforce high confidence threshold
                    chord_groups.append({
                        "name": best_chord,
                        "time": sorted_group[0].start_time,
                        "confidence": round(max_score, 2)
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
