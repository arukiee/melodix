import asyncio
import json
from typing import AsyncGenerator

import aubio
import numpy as np
import sounddevice as sd
from pydantic import BaseModel

# Simple note detection using aubio pitch detection

def detect_pitch(audio_chunk: np.ndarray, samplerate: int = 44100) -> float:
    """Return pitch in Hz for a given audio chunk using aubio."""
    pitch_o = aubio.pitch("default", 2048, 1024, samplerate)
    pitch_o.set_unit("Hz")
    pitch_o.set_silence(-40)
    return pitch_o(audio_chunk.astype(np.float32))[0]

class NoteEvent(BaseModel):
    timestamp: float  # seconds since start
    pitch_hz: float
    midi_note: int
    velocity: float = 1.0

async def audio_stream() -> AsyncGenerator[NoteEvent, None]:
    """Yield NoteEvent objects from microphone in real time."""
    samplerate = 44100
    blocksize = 1024
    audio_queue = []
    def callback(indata, frames, time, status):
        audio_queue.append((indata.copy(), time))
    with sd.InputStream(channels=1, samplerate=samplerate, blocksize=blocksize, callback=callback):
        while True:
            if audio_queue:
                data, t = audio_queue.pop(0)
                pitch = detect_pitch(data[:,0], samplerate)
                if pitch > 0:
                    midi = int(round(69 + 12 * np.log2(pitch / 440.0)))
                    yield NoteEvent(timestamp=t, pitch_hz=pitch, midi_note=midi)
            else:
                await asyncio.sleep(0.001)
