"""Clean Basic Pitch events into a monophonic, quantized melody."""

from __future__ import annotations

from typing import Any

import numpy as np


def _scalar_confidence(value: Any) -> float:
    """Normalize Basic Pitch scalar or nested-list confidence values."""
    array = np.asarray(value).reshape(-1)
    return float(array[0]) if array.size else 0.0


def _pyin_pitch(y: np.ndarray, sample_rate: int, start: float, end: float) -> float | None:
    import librosa

    first = max(0, int(start * sample_rate))
    last = min(len(y), max(first + 1, int(end * sample_rate)))
    segment = y[first:last]
    if len(segment) < sample_rate // 20:
        return None
    f0, _, voiced_probability = librosa.pyin(
        segment,
        fmin=librosa.note_to_hz("C2"),
        fmax=librosa.note_to_hz("C7"),
        sr=sample_rate,
        frame_length=2048,
        hop_length=256,
    )
    valid = np.isfinite(f0) & (voiced_probability >= 0.55)
    return float(np.median(f0[valid])) if np.any(valid) else None


def _tempo_grid(y: np.ndarray, sample_rate: int) -> float:
    import librosa

    # Prefer the public feature API so callers/tests can replace the estimator
    # without depending on librosa's legacy beat alias.
    tempo_fn = getattr(librosa.feature, "tempo", None) or librosa.beat.tempo
    tempo = tempo_fn(y=y, sr=sample_rate)
    bpm = float(np.asarray(tempo).reshape(-1)[0]) if np.size(tempo) else 120.0
    return 60.0 / max(40.0, min(240.0, bpm)) / 4.0


def _path_scores(
    slices: list[list[tuple[float, float, int, int, float]]],
) -> list[tuple[float, float, int, int, float]]:
    """Select a globally coherent melody from overlapping transcription notes."""
    paths: list[list[float]] = []
    parents: list[list[int]] = []
    for index, candidates in enumerate(slices):
        scores = []
        links = []
        for event in candidates:
            pitch = int(event[2])
            duration = max(0.0, float(event[1]) - float(event[0]))
            # Basic Pitch confidence is useful but imperfect. Favor sustained,
            # mid/high register candidates slightly without enforcing a range.
            local = 2.0 * _scalar_confidence(event[4]) + min(duration, 1.0) * 0.25
            local += min(max(pitch - 48, 0), 36) * 0.008
            if index == 0:
                scores.append(local)
                links.append(-1)
                continue
            previous = slices[index - 1]
            options = [
                (paths[index - 1][j] - min(abs(pitch - int(prior[2])), 24) * 0.035, j)
                for j, prior in enumerate(previous)
            ]
            best_score, best_parent = max(options)
            scores.append(best_score + local)
            links.append(best_parent)
        paths.append(scores)
        parents.append(links)

    if not slices:
        return []
    cursor = max(range(len(paths[-1])), key=paths[-1].__getitem__)
    selected = []
    for index in range(len(slices) - 1, -1, -1):
        selected.append(slices[index][cursor])
        cursor = parents[index][cursor]
    return list(reversed(selected))


def clean_melody_events(
    note_events: list[tuple[float, float, int, int, float]],
    audio_path: str,
    is_midi: bool = False,
) -> list[tuple[float, float, int, int, float]]:
    """Select a coherent monophonic melody, refine safe pitches, and quantize.

    When *is_midi* is True the input comes from a MIDI file whose pitches are
    already exact, so librosa loading and pYIN correction are skipped.  The
    tempo grid is derived from the MIDI's embedded tempo via pretty_midi.
    """
    if not note_events:
        return []

    y: np.ndarray | None = None
    sample_rate: int = 22050

    if is_midi:
        import pretty_midi
        pm = pretty_midi.PrettyMIDI(audio_path)
        tempo_changes = pm.get_tempo_changes()
        if tempo_changes[1].size:
            bpm = float(tempo_changes[1][0])
        else:
            bpm = float(pm.estimate_tempo()) if hasattr(pm, "estimate_tempo") else 120.0
        bpm = max(40.0, min(240.0, bpm))
        grid = 60.0 / bpm / 4.0
    else:
        import librosa
        y, sample_rate = librosa.load(audio_path, sr=22050, mono=True)
        grid = _tempo_grid(y, sample_rate)

    boundaries = sorted({float(event[0]) for event in note_events} | {float(event[1]) for event in note_events})
    active_slices = [
        [event for event in note_events if event[0] < end and event[1] > start]
        for start, end in zip(boundaries, boundaries[1:])
    ]
    active_slices = [candidates for candidates in active_slices if candidates]
    path = _path_scores(active_slices)
    selected: list[tuple[float, float, int, int, float]] = []

    for (start, end), event in zip(
        [(left, right) for left, right in zip(boundaries, boundaries[1:])
         if any(note[0] < right and note[1] > left for note in note_events)],
        path,
    ):
        pitch = int(event[2])

        # pYIN assumes one dominant fundamental. Applying it to polyphonic
        # slices can silently replace a valid melody note with a chord tone.
        active_count = sum(note[0] < end and note[1] > start for note in note_events)
        if not is_midi and y is not None and active_count == 1:
            import librosa as _lr
            pyin_hz = _pyin_pitch(y, sample_rate, start, end)
            if pyin_hz is not None:
                pyin_midi = int(round(float(_lr.hz_to_midi(pyin_hz))))
                pitch = max(0, min(127, pyin_midi))

        selected.append((start, end, pitch, int(event[3]), _scalar_confidence(event[4])))

    merged: list[tuple[float, float, int, int, float]] = []
    for start, end, pitch, velocity, confidence in selected:
        if merged and merged[-1][2] == pitch and abs(merged[-1][1] - start) < 0.05:
            previous = merged[-1]
            merged[-1] = (previous[0], end, pitch, max(previous[3], velocity), max(previous[4], confidence))
        else:
            merged.append((start, end, pitch, velocity, confidence))

    quantized = []
    for start, end, pitch, velocity, confidence in merged:
        quantized_start = max(0.0, round(start / grid) * grid)
        quantized_end = max(quantized_start + grid, round(end / grid) * grid)
        if quantized and quantized_start < quantized[-1][1] and pitch != quantized[-1][2]:
            quantized_start = quantized[-1][1]
        if quantized_end > quantized_start:
            quantized.append((quantized_start, quantized_end, pitch, velocity, confidence))
    return quantized


def melody_payload(events: list[tuple[float, float, int, int, float]]) -> list[dict[str, Any]]:
    """Return the lesson engine's requested note-event shape."""
    note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    return [
        {
            "note": f"{note_names[pitch % 12]}{pitch // 12 - 1}",
            "midiNumber": pitch,
            "startTime": round(start, 6),
            "duration": round(end - start, 6),
        }
        for start, end, pitch, _, _ in events
    ]
