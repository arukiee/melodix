"""
Performance benchmark smoke tests for the import pipeline.
These are assertion-based tests that catch accidental O(n²) regressions,
not load tests.
"""
import time
import pytest
from app.services.music_engine.importers.musicxml_importer import MusicXMLImporter
from app.services.music_engine.importers.midi_importer import MIDIImporter
from app.services.music_engine.importers.validator import ImportValidator
from app.services.music_engine.importers.chord_extractor import ChordExtractor
from app.services.music_engine.converters.timeline_builder import TimelineBuilder
from app.services.music_engine.converters.mission_builder import MissionBuilder


def _build_large_musicxml(note_count: int) -> bytes:
    """Generate a MusicXML string with a given number of notes."""
    measures = []
    notes_per_measure = 4
    measure_num = 1
    notes_added = 0

    while notes_added < note_count:
        notes_in_this = []
        for _ in range(min(notes_per_measure, note_count - notes_added)):
            notes_in_this.append(
                '<note><pitch><step>C</step><octave>4</octave></pitch><duration>4</duration></note>'
            )
            notes_added += 1
        measures.append(f'<measure number="{measure_num}">{"".join(notes_in_this)}</measure>')
        measure_num += 1

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="3.1">
  <work><work-title>Benchmark Song</work-title></work>
  <part-list><score-part id="P1"><part-name>Piano</part-name></score-part></part-list>
  <part id="P1">
    <measure number="0">
      <attributes>
        <divisions>1</divisions>
        <key><fifths>0</fifths></key>
        <time><beats>4</beats><beat-type>4</beat-type></time>
      </attributes>
    </measure>
    {"".join(measures)}
  </part>
</score-partwise>"""
    return xml.encode("utf-8")


class TestPipelineBenchmarks:
    def test_musicxml_parse_100_notes(self):
        """MusicXML parsing of 100 notes should complete in < 200ms."""
        xml_bytes = _build_large_musicxml(100)
        importer = MusicXMLImporter()

        start = time.perf_counter()
        result = importer.parse(xml_bytes)
        elapsed = time.perf_counter() - start

        assert len(result["notes"]) == 100
        assert elapsed < 0.2, f"MusicXML parse took {elapsed:.3f}s (limit: 0.2s)"

    def test_validation_speed(self):
        """Validation of a 100-note song should complete in < 50ms."""
        xml_bytes = _build_large_musicxml(100)
        parsed = MusicXMLImporter().parse(xml_bytes)

        start = time.perf_counter()
        ImportValidator.validate(parsed)
        elapsed = time.perf_counter() - start

        assert elapsed < 0.05, f"Validation took {elapsed:.3f}s (limit: 0.05s)"

    def test_chord_extraction_speed(self):
        """Chord extraction from 100 notes should complete in < 50ms."""
        xml_bytes = _build_large_musicxml(100)
        parsed = MusicXMLImporter().parse(xml_bytes)

        start = time.perf_counter()
        ChordExtractor.extract_chords(parsed["notes"])
        elapsed = time.perf_counter() - start

        assert elapsed < 0.05, f"Chord extraction took {elapsed:.3f}s (limit: 0.05s)"

    def test_timeline_build_speed(self):
        """Timeline building from 100 notes should complete in < 50ms."""
        xml_bytes = _build_large_musicxml(100)
        parsed = MusicXMLImporter().parse(xml_bytes)

        start = time.perf_counter()
        TimelineBuilder.build_expected_events(parsed)
        elapsed = time.perf_counter() - start

        assert elapsed < 0.05, f"Timeline build took {elapsed:.3f}s (limit: 0.05s)"

    def test_mission_generation_speed(self):
        """Mission generation from 100 notes should complete in < 50ms."""
        xml_bytes = _build_large_musicxml(100)
        parsed = MusicXMLImporter().parse(xml_bytes)

        start = time.perf_counter()
        MissionBuilder.generate_missions(parsed)
        elapsed = time.perf_counter() - start

        assert elapsed < 0.05, f"Mission generation took {elapsed:.3f}s (limit: 0.05s)"

    def test_full_pipeline_speed(self):
        """Full pipeline (parse → validate → chords → timeline → missions) for 100 notes < 500ms."""
        xml_bytes = _build_large_musicxml(100)

        start = time.perf_counter()
        importer = MusicXMLImporter()
        parsed = importer.parse(xml_bytes)
        ImportValidator.validate(parsed)
        ChordExtractor.extract_chords(parsed["notes"])
        TimelineBuilder.build_expected_events(parsed)
        MissionBuilder.generate_missions(parsed)
        elapsed = time.perf_counter() - start

        assert elapsed < 0.5, f"Full pipeline took {elapsed:.3f}s (limit: 0.5s)"
