"""
Phrase builder service.

Splits a flat list of transcription notes into musically-bounded phrases
for Level 3 (Listen / Watch / Play) practice.

Boundary priority (applied in order, first match wins):
  1. lyric_clause  — the previous syllable ends with  , . ? ! ;
  2. measure       — measure_number changes
  3. rest          — gap between consecutive notes > 0.3 s
  4. long_note     — note duration > 1.5 × section average note duration
  5. max_count     — 8-note hard cap
"""

from __future__ import annotations

import re
import uuid
from statistics import mean
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_REST_GAP_SEC      = 0.3     # seconds gap that signals a rest boundary
_LONG_NOTE_RATIO   = 1.5     # multiple of average duration
_MAX_NOTES_PHRASE  = 8       # fallback hard cap


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class PhraseBuilder:
    """Convert a note list + lyric syllables into SongPhrase dicts."""

    @staticmethod
    def build(
        notes: List[Any],
        section_start: float = 0.0,
        syllables: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Args:
            notes:         TranscriptionNote objects (must have .start_time,
                           .duration, .note_name, and optionally .measure_number).
            section_start: Absolute start time of the section (used for relative_time).
            syllables:     LyricAlignment['syllables'] list, aligned by index to notes.

        Returns:
            List of SongPhrase dicts ready for JSON serialisation.
        """
        if not notes:
            return []

        avg_dur = _safe_mean([getattr(n, "duration", 0.5) for n in notes])
        phrases: List[Dict[str, Any]] = []
        current: List[Any] = []
        current_syl_indices: List[int] = []

        for i, note in enumerate(notes):
            if current:
                reason = _boundary_reason(
                    prev_note    = current[-1],
                    curr_note    = note,
                    prev_syl_idx = current_syl_indices[-1] if current_syl_indices else None,
                    syllables    = syllables,
                    avg_dur      = avg_dur,
                    phrase_len   = len(current),
                )
                if reason:
                    phrases.append(_make_phrase(
                        notes          = current,
                        syl_indices    = current_syl_indices,
                        syllables      = syllables,
                        section_start  = section_start,
                        boundary_reason= reason,
                        phrase_index   = len(phrases),
                    ))
                    current = []
                    current_syl_indices = []

            current.append(note)
            current_syl_indices.append(i)

        # Flush last phrase
        if current:
            phrases.append(_make_phrase(
                notes          = current,
                syl_indices    = current_syl_indices,
                syllables      = syllables,
                section_start  = section_start,
                boundary_reason= "max_count",   # last phrase has no natural boundary
                phrase_index   = len(phrases),
            ))

        # Back-fill phraseTotal now we know the final count
        total = len(phrases)
        for p in phrases:
            p["phraseTotal"] = total

        return phrases


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_CLAUSE_END_CHARS = set(",.?!;")


def _boundary_reason(
    prev_note: Any,
    curr_note: Any,
    prev_syl_idx: Optional[int],
    syllables: Optional[List[Dict[str, Any]]],
    avg_dur: float,
    phrase_len: int,
) -> Optional[str]:
    """Return the reason string if a boundary should be placed, else None."""

    # Priority 1: lyric clause boundary
    if syllables and prev_syl_idx is not None and prev_syl_idx < len(syllables):
        syl_text = syllables[prev_syl_idx].get("text", "")
        if syl_text and syl_text[-1] in _CLAUSE_END_CHARS:
            return "lyric_clause"

    # Priority 2: measure boundary
    prev_measure = getattr(prev_note, "measure_number", None)
    curr_measure = getattr(curr_note, "measure_number", None)
    if prev_measure is not None and curr_measure is not None and curr_measure != prev_measure:
        return "measure"

    # Priority 3: rest (gap > threshold)
    prev_end = getattr(prev_note, "start_time", 0.0) + getattr(prev_note, "duration", 0.5)
    curr_start = getattr(curr_note, "start_time", 0.0)
    if curr_start - prev_end > _REST_GAP_SEC:
        return "rest"

    # Priority 4: long note (previous note was unusually long)
    prev_dur = getattr(prev_note, "duration", 0.5)
    if avg_dur > 0 and prev_dur > avg_dur * _LONG_NOTE_RATIO:
        return "long_note"

    # Priority 5: max-count fallback
    if phrase_len >= _MAX_NOTES_PHRASE:
        return "max_count"

    return None


def _make_phrase(
    notes: List[Any],
    syl_indices: List[int],
    syllables: Optional[List[Dict[str, Any]]],
    section_start: float,
    boundary_reason: str,
    phrase_index: int,
) -> Dict[str, Any]:
    """Construct a single SongPhrase dict."""
    phrase_start = getattr(notes[0], "start_time", section_start)

    expected_events: List[Dict[str, Any]] = []
    for n in notes:
        eid = str(uuid.uuid4())
        expected_events.append({
            "id": eid,
            "note": n.note_name,
            "relative_time": max(0.0, getattr(n, "start_time", phrase_start) - phrase_start),
            "duration": getattr(n, "duration", 0.5),
            "hand": getattr(n, "hand", "RIGHT").lower(),
        })

    # Attach syllable subset
    phrase_syllables: List[Dict[str, Any]] = []
    if syllables:
        for local_i, global_i in enumerate(syl_indices):
            if global_i < len(syllables):
                syl = dict(syllables[global_i])
                # Update the noteEventId to match this phrase's event
                if local_i < len(expected_events):
                    syl["noteEventIds"] = [expected_events[local_i]["id"]]
                phrase_syllables.append(syl)

    return {
        "id": str(uuid.uuid4()),
        "phraseIndex": phrase_index,
        "phraseTotal": 0,          # filled in by caller after all phrases are built
        "boundaryReason": boundary_reason,
        "expectedEvents": expected_events,
        "lyricSyllables": phrase_syllables if phrase_syllables else None,
    }


def _safe_mean(values: List[float]) -> float:
    return mean(values) if values else 0.5
