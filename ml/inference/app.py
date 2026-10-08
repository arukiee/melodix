"""Standalone ML inference service. It never substitutes symbolic guesses for the learned model."""

import io
import os
import time
import wave
from pathlib import Path

import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

app = FastAPI(title="Melodix Transcription ML Service", version="0.1.0")
MODEL_VERSION = os.getenv("MELODIX_MODEL_VERSION", "cnn_bilstm_untrained")
CHECKPOINT = Path(os.getenv("MELODIX_CHECKPOINT", "ml/checkpoints/best.pt"))
CONFIG_PATH = Path(os.getenv("MELODIX_CONFIG", "ml/configs/transcription.yaml"))
_transcriber = None


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_version: str


class ModelInfoResponse(BaseModel):
    model_version: str
    architecture: str
    keys: int = Field(88, description="Number of independently predicted piano keys")
    model_loaded: bool
    checkpoint_loaded: bool
    status: str


class AudioQualityResponse(BaseModel):
    noise_score: float = Field(ge=0, le=1)
    rms_level: float = Field(ge=0, le=1)
    clipping_detected: bool
    usable: bool


class NoteEventResponse(BaseModel):
    midi_pitch: int = Field(ge=21, le=108)
    pitch_name: str
    onset_time_ms: float = Field(ge=0)
    offset_time_ms: float = Field(ge=0)
    velocity: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)


class TranscribeResponse(BaseModel):
    model_version: str
    model_loaded: bool
    inference_latency_ms: float = Field(ge=0)
    audio_quality: AudioQualityResponse
    notes: list[NoteEventResponse]
    session_id: str | None = None


def audio_quality(samples: np.ndarray) -> dict[str, float | bool]:
    samples = samples.astype(np.float32)
    rms = float(np.sqrt(np.mean(samples * samples))) if samples.size else 0.0
    clipping = bool(np.any(np.abs(samples) >= 0.999)) if samples.size else False
    noise_score = float(min(1.0, np.std(samples[: max(1, len(samples) // 10)]) * 5)) if samples.size else 1.0
    return {
        "noise_score": noise_score,
        "rms_level": min(1.0, rms),
        "clipping_detected": clipping,
        "usable": bool(samples.size and rms >= 0.005 and not clipping),
    }


def read_wav(payload: bytes) -> tuple[np.ndarray, int]:
    try:
        with wave.open(io.BytesIO(payload), "rb") as stream:
            if stream.getsampwidth() != 2:
                raise HTTPException(400, "Only 16-bit PCM WAV is supported")
            sample_rate = stream.getframerate()
            channels = stream.getnchannels()
            samples = np.frombuffer(stream.readframes(stream.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
            if channels > 1:
                samples = samples.reshape(-1, channels).mean(axis=1)
            return samples, sample_rate
    except (wave.Error, ValueError) as exc:
        raise HTTPException(400, "Invalid WAV audio") from exc


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return {"status": "ok", "model_loaded": CHECKPOINT.exists(), "model_version": MODEL_VERSION}


@app.get("/model-info", response_model=ModelInfoResponse)
def model_info() -> ModelInfoResponse:
    return {
        "model_version": MODEL_VERSION,
        "architecture": "frequency_aware_cnn_bilstm",
        "keys": 88,
        "model_loaded": CHECKPOINT.exists(),
        "checkpoint_loaded": CHECKPOINT.exists(),
        "status": "trained_checkpoint_required" if not CHECKPOINT.exists() else "ready",
    }


@app.post("/audio-quality", response_model=AudioQualityResponse)
async def audio_quality_endpoint(audio: UploadFile = File(...)) -> AudioQualityResponse:
    samples, _ = read_wav(await audio.read())
    return audio_quality(samples)


@app.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(audio: UploadFile = File(...), sample_rate: int | None = Form(None), session_id: str | None = Form(None)) -> TranscribeResponse:
    samples, source_rate = read_wav(await audio.read())
    quality = audio_quality(samples)
    if not CHECKPOINT.exists():
        raise HTTPException(503, detail={"message": "Trained CNN-BiLSTM checkpoint is unavailable", "audio_quality": quality})
    global _transcriber
    if _transcriber is None:
        try:
            import yaml
            from ml.inference.transcriber import Transcriber
            _transcriber = Transcriber(CHECKPOINT, yaml.safe_load(CONFIG_PATH.read_text()))
        except (OSError, RuntimeError, ImportError, KeyError) as exc:
            raise HTTPException(503, detail={"message": "Trained checkpoint could not be loaded", "error": str(exc)}) from exc
    notes, latency = _transcriber.transcribe(samples)
    for note in notes:
        note["pitch_name"] = f"{('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')[note['midi_pitch'] % 12]}{note['midi_pitch'] // 12 - 1}"
    return {"model_version": _transcriber.version, "model_loaded": True, "inference_latency_ms": latency, "audio_quality": quality, "notes": notes, "session_id": session_id}
