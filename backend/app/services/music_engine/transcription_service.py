"""
Transcription Service — runs Basic Pitch inference on audio files.

This is the core ML component of the Melodix pipeline.

Flow:
  Download AudioAsset from MinIO
    ↓
  Verify SHA-256
    ↓
  Run Basic Pitch predict()
    ↓
  Basic Pitch internally resamples to 22050 Hz mono
    ↓
  Returns: model_output, midi_data, note_events
    ↓
  Save artifacts to MinIO (raw MIDI, model outputs, note events CSV)
    ↓
  Convert note_events → TranscriptionNote rows
    ↓
  Melodix confidence computation per note
    ↓
  Store in database

IMPORTANT:
  - Basic Pitch handles resampling internally — we do NOT pre-resample
  - Confidence is MELODIX-COMPUTED from model activation data,
    not a value Basic Pitch labels as "confidence"
  - All raw artifacts are preserved in MinIO for provenance
"""

import uuid
import time
import hashlib
import logging
import tempfile
import os
import csv
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple

import numpy as np

from sqlalchemy.orm import Session

from app.models.audio_asset import AudioAsset
from app.models.processing_job import ProcessingJob
from app.models.transcription import Transcription
from app.models.transcription_note import TranscriptionNote

logger = logging.getLogger(__name__)

# MIDI note number → note name lookup
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def midi_to_note_name(midi_number: int) -> str:
    """Convert MIDI note number (0-127) to note name like 'C4', 'E4'."""
    octave = (midi_number // 12) - 1
    note_idx = midi_number % 12
    return f"{NOTE_NAMES[note_idx]}{octave}"


class TranscriptionService:
    """
    Runs Basic Pitch automatic music transcription on audio files.
    
    Basic Pitch is an open-source AMT model (Apache-2.0) that:
    - Accepts common audio formats (WAV, MP3, FLAC, M4A, OGG)
    - Resamples to 22050 Hz mono internally
    - Supports polyphonic transcription
    - Outputs MIDI data and note events
    - Works best with single-instrument audio (piano for V1)
    
    The service preserves all raw artifacts in MinIO:
    - raw.mid (MIDI output)
    - model_output.npz (frame/onset/contour activations)
    - note_events.csv (start, end, pitch, velocity, confidence)
    """

    def transcribe(
        self, audio_asset: AudioAsset, job: ProcessingJob, db: Session
    ) -> Dict[str, Any]:
        """
        Run Basic Pitch transcription on an audio asset.
        
        Returns:
            {
                "transcription_id": str,
                "note_count": int,
                "duration_seconds": float,
                "processing_time_ms": int,
            }
        """
        start_time = time.time()

        # ── 1. Download from MinIO ────────────────────────────────────────
        from app.storage.minio_service import minio_service

        content = minio_service.download_bytes(audio_asset.storage_path)
        if not content:
            raise ValueError(f"Failed to download audio from MinIO: {audio_asset.storage_path}")

        # ── 2. Verify SHA-256 ─────────────────────────────────────────────
        computed_hash = hashlib.sha256(content).hexdigest()
        if computed_hash != audio_asset.file_hash_sha256:
            raise ValueError(
                f"SHA-256 mismatch: expected {audio_asset.file_hash_sha256}, "
                f"got {computed_hash}. File integrity compromised."
            )

        # ── 3. Write to temp file ─────────────────────────────────────────
        # Basic Pitch needs a file path, not raw bytes
        ext = audio_asset.format
        with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
            tmp.write(content)
            audio_path = tmp.name

        try:
            notes_with_confidence = []
            bp_version = "N/A (MIDI Source)"
            model_output_path = None
            note_events_path = None
            midi_path = None
            
            # If the source is already MIDI, just parse it and skip Basic Pitch
            if ext in ["mid", "midi"]:
                import pretty_midi
                logger.info(f"Source is MIDI, parsing directly: {audio_asset.original_filename}")
                pm = pretty_midi.PrettyMIDI(audio_path)
                
                # Extract all notes from all instruments
                for inst in pm.instruments:
                    if not inst.is_drum:
                        for note in inst.notes:
                            # start, end, pitch, velocity, confidence (1.0 for true MIDI)
                            notes_with_confidence.append((
                                float(note.start), float(note.end), int(note.pitch), int(note.velocity), 1.0
                            ))
                
                # Sort by start time
                notes_with_confidence.sort(key=lambda x: x[0])
                
                # Save the MIDI artifact
                transcription_id = uuid.uuid4()
                midi_storage_path = f"transcription/{transcription_id}/raw.mid"
                minio_service.upload_file(midi_storage_path, audio_path, "audio/midi")
                midi_path = midi_storage_path
                
                if not notes_with_confidence:
                    raise ValueError("MIDI file contained no recognizable notes.")
                    
            else:
                # ── 4. Run Basic Pitch ────────────────────────────────────────
                # Basic Pitch handles resampling to 22050 Hz and mono conversion
                from basic_pitch.inference import predict
                from basic_pitch import ICASSP_2022_MODEL_PATH
    
                logger.info(f"Running Basic Pitch on {audio_asset.original_filename} ({audio_asset.file_size_bytes} bytes)")
    
                # predict() returns (model_output, midi_data, note_events)
                # Tuned parameters:
                # - onset_threshold=0.50 (balanced onset precision for piano attacks)
                # - frame_threshold=0.30 (suppresses spurious frame noise)
                # - minimum_note_length=50.0ms (tuned from 58ms to capture fast piano staccato)
                # - minimum_frequency=80.0Hz (piano low E1 range boundary)
                # - maximum_frequency=3000.0Hz (piano upper F7 range boundary)
                model_output, midi_data, note_events = predict(
                    audio_path,
                    onset_threshold=0.50,
                    frame_threshold=0.30,
                    minimum_note_length=50.0,
                    minimum_frequency=80.0,
                    maximum_frequency=3000.0,
                )
    
                if not note_events or len(note_events) == 0:
                    raise ValueError(
                        "Basic Pitch produced no note events. "
                        "The audio may not contain recognizable pitched content."
                    )

            if ext not in ["mid", "midi"]:
                # ── 5. Save artifacts to MinIO ────────────────────────────────
                transcription_id = uuid.uuid4()
                base_path = f"transcription/{transcription_id}"
    
                # Save raw MIDI
                with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as midi_tmp:
                    midi_data.write(midi_tmp.name)
                    midi_storage_path = f"{base_path}/raw.mid"
                    minio_service.upload_file(midi_storage_path, midi_tmp.name, "audio/midi")
                    midi_path = midi_storage_path
                    os.unlink(midi_tmp.name)
    
                # Save model output (numpy arrays)
                try:
                    with tempfile.NamedTemporaryFile(suffix=".npz", delete=False) as npz_tmp:
                        # model_output is a dict of numpy arrays
                        np.savez_compressed(npz_tmp.name, **{
                            k: v for k, v in model_output.items()
                            if isinstance(v, np.ndarray)
                        })
                        model_output_storage = f"{base_path}/model_output.npz"
                        minio_service.upload_file(model_output_storage, npz_tmp.name)
                        model_output_path = model_output_storage
                        os.unlink(npz_tmp.name)
                except Exception as e:
                    logger.warning(f"Could not save model output: {e}")
    
                # Save note events as CSV
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".csv", delete=False, newline=""
                ) as csv_tmp:
                    writer = csv.writer(csv_tmp)
                    writer.writerow([
                        "start_time", "end_time", "midi_number",
                        "velocity", "confidence"
                    ])
                    for event in note_events:
                        start, end, pitch, vel, conf = (
                            event[0], event[1], int(event[2]),
                            int(event[3]), float(event[4]) if len(event) > 4 else 0.0
                        )
                        writer.writerow([
                            round(start, 6), round(end, 6), pitch, vel, round(conf, 6)
                        ])
                    csv_path = csv_tmp.name
    
                note_events_storage = f"{base_path}/note_events.csv"
                minio_service.upload_file(note_events_storage, csv_path)
                note_events_path = note_events_storage
                os.unlink(csv_path)
    
                # ── 6. Get Basic Pitch version ────────────────────────────────
                try:
                    import basic_pitch
                    bp_version = getattr(basic_pitch, "__version__", "unknown")
                except Exception:
                    bp_version = "unknown"
    
                # ── 7. Compute Melodix confidence per note ────────────────────
                notes_with_confidence = self._compute_note_confidence(
                    note_events, model_output
                )

            # ── 8. Calculate duration ─────────────────────────────────────
            if notes_with_confidence:
                max_end = max(e[1] for e in notes_with_confidence)
            else:
                max_end = 0.0

            processing_time_ms = int((time.time() - start_time) * 1000)

            # ── 9. Create Transcription record ────────────────────────────
            transcription = Transcription(
                id=transcription_id,
                processing_job_id=job.id,
                audio_asset_id=audio_asset.id,
                song_id=job.song_id,
                model_name="basic-pitch",
                model_version=bp_version,
                raw_midi_path=midi_path,
                model_output_path=model_output_path,
                note_events_path=note_events_path,
                note_count=len(notes_with_confidence),
                duration_seconds=round(max_end, 3),
                processing_time_ms=processing_time_ms,
            )
            db.add(transcription)
            db.flush()  # Get the ID before adding notes

            # ── 10. Create TranscriptionNote rows ─────────────────────────
            for idx, (start, end, pitch, vel, confidence) in enumerate(
                notes_with_confidence
            ):
                note = TranscriptionNote(
                    transcription_id=transcription_id,
                    sequence_index=idx,
                    midi_number=int(pitch),
                    note_name=midi_to_note_name(int(pitch)),
                    start_time=round(float(start), 6),
                    end_time=round(float(end), 6),
                    duration=round(float(end) - float(start), 6),
                    velocity=min(127, max(0, int(vel))),
                    confidence=round(float(confidence), 4),
                    is_validated=False,
                    hand="UNASSIGNED",
                )
                db.add(note)

            db.commit()

            logger.info(
                f"Transcription completed: {len(notes_with_confidence)} notes, "
                f"duration={max_end:.1f}s, model=basic-pitch v{bp_version}, "
                f"time={processing_time_ms}ms"
            )

            return {
                "transcription_id": str(transcription_id),
                "note_count": len(notes_with_confidence),
                "duration_seconds": round(max_end, 3),
                "processing_time_ms": processing_time_ms,
            }

        finally:
            # Clean up temp audio file
            if os.path.exists(audio_path):
                os.unlink(audio_path)

    def _compute_note_confidence(
        self,
        note_events: list,
        model_output: dict,
    ) -> List[Tuple[float, float, int, int, float]]:
        """
        Compute Melodix confidence score for each note.
        
        Basic Pitch exposes raw model outputs (frame activations, onset 
        activations, pitch contours). We derive a per-note confidence 
        from the activation values at each note's time-frequency position.
        
        This is OUR computation, not something Basic Pitch provides as 
        a labeled "confidence" value.
        
        Returns list of (start, end, pitch, velocity, confidence) tuples.
        """
        notes_with_confidence = []

        # Extract frame-level activations if available
        # model_output keys typically include 'note', 'onset', 'contour'
        note_activation = model_output.get("note")
        onset_activation = model_output.get("onset")

        for event in note_events:
            start = float(event[0])
            end = float(event[1])
            pitch = int(event[2])
            vel = int(event[3])

            # Compute confidence from model activations
            confidence = self._activation_confidence(
                start, end, pitch,
                note_activation, onset_activation
            )

            notes_with_confidence.append((start, end, pitch, vel, confidence))

        return notes_with_confidence

    def _activation_confidence(
        self,
        start_time: float,
        end_time: float,
        midi_pitch: int,
        note_activation: np.ndarray | None,
        onset_activation: np.ndarray | None,
    ) -> float:
        """
        Compute confidence from model frame-level activations.
        
        Approach:
        1. Find the frames corresponding to the note's time range
        2. Find the frequency bin corresponding to the note's pitch
        3. Average the activation values across those frames
        4. Weight by onset activation strength
        
        If model activations aren't available, fall back to a 
        duration/velocity heuristic.
        """
        # Model parameters (Basic Pitch default)
        AUDIO_SAMPLE_RATE = 22050
        FFT_HOP = 256
        ANNOT_N_FRAMES = AUDIO_SAMPLE_RATE // FFT_HOP  # ~86 frames per second
        CONTOUR_BINS_PER_SEMITONE = 3
        N_FREQ_BINS_NOTES = 88  # piano range
        MIDI_OFFSET = 21  # A0 = MIDI 21

        if note_activation is not None:
            try:
                # Squeeze extra batch dimension if 3D
                if note_activation.ndim == 3:
                    note_activation = note_activation[0]
                if onset_activation is not None and onset_activation.ndim == 3:
                    onset_activation = onset_activation[0]

                # Convert time to frame indices
                start_frame = int(start_time * ANNOT_N_FRAMES)
                end_frame = int(end_time * ANNOT_N_FRAMES)

                # Convert MIDI pitch to frequency bin index
                pitch_bin = midi_pitch - MIDI_OFFSET

                if (
                    0 <= pitch_bin < note_activation.shape[-1]
                    and start_frame < note_activation.shape[0]
                ):
                    end_frame = min(end_frame, note_activation.shape[0])
                    if end_frame > start_frame:
                        # Mean activation across the note's duration
                        note_act = float(
                            np.mean(
                                note_activation[start_frame:end_frame, pitch_bin]
                            )
                        )

                        # Weight by onset activation if available
                        onset_weight = 1.0
                        if onset_activation is not None:
                            onset_frame = min(
                                start_frame, onset_activation.shape[0] - 1
                            )
                            if 0 <= pitch_bin < onset_activation.shape[-1]:
                                onset_weight = float(
                                    onset_activation[onset_frame, pitch_bin]
                                )
                                onset_weight = 0.5 + 0.5 * min(onset_weight, 1.0)

                        # Combine: activation × onset weight
                        confidence = min(1.0, note_act * onset_weight)
                        return round(max(0.0, confidence), 4)

            except (IndexError, ValueError) as e:
                logger.warning(f"Error reading Basic Pitch model activations ({e}); falling back to heuristic confidence.")

        # Fallback: duration/velocity heuristic
        logger.warning(
            f"Basic Pitch model activations missing or inaccessible for MIDI pitch {midi_pitch} at {start_time:.2f}s; "
            "falling back to heuristic note confidence score."
        )
        duration = end_time - start_time
        duration_score = min(1.0, duration / 0.5)  # 0.5s = full score
        velocity_score = min(1.0, midi_pitch / 100.0)  # rough proxy

        return round(0.3 + 0.4 * duration_score + 0.3 * velocity_score, 4)
