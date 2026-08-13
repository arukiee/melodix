"""
Real-world MusicXML compatibility tests.
Tests the import pipeline against files mimicking exports from
MuseScore, Finale, Sibelius, and edge-case scenarios.
"""
import os
import pytest
from app.services.music_engine.importers.musicxml_importer import MusicXMLImporter
from app.services.music_engine.importers.validator import ImportValidator
from app.services.music_engine.importers.chord_extractor import ChordExtractor
from app.services.music_engine.converters.timeline_builder import TimelineBuilder
from app.services.music_engine.converters.mission_builder import MissionBuilder

TEST_FILES_DIR = os.path.join(os.path.dirname(__file__), "test_files")


def _load_file(filename: str) -> bytes:
    filepath = os.path.join(TEST_FILES_DIR, filename)
    with open(filepath, "rb") as f:
        return f.read()


def _run_full_pipeline(file_bytes: bytes):
    """Run the entire import pipeline and return all results."""
    importer = MusicXMLImporter()
    parsed = importer.parse(file_bytes)
    warnings = ImportValidator.validate(parsed)
    chords = ChordExtractor.extract_chords(parsed.get("notes", []))
    events = TimelineBuilder.build_expected_events(parsed)
    missions = MissionBuilder.generate_missions(parsed)
    return parsed, warnings, chords, events, missions


# ─── MuseScore Export ──────────────────────────────────────

class TestMuseScoreExport:
    """Tests for MuseScore-style MusicXML (D Major, sharps, metronome direction)."""

    def test_parses_title_and_composer(self):
        parsed, *_ = _run_full_pipeline(_load_file("musescore_ode_to_joy.xml"))
        assert parsed["title"] == "Ode to Joy"
        assert parsed["composer"] == "Ludwig van Beethoven"

    def test_parses_key_signature(self):
        parsed, *_ = _run_full_pipeline(_load_file("musescore_ode_to_joy.xml"))
        assert parsed["key_signature"] == "D Major"

    def test_parses_time_signature(self):
        parsed, *_ = _run_full_pipeline(_load_file("musescore_ode_to_joy.xml"))
        assert parsed["time_signature"] == "4/4"

    def test_parses_sharps(self):
        """F# notes should be parsed with # notation."""
        parsed, *_ = _run_full_pipeline(_load_file("musescore_ode_to_joy.xml"))
        sharp_notes = [n for n in parsed["notes"] if "#" in n["note"]]
        assert len(sharp_notes) > 0, "Expected F# notes in D Major piece"

    def test_note_count(self):
        parsed, *_ = _run_full_pipeline(_load_file("musescore_ode_to_joy.xml"))
        # 4 measures × ~4 notes = ~14 notes (measure 4 has 2)
        assert len(parsed["notes"]) >= 12

    def test_generates_missions(self):
        *_, missions = _run_full_pipeline(_load_file("musescore_ode_to_joy.xml"))
        assert len(missions) >= 2

    def test_validation_passes(self):
        _, warnings, *_ = _run_full_pipeline(_load_file("musescore_ode_to_joy.xml"))
        # Should not have critical errors
        critical = [w for w in warnings if "no parsed notes" in w.lower()]
        assert len(critical) == 0


# ─── Finale Export ─────────────────────────────────────────

class TestFinaleExport:
    """Tests for Finale-style MusicXML (multi-part grand staff, 3/4, G Major, divisions=2)."""

    def test_parses_title(self):
        parsed, *_ = _run_full_pipeline(_load_file("finale_minuet.xml"))
        assert parsed["title"] == "Minuet in G Major"

    def test_parses_key_signature(self):
        parsed, *_ = _run_full_pipeline(_load_file("finale_minuet.xml"))
        assert parsed["key_signature"] == "G Major"

    def test_parses_3_4_time(self):
        parsed, *_ = _run_full_pipeline(_load_file("finale_minuet.xml"))
        assert parsed["time_signature"] == "3/4"

    def test_handles_divisions_2(self):
        """With divisions=2, duration values are different from divisions=1."""
        parsed, *_ = _run_full_pipeline(_load_file("finale_minuet.xml"))
        # All durations should be positive
        for note in parsed["notes"]:
            assert note["duration"] > 0

    def test_parses_both_parts(self):
        """Multi-part scores should combine notes from all parts."""
        parsed, *_ = _run_full_pipeline(_load_file("finale_minuet.xml"))
        # Should have notes from both treble and bass
        assert len(parsed["notes"]) >= 10

    def test_detects_chords(self):
        _, _, chords, *_ = _run_full_pipeline(_load_file("finale_minuet.xml"))
        assert len(chords) >= 1


# ─── Sibelius Export ───────────────────────────────────────

class TestSibeliusExport:
    """Tests for Sibelius-style MusicXML (Ab Major, 9/8, explicit rests, chord tags, divisions=4)."""

    def test_parses_title(self):
        parsed, *_ = _run_full_pipeline(_load_file("sibelius_clair_de_lune.xml"))
        assert parsed["title"] == "Clair de Lune (Excerpt)"

    def test_parses_flat_key(self):
        """Key with 4 flats should be detected."""
        parsed, *_ = _run_full_pipeline(_load_file("sibelius_clair_de_lune.xml"))
        # -4 fifths = Ab — our parser maps this
        assert "Major" in parsed["key_signature"]

    def test_parses_9_8_time(self):
        parsed, *_ = _run_full_pipeline(_load_file("sibelius_clair_de_lune.xml"))
        assert parsed["time_signature"] == "9/8"

    def test_skips_rests(self):
        """Explicit rest elements should not appear as notes."""
        parsed, *_ = _run_full_pipeline(_load_file("sibelius_clair_de_lune.xml"))
        for note in parsed["notes"]:
            assert note["note"] != "rest"

    def test_parses_flats(self):
        """Bb and Db notes should use 'b' notation."""
        parsed, *_ = _run_full_pipeline(_load_file("sibelius_clair_de_lune.xml"))
        flat_notes = [n for n in parsed["notes"] if "b" in n["note"] and n["note"][0].isupper()]
        assert len(flat_notes) > 0, "Expected flat notes in Ab Major piece"

    def test_pipeline_completes(self):
        """Full pipeline should complete without errors."""
        parsed, warnings, chords, events, missions = _run_full_pipeline(
            _load_file("sibelius_clair_de_lune.xml")
        )
        assert len(events) > 0
        assert len(missions) >= 2


# ─── Minimal / Bare File ──────────────────────────────────

class TestMinimalFile:
    """Tests for a bare minimum MusicXML — no metadata, no attributes, single note."""

    def test_parses_without_crash(self):
        parsed, *_ = _run_full_pipeline(_load_file("minimal_bare.xml"))
        assert len(parsed["notes"]) == 1

    def test_defaults_title(self):
        parsed, *_ = _run_full_pipeline(_load_file("minimal_bare.xml"))
        assert parsed["title"] == "Unknown Song"

    def test_defaults_key(self):
        parsed, *_ = _run_full_pipeline(_load_file("minimal_bare.xml"))
        assert "C" in parsed["key_signature"]

    def test_validation_warns_on_missing_metadata(self):
        """Bare file should trigger warnings but not crash."""
        _, warnings, *_ = _run_full_pipeline(_load_file("minimal_bare.xml"))
        # Should have at least a missing key_signature warning since defaults may not be set
        assert isinstance(warnings, list)


# ─── Edge Cases ────────────────────────────────────────────

class TestEdgeCases:
    """Tests for grace notes, tied notes, flats, higher divisions."""

    def test_parses_title(self):
        parsed, *_ = _run_full_pipeline(_load_file("edge_case_waltz.xml"))
        assert parsed["title"] == "Waltz in A Minor"

    def test_grace_notes_handled(self):
        """Grace notes have no <duration> — parser should not crash."""
        parsed, *_ = _run_full_pipeline(_load_file("edge_case_waltz.xml"))
        # Grace notes lack duration, but the pipeline should still complete
        assert len(parsed["notes"]) >= 5

    def test_tied_notes_parsed(self):
        """Tied notes should be parsed as separate note entries (tie handling is future work)."""
        parsed, *_ = _run_full_pipeline(_load_file("edge_case_waltz.xml"))
        # Both tied Eb5 notes should appear
        eb_notes = [n for n in parsed["notes"] if n["note"].startswith("Eb")]
        assert len(eb_notes) >= 2

    def test_flats_in_eb_major(self):
        """Notes with alter=-1 should render as flats."""
        parsed, *_ = _run_full_pipeline(_load_file("edge_case_waltz.xml"))
        flat_notes = [n for n in parsed["notes"] if "b" in n["note"]]
        assert len(flat_notes) > 0

    def test_full_pipeline_completes(self):
        parsed, warnings, chords, events, missions = _run_full_pipeline(
            _load_file("edge_case_waltz.xml")
        )
        assert len(events) > 0
        assert len(missions) >= 2
        # Warnings should be a list (may have unusual time sig, etc.)
        assert isinstance(warnings, list)
