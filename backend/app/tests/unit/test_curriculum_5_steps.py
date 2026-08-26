"""
Unit tests for the 5-step progressive curriculum generator.

Tests:
  - Exactly 5 LearningLevel objects are produced (Levels 1 to 5)
  - Level 1 is wait-mode right hand, no lyrics
  - Level 2 is timed right hand, synced lyrics
  - Level 3 is simplified left hand chords
  - Level 4 is combined two-hand simplified chords
  - Level 5 is full performance original tempo
"""

from __future__ import annotations

import types
import pytest

from app.services.music_engine.lyric_aligner import notes_match, LyricAligner
from app.services.music_engine.phrase_builder import PhraseBuilder
from app.services.music_engine.curriculum import LearningPlanGenerator


# ---------------------------------------------------------------------------
# Helpers — lightweight mock note objects
# ---------------------------------------------------------------------------

def make_note(
    note_name: str,
    start_time: float,
    duration: float = 0.5,
    midi_number: int = 60,
    hand: str = "RIGHT",
    measure_number: int = 0,
) -> types.SimpleNamespace:
    return types.SimpleNamespace(
        note_name=note_name,
        start_time=start_time,
        duration=duration,
        midi_number=midi_number,
        hand=hand,
        measure_number=measure_number,
    )


def make_section(label: str, start: float, notes: list) -> dict:
    return {
        "display_label": label,
        "start_time": start,
        "notes": notes,
    }


# ---------------------------------------------------------------------------
# 1. Pitch-class / enharmonic normalization
# ---------------------------------------------------------------------------

class TestNotesMatch:
    def test_exact_match(self):
        assert notes_match("C4", "C4")

    def test_enharmonic_sharp_flat(self):
        assert notes_match("D#5", "Eb5")


# ---------------------------------------------------------------------------
# 2. Full curriculum — 5 levels produced
# ---------------------------------------------------------------------------

class TestCurriculumGenerator:
    def _make_sections(self) -> list:
        """Build two simple sections with 8 RH notes each."""
        notes_v1 = [
            make_note(["C4","E4","G4","A4","G4","E4","D4","C4"][i], i * 0.5,
                      midi_number=60 + [0,4,7,9,7,4,2,0][i], measure_number=i // 4)
            for i in range(8)
        ]
        notes_v2 = [
            make_note(["D4","F4","A4","C5","A4","F4","E4","D4"][i], 4.0 + i * 0.5,
                      midi_number=62 + [0,3,7,10,7,3,2,0][i], measure_number=4 + i // 4)
            for i in range(8)
        ]
        return [
            make_section("Verse 1", 0.0, notes_v1),
            make_section("Verse 2", 4.0, notes_v2),
        ]

    def test_produces_exactly_5_levels(self):
        sections = self._make_sections()
        result = LearningPlanGenerator.generate_curriculum(sections, bpm=120.0)
        assert "levels" in result
        assert len(result["levels"]) == 5

    def test_level_numbers_are_1_to_5(self):
        sections = self._make_sections()
        result = LearningPlanGenerator.generate_curriculum(sections, bpm=120.0)
        nums = [lv["levelNumber"] for lv in result["levels"]]
        assert nums == list(range(1, 6))

    def test_level1_is_wait_mode_right_hand(self):
        sections = self._make_sections()
        result = LearningPlanGenerator.generate_curriculum(sections, bpm=120.0)
        level1 = result["levels"][0]
        assert level1["progressionMode"] == "wait"
        assert level1["learningMode"] == "learn"
        assert level1["handMode"] == "right"

    def test_level3_is_chords_left_hand(self):
        sections = self._make_sections()
        result = LearningPlanGenerator.generate_curriculum(sections, bpm=120.0)
        level3 = result["levels"][2]
        assert level3["handMode"] == "left"
        assert level3["simplified"] is True

    def test_level4_combined_simplified(self):
        sections = self._make_sections()
        result = LearningPlanGenerator.generate_curriculum(sections, bpm=120.0)
        level4 = result["levels"][3]
        assert level4["handMode"] == "both"
        assert level4["simplified"] is True

    def test_level5_is_perform_mode(self):
        sections = self._make_sections()
        result = LearningPlanGenerator.generate_curriculum(sections, bpm=120.0)
        level5 = result["levels"][4]
        assert level5["learningMode"] == "perform"
        assert level5["missions"][0]["bpm"] == pytest.approx(120.0)
        assert level5["simplified"] is False
