"""
Automated End-to-End Workflow Latency SLA Tests (Phase 2D)
Verifies performance SLAs across all 7 stages of student practice workflow:
Import -> Validation -> Chords -> Timeline -> DB -> Pitch DSP -> Scoring -> AI.
"""
import pytest
import numpy as np
from app.core.database import SessionLocal
from app.models.song import Song
from app.services.music_engine.profiler import WorkflowProfiler
from app.services.music_engine.importers.musicxml_importer import MusicXMLImporter
from app.services.music_engine.importers.validator import ImportValidator
from app.services.music_engine.importers.chord_extractor import ChordExtractor
from app.services.music_engine.converters.timeline_builder import TimelineBuilder
from app.services.music_engine.converters.mission_builder import MissionBuilder
from app.services.music_engine.analyzer import AutocorrelationAnalyzer
from app.services.music_engine.base_analyzer import AnalysisRequest
from app.api.ai import AICoachRequest

SAMPLE_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="3.1">
  <work><work-title>SLA Test</work-title></work>
  <part-list><score-part id="P1"><part-name>Piano</part-name></score-part></part-list>
  <part id="P1">
    <measure number="1">
      <attributes><divisions>1</divisions><key><fifths>0</fifths></key><time><beats>4</beats><beat-type>4</beat-type></time></attributes>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>1</duration></note>
      <note><pitch><step>E</step><octave>4</octave></pitch><duration>1</duration></note>
    </measure>
  </part>
</score-partwise>"""


class TestE2EWorkflowSLAs:
    def test_dsp_pitch_detection_under_50ms(self):
        """DSP Autocorrelation Pitch Detection on 0.5s audio must complete in < 50ms."""
        analyzer = AutocorrelationAnalyzer()
        t = np.linspace(0, 0.5, int(22050 * 0.5), False)
        audio = np.sin(2 * np.pi * 440.0 * t).astype(np.float32)
        req = AnalysisRequest(audio_data=audio, sample_rate=22050, target_bpm=80, expected_events=[])

        profiler = WorkflowProfiler()
        with profiler.measure("DSP"):
            res = analyzer.analyze(req)

        stats = profiler.compute_stats()
        assert stats["DSP"]["avg_ms"] < 50.0, f"DSP pitch detection took {stats['DSP']['avg_ms']:.2f}ms (SLA: 50ms)"

    def test_full_pipeline_e2e_under_200ms(self):
        """Complete 7-stage practice workflow must execute in < 200ms."""
        profiler = WorkflowProfiler()
        db = SessionLocal()

        t = np.linspace(0, 0.5, int(22050 * 0.5), False)
        audio = np.sin(2 * np.pi * 261.63 * t).astype(np.float32)
        analyzer = AutocorrelationAnalyzer()

        try:
            with profiler.measure("Full Workflow"):
                # 1. Parse
                parsed = MusicXMLImporter().parse(SAMPLE_XML)
                # 2. Validate & Chords
                ImportValidator.validate(parsed)
                ChordExtractor.extract_chords(parsed["notes"])
                # 3. Timeline & Missions
                events = TimelineBuilder.build_expected_events(parsed)
                missions = MissionBuilder.generate_missions(parsed)
                # 4. DB Save & Query
                song = Song(title="SLA Song", composer="Test", difficulty="Level 1", bpm=80, missions=missions)
                db.add(song)
                db.commit()
                db.refresh(song)
                # 5. Pitch Detection
                req = AnalysisRequest(audio_data=audio, sample_rate=22050, target_bpm=80, expected_events=events)
                analysis_res = analyzer.analyze(req)
                # 6. AI Prompt
                ai_req = AICoachRequest(song_title=song.title, accuracy=analysis_res.overallScore, rhythm_score=analysis_res.rhythmAccuracy)

            # Cleanup
            db.query(Song).filter(Song.title == "SLA Song").delete(synchronize_session=False)
            db.commit()

            stats = profiler.compute_stats()
            e2e_ms = stats["Full Workflow"]["avg_ms"]
            assert e2e_ms < 200.0, f"E2E workflow took {e2e_ms:.2f}ms (SLA: 200ms)"
        finally:
            db.close()
