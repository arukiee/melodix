"""MAESTRO-compatible audio features and frame/onset/offset labels."""

from dataclasses import dataclass
from pathlib import Path

import numpy as np

def load_wav(file_path: str | Path) -> tuple[np.ndarray, int]:
    """Load a WAV file and return audio data as a float32 numpy array and its sample rate.

    Tries soundfile first, falls back to librosa.
    """
    try:
        import soundfile as sf
        data, sr = sf.read(str(file_path), dtype='float32')
        if data.ndim > 1:
            data = data.mean(axis=1)
        return data, sr
    except Exception as e:
        try:
            import librosa
            data, sr = librosa.load(str(file_path), sr=None, mono=True, dtype=np.float32)
            return data, sr
        except Exception as exc:
            raise RuntimeError(f"Failed to load wav file {file_path}: {e}; fallback error: {exc}")


@dataclass(frozen=True)
class AudioConfig:
    sample_rate: int = 16000
    n_fft: int = 2048
    hop_length: int = 320
    n_mels: int = 128
    f_min: float = 27.5
    f_max: float = 4186.0


def log_mel_spectrogram(audio: np.ndarray, config: AudioConfig) -> np.ndarray:
    try:
        import librosa
    except ImportError as exc:
        raise RuntimeError("Install ml/requirements.txt for audio preprocessing") from exc
    audio = librosa.resample(audio.astype(np.float32), orig_sr=config.sample_rate, target_sr=config.sample_rate)
    mel = librosa.feature.melspectrogram(
        y=audio, sr=config.sample_rate, n_fft=config.n_fft, hop_length=config.hop_length,
        n_mels=config.n_mels, fmin=config.f_min, fmax=config.f_max, power=2.0,
    )
    return librosa.power_to_db(mel, ref=np.max).astype(np.float32)


def midi_labels(midi_path: str | Path, frame_count: int, config: AudioConfig) -> dict[str, np.ndarray]:
    try:
        import pretty_midi
    except ImportError as exc:
        raise RuntimeError("Install ml/requirements.txt for MIDI label generation") from exc
    frame_seconds = config.hop_length / config.sample_rate
    labels = {name: np.zeros((frame_count, 88), dtype=np.float32) for name in ("onset", "frame", "offset", "velocity")}
    midi = pretty_midi.PrettyMIDI(str(midi_path))
    for instrument in midi.instruments:
        if instrument.is_drum:
            continue
        for note in instrument.notes:
            key = note.pitch - 21
            if not 0 <= key < 88:
                continue
            start = max(0, min(frame_count - 1, int(note.start / frame_seconds)))
            end = max(start + 1, min(frame_count, int(np.ceil(note.end / frame_seconds))))
            labels["onset"][start, key] = 1.0
            labels["frame"][start:end, key] = 1.0
            labels["offset"][end - 1, key] = 1.0
            labels["velocity"][start:end, key] = note.velocity / 127.0
    return labels
