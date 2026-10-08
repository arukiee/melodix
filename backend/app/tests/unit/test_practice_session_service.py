from __future__ import annotations

from copy import deepcopy
import uuid

from app.services.music_engine.practice_session_service import _stabilize_ids, apply_progress


def _curriculum() -> dict:
    return {
        "lesson_id": "temporary",
        "levels": [
            {
                "id": "level-a",
                "levelNumber": 1,
                "missions": [
                    {"id": "mission-a", "title": "First", "expectedEvents": [{"id": "event-a", "note": "C4"}]},
                    {"id": "mission-b", "title": "Second", "expectedEvents": [{"id": "event-b", "note": "D4"}]},
                ],
            },
            {
                "id": "level-b",
                "levelNumber": 2,
                "missions": [{"id": "mission-c", "title": "Third", "expectedEvents": []}],
            },
        ],
        "phases": [{"id": "phase-a", "missions": [{"id": "mission-a", "expectedEvents": [{"id": "event-a"}]}]}],
        "phrases": [{"id": "phrase-a", "expectedEvents": [{"id": "event-a"}]}],
        "lyricAlignment": {"syllables": [{"noteEventIds": ["event-a"]}]},
    }


def test_curriculum_ids_are_stable_for_a_processing_job():
    job_id = uuid.uuid4()
    first = _stabilize_ids(_curriculum(), job_id)
    second = _stabilize_ids(_curriculum(), job_id)

    assert first == second
    assert first["lesson_id"] == str(job_id)
    assert first["levels"][0]["missions"][0]["id"] == first["phases"][0]["missions"][0]["id"]


def test_progress_restores_next_mission_in_curriculum_order():
    curriculum = _stabilize_ids(_curriculum(), uuid.uuid4())
    first_mission = curriculum["levels"][0]["missions"][0]["id"]
    second_mission = curriculum["levels"][0]["missions"][1]["id"]

    result = apply_progress(deepcopy(curriculum), {"completed_mission_ids": [first_mission]})

    missions = [mission for level in result["levels"] for mission in level["missions"]]
    assert [mission["status"] for mission in missions] == ["completed", "available", "locked"]
    assert result["current_mission_id"] == second_mission
    assert result["overall_progress"] == 33.33
