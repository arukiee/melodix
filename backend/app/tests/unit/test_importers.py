import pytest
from app.services.music_engine.importers.musicxml_importer import MusicXMLImporter
from app.services.music_engine.importers.midi_importer import MIDIImporter
from app.services.music_engine.converters.timeline_builder import TimelineBuilder
from app.services.music_engine.converters.mission_builder import MissionBuilder

def test_musicxml_importer_fallback():
    importer = MusicXMLImporter()
    res = importer.parse(b"invalid xml")
    assert res["title"] == "Mary Had a Little Lamb"
    assert len(res["notes"]) > 0

def test_midi_importer_fallback():
    importer = MIDIImporter()
    res = importer.parse(b"invalid midi header")
    assert res["title"] == "Twinkle Twinkle Little Star"
    assert len(res["notes"]) > 0

def test_timeline_builder():
    parsed = {
        "bpm": 60,
        "notes": [
            {"note": "C4", "duration": 1.0, "measure": 0},
            {"note": "E4", "duration": 2.0, "measure": 0}
        ]
    }
    events = TimelineBuilder.build_expected_events(parsed)
    assert len(events) == 2
    assert events[0].note == "C4"
    assert events[0].relative_time == 0.0
    assert events[0].duration == 1.0 # 60 BPM -> 1s
    assert events[1].note == "E4"
    assert events[1].duration == 2.0

def test_mission_builder():
    parsed = {
        "bpm": 80,
        "notes": [{"note": "G4", "duration": 1.0, "measure": 0}]
    }
    missions = MissionBuilder.generate_missions(parsed)
    assert len(missions) == 3
    assert missions[0]["type"] == "listen"
    assert missions[1]["type"] == "right_hand"
    assert missions[2]["type"] == "both_hands"
