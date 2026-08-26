"""
Lyric alignment service.

Runs a 4-tier confidence pipeline to map lyric text to right-hand
note events:

  Tier 1 — Source-attached timing (e.g. LRC / MusicXML lyrics)
  Tier 2 — Curated built-in dictionary (popular teaching songs)
  Tier 3 — Procedural syllabification (word-level vowel splitting)
  Tier 4 — Line / word fallback (always succeeds, lowest confidence)

Returns a ``LyricAlignment`` dict with:
  alignmentLevel: "syllable" | "word" | "line" | "none"
  confidence:     0.0 – 1.0
  syllables:      list of LyricSyllable dicts
"""

from __future__ import annotations

import re
import uuid
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ENHARMONIC_PAIRS = {
    "C#": "Db", "Db": "C#",
    "D#": "Eb", "Eb": "D#",
    "F#": "Gb", "Gb": "F#",
    "G#": "Ab", "Ab": "G#",
    "A#": "Bb", "Bb": "A#",
}

# Notes in chromatic order (C=0 … B=11)
_PITCH_CLASS_MAP: Dict[str, int] = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3,
    "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8,
    "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11,
}


def note_to_midi(note_name: str) -> Optional[int]:
    """Convert a note string like 'D#5' or 'Bb4' to a MIDI number.
    Returns None if the note cannot be parsed."""
    m = re.match(r"^([A-G][#b]?)(\d+)$", note_name.strip())
    if not m:
        return None
    pitch_class_str = m.group(1)
    octave = int(m.group(2))
    pc = _PITCH_CLASS_MAP.get(pitch_class_str)
    if pc is None:
        return None
    return (octave + 1) * 12 + pc


def notes_match(expected: str, played: str) -> bool:
    """Return True when two note names are enharmonically identical.

    Compares via MIDI numbers so that D#5 == Eb5, etc.
    Falls back to normalized string compare if MIDI parse fails.
    """
    midi_a = note_to_midi(expected)
    midi_b = note_to_midi(played)
    if midi_a is not None and midi_b is not None:
        return midi_a == midi_b
    # Fallback: strip octave, uppercase, compare
    def _bare(n: str) -> str:
        return re.sub(r"\d+$", "", n.strip()).upper()
    return _bare(expected) == _bare(played)


# ---------------------------------------------------------------------------
# Built-in lyric dictionary  (syllable-level, Tier 2)
# ---------------------------------------------------------------------------

# Keys: lowercase song title (or close substring).
# Values: list of syllable strings aligned left-to-right to right-hand notes.
# Punctuation on the last syllable of a clause marks a phrase boundary.

_KNOWN_LYRICS: Dict[str, List[str]] = {
    "ode to joy": [
        "Joy-", "ful,", "joy-", "ful,", "we", "a-", "dore", "thee,",
        "God", "of", "glo-", "ry,", "Lord", "of", "love;",
        "Hearts", "un-", "fold", "like", "flow'rs", "be-", "fore", "thee,",
        "O-", "p'ning", "to", "the", "sun", "a-", "bove.",
    ],
    "twinkle twinkle": [
        "Twin-", "kle,", "twin-", "kle,", "lit-", "tle", "star,",
        "How", "I", "won-", "der", "what", "you", "are!",
        "Up", "a-", "bove", "the", "world", "so", "high,",
        "Like", "a", "dia-", "mond", "in", "the", "sky.",
    ],
    "perfect": [
        "I", "found", "a", "love", "for", "me,",
        "Dar-", "ling,", "just", "dive", "right", "in,",
        "Fol-", "low", "my", "lead.",
        "Well,", "I", "found", "a", "girl,",
        "beau-", "ti-", "ful", "and", "sweet.",
    ],
    "happy birthday": [
        "Hap-", "py", "birth-", "day", "to", "you,",
        "Hap-", "py", "birth-", "day", "to", "you,",
        "Hap-", "py", "birth-", "day,", "dear", "friend,",
        "Hap-", "py", "birth-", "day", "to", "you!",
    ],
    "clair de lune": [
        "Ton", "â-", "me", "est", "un", "pay-", "sa-", "ge",
        "fa-", "vo-", "ri,",
        "Que", "vont", "char-", "mant",
        "mas-", "ques", "et", "ber-", "ga-", "mas-", "ques.",
    ],
    "minuet in g": [
        "Min-", "u-", "et,", "so", "light", "and", "gay,",
        "Notes", "that", "dance", "and", "seem", "to", "play.",
    ],
    "amazing grace": [
        "A-", "ma-", "zing", "grace,", "how", "sweet", "the", "sound,",
        "That", "saved", "a", "wretch", "like", "me.",
        "I", "once", "was", "lost,", "but", "now", "am", "found,",
        "Was", "blind,", "but", "now", "I", "see.",
    ],
    "fur elise": [
        "Dah", "dah", "dah", "dah—", "na", "na", "na", "na—",
        "na", "dah", "dah", "dah—", "na", "na", "na", "na—",
    ],
}


# ---------------------------------------------------------------------------
# Tier 3 — Procedural syllabification
# ---------------------------------------------------------------------------

def _syllabify(word: str) -> List[str]:
    """Split a word into rough syllables using vowel-consonant boundaries.

    Simple heuristic: split before each vowel that follows a consonant.
    E.g. "melody" → ["me-", "lo-", "dy"]
    """
    vowels = set("aeiouAEIOU")
    result: List[str] = []
    current = ""
    for i, ch in enumerate(word):
        current += ch
        # If the current char is a vowel and the next char is a consonant,
        # or we are at the last char of a vowel cluster → cut here.
        if ch in vowels and i + 1 < len(word) and word[i + 1] not in vowels:
            result.append(current + "-")
            current = ""
    if current:
        result.append(current)
    return result if result else [word]


def _words_to_syllables(text: str) -> List[str]:
    """Procedurally syllabify each word in a lyric string."""
    words = text.split()
    syllables: List[str] = []
    for i, word in enumerate(words):
        parts = _syllabify(word)
        # Remove trailing dash from last syllable of last word
        if i == len(words) - 1 and parts:
            parts[-1] = parts[-1].rstrip("-")
        syllables.extend(parts)
    return syllables


# ---------------------------------------------------------------------------
# Main aligner
# ---------------------------------------------------------------------------

class LyricAligner:
    """Maps lyric text to note events via the 4-tier pipeline."""

    @staticmethod
    def align(
        note_events: List[Dict[str, Any]],
        song_title: str,
        source_syllables: Optional[List[str]] = None,
        raw_lyric_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run the lyric alignment pipeline and return a LyricAlignment dict.

        Args:
            note_events:      Right-hand expected events (dicts with 'note', 'id', etc.).
            song_title:       Used for Tier 2 curated lookup.
            source_syllables: If the import source already provides timed syllables (Tier 1).
            raw_lyric_text:   Full lyric text for procedural syllabification (Tier 3/4).

        Returns:
            {
                "alignmentLevel": "syllable" | "word" | "line" | "none",
                "confidence": 0.0–1.0,
                "syllables": [...LyricSyllable dicts...]
            }
        """
        n = len(note_events)

        # --- Tier 1: source-attached syllables --------------------------------
        if source_syllables and len(source_syllables) >= max(1, n // 2):
            syls = _pad_or_trim(source_syllables, n)
            return _build_result(syls, note_events, "syllable", 0.95)

        # --- Tier 2: curated dictionary ----------------------------------------
        curated = LyricAligner._curated_lookup(song_title)
        if curated:
            syls = _pad_or_trim(curated, n)
            return _build_result(syls, note_events, "syllable", 0.90)

        # --- Tier 3: procedural syllabification --------------------------------
        if raw_lyric_text and raw_lyric_text.strip():
            syls = _words_to_syllables(raw_lyric_text)
            if syls:
                syls = _pad_or_trim(syls, n)
                confidence = min(0.75, len(syls) / max(n, 1) * 0.75)
                level = "syllable" if confidence >= 0.6 else "word"
                return _build_result(syls, note_events, level, confidence)

        # --- Tier 4: line fallback (always succeeds) ---------------------------
        # Group notes into 4-note chunks, label each chunk with a placeholder line
        chunk_size = 4
        line_labels = [
            "♪ phrase " + str(i + 1)
            for i in range((n + chunk_size - 1) // chunk_size)
        ]
        syls: List[str] = []
        for i in range(n):
            chunk_idx = i // chunk_size
            # First note of chunk gets the label, rest get empty
            syls.append(line_labels[chunk_idx] if i % chunk_size == 0 else "")
        return _build_result(syls, note_events, "line", 0.30)

    # ------------------------------------------------------------------

    @staticmethod
    def _curated_lookup(song_title: str) -> Optional[List[str]]:
        normalized = song_title.lower().strip()
        # Exact match
        if normalized in _KNOWN_LYRICS:
            return _KNOWN_LYRICS[normalized]
        # Substring match
        for key, syls in _KNOWN_LYRICS.items():
            if key in normalized or normalized in key:
                return syls
        return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pad_or_trim(syllables: List[str], target_len: int) -> List[str]:
    """Repeat syllables cyclically if too short; trim if too long."""
    if not syllables:
        return [""] * target_len
    result: List[str] = []
    for i in range(target_len):
        result.append(syllables[i % len(syllables)])
    return result


def _build_result(
    syllables: List[str],
    note_events: List[Dict[str, Any]],
    alignment_level: str,
    confidence: float,
) -> Dict[str, Any]:
    """Build the final LyricAlignment structure."""
    syllable_records = []
    for i, (syl, event) in enumerate(zip(syllables, note_events)):
        event_id = event.get("id") or str(uuid.uuid4())
        # Retroactively attach the ID to the event so it can be referenced
        if "id" not in event:
            event["id"] = event_id
        syllable_records.append({
            "text": syl,
            "alignmentLevel": alignment_level,
            "noteEventIds": [event_id],
        })
    return {
        "alignmentLevel": alignment_level,
        "confidence": round(confidence, 4),
        "syllables": syllable_records,
    }
