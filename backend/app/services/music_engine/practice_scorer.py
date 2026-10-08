"""
Practice scoring utilities for Melodix.

Implements the per-segment scoring pipeline described in the EFQ-style spec:

  classify_note_errors()   — tags each student note with error types
  score_segment()          — returns accuracy + expressiveness scores for one phrase
  build_session_summary()  — averages a list of SegmentScore objects

All functions are pure / stateless — no DB access, no model inference.
They operate only on the note-event dicts that the CNN-BiLSTM already outputs.

References:
  Nakamura et al. (2015), Flossmann et al. (2010) — threshold provenance.
  Weights (EFQ_WEIGHT_*) come from a single paper; treat as provisional until
  validated on real student recordings.
"""

from __future__ import annotations

import math
import statistics
from typing import Any, Dict, List, Set

from app.services.music_engine.score_constants import (
    CONSISTENCY_PLACEHOLDER,
    DYNAMICS_ERROR_THRESHOLD_VEL,
    EFQ_WEIGHT_CONSISTENCY,
    EFQ_WEIGHT_DYNAMIC_VARIANCE,
    EFQ_WEIGHT_TEMPORAL_STABILITY,
    EXPECTED_IOI_STD_S,
    EXPECTED_VEL_VARIANCE,
    TIMING_ERROR_THRESHOLD_S,
)

# ---------------------------------------------------------------------------
# Public type aliases
# ---------------------------------------------------------------------------

NoteEvent = Dict[str, Any]   # any dict with keys: note, onset, velocity


# ---------------------------------------------------------------------------
# Error classification
# ---------------------------------------------------------------------------

ERROR_CORRECT          = "correct"
ERROR_PITCH            = "pitch_error"
ERROR_TIMING           = "timing_error"
ERROR_DYNAMICS         = "dynamics_error"


def classify_note_errors(
    student_note: NoteEvent,
    reference_note: NoteEvent,
) -> Set[str]:
    """
    Compare one student note against its matched reference note and return
    a set of error tags.

    A note with no errors returns {ERROR_CORRECT}.  A note CAN carry multiple
    error tags simultaneously (e.g. wrong pitch AND late onset).

    Args:
        student_note:    Dict with keys "note" (str), "onset" (float, seconds),
                         "velocity" (int, 0–127).
        reference_note:  Same shape, from the curriculum/phrase reference.

    Returns:
        Set of error tag strings (see ERROR_* constants above).
    """
    tags: Set[str] = set()

    # --- Pitch ---
    if student_note.get("note") != reference_note.get("note"):
        tags.add(ERROR_PITCH)

    # --- Timing ---
    student_onset   = float(student_note.get("onset", 0.0))
    reference_onset = float(reference_note.get("onset", 0.0))
    if abs(student_onset - reference_onset) > TIMING_ERROR_THRESHOLD_S:
        tags.add(ERROR_TIMING)

    # --- Dynamics ---
    student_vel   = int(student_note.get("velocity", 64))
    reference_vel = int(reference_note.get("velocity", 64))
    if abs(student_vel - reference_vel) > DYNAMICS_ERROR_THRESHOLD_VEL:
        tags.add(ERROR_DYNAMICS)

    if not tags:
        tags.add(ERROR_CORRECT)

    return tags


# ---------------------------------------------------------------------------
# Expressiveness sub-scores
# ---------------------------------------------------------------------------

def _dynamic_variance_score(student_notes: List[NoteEvent]) -> float:
    """
    Normalised dynamic variance [0, 1].

    Variance of student velocities within the segment, normalised against
    EXPECTED_VEL_VARIANCE.  Clamped to [0, 1].
    """
    velocities = [int(n.get("velocity", 64)) for n in student_notes]
    if len(velocities) < 2:
        return 0.0
    var = statistics.variance(velocities)
    return min(1.0, var / EXPECTED_VEL_VARIANCE)


def _temporal_stability_score(student_notes: List[NoteEvent]) -> float:
    """
    Normalised temporal stability [0, 1].

    Lower IOI standard deviation → more stable → higher score.
    Uses `1 - normalised_std` so that perfect metronomic timing yields 1.0.
    """
    onsets = sorted(float(n.get("onset", 0.0)) for n in student_notes)
    if len(onsets) < 2:
        return 1.0   # single note = perfectly "stable"
    ioi = [onsets[i + 1] - onsets[i] for i in range(len(onsets) - 1)]
    if len(ioi) < 2:
        return 1.0
    std = statistics.stdev(ioi)
    normalised_std = min(1.0, std / EXPECTED_IOI_STD_S)
    return 1.0 - normalised_std


def _expressiveness_score(student_notes: List[NoteEvent]) -> float:
    """
    EFQ-style expressiveness score on a 0–5 scale.

    Formula:
        5 × (0.40 × DV  +  0.35 × TS  +  0.25 × consistency_placeholder)

    KNOWN SIMPLIFICATION: consistency_placeholder is a fixed constant (0.7)
    until a real note-grouping-consistency measure is implemented.
    """
    dv = _dynamic_variance_score(student_notes)
    ts = _temporal_stability_score(student_notes)
    # KNOWN SIMPLIFICATION — replace CONSISTENCY_PLACEHOLDER once grouping
    # analysis is available.
    cp = CONSISTENCY_PLACEHOLDER

    raw = (
        EFQ_WEIGHT_DYNAMIC_VARIANCE   * dv
        + EFQ_WEIGHT_TEMPORAL_STABILITY * ts
        + EFQ_WEIGHT_CONSISTENCY        * cp
    )
    return round(5.0 * raw, 3)


# ---------------------------------------------------------------------------
# Segment scoring
# ---------------------------------------------------------------------------

class SegmentScore:
    """Holds the scoring result for a single phrase/segment."""

    def __init__(
        self,
        segment_id: str,
        accuracy_score: float,
        expressiveness_score: float,
        error_tags: List[Dict[str, Any]],
    ) -> None:
        self.segment_id          = segment_id
        self.accuracy_score      = accuracy_score       # 0.0 – 1.0
        self.expressiveness_score = expressiveness_score  # 0.0 – 5.0
        self.error_tags          = error_tags           # list of per-note tag dicts

    def to_dict(self) -> Dict[str, Any]:
        return {
            "segment_id":           self.segment_id,
            "accuracy_score":       round(self.accuracy_score, 4),
            "expressiveness_score": round(self.expressiveness_score, 3),
            "error_tags":           self.error_tags,
        }


def score_segment(
    segment_id: str,
    student_notes: List[NoteEvent],
    reference_notes: List[NoteEvent],
) -> SegmentScore:
    """
    Score one phrase/segment.

    Matching strategy: zip student notes to reference notes positionally (index-aligned).
    If the student played fewer notes than the reference, the unmatched reference
    notes count as missed (pitch_error).  Extra student notes beyond the reference
    are ignored for accuracy (they contribute to expressiveness as-is).

    Args:
        segment_id:      Opaque string ID (matches the phrase ID from PhraseBuilder).
        student_notes:   List of dicts output by CNN-BiLSTM / Transcriber for this chunk.
        reference_notes: List of dicts from the curriculum's expectedEvents for this phrase.

    Returns:
        SegmentScore instance.
    """
    if not reference_notes:
        # No reference to compare against — return a neutral score
        return SegmentScore(
            segment_id=segment_id,
            accuracy_score=1.0,
            expressiveness_score=_expressiveness_score(student_notes),
            error_tags=[],
        )

    per_note_tags: List[Dict[str, Any]] = []
    total = len(reference_notes)
    flagged = 0

    for i, ref in enumerate(reference_notes):
        if i < len(student_notes):
            stu = student_notes[i]
            tags = classify_note_errors(stu, ref)
        else:
            # Student missed this note entirely
            tags = {ERROR_PITCH}

        is_flagged = tags != {ERROR_CORRECT}
        if is_flagged:
            flagged += 1

        per_note_tags.append({
            "position":   i,
            "ref_note":   ref.get("note"),
            "stu_note":   student_notes[i].get("note") if i < len(student_notes) else None,
            "tags":       sorted(tags),
        })

    accuracy = 1.0 - (flagged / total)
    expr     = _expressiveness_score(student_notes)

    return SegmentScore(
        segment_id=segment_id,
        accuracy_score=round(accuracy, 4),
        expressiveness_score=expr,
        error_tags=per_note_tags,
    )


# ---------------------------------------------------------------------------
# Session summary
# ---------------------------------------------------------------------------

def build_session_summary(segment_scores: List[SegmentScore]) -> Dict[str, Any]:
    """
    Compute an overall session summary by averaging across all scored segments.

    Args:
        segment_scores: All SegmentScore objects accumulated during the session.

    Returns:
        Dict with overall_accuracy (0–1) and overall_expressiveness (0–5).
    """
    if not segment_scores:
        return {"overall_accuracy": 0.0, "overall_expressiveness": 0.0, "segments_scored": 0}

    acc  = statistics.mean(s.accuracy_score       for s in segment_scores)
    expr = statistics.mean(s.expressiveness_score for s in segment_scores)

    return {
        "overall_accuracy":       round(acc,  4),
        "overall_expressiveness": round(expr, 3),
        "segments_scored":        len(segment_scores),
    }
