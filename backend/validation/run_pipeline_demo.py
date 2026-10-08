
import json
import logging
import os
import sys
import shutil
from pathlib import Path

# Ensure project root is on PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from backend.app.services.orchestrator.source_discovery import SourceDiscoveryService
from ml.inference.transcriber import Transcriber
# AudioAsset import removed (not needed for this validation script)
from backend.app.services.music_engine.bpm_detector import BPMDetector
from backend.app.services.music_engine.curriculum import LearningPlanGenerator as CurriculumBuilder
from backend.app.services.music_engine.transcription_service import midi_to_note_name as midi_to_note
from backend.app.services.music_engine.melody_extractor import extract_melody

import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)

# Simple ground‑truth notes (pitch name, onset seconds, duration seconds)
GROUND_TRUTH = {
    "Happy Birthday": {
        "bpm": 120,
        "notes": [
            {"pitch": "C4", "onset": 0.0, "duration": 0.5},
            {"pitch": "C4", "onset": 0.5, "duration": 0.5},
            {"pitch": "D4", "onset": 1.0, "duration": 1.0},
            {"pitch": "C4", "onset": 2.0, "duration": 1.0},
            {"pitch": "F4", "onset": 3.0, "duration": 1.0},
            {"pitch": "E4", "onset": 4.0, "duration": 2.0}
        ]
    },
    "Twinkle Twinkle Little Star": {
        "bpm": 100,
        "notes": [
            {"pitch": "C4", "onset": 0.0, "duration": 0.5},
            {"pitch": "C4", "onset": 0.5, "duration": 0.5},
            {"pitch": "G4", "onset": 1.0, "duration": 0.5},
            {"pitch": "G4", "onset": 1.5, "duration": 0.5},
            {"pitch": "A4", "onset": 2.0, "duration": 0.5},
            {"pitch": "A4", "onset": 2.5, "duration": 0.5},
            {"pitch": "G4", "onset": 3.0, "duration": 1.0}
        ]
    },
    "Shape of You": {
        "bpm": 96,
        "notes": []
    }
}

# Directories for temporary audio and reports
BASE_DIR = PROJECT_ROOT / "backend" / "scratch" / "validation"
BASE_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR = BASE_DIR / "results"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

def midi_to_name(midi):
    return midi_to_note(midi)

def load_transcriber():
    checkpoint_path = os.getenv(
        "CHECKPOINT_PATH",
        PROJECT_ROOT / "backend" / "ml" / "checkpoints" / "latest.pt",
    )
    # Use the correct default config location (YAML) if the JSON file is missing
    default_config_path = PROJECT_ROOT / "ml" / "configs" / "transcription.yaml"
    config_path = os.getenv("TRANSCRIBER_CONFIG", default_config_path)
    # Load YAML or JSON based on file extension
    if str(config_path).endswith(".yaml") or str(config_path).endswith(".yml"):
        import yaml
        with open(config_path) as f:
            config = yaml.safe_load(f)
    else:
        with open(config_path) as f:
            config = json.load(f)
    return Transcriber(checkpoint_path, config, device="cpu")

def select_best_candidate(results):
    from backend.app.services.orchestrator.source_discovery import select_best_candidate as sd_select
    return sd_select(results)

def run_for_song(title):
    print(f"=== Processing {title} ===")
    # Search YouTube for a suitable audio candidate using the registered provider
    import asyncio, logging
    logger = logging.getLogger(__name__)
    from app.services.search.search_engine import search_engine
    from app.schemas.search import SearchFilter
    youtube_provider = search_engine.get_provider("YouTube")
    ordered_candidates = []
    if youtube_provider:
        try:
            results = asyncio.run(youtube_provider.search(title, filters=SearchFilter(limit=10)))
        except Exception as e:
            logger.warning(f"YouTube search failed for '{title}': {e}")
            results = []
        if results:
            best = select_best_candidate(results)
            if best:
                ordered_candidates.append(best)
                ordered_candidates.extend([r for r in results if r.id != best.id])
            else:
                ordered_candidates = list(results)

    if not ordered_candidates:
        raise RuntimeError(f"No YouTube candidates found for '{title}'")

    # Download audio with fallback to next candidate if download fails
    youtube_url = None
    wav_path = BASE_DIR / f"{title.replace(' ', '_').lower()}.wav"
    audio_np, sr = None, None
    last_error = None

    for candidate in ordered_candidates:
        candidate_url = f"https://www.youtube.com/watch?v={candidate.id}"
        print(f"Trying YouTube candidate: {candidate_url} ('{getattr(candidate, 'title', candidate.id)}')")
        try:
            audio_path = SourceDiscoveryService._download_youtube_audio(candidate_url)
            shutil.copy(audio_path, wav_path)
            print(f"Saved downloaded file to {wav_path}")
            from ml.data.preprocessing import load_wav
            audio_np, sr = load_wav(str(wav_path))
            youtube_url = candidate_url
            break
        except Exception as e:
            logger.warning(f"Download failed for candidate {candidate.id}: {e}")
            last_error = e

    if not youtube_url or audio_np is None:
        print(f"⚠️ ALL AUDIO DOWNLOAD CANDIDATES FAILED for '{title}' — {last_error}. This result is INVALID.")
        report = {
            "title": title,
            "youtube_url": None,
            "status": "FAILURE",
            "error": f"AUDIO_LOAD_FAILED: All candidates failed. Last error: {last_error}"
        }
        report_path = REPORTS_DIR / f"{title.replace(' ', '_').lower()}_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"Report written to {report_path}")
        return


    # ── Basic Pitch transcription (Phase 2 harmony) — non-fatal ─────────────
    # A missing model checkpoint must not prevent melody extraction from running.
    notes: list = []
    latency: float = 0.0
    bpm_result: dict = {"tempo_bpm": 0.0, "confidence": 0.0}
    phrase_count: int = 0
    pitch_errors: list = []
    octave_shifts: list = []
    basic_pitch_result: dict = {"status": "SKIPPED"}

    try:
        transcriber = load_transcriber()
        notes, latency = transcriber.transcribe(audio_np)
        print(f"Basic Pitch produced {len(notes)} notes (latency {latency:.1f} ms)")

        bpm_detector = BPMDetector()
        bpm_result = bpm_detector.detect(audio_np, None)
        print(f"Detected BPM: {bpm_result['tempo_bpm']:.1f} (confidence {bpm_result['confidence']:.2f})")

        curriculum = CurriculumBuilder()
        lesson = curriculum.build_lesson(notes, bpm_result['tempo_bpm'])
        phrase_count = len(lesson.phrases)
        print(f"Lesson contains {phrase_count} phrases")

        gt_notes = GROUND_TRUTH[title].get("notes", [])
        for i, note in enumerate(notes[: len(gt_notes)]):
            pred_name = midi_to_name(note["pitch"])
            gt_name = gt_notes[i]["pitch"]
            if pred_name != gt_name:
                pitch_errors.append({"index": i, "pred": pred_name, "gt": gt_name})
                if pred_name[0] == gt_name[0]:
                    try:
                        octave_shifts.append(int(pred_name[-1]) - int(gt_name[-1]))
                    except Exception:
                        pass

        basic_pitch_result = {
            "status": "OK",
            "note_count": len(notes),
            "latency_ms": latency,
            "sample": notes[:10],
        }
    except Exception as bp_exc:
        print(f"  ⚠️  Basic Pitch SKIPPED: {bp_exc}")
        basic_pitch_result = {"status": "FAILURE", "error": str(bp_exc)}
    # ─────────────────────────────────────────────────────────────────────────

    # ── Melody extraction (Phase 1) ───────────────────────────────────────────
    print(f"Running melody extraction for '{title}' …")
    melody_result: dict = {"status": "SKIPPED", "error": None}
    try:
        mel = extract_melody(wav_path, vocals_rms_threshold=0.01)
        print(
            f"  stem_used={mel['stem_used']}  "
            f"vocals_rms={mel['vocals_rms']:.4f}  "
            f"notes={mel['note_count']}"
        )
        melody_result = {
            "status": "OK",
            "stem_used": mel["stem_used"],
            "vocals_rms": round(mel["vocals_rms"], 6),
            "note_count": mel["note_count"],
            "sample": mel["notes"][:20],
        }
    except Exception as mel_exc:
        print(f"  ⚠️  Melody extraction FAILED: {mel_exc}")
        melody_result = {"status": "FAILURE", "error": str(mel_exc)}
    # ─────────────────────────────────────────────────────────────────────────

    report = {
        "title": title,
        "youtube_url": youtube_url,
        "basic_pitch": basic_pitch_result,
        "melody": melody_result,
        "bpm": bpm_result,
        "curriculum": {"phrase_count": phrase_count},
        "ground_truth": GROUND_TRUTH[title],
        "pitch_errors": pitch_errors,
        "octave_shifts": octave_shifts,
    }
    report_path = REPORTS_DIR / f"{title.replace(' ', '_').lower()}_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Report written to {report_path}")

def main():
    for title in ["Happy Birthday", "Twinkle Twinkle Little Star", "Shape of You"]:
        try:
            run_for_song(title)
        except Exception as e:
            print(f"Error processing {title}: {e}")
    print("All songs processed.")

if __name__ == "__main__":
    main()
