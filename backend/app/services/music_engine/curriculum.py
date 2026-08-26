"""
Learning plan generator — Simplified 5-step natural curriculum.

Levels:
  1  1️⃣ Learn the Notes         — wait-mode, right hand only, no lyrics.
  2  2️⃣ Melody with Lyrics      — timed scrolling, right hand only, synchronized lyrics.
  3  3️⃣ Learn the Chords        — left hand chords practice (one bass note per chord/measure).
  4  4️⃣ Melody + Chords + Lyrics — both hands combined, simplified left hand, synchronized lyrics.
  5  5️⃣ Full Song Performance    — original tempo, both hands, full arrangement.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from app.services.music_engine.lyric_aligner import LyricAligner
from app.services.music_engine.phrase_builder import PhraseBuilder


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _to_event(note: Any, base_time: float = 0.0) -> Dict[str, Any]:
    """Convert a TranscriptionNote to an ExpectedEvent dict."""
    eid = str(uuid.uuid4())
    return {
        "id": eid,
        "note": note.note_name,
        "relative_time": max(0.0, getattr(note, "start_time", 0.0) - base_time),
        "duration": getattr(note, "duration", 0.5),
        "hand": getattr(note, "hand", "RIGHT").lower(),
    }


def _make_mission(
    *,
    title: str,
    mission_type: str,
    level_number: int,
    progression_mode: str,
    hand_mode: str,
    bpm: float,
    learning_goal: str,
    xp_reward: int,
    status: str = "locked",
    simplified: bool = False,
    expected_events: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "title": title,
        "type": mission_type,
        "status": status,
        "progress": 0,
        "bpm": bpm,
        "levelNumber": level_number,
        "progressionMode": progression_mode,
        "handMode": hand_mode,
        "simplified": simplified,
        "learningGoal": learning_goal,
        "xpReward": xp_reward,
        "expectedEvents": expected_events or [],
    }


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------

class LearningPlanGenerator:

    @staticmethod
    def generate_curriculum(
        sections: List[Dict[str, Any]],
        bpm: float,
        song_title: str = "Song",
        raw_lyric_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build the simplified 5-step natural song-learning curriculum.

        Returns:
          phases        — legacy sidebar compatibility
          levels        — exactly 5 structured levels (1 to 5)
          lyricAlignment — song-level lyric alignment (confidence-scored)
          phrases        — musically-bounded phrase list (retained for Level 3 reference)
        """
        slow_bpm   = max(40.0, bpm * 0.60)
        medium_bpm = max(50.0, bpm * 0.80)

        # ------------------------------------------------------------------
        # Gather all right-hand and left-hand notes across all sections
        # ------------------------------------------------------------------
        all_right_notes: List[Any] = []
        all_left_notes: List[Any] = []
        all_notes: List[Any] = []

        for section in sections:
            section_notes = section.get("notes", [])
            all_notes.extend(section_notes)
            for n in section_notes:
                if getattr(n, "hand", "RIGHT") == "LEFT":
                    all_left_notes.append(n)
                else:
                    all_right_notes.append(n)

        # Sort by start time
        all_right_notes.sort(key=lambda n: getattr(n, "start_time", 0.0))
        all_left_notes.sort(key=lambda n: getattr(n, "start_time", 0.0))
        all_notes.sort(key=lambda n: getattr(n, "start_time", 0.0))

        # ------------------------------------------------------------------
        # Build song-level lyric alignment
        # ------------------------------------------------------------------
        rh_events_raw = [_to_event(n) for n in all_right_notes]
        lyric_alignment = LyricAligner.align(
            note_events=rh_events_raw,
            song_title=song_title,
            raw_lyric_text=raw_lyric_text,
        )

        # ------------------------------------------------------------------
        # Build phrase list using musical boundaries
        # ------------------------------------------------------------------
        all_phrases = PhraseBuilder.build(
            notes=all_right_notes,
            section_start=getattr(all_right_notes[0], "start_time", 0.0) if all_right_notes else 0.0,
            syllables=lyric_alignment["syllables"],
        )

        # ------------------------------------------------------------------
        # Level 1 — Learn the Notes (wait-mode, right hand only, no lyrics)
        # ------------------------------------------------------------------
        level1_missions = []
        for s_idx, section in enumerate(sections):
            section_notes = section.get("notes", [])
            rh_notes = [n for n in section_notes if getattr(n, "hand", "RIGHT") != "LEFT"]
            if not rh_notes:
                continue
            start = getattr(rh_notes[0], "start_time", 0.0)
            events = [_to_event(n, start) for n in rh_notes]
            level1_missions.append(_make_mission(
                title=f"Melody: One Note at a Time — {section['display_label']}",
                mission_type="right_hand",
                level_number=1,
                progression_mode="wait",
                hand_mode="right",
                bpm=slow_bpm,
                learning_goal=(
                    "Right hand only. Hear the note and play when ready. "
                    "No lyrics shown — focus purely on learning the note sequence."
                ),
                xp_reward=50,
                status="available" if s_idx == 0 else "locked",
                expected_events=events,
            ))

        # ------------------------------------------------------------------
        # Level 2 — Melody with Lyrics (timed scrolling, right hand only, lyrics sync)
        # ------------------------------------------------------------------
        level2_missions = []
        for s_idx, section in enumerate(sections):
            section_notes = section.get("notes", [])
            rh_notes = [n for n in section_notes if getattr(n, "hand", "RIGHT") != "LEFT"]
            if not rh_notes:
                continue
            start = getattr(rh_notes[0], "start_time", 0.0)
            events = [_to_event(n, start) for n in rh_notes]
            level2_missions.append(_make_mission(
                title=f"Melody with Lyrics — {section['display_label']}",
                mission_type="right_hand",
                level_number=2,
                progression_mode="timed",
                hand_mode="right",
                bpm=slow_bpm,
                learning_goal=(
                    "Right hand melody with timing. Lyrics appear synchronized "
                    "with notes to help you connect melody with singing."
                ),
                xp_reward=75,
                expected_events=events,
            ))

        # ------------------------------------------------------------------
        # Level 3 — Learn the Chords (wait-mode / timed, left hand only, chord mappings)
        # ------------------------------------------------------------------
        level3_missions = []
        for s_idx, section in enumerate(sections):
            section_notes = section.get("notes", [])
            lh_events = LearningPlanGenerator._simplified_bass(
                section_notes=section_notes,
                section_start=section.get("start_time", 0.0),
            )
            if not lh_events:
                continue
            level3_missions.append(_make_mission(
                title=f"Left Hand Chords — {section['display_label']}",
                mission_type="left_hand",
                level_number=3,
                progression_mode="timed",
                hand_mode="left",
                bpm=slow_bpm,
                simplified=True,
                learning_goal=(
                    "Left hand only. Learn and practice the accompaniment chords "
                    "used in this section (one bass note per chord/measure)."
                ),
                xp_reward=100,
                expected_events=lh_events,
            ))

        # ------------------------------------------------------------------
        # Level 4 — Melody + Chords + Lyrics (both hands combined, lyrics sync)
        # ------------------------------------------------------------------
        level4_missions = []
        for s_idx, section in enumerate(sections):
            section_notes = section.get("notes", [])
            rh_notes = [n for n in section_notes if getattr(n, "hand", "RIGHT") != "LEFT"]
            if not rh_notes:
                continue
            start = getattr(rh_notes[0], "start_time", 0.0)
            rh_events = [_to_event(n, start) for n in rh_notes]
            lh_events = LearningPlanGenerator._simplified_bass(
                section_notes=section_notes,
                section_start=section.get("start_time", 0.0),
            )
            combined = sorted(rh_events + lh_events, key=lambda e: e.get("relative_time", 0.0))
            level4_missions.append(_make_mission(
                title=f"Melody + Chords combined — {section['display_label']}",
                mission_type="both_hands",
                level_number=4,
                progression_mode="timed",
                hand_mode="both",
                bpm=medium_bpm,
                simplified=True,
                learning_goal=(
                    "Combine both hands. Right hand plays the melody, Left hand "
                    "keys simplified chords. Synced lyrics remain visible."
                ),
                xp_reward=150,
                expected_events=combined,
            ))

        # ------------------------------------------------------------------
        # Level 5 — Full Song Performance (original tempo, both hands, original arrangement)
        # ------------------------------------------------------------------
        all_events_full = [_to_event(n) for n in all_notes]
        level5_mission = _make_mission(
            title="Full Song — Original Arrangement",
            mission_type="performance",
            level_number=5,
            progression_mode="timed",
            hand_mode="both",
            bpm=bpm,
            simplified=False,
            learning_goal=(
                "Both hands, full arrangement, original tempo. "
                "Perform the complete song for your final score."
            ),
            xp_reward=500,
            expected_events=all_events_full,
        )

        # ------------------------------------------------------------------
        # Assemble 5 structured LearningLevel objects
        # ------------------------------------------------------------------
        levels = [
            {
                "id": str(uuid.uuid4()),
                "levelNumber": 1,
                "title": "1️⃣ Learn the Notes",
                "learningMode": "learn",
                "handMode": "right",
                "progressionMode": "wait",
                "simplified": False,
                "missions": level1_missions,
            },
            {
                "id": str(uuid.uuid4()),
                "levelNumber": 2,
                "title": "2️⃣ Melody with Lyrics",
                "learningMode": "learn",
                "handMode": "right",
                "progressionMode": "timed",
                "simplified": False,
                "missions": level2_missions,
            },
            {
                "id": str(uuid.uuid4()),
                "levelNumber": 3,
                "title": "3️⃣ Learn the Chords",
                "learningMode": "practice",
                "handMode": "left",
                "progressionMode": "timed",
                "simplified": True,
                "missions": level3_missions,
            },
            {
                "id": str(uuid.uuid4()),
                "levelNumber": 4,
                "title": "4️⃣ Melody + Chords + Lyrics",
                "learningMode": "practice",
                "handMode": "both",
                "progressionMode": "timed",
                "simplified": True,
                "missions": level4_missions,
            },
            {
                "id": str(uuid.uuid4()),
                "levelNumber": 5,
                "title": "5️⃣ Full Song Performance",
                "learningMode": "perform",
                "handMode": "both",
                "progressionMode": "timed",
                "simplified": False,
                "missions": [level5_mission],
            },
        ]

        # Legacy phases mapping for sidebar fallback
        phases = []
        for s_idx, section in enumerate(sections):
            section_notes = section.get("notes", [])
            rh_notes = [n for n in section_notes if getattr(n, "hand", "RIGHT") != "LEFT"]
            if not rh_notes:
                continue
            start = getattr(rh_notes[0], "start_time", 0.0)
            phases.append({
                "id": str(uuid.uuid4()),
                "title": section["display_label"],
                "missions": [
                    _make_mission(
                        title=f"Practice — {section['display_label']}",
                        mission_type="right_hand",
                        level_number=1,
                        progression_mode="wait",
                        hand_mode="right",
                        bpm=slow_bpm,
                        learning_goal="Start learning this section.",
                        xp_reward=50,
                        status="available" if s_idx == 0 else "locked",
                        expected_events=[_to_event(n, start) for n in rh_notes],
                    )
                ],
            })
        phases.append({
            "id": str(uuid.uuid4()),
            "title": "Full Song Performance",
            "missions": [level5_mission],
        })

        return {
            "lesson_id": str(uuid.uuid4()),
            "overall_progress": 0,
            "phases": phases,
            "levels": levels,
            "lyricAlignment": lyric_alignment,
            "phrases": all_phrases,
        }

    @staticmethod
    def _simplified_bass(
        section_notes: List[Any],
        section_start: float,
    ) -> List[Dict[str, Any]]:
        """Build simplified left-hand bass: one bass note per measure/chord change."""
        left_notes = [n for n in section_notes if getattr(n, "hand", "RIGHT") == "LEFT"]
        source = left_notes if left_notes else [
            n for n in section_notes if getattr(n, "hand", "RIGHT") != "LEFT"
        ]

        if not source:
            return []

        by_measure: Dict[int, List[Any]] = {}
        for n in source:
            m_num = getattr(n, "measure_number", 0) or 0
            by_measure.setdefault(m_num, []).append(n)

        result: List[Dict[str, Any]] = []
        for m_num in sorted(by_measure.keys()):
            notes_in_m = by_measure[m_num]
            # Lowest pitch
            bass = min(
                notes_in_m,
                key=lambda n: getattr(n, "midi_number", 60) or 60,
            )
            note_name = bass.note_name
            if not left_notes:
                note_name = _drop_octave(note_name)

            result.append({
                "id": str(uuid.uuid4()),
                "note": note_name,
                "relative_time": max(0.0, getattr(bass, "start_time", 0.0) - section_start),
                "duration": 2.0,
                "hand": "left",
            })

        return result


def _drop_octave(note_name: str) -> str:
    import re
    m = re.match(r"^([A-G][#b]?)(\d+)$", note_name)
    if m:
        return f"{m.group(1)}{max(1, int(m.group(2)) - 1)}"
    return note_name
