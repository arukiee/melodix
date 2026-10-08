"""
Melody Extractor — Demucs stem separation + torchcrepe pitch tracking.

Pipeline
--------
1. separate_stems()   — Run Demucs htdemucs model to split audio into
                        {vocals, drums, bass, other} stems.
2. select_melody_stem() — Choose vocals if RMS > threshold, else fall
                          back to "other" (lead instruments for instrumentals).
3. track_melody()     — Run torchcrepe on the chosen mono stem to produce
                        a dense (time, frequency) pitch curve.
4. pitch_curve_to_notes() — Group voiced frames into note events, snap
                             pitch to the nearest semitone, compute velocity
                             from per-note RMS, and return the canonical
                             note-event schema already used by Basic Pitch.

Output schema (each note dict)
-------------------------------
{
    "pitch":    "C4",    # note name string
    "midi":     60,      # MIDI note number
    "onset":    1.23,    # seconds
    "duration": 0.45,    # seconds
    "velocity": 87,      # 0-127
}

Devices
-------
Automatically uses CUDA if torch.cuda.is_available(), otherwise CPU.
Both Demucs and torchcrepe respect this selection.

Dependencies (see ml/requirements.txt)
---------------------------------------
  demucs==4.0.1
  torchcrepe==0.0.23
  torch>=2.0,<3.0
  torchaudio>=2.0,<3.0
  librosa==0.10.2.post1
  soundfile==0.12.1
"""

from __future__ import annotations

import logging
import shutil
import tempfile
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Default RMS threshold to decide whether the vocals stem carries melody.
DEFAULT_VOCALS_RMS_THRESHOLD: float = 0.01

#: Velocity range for the linear RMS → velocity mapping.
VELOCITY_MIN: int = 30
VELOCITY_MAX: int = 127

#: torchcrepe hop size in samples at 16 kHz (≈ 10 ms per frame).
CREPE_HOP_LENGTH: int = 160

#: Confidence threshold below which a frame is considered "unvoiced".
CREPE_VOICE_THRESHOLD: float = 0.5

#: Minimum note duration (seconds); shorter events are discarded as noise.
MIN_NOTE_DURATION: float = 0.10

#: MIDI note name lookup — C4 == MIDI 60.
_NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def _midi_to_note_name(midi: int) -> str:
    """Convert a MIDI note number to a human-readable name like 'C4'."""
    octave = (midi // 12) - 1
    name = _NOTE_NAMES[midi % 12]
    return f"{name}{octave}"


# ---------------------------------------------------------------------------
# Step 1 — Stem separation
# ---------------------------------------------------------------------------

def separate_stems(audio_path: Path | str, *, device: str | None = None) -> dict[str, Path]:
    """
    Run Demucs ``htdemucs`` on *audio_path* and return a dict mapping stem
    names → paths to the separated mono WAV files.

    Parameters
    ----------
    audio_path:
        Path to the source audio file (WAV, MP3, FLAC, …).
    device:
        ``"cuda"``, ``"cpu"``, or ``None`` (auto-detect).

    Returns
    -------
    dict with keys ``"vocals"``, ``"drums"``, ``"bass"``, ``"other"`` and
    ``Path`` values pointing to 44.1 kHz stereo WAV files written by Demucs.
    """
    import torch

    audio_path = Path(audio_path)
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    logger.info("separate_stems: device=%s  source=%s", device, audio_path)

    # Check for cached stems in <audio_path.parent>/stems/<audio_stem>
    track_name = audio_path.stem
    stems_dir = audio_path.parent / "stems" / track_name
    if stems_dir.exists():
        stem_paths: dict[str, Path] = {}
        all_found = True
        for stem_name in ("vocals", "drums", "bass", "other"):
            p = stems_dir / f"{stem_name}.wav"
            if not p.exists():
                p = stems_dir / f"{stem_name}.mp3"
            if p.exists():
                stem_paths[stem_name] = p
            else:
                all_found = False
                break
        if all_found:
            logger.info("separate_stems: reusing cached stems from %s", stems_dir)
            return stem_paths

    try:
        import demucs.separate as demucs_sep
    except ImportError as exc:
        raise ImportError(
            "demucs is not installed.  Run: pip install 'demucs==4.0.1'"
        ) from exc

    out_dir = stems_dir.parent / f"_tmp_{track_name}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Demucs CLI equivalent: demucs -n htdemucs --out <out_dir> <audio_path>
    # We call the Python API directly so we can capture stems programmatically.
    demucs_sep.main(
        [
            "--device", device,
            "--out", str(out_dir),
            "--name", "htdemucs",
            str(audio_path),
        ]
    )

    # Demucs writes to: <out_dir>/htdemucs/<track_name>/<stem>.mp3 or .wav
    produced_dir = out_dir / "htdemucs" / track_name
    if not produced_dir.exists():
        raise RuntimeError(
            f"Demucs output directory not found: {produced_dir}.  "
            "Check that demucs ran successfully."
        )

    stems_dir.mkdir(parents=True, exist_ok=True)
    stem_paths: dict[str, Path] = {}
    for stem_name in ("vocals", "drums", "bass", "other"):
        p = produced_dir / f"{stem_name}.wav"
        if not p.exists():
            p = produced_dir / f"{stem_name}.mp3"
        if not p.exists():
            raise FileNotFoundError(
                f"Expected stem not found: {p}.  Demucs output: {list(produced_dir.iterdir())}"
            )
        dest = stems_dir / p.name
        if not dest.exists():
            shutil.copy(p, dest)
        stem_paths[stem_name] = dest

    # Clean up temp dir
    shutil.rmtree(out_dir, ignore_errors=True)

    logger.info("separate_stems: stems written to %s", stems_dir)
    return stem_paths


# ---------------------------------------------------------------------------
# Step 2 — Stem selection
# ---------------------------------------------------------------------------

def select_melody_stem(
    stems: dict[str, Path],
    *,
    threshold: float = DEFAULT_VOCALS_RMS_THRESHOLD,
) -> tuple[Path, str, float]:
    """
    Decide whether to use the *vocals* or the *other* stem for melody tracking.

    The vocals stem RMS is computed and compared against *threshold*.  The
    actual RMS value is always returned so the caller can log it for future
    threshold tuning.

    Returns
    -------
    (chosen_path, chosen_stem_name, vocals_rms)
    """
    import soundfile as sf

    vocals_path = stems["vocals"]

    # Load a centre chunk of the track (up to 60 s) for the RMS check.
    # We avoid loading entire long tracks just to compute a quick energy metric.
    try:
        info = sf.info(str(vocals_path))
        total_frames = info.frames
        sr = info.samplerate
        chunk_frames = min(total_frames, int(60 * sr))
        start_frame = max(0, (total_frames - chunk_frames) // 2)

        vocals_audio, _ = sf.read(
            str(vocals_path),
            start=start_frame,
            frames=chunk_frames,
            dtype="float32",
            always_2d=True,
        )
        vocals_mono = vocals_audio.mean(axis=1)
        vocals_rms = float(np.sqrt(np.mean(vocals_mono ** 2)))
    except Exception as exc:
        logger.warning(
            "select_melody_stem: could not compute vocals RMS (%s) — "
            "defaulting to 'other' stem",
            exc,
        )
        vocals_rms = 0.0

    if vocals_rms >= threshold:
        chosen = "vocals"
        logger.info(
            "select_melody_stem: vocals RMS=%.4f >= threshold=%.4f → using vocals stem",
            vocals_rms,
            threshold,
        )
    else:
        chosen = "other"
        logger.info(
            "select_melody_stem: vocals RMS=%.4f < threshold=%.4f → "
            "falling back to 'other' stem (instrumental track)",
            vocals_rms,
            threshold,
        )

    return stems[chosen], chosen, vocals_rms


# ---------------------------------------------------------------------------
# Step 3 — Pitch tracking with torchcrepe
# ---------------------------------------------------------------------------

def track_melody(
    stem_path: Path | str,
    *,
    device: str | None = None,
) -> dict[str, Any]:
    """
    Run torchcrepe on *stem_path* and return a dict with:

    - ``times``      — 1-D float32 array, frame centre times in seconds
    - ``frequencies``— 1-D float32 array, predicted Hz per frame (0 = unvoiced)
    - ``confidence`` — 1-D float32 array, model confidence per frame [0, 1]
    - ``sample_rate``— integer sample rate used internally by torchcrepe (16000)

    Parameters
    ----------
    stem_path:
        Path to a WAV/MP3 file of the isolated melody stem.
    device:
        ``"cuda"``, ``"cpu"``, or ``None`` (auto-detect).
    """
    import torch
    import torchaudio

    try:
        import torchcrepe
    except ImportError as exc:
        raise ImportError(
            "torchcrepe is not installed.  Run: pip install 'torchcrepe==0.0.23'"
        ) from exc

    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    stem_path = Path(stem_path)
    logger.info("track_melody: loading %s on device=%s", stem_path, device)

    # torchcrepe expects 16 kHz mono.
    CREPE_SR = 16000
    try:
        import soundfile as sf
        audio_np, sr = sf.read(str(stem_path), dtype="float32")
        if audio_np.ndim > 1:
            audio_np = audio_np.mean(axis=1)
        waveform = torch.from_numpy(audio_np).unsqueeze(0)
    except Exception as exc:
        logger.info("soundfile.read failed (%s) — falling back to torchaudio", exc)
        waveform, sr = torchaudio.load(str(stem_path))

    if waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0, keepdim=True)   # → (1, T)
    if sr != CREPE_SR:
        resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=CREPE_SR)
        waveform = resampler(waveform)

    audio_tensor = waveform.squeeze(0).to(device)  # (T,)

    # Pad to minimum length torchcrepe requires.
    if audio_tensor.shape[0] < CREPE_HOP_LENGTH * 2:
        audio_tensor = torch.nn.functional.pad(
            audio_tensor, (0, CREPE_HOP_LENGTH * 2 - audio_tensor.shape[0])
        )

    logger.info(
        "track_melody: running torchcrepe (full model, hop=%d) on %.1f s of audio",
        CREPE_HOP_LENGTH,
        audio_tensor.shape[0] / CREPE_SR,
    )

    frequencies, confidence = torchcrepe.predict(
        audio_tensor.unsqueeze(0),           # (1, T)
        CREPE_SR,
        hop_length=CREPE_HOP_LENGTH,
        fmin=32.70,                          # C1
        fmax=2093.00,                        # C7
        model="full",
        return_periodicity=True,
        batch_size=512,
        device=device,
        decoder=torchcrepe.decode.viterbi,   # smoother than greedy
    )

    # Both tensors: shape (1, frames)
    freqs_np = frequencies.squeeze(0).cpu().float().numpy()
    conf_np = confidence.squeeze(0).cpu().float().numpy()

    n_frames = freqs_np.shape[0]
    times_np = np.arange(n_frames, dtype=np.float32) * (CREPE_HOP_LENGTH / CREPE_SR)

    return {
        "times": times_np,
        "frequencies": freqs_np,
        "confidence": conf_np,
        "sample_rate": CREPE_SR,
    }


# ---------------------------------------------------------------------------
# Step 4 — Pitch curve → discrete note events
# ---------------------------------------------------------------------------

def merge_nearby_notes(
    notes: list[dict[str, Any]],
    *,
    max_gap: float = 0.15,
    max_semitone_diff: int = 1,
) -> list[dict[str, Any]]:
    """
    Merge consecutive notes if the gap between them is <= max_gap seconds and
    their MIDI pitch difference is <= max_semitone_diff semitones.

    This prevents vibrato and small pitch micro-fluctuations from fragmenting
    a single sustained vocal/instrumental note into multiple short note events.
    """
    if not notes:
        return []

    current = [dict(n) for n in notes]
    for _ in range(3):
        merged: list[dict[str, Any]] = []
        for note in current:
            if not merged:
                merged.append(dict(note))
                continue

            prev = merged[-1]
            prev_offset = prev["onset"] + prev["duration"]
            gap = note["onset"] - prev_offset
            semitone_diff = abs(note["midi"] - prev["midi"])

            if gap <= max_gap and semitone_diff <= max_semitone_diff:
                prev_duration = prev["duration"]
                new_offset = max(prev_offset, note["onset"] + note["duration"])
                prev["duration"] = round(new_offset - prev["onset"], 4)

                # If the incoming note segment is longer than previous segment,
                # use its pitch name/MIDI for the merged note
                if note["duration"] > prev_duration:
                    prev["pitch"] = note["pitch"]
                    prev["midi"] = note["midi"]

                prev["velocity"] = max(prev["velocity"], note["velocity"])
            else:
                merged.append(dict(note))

        if len(merged) == len(current):
            break
        current = merged

    return current


def pitch_curve_to_notes(
    pitch_curve: dict[str, Any],
    *,
    voice_threshold: float = CREPE_VOICE_THRESHOLD,
    min_note_duration: float = MIN_NOTE_DURATION,
    max_gap: float = 0.15,
    max_semitone_diff: int = 1,
) -> list[dict[str, Any]]:
    """
    Convert a dense pitch curve (output of ``track_melody``) into a list of
    discrete note events.

    Algorithm
    ---------
    1. Mask unvoiced frames (confidence < *voice_threshold* or freq ≤ 0).
    2. Convert Hz → nearest MIDI semitone.
    3. Group consecutive voiced frames that share the same MIDI pitch into
       raw note events.
    4. Compute per-note RMS from frequency confidence as velocity.
    5. Merge nearby same/similar pitch notes (gap ≤ *max_gap*, pitch diff ≤ *max_semitone_diff*)
       to consolidate vibrato and micro-fluctuations.
    6. Discard notes shorter than *min_note_duration*.

    Returns
    -------
    List of dicts matching the canonical note-event schema::

        {
            "pitch":    "C4",
            "midi":     60,
            "onset":    1.23,    # seconds
            "duration": 0.45,    # seconds
            "velocity": 87,
        }
    """
    times: np.ndarray = pitch_curve["times"]
    freqs: np.ndarray = pitch_curve["frequencies"]
    conf: np.ndarray = pitch_curve["confidence"]

    # --- voiced mask ---
    voiced = (conf >= voice_threshold) & (freqs > 0.0)

    # --- Hz → MIDI (semitone snapping) ---
    midi_float = np.where(voiced, 12.0 * np.log2(np.maximum(freqs, 1e-6) / 440.0) + 69.0, np.nan)
    midi_int = np.where(voiced, np.rint(np.nan_to_num(midi_float, nan=-1.0)).astype(np.int32), -1)

    # --- group consecutive same-pitch voiced frames ---
    raw_notes: list[dict[str, Any]] = []
    n = len(times)
    i = 0
    while i < n:
        if not voiced[i]:
            i += 1
            continue

        pitch = int(midi_int[i])
        onset_idx = i

        # Extend while same pitch and voiced
        while i < n and voiced[i] and int(midi_int[i]) == pitch:
            i += 1
        offset_idx = i  # exclusive

        onset = float(times[onset_idx])
        # Use the next frame start as offset (or last frame end).
        if offset_idx < n:
            offset = float(times[offset_idx])
        else:
            hop_s = float(times[1] - times[0]) if n > 1 else 0.01
            offset = float(times[offset_idx - 1]) + hop_s

        duration = offset - onset

        # Velocity from mean confidence over the note span, scaled linearly.
        mean_conf = float(conf[onset_idx:offset_idx].mean())
        velocity = int(
            VELOCITY_MIN + (VELOCITY_MAX - VELOCITY_MIN) * np.clip(mean_conf, 0.0, 1.0)
        )
        # Guard MIDI pitch to valid range [21, 108] (piano range).
        pitch = int(np.clip(pitch, 21, 108))

        raw_notes.append(
            {
                "pitch": _midi_to_note_name(pitch),
                "midi": pitch,
                "onset": round(onset, 4),
                "duration": round(duration, 4),
                "velocity": velocity,
            }
        )

    # Merge nearby vibrato/same-pitch notes
    merged_notes = merge_nearby_notes(
        raw_notes,
        max_gap=max_gap,
        max_semitone_diff=max_semitone_diff,
    )

    # Filter out noise blips shorter than min_note_duration
    filtered_notes = [n for n in merged_notes if n["duration"] >= min_note_duration]

    logger.info("pitch_curve_to_notes: %d raw -> %d merged -> %d note events extracted",
                len(raw_notes), len(merged_notes), len(filtered_notes))
    return filtered_notes


# ---------------------------------------------------------------------------
# High-level convenience entry point
# ---------------------------------------------------------------------------

def extract_melody(
    audio_path: Path | str,
    *,
    vocals_rms_threshold: float = DEFAULT_VOCALS_RMS_THRESHOLD,
    device: str | None = None,
    min_note_duration: float = MIN_NOTE_DURATION,
    max_gap: float = 0.15,
    max_semitone_diff: int = 1,
) -> dict[str, Any]:
    """
    Full end-to-end melody extraction.

    Parameters
    ----------
    audio_path:
        Path to the downloaded song audio file.
    vocals_rms_threshold:
        RMS energy cutoff for vocals vs. other stem selection.
    device:
        ``"cuda"`` / ``"cpu"`` / ``None`` (auto).
    min_note_duration:
        Minimum note duration threshold in seconds (default 0.10s).
    max_gap:
        Maximum gap in seconds between consecutive notes to merge (default 0.15s).
    max_semitone_diff:
        Maximum semitone difference to merge (default 1).

    Returns
    -------
    Dict with:

    - ``"notes"``        — list of note-event dicts (Phase 1 melody)
    - ``"stem_used"``    — ``"vocals"`` or ``"other"``
    - ``"vocals_rms"``   — float, actual RMS of the vocals stem
    - ``"note_count"``   — int
    """
    import torch

    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    logger.info("extract_melody: starting  audio=%s  device=%s", audio_path, device)

    stems = separate_stems(audio_path, device=device)
    melody_stem_path, stem_used, vocals_rms = select_melody_stem(
        stems, threshold=vocals_rms_threshold
    )
    pitch_curve = track_melody(melody_stem_path, device=device)
    notes = pitch_curve_to_notes(
        pitch_curve,
        min_note_duration=min_note_duration,
        max_gap=max_gap,
        max_semitone_diff=max_semitone_diff,
    )

    logger.info(
        "extract_melody: done  stem=%s  vocals_rms=%.4f  notes=%d",
        stem_used,
        vocals_rms,
        len(notes),
    )

    return {
        "notes": notes,
        "stem_used": stem_used,
        "vocals_rms": vocals_rms,
        "note_count": len(notes),
    }

