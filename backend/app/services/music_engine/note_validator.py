"""
Note Validator — post-processes raw Basic Pitch output.

Applies deterministic validation rules to clean up transcription noise:
  - Merge short fragments of the same pitch
  - Discard micro-notes (likely noise)
  - Merge overlapping duplicate pitches
  - Discard inaudible notes (very low velocity)
  - FLAG large jumps for context analysis (NOT auto-delete)
  - FLAG unreasonable silence gaps

IMPORTANT: Impossible jumps (>2 octaves in <100ms) are FLAGS, not deletions.
A C2→C5 jump can genuinely happen in expert piano performance.
"""

import logging
from typing import Dict, Any

from sqlalchemy.orm import Session

from app.models.transcription_note import TranscriptionNote
from app.core.enums import ValidationAction

logger = logging.getLogger(__name__)


class NoteValidator:
    """
    Validates and cleans up raw transcription notes.
    
    Each rule produces a ValidationAction (KEEP, MERGE, DISCARD, FLAG)
    with a reason string for full traceability.
    """

    # Thresholds
    MERGE_GAP_THRESHOLD = 0.080      # seconds — merge same-pitch notes <80ms apart
    MIN_NOTE_DURATION = 0.030        # seconds — discard notes <30ms
    MIN_VELOCITY = 5                 # discard notes with velocity <5
    LARGE_JUMP_SEMITONES = 24        # 2 octaves
    LARGE_JUMP_TIME_THRESHOLD = 0.1  # seconds
    SILENCE_GAP_THRESHOLD = 5.0      # seconds — flag gaps >5s mid-piece

    def validate_notes(self, transcription_id: str, db: Session) -> Dict[str, Any]:
        """
        Validate all notes in a transcription.
        
        Returns stats:
            {
                "total": int,
                "kept": int,
                "merged": int,
                "discarded": int,
                "flagged": int,
            }
        """
        import uuid
        notes = db.query(TranscriptionNote).filter(
            TranscriptionNote.transcription_id == uuid.UUID(transcription_id)
        ).order_by(TranscriptionNote.start_time).all()

        if not notes:
            return {"total": 0, "kept": 0, "merged": 0, "discarded": 0, "flagged": 0}

        stats = {"total": len(notes), "kept": 0, "merged": 0, "discarded": 0, "flagged": 0}

        # ── Pass 1: Micro-note removal ────────────────────────────────────
        for note in notes:
            if note.duration < self.MIN_NOTE_DURATION:
                note.validation_action = ValidationAction.DISCARD.value
                note.validation_reason = (
                    f"Note too short: {note.duration*1000:.0f}ms "
                    f"(threshold: {self.MIN_NOTE_DURATION*1000:.0f}ms). Likely noise."
                )
                note.is_validated = True
                stats["discarded"] += 1
                continue

            if note.velocity < self.MIN_VELOCITY:
                note.validation_action = ValidationAction.DISCARD.value
                note.validation_reason = (
                    f"Velocity too low: {note.velocity} "
                    f"(threshold: {self.MIN_VELOCITY}). Below audible threshold."
                )
                note.is_validated = True
                stats["discarded"] += 1

        # ── Pass 2: Merge consecutive same-pitch fragments ────────────────
        active_notes = [n for n in notes if n.validation_action != ValidationAction.DISCARD.value]
        i = 0
        while i < len(active_notes) - 1:
            current = active_notes[i]
            next_note = active_notes[i + 1]

            # Same pitch, close together → merge
            if (
                current.midi_number == next_note.midi_number
                and (next_note.start_time - current.end_time) < self.MERGE_GAP_THRESHOLD
            ):
                # Extend current note to cover both
                current.end_time = max(current.end_time, next_note.end_time)
                current.duration = current.end_time - current.start_time
                current.velocity = max(current.velocity, next_note.velocity)
                current.confidence = max(current.confidence, next_note.confidence)
                current.validation_action = ValidationAction.MERGE.value
                current.validation_reason = (
                    f"Merged with following {next_note.note_name} "
                    f"(gap: {(next_note.start_time - current.end_time)*1000:.0f}ms). "
                    f"New duration: {current.duration*1000:.0f}ms."
                )
                current.is_validated = True
                stats["merged"] += 1

                # Mark the absorbed note as discarded
                next_note.validation_action = ValidationAction.DISCARD.value
                next_note.validation_reason = (
                    f"Merged into preceding {current.note_name} "
                    f"(fragment of sustained note)."
                )
                next_note.is_validated = True
                stats["discarded"] += 1

                # Remove from active list and don't advance
                active_notes.pop(i + 1)
            else:
                i += 1

        # ── Pass 3: Overlapping same-pitch detection ──────────────────────
        active_notes = [n for n in notes if n.validation_action != ValidationAction.DISCARD.value]
        for i in range(len(active_notes)):
            for j in range(i + 1, len(active_notes)):
                a, b = active_notes[i], active_notes[j]
                if b.start_time >= a.end_time:
                    break  # no more overlaps possible
                if a.midi_number == b.midi_number:
                    # Same pitch overlapping → merge into the earlier note
                    a.end_time = max(a.end_time, b.end_time)
                    a.duration = a.end_time - a.start_time
                    a.confidence = max(a.confidence, b.confidence)
                    a.validation_action = ValidationAction.MERGE.value
                    a.validation_reason = (
                        f"Merged with overlapping {b.note_name} at "
                        f"{b.start_time:.3f}s. Duplicate detection."
                    )
                    a.is_validated = True

                    b.validation_action = ValidationAction.DISCARD.value
                    b.validation_reason = "Overlapping duplicate — merged into earlier note."
                    b.is_validated = True
                    stats["discarded"] += 1

        # ── Pass 4: Large jump detection (FLAG, not auto-delete) ──────────
        active_notes = [
            n for n in notes
            if n.validation_action not in (ValidationAction.DISCARD.value, None)
            or n.validation_action is None
        ]
        active_notes = [
            n for n in notes
            if n.validation_action != ValidationAction.DISCARD.value
        ]

        for i in range(len(active_notes) - 1):
            current = active_notes[i]
            next_note = active_notes[i + 1]
            time_gap = next_note.start_time - current.end_time
            pitch_gap = abs(next_note.midi_number - current.midi_number)

            if pitch_gap > self.LARGE_JUMP_SEMITONES and time_gap < self.LARGE_JUMP_TIME_THRESHOLD:
                # FLAG — could be real expert passage
                # Context analysis: check surrounding note density
                surrounding_density = self._get_local_density(active_notes, i, window=1.0)

                if surrounding_density < 2.0:
                    # Low density context — more likely noise
                    next_note.validation_action = ValidationAction.FLAG.value
                    next_note.validation_reason = (
                        f"Large pitch jump: {current.note_name}→{next_note.note_name} "
                        f"({pitch_gap} semitones in {time_gap*1000:.0f}ms). "
                        f"Low surrounding density ({surrounding_density:.1f} notes/s) — "
                        f"flagged for review."
                    )
                else:
                    # High density — likely intentional fast passage
                    next_note.validation_action = ValidationAction.FLAG.value
                    next_note.validation_reason = (
                        f"Large pitch jump: {current.note_name}→{next_note.note_name} "
                        f"({pitch_gap} semitones in {time_gap*1000:.0f}ms). "
                        f"High density context ({surrounding_density:.1f} notes/s) — "
                        f"likely intentional. Flagged but kept."
                    )
                next_note.is_validated = True
                stats["flagged"] += 1

        # ── Pass 5: Silence gap detection ─────────────────────────────────
        active_notes = [
            n for n in notes
            if n.validation_action != ValidationAction.DISCARD.value
        ]
        for i in range(len(active_notes) - 1):
            gap = active_notes[i + 1].start_time - active_notes[i].end_time
            if gap > self.SILENCE_GAP_THRESHOLD:
                active_notes[i + 1].validation_action = ValidationAction.FLAG.value
                active_notes[i + 1].validation_reason = (
                    f"Unreasonable silence gap: {gap:.1f}s before this note. "
                    f"May indicate section break or missed notes."
                )
                active_notes[i + 1].is_validated = True
                stats["flagged"] += 1

        # ── Mark remaining as KEEP ────────────────────────────────────────
        for note in notes:
            if note.validation_action is None:
                note.validation_action = ValidationAction.KEEP.value
                note.validation_reason = "Passed all validation checks."
                note.is_validated = True
                stats["kept"] += 1

        db.commit()

        logger.info(
            f"Note validation for {transcription_id}: "
            f"{stats['total']} total, {stats['kept']} kept, "
            f"{stats['merged']} merged, {stats['discarded']} discarded, "
            f"{stats['flagged']} flagged"
        )

        return stats

    def _get_local_density(self, notes: list, center_idx: int, window: float) -> float:
        """
        Calculate note density (notes per second) in a time window
        around the given note index.
        """
        if not notes or center_idx >= len(notes):
            return 0.0

        center_time = notes[center_idx].start_time
        start = center_time - window / 2
        end = center_time + window / 2

        count = sum(
            1 for n in notes
            if start <= n.start_time <= end
        )

        return count / window if window > 0 else 0.0
