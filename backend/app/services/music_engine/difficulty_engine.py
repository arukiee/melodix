"""
Difficulty Engine — computes difficulty metrics and generates
Easy/Medium/Hard/Expert variants from real transcriptions.

PRINCIPLES:
  1. Every note in every difficulty level is DERIVED from the real 
     transcription. Easy doesn't invent new notes — it selects the 
     most important subset.
  2. Expert = the validated source transcription, unmodified.
  3. Note importance scoring uses actual features: pitch salience,
     onset strength, rhythmic position, duration, isolation.
  4. Difficulty metrics are computed from actual note data, not static.
"""

import uuid
import logging
from typing import Dict, Any, List, Optional
from collections import defaultdict

import numpy as np
from sqlalchemy.orm import Session

from app.models.transcription import Transcription
from app.models.transcription_note import TranscriptionNote
from app.models.difficulty_variant import DifficultyVariant
from app.models.difficulty_note import DifficultyNote
from app.core.enums import DifficultyLevel, HandAssignment

logger = logging.getLogger(__name__)

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Difficulty engine version for provenance
ENGINE_VERSION = "1.0.0"

# Note importance thresholds per difficulty level
IMPORTANCE_THRESHOLDS = {
    DifficultyLevel.EASY.value: 0.7,
    DifficultyLevel.MEDIUM.value: 0.4,
    DifficultyLevel.HARD.value: 0.15,
    DifficultyLevel.EXPERT.value: 0.0,  # all notes
}

# Tempo multipliers per difficulty
TEMPO_MULTIPLIERS = {
    DifficultyLevel.EASY.value: 0.60,
    DifficultyLevel.MEDIUM.value: 0.80,
    DifficultyLevel.HARD.value: 0.95,
    DifficultyLevel.EXPERT.value: 1.00,
}

# Hands configuration
HANDS_CONFIG = {
    DifficultyLevel.EASY.value: "RH",
    DifficultyLevel.MEDIUM.value: "BOTH",
    DifficultyLevel.HARD.value: "BOTH",
    DifficultyLevel.EXPERT.value: "BOTH",
}


class DifficultyMetrics:
    """Computed difficulty features — every value from actual analysis."""

    def __init__(
        self,
        notes_per_second: float = 0.0,
        polyphony_ratio: float = 0.0,
        chord_density: float = 0.0,
        avg_hand_jump_semitones: float = 0.0,
        max_hand_jump_semitones: int = 0,
        tempo_bpm: float = 0.0,
        syncopation_ratio: float = 0.0,
        pitch_range_semitones: int = 0,
        max_simultaneous_notes: int = 0,
    ):
        self.notes_per_second = notes_per_second
        self.polyphony_ratio = polyphony_ratio
        self.chord_density = chord_density
        self.avg_hand_jump_semitones = avg_hand_jump_semitones
        self.max_hand_jump_semitones = max_hand_jump_semitones
        self.tempo_bpm = tempo_bpm
        self.syncopation_ratio = syncopation_ratio
        self.pitch_range_semitones = pitch_range_semitones
        self.max_simultaneous_notes = max_simultaneous_notes

    @property
    def difficulty_score(self) -> float:
        """
        Weighted sum of normalized features → 0.0 to 1.0.
        
        Weights:
          note_density:  0.20
          polyphony:     0.15
          chord_density: 0.10
          hand_jump:     0.15
          tempo:         0.15
          syncopation:   0.10
          pitch_range:   0.10
          simultaneous:  0.05
        """
        # Normalize each feature to 0-1
        nd = min(1.0, self.notes_per_second / 8.0)     # 8 nps = max
        poly = self.polyphony_ratio                      # already 0-1
        cd = min(1.0, self.chord_density / 2.0)          # 2 chords/s = max
        hj = min(1.0, self.avg_hand_jump_semitones / 12.0)  # octave = max
        tp = min(1.0, self.tempo_bpm / 180.0)            # 180 bpm = max
        syn = self.syncopation_ratio                      # already 0-1
        pr = min(1.0, self.pitch_range_semitones / 48.0)  # 4 octaves = max
        sn = min(1.0, self.max_simultaneous_notes / 6.0)  # 6 notes = max

        return round(
            nd * 0.20 + poly * 0.15 + cd * 0.10 + hj * 0.15 +
            tp * 0.15 + syn * 0.10 + pr * 0.10 + sn * 0.05,
            4,
        )

    @property
    def difficulty_level(self) -> str:
        score = self.difficulty_score
        if score < 0.25:
            return DifficultyLevel.EASY.value
        elif score < 0.50:
            return DifficultyLevel.MEDIUM.value
        elif score < 0.75:
            return DifficultyLevel.HARD.value
        else:
            return DifficultyLevel.EXPERT.value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "notes_per_second": round(self.notes_per_second, 3),
            "polyphony_ratio": round(self.polyphony_ratio, 3),
            "chord_density": round(self.chord_density, 3),
            "avg_hand_jump_semitones": round(self.avg_hand_jump_semitones, 2),
            "max_hand_jump_semitones": self.max_hand_jump_semitones,
            "tempo_bpm": round(self.tempo_bpm, 2),
            "syncopation_ratio": round(self.syncopation_ratio, 3),
            "pitch_range_semitones": self.pitch_range_semitones,
            "max_simultaneous_notes": self.max_simultaneous_notes,
            "difficulty_score": self.difficulty_score,
            "difficulty_level": self.difficulty_level,
        }


class DifficultyEngine:
    """
    Computes difficulty metrics and generates Easy/Medium/Hard/Expert
    variants from a real transcription.
    """

    def generate_variants(
        self,
        transcription_id: str,
        processing_job_id: uuid.UUID,
        bpm_result: Optional[Dict[str, Any]],
        db: Session,
    ) -> Dict[str, int]:
        """
        Generate all 4 difficulty variants for a transcription.
        
        Returns:
            {"EASY": 45, "MEDIUM": 120, "HARD": 280, "EXPERT": 340}
            (note counts per variant)
        """
        trans_uuid = uuid.UUID(transcription_id)
        transcription = db.query(Transcription).filter(
            Transcription.id == trans_uuid
        ).first()

        if not transcription:
            raise ValueError(f"Transcription {transcription_id} not found")

        # Get all valid notes (not discarded)
        notes = db.query(TranscriptionNote).filter(
            TranscriptionNote.transcription_id == trans_uuid,
            TranscriptionNote.validation_action != "DISCARD",
        ).order_by(TranscriptionNote.start_time).all()

        if not notes:
            logger.warning(f"No valid notes for transcription {transcription_id}")
            return {}

        # ── Compute difficulty metrics from actual note data ──────────────
        tempo = bpm_result.get("tempo_bpm", 120.0) if bpm_result else 120.0
        metrics = self._compute_metrics(notes, tempo)

        # ── Compute note importance scores ────────────────────────────────
        self._compute_importance_scores(notes)

        # ── Generate variants ─────────────────────────────────────────────
        summary = {}
        for level in [
            DifficultyLevel.EASY.value,
            DifficultyLevel.MEDIUM.value,
            DifficultyLevel.HARD.value,
            DifficultyLevel.EXPERT.value,
        ]:
            count = self._create_variant(
                level, notes, metrics, transcription, processing_job_id, db
            )
            summary[level] = count

        db.commit()

        logger.info(
            f"Difficulty variants generated for {transcription_id}: "
            f"difficulty_score={metrics.difficulty_score:.2f} "
            f"({metrics.difficulty_level}), "
            f"variants={summary}"
        )

        return summary

    def _compute_metrics(
        self, notes: List[TranscriptionNote], tempo_bpm: float
    ) -> DifficultyMetrics:
        """Compute actual difficulty metrics from note data."""
        if not notes:
            return DifficultyMetrics()

        duration = notes[-1].end_time - notes[0].start_time
        if duration <= 0:
            duration = 1.0

        # Notes per second
        nps = len(notes) / duration

        # Pitch range
        pitches = [n.midi_number for n in notes]
        pitch_range = max(pitches) - min(pitches)

        # Hand jumps (consecutive notes in same hand)
        jumps = []
        for i in range(len(notes) - 1):
            if notes[i].hand == notes[i + 1].hand:
                jump = abs(notes[i + 1].midi_number - notes[i].midi_number)
                jumps.append(jump)
        avg_jump = float(np.mean(jumps)) if jumps else 0.0
        max_jump = max(jumps) if jumps else 0

        # Polyphony: % of time with >1 simultaneous note
        poly_time = 0.0
        for i, note in enumerate(notes):
            overlapping = sum(
                1 for other in notes
                if other.id != note.id
                and other.start_time < note.end_time
                and other.end_time > note.start_time
            )
            if overlapping > 0:
                poly_time += note.duration
        polyphony_ratio = min(1.0, poly_time / duration)

        # Max simultaneous notes
        max_simultaneous = 1
        for note in notes:
            simultaneous = sum(
                1 for other in notes
                if other.start_time < note.end_time
                and other.end_time > note.start_time
            )
            max_simultaneous = max(max_simultaneous, simultaneous)

        # Chord density: simultaneous groups per second
        chord_groups = 0
        visited = set()
        for note in notes:
            if note.id in visited:
                continue
            group = [
                other for other in notes
                if abs(other.start_time - note.start_time) < 0.05
                and other.id not in visited
            ]
            if len(group) > 1:
                chord_groups += 1
                for g in group:
                    visited.add(g.id)
        chord_density = chord_groups / duration

        # Syncopation: rough estimate (notes on off-beats)
        beat_duration = 60.0 / max(tempo_bpm, 1)
        syncopated = sum(
            1 for n in notes
            if (n.start_time % beat_duration) > beat_duration * 0.25
            and (n.start_time % beat_duration) < beat_duration * 0.75
        )
        syncopation_ratio = syncopated / len(notes) if notes else 0.0

        return DifficultyMetrics(
            notes_per_second=nps,
            polyphony_ratio=polyphony_ratio,
            chord_density=chord_density,
            avg_hand_jump_semitones=avg_jump,
            max_hand_jump_semitones=max_jump,
            tempo_bpm=tempo_bpm,
            syncopation_ratio=syncopation_ratio,
            pitch_range_semitones=pitch_range,
            max_simultaneous_notes=max_simultaneous,
        )

    def _compute_importance_scores(self, notes: List[TranscriptionNote]):
        """
        Score each note's musical importance using actual features.
        
        NOT blind "is this the melody?" — uses:
          1. Pitch salience: highest pitch in time window → more important
          2. Onset strength: higher velocity → likely melody
          3. Duration: longer notes → more important
          4. Isolation: solo notes more important than inner chord voices
          5. Rhythmic position: approximated by start_time alignment
        """
        if not notes:
            return

        # Pre-compute global stats
        all_pitches = [n.midi_number for n in notes]
        pitch_range = max(all_pitches) - min(all_pitches) if len(all_pitches) > 1 else 1
        min_pitch = min(all_pitches)
        max_velocity = max(n.velocity for n in notes)
        max_duration = max(n.duration for n in notes)

        for note in notes:
            scores = []

            # 1. Pitch salience: higher pitch in local window = more important
            # (melody tends to be the highest voice)
            window = 0.1  # 100ms window
            local_notes = [
                n for n in notes
                if abs(n.start_time - note.start_time) < window
            ]
            local_pitches = [n.midi_number for n in local_notes]
            if local_pitches:
                pitch_rank = sorted(local_pitches, reverse=True).index(note.midi_number)
                pitch_salience = 1.0 - (pitch_rank / max(len(local_pitches), 1))
            else:
                pitch_salience = 0.5
            scores.append(pitch_salience * 0.25)

            # 2. Onset strength: velocity as proxy
            velocity_score = note.velocity / max(max_velocity, 1)
            scores.append(velocity_score * 0.20)

            # 3. Duration weight: longer notes more important
            duration_score = note.duration / max(max_duration, 0.01)
            scores.append(min(1.0, duration_score) * 0.20)

            # 4. Isolation: solo notes > chord inner voices
            simultaneous = len([
                n for n in notes
                if n.id != note.id
                and abs(n.start_time - note.start_time) < 0.05
            ])
            isolation = 1.0 / (1.0 + simultaneous)
            scores.append(isolation * 0.20)

            # 5. Rhythmic position: notes closer to beat positions
            # (approximated — use modular distance to quarter note grid)
            beat_approx = 0.5  # assume ~120 BPM
            beat_distance = note.start_time % beat_approx
            on_beat = 1.0 - min(beat_distance, beat_approx - beat_distance) / (beat_approx / 2)
            scores.append(on_beat * 0.15)

            note.importance_score = round(sum(scores), 4)

    def _create_variant(
        self,
        level: str,
        source_notes: List[TranscriptionNote],
        metrics: DifficultyMetrics,
        transcription: Transcription,
        processing_job_id: uuid.UUID,
        db: Session,
    ) -> int:
        """Create a single difficulty variant with selected notes."""
        threshold = IMPORTANCE_THRESHOLDS[level]
        tempo_mult = TEMPO_MULTIPLIERS[level]
        hands = HANDS_CONFIG[level]

        # Select notes based on importance threshold
        if level == DifficultyLevel.EXPERT.value:
            # Expert = ALL valid notes, unmodified
            selected = source_notes
        else:
            selected = [
                n for n in source_notes
                if getattr(n, 'importance_score', 0.5) >= threshold
            ]

        # For EASY: also enforce single notes (no chords)
        if level == DifficultyLevel.EASY.value:
            selected = self._simplify_to_single_notes(selected)

        # For EASY: right hand only
        if hands == "RH":
            # Keep all selected but mark as right hand
            pass  # Hand assignment stays in DifficultyNote

        # Compute variant-specific metrics
        variant_metrics = self._compute_metrics(selected, metrics.tempo_bpm * tempo_mult)

        # Create DifficultyVariant
        variant = DifficultyVariant(
            id=uuid.uuid4(),
            transcription_id=transcription.id,
            song_id=transcription.song_id,
            processing_job_id=processing_job_id,
            level=level,
            metrics=variant_metrics.to_dict(),
            difficulty_score=variant_metrics.difficulty_score,
            note_count=len(selected),
            tempo_multiplier=tempo_mult,
            hands_used=hands,
            engine_version=ENGINE_VERSION,
        )
        db.add(variant)
        db.flush()

        # Create DifficultyNote rows with provenance link
        for idx, source_note in enumerate(selected):
            hand = "RIGHT" if hands == "RH" else source_note.hand
            if hand == "UNASSIGNED":
                hand = "RIGHT"

            diff_note = DifficultyNote(
                difficulty_variant_id=variant.id,
                source_note_id=source_note.id,
                sequence_index=idx,
                midi_number=source_note.midi_number,
                note_name=source_note.note_name,
                start_time=source_note.start_time,
                end_time=source_note.end_time,
                duration=source_note.duration,
                velocity=source_note.velocity,
                hand=hand,
                measure_number=source_note.measure_number,
                beat_position=source_note.beat_position,
                importance_score=getattr(source_note, 'importance_score', 0.5),
            )
            db.add(diff_note)

        return len(selected)

    def _simplify_to_single_notes(
        self, notes: List[TranscriptionNote]
    ) -> List[TranscriptionNote]:
        """
        For Easy mode: reduce chords to single notes.
        Keep the highest-importance note from each simultaneous group.
        """
        if not notes:
            return []

        result = []
        used = set()

        for note in notes:
            if note.id in used:
                continue

            # Find simultaneous notes
            group = [
                n for n in notes
                if n.id not in used
                and abs(n.start_time - note.start_time) < 0.05
            ]

            if len(group) > 1:
                # Keep the most important note
                best = max(group, key=lambda n: getattr(n, 'importance_score', 0.5))
                result.append(best)
                for g in group:
                    used.add(g.id)
            else:
                result.append(note)
                used.add(note.id)

        return result
