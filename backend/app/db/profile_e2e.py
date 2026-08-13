"""
End-to-End Workflow Profiling Script (Phase 2D)
Simulates complete student practice workflow: Score Import -> Practice Session ->
Audio Pitch Detection -> Performance Evaluation -> AI Coaching Generation.

Computes latency distributions: Average, Median, P95, P99, Max across 50 iterations.
"""
import sys
import numpy as np
import time

from app.core.database import SessionLocal
from app.models.song import Song
from app.services.music_engine.profiler import WorkflowProfiler
from app.services.music_engine.importers.musicxml_importer import MusicXMLImporter
from app.services.music_engine.importers.validator import ImportValidator
from app.services.music_engine.importers.chord_extractor import ChordExtractor
from app.services.music_engine.converters.timeline_builder import TimelineBuilder
from app.services.music_engine.converters.mission_builder import MissionBuilder
from app.services.music_engine.analyzer import AutocorrelationAnalyzer
from app.services.music_engine.base_analyzer import AnalysisRequest, ExpectedEvent
from app.api.ai import AICoachRequest

SAMPLE_MUSICXML = b"""<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="3.1">
  <work><work-title>Profiling Prelude</work-title></work>
  <part-list><score-part id="P1"><part-name>Piano</part-name></score-part></part-list>
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>1</divisions>
        <key><fifths>0</fifths></key>
        <time><beats>4</beats><beat-type>4</beat-type></time>
      </attributes>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>1</duration></note>
      <note><pitch><step>E</step><octave>4</octave></pitch><duration>1</duration></note>
      <note><pitch><step>G</step><octave>4</octave></pitch><duration>1</duration></note>
      <note><pitch><step>C</step><octave>5</octave></pitch><duration>1</duration></note>
    </measure>
  </part>
</score-partwise>"""


def _generate_synthetic_audio(freq: float = 440.0, duration_sec: float = 0.5, sr: int = 22050) -> np.ndarray:
    """Generates a clean sine wave audio segment for pitch analysis profiling."""
    t = np.linspace(0, duration_sec, int(sr * duration_sec), False)
    tone = np.sin(2 * np.pi * freq * t)
    return tone.astype(np.float32)


def run_e2e_profile():
    profiler = WorkflowProfiler()
    db = SessionLocal()

    print("\n==========================================================")
    print("      MELODIX END-TO-END WORKFLOW PERFORMANCE PROFILE      ")
    print("==========================================================\n")

    iterations = 50
    synthetic_audio = _generate_synthetic_audio(freq=261.63, duration_sec=0.5) # C4 sine wave

    try:
        pitch_analyzer = AutocorrelationAnalyzer()

        for i in range(iterations):
            # Stage 1: MusicXML Parse
            with profiler.measure("1. MusicXML Parsing"):
                importer = MusicXMLImporter()
                parsed = importer.parse(SAMPLE_MUSICXML)

            # Stage 2: Validation & Chord Extraction
            with profiler.measure("2. Validation & Chords"):
                ImportValidator.validate(parsed)
                ChordExtractor.extract_chords(parsed["notes"])

            # Stage 3: Timeline & Mission Building
            with profiler.measure("3. Timeline & Missions"):
                events = TimelineBuilder.build_expected_events(parsed)
                missions = MissionBuilder.generate_missions(parsed)

            # Stage 4: DB Persistence & Fetch
            with profiler.measure("4. DB Save & Query"):
                song = Song(
                    title=f"E2E Profile Song #{i}",
                    composer="Profiler",
                    difficulty="Level 1",
                    bpm=80,
                    key_signature="C Major",
                    time_signature="4/4",
                    missions=missions
                )
                db.add(song)
                db.commit()
                db.refresh(song)
                # Fetch back
                fetched = db.query(Song).filter(Song.id == song.id).first()

            # Stage 5: Audio Pitch Analysis (Autocorrelation DSP)
            req = AnalysisRequest(
                audio_data=synthetic_audio,
                sample_rate=22050,
                target_bpm=80,
                expected_events=events
            )
            with profiler.measure("5. DSP Pitch Detection"):
                analysis_res = pitch_analyzer.analyze(req)

            # Stage 6: Scoring & Evaluation
            with profiler.measure("6. Performance Scoring"):
                score = analysis_res.overallScore

            # Stage 7: AI Coaching Feedback (Prompt construction & Fallback)
            with profiler.measure("7. AI Coach Generation"):
                ai_req = AICoachRequest(
                    song_title="Profiling Prelude",
                    accuracy=score,
                    rhythm_score=analysis_res.rhythmAccuracy,
                    difficulty="Level 1"
                )
                # Fallback advice generation timing
                if ai_req.rhythm_score < 90:
                    advice = f"Focus on keeping a steady pulse through complex measures in {ai_req.song_title}."
                else:
                    advice = f"Excellent performance on {ai_req.song_title}! Focus next on dynamic expression."

        # Cleanup DB
        db.query(Song).filter(Song.composer == "Profiler").delete(synchronize_session=False)
        db.commit()

        # Compute & Print Statistics
        stats = profiler.compute_stats()

        print(f"{'Workflow Stage':<28} {'Avg (ms)':<10} {'Median':<10} {'P95 (ms)':<10} {'P99 (ms)':<10} {'Max (ms)':<10}")
        print("------------------------------------------------------------------------------------------")
        
        total_avg = 0.0
        for stage, s in stats.items():
            print(f"{stage:<28} {s['avg_ms']:<10.2f} {s['median_ms']:<10.2f} {s['p95_ms']:<10.2f} {s['p99_ms']:<10.2f} {s['max_ms']:<10.2f}")
            total_avg += s['avg_ms']

        print("------------------------------------------------------------------------------------------")
        print(f"{'TOTAL END-TO-END WORKFLOW':<28} {total_avg:<10.2f} ms")
        print("==========================================================================================\n")

    finally:
        db.close()


if __name__ == "__main__":
    run_e2e_profile()
