"""
BPM Detector — computes tempo with Melodix-computed confidence.

Uses librosa.beat.beat_track() for tempo estimation and beat tracking.

IMPORTANT:
  librosa.beat.beat_track() returns tempo and beat locations.
  It does NOT return a confidence score.
  
  The confidence is MELODIX-COMPUTED from:
    - Beat interval consistency (std dev of inter-beat intervals)
    - Onset alignment (% of beats aligned with detected onsets)
    - Tempo stability (variance across windowed estimates)
    - Autocorrelation peak strength from onset envelope

  We never falsely attribute the confidence to librosa.
"""

import logging
import tempfile
import os
import hashlib
from typing import Dict, Any, Optional

import numpy as np
from sqlalchemy.orm import Session

from app.models.audio_asset import AudioAsset

logger = logging.getLogger(__name__)


class BPMDetector:
    """
    Detects tempo (BPM) and beat positions from audio.
    
    Output:
    {
        "tempo_bpm": 91.82,
        "beat_times": [0.52, 1.17, 1.82, ...],
        "confidence": 0.87,   # MELODIX-COMPUTED
        "time_signature": "4/4",
        "method": "librosa_beat_track",
        "engine_version": "1.0.0"
    }
    """

    ENGINE_VERSION = "1.0.0"

    def detect(self, audio_asset: AudioAsset, db: Session) -> Dict[str, Any]:
        """
        Detect BPM and beat positions from an audio asset.
        
        Returns BPM result dict with Melodix-computed confidence.
        """
        import librosa

        # ── 1. Load audio ─────────────────────────────────────────────────
        from app.storage.minio_service import minio_service

        content = minio_service.download_bytes(audio_asset.storage_path)
        if not content:
            raise ValueError(f"Failed to download audio: {audio_asset.storage_path}")

        ext = audio_asset.format
        with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
            tmp.write(content)
            audio_path = tmp.name

        try:
            # librosa loads and resamples
            y, sr = librosa.load(audio_path, sr=22050, mono=True)

            if len(y) < sr:
                return {
                    "tempo_bpm": 0.0,
                    "beat_times": [],
                    "confidence": 0.0,
                    "time_signature": "4/4",
                    "method": "librosa_beat_track",
                    "engine_version": self.ENGINE_VERSION,
                    "warning": "Audio too short for reliable tempo detection.",
                }

            # ── 2. Onset strength envelope ────────────────────────────────
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)

            # ── 3. Beat tracking ──────────────────────────────────────────
            # Returns: tempo (float), beat_frames (ndarray)
            tempo, beat_frames = librosa.beat.beat_track(
                y=y, sr=sr, onset_envelope=onset_env
            )

            # Convert beat frames to times
            beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()

            # Handle librosa returning tempo as array in some versions
            if hasattr(tempo, '__len__'):
                tempo = float(tempo[0]) if len(tempo) > 0 else 0.0
            else:
                tempo = float(tempo)

            # ── 4. Melodix confidence computation ─────────────────────────
            confidence = self._compute_confidence(
                tempo, beat_times, onset_env, sr
            )

            # ── 5. Estimate time signature ────────────────────────────────
            time_signature = self._estimate_time_signature(beat_times, onset_env, sr)

            result = {
                "tempo_bpm": round(tempo, 2),
                "beat_times": [round(t, 4) for t in beat_times],
                "confidence": round(confidence, 4),
                "time_signature": time_signature,
                "method": "librosa_beat_track",
                "engine_version": self.ENGINE_VERSION,
            }

            # Add warning if confidence is low
            if confidence < 0.5:
                result["warning"] = (
                    f"Tempo detection uncertain (confidence: {confidence:.2f}). "
                    f"BPM estimate of {tempo:.1f} may not be reliable."
                )

            logger.info(
                f"BPM detected: {tempo:.1f} BPM, "
                f"confidence={confidence:.2f}, "
                f"beats={len(beat_times)}, "
                f"time_sig={time_signature}"
            )

            return result

        finally:
            if os.path.exists(audio_path):
                os.unlink(audio_path)

    def _compute_confidence(
        self,
        tempo: float,
        beat_times: list,
        onset_env: np.ndarray,
        sr: int,
    ) -> float:
        """
        Compute Melodix confidence score for tempo detection.
        
        NOT from librosa — this is our own computation.
        
        Features:
        1. Beat interval consistency — low std dev = high confidence
        2. Onset alignment — what % of beats align with onset peaks
        3. Tempo stability — agreement across windowed estimates
        4. Autocorrelation peak strength from onset envelope
        """
        if not beat_times or len(beat_times) < 3 or tempo <= 0:
            return 0.0

        scores = []

        # ── Feature 1: Beat interval consistency ─────────────────────────
        intervals = np.diff(beat_times)
        if len(intervals) > 1:
            expected_interval = 60.0 / tempo
            interval_deviations = np.abs(intervals - expected_interval)
            mean_deviation = float(np.mean(interval_deviations))
            # Normalize: 0 deviation = 1.0, >0.2s deviation = 0.0
            consistency = max(0.0, 1.0 - (mean_deviation / 0.2))
            scores.append(("interval_consistency", consistency, 0.35))

        # ── Feature 2: Onset alignment ───────────────────────────────────
        import librosa
        onset_times = librosa.onset.onset_detect(
            onset_envelope=onset_env, sr=sr, units="time"
        )
        if len(onset_times) > 0 and len(beat_times) > 0:
            aligned = 0
            for bt in beat_times:
                # Check if any onset is within 50ms of this beat
                dists = np.abs(np.array(onset_times) - bt)
                if np.min(dists) < 0.05:
                    aligned += 1
            alignment_ratio = aligned / len(beat_times)
            scores.append(("onset_alignment", alignment_ratio, 0.25))

        # ── Feature 3: Tempo stability ───────────────────────────────────
        # Estimate tempo in overlapping windows
        window_tempos = []
        window_size = min(len(beat_times) // 2, 8)
        if window_size >= 3:
            for i in range(0, len(beat_times) - window_size, max(1, window_size // 2)):
                window = beat_times[i:i + window_size]
                w_intervals = np.diff(window)
                if len(w_intervals) > 0 and np.mean(w_intervals) > 0:
                    w_tempo = 60.0 / np.mean(w_intervals)
                    window_tempos.append(w_tempo)

            if len(window_tempos) > 1:
                tempo_std = float(np.std(window_tempos))
                # Normalize: 0 std = 1.0, >10 BPM std = 0.0
                stability = max(0.0, 1.0 - (tempo_std / 10.0))
                scores.append(("tempo_stability", stability, 0.25))

        # ── Feature 4: Autocorrelation peak strength ─────────────────────
        if len(onset_env) > 0:
            autocorr = np.correlate(onset_env, onset_env, mode="full")
            autocorr = autocorr[len(autocorr) // 2:]
            if len(autocorr) > 1 and autocorr[0] > 0:
                autocorr_norm = autocorr / autocorr[0]
                # Find the peak at the expected tempo lag
                expected_lag = int(sr / (256 * tempo / 60))  # frames
                search_start = max(1, expected_lag - 5)
                search_end = min(len(autocorr_norm), expected_lag + 5)
                if search_end > search_start:
                    peak_val = float(np.max(autocorr_norm[search_start:search_end]))
                    scores.append(("autocorr_peak", peak_val, 0.15))

        # ── Weighted average ─────────────────────────────────────────────
        if not scores:
            return 0.0

        total_weight = sum(w for _, _, w in scores)
        confidence = sum(s * w for _, s, w in scores) / total_weight if total_weight > 0 else 0.0

        return max(0.0, min(1.0, confidence))

    def _estimate_time_signature(
        self,
        beat_times: list,
        onset_env: np.ndarray,
        sr: int,
    ) -> str:
        """
        Estimate time signature from beat pattern.
        
        Simple heuristic: check if beats group naturally in 3s or 4s
        based on onset accent patterns.
        """
        if len(beat_times) < 8:
            return "4/4"  # default

        import librosa

        # Get onset strength at each beat position
        beat_strengths = []
        hop_length = 512
        for bt in beat_times:
            frame = librosa.time_to_frames(bt, sr=sr, hop_length=hop_length)
            if 0 <= frame < len(onset_env):
                beat_strengths.append(float(onset_env[frame]))
            else:
                beat_strengths.append(0.0)

        if len(beat_strengths) < 6:
            return "4/4"

        # Check for 3/4: every 3rd beat should be stronger
        accent_3 = sum(
            beat_strengths[i]
            for i in range(0, len(beat_strengths), 3)
        ) / max(1, len(beat_strengths) // 3)

        accent_4 = sum(
            beat_strengths[i]
            for i in range(0, len(beat_strengths), 4)
        ) / max(1, len(beat_strengths) // 4)

        non_accent_mean = float(np.mean(beat_strengths))

        if non_accent_mean > 0:
            ratio_3 = accent_3 / non_accent_mean
            ratio_4 = accent_4 / non_accent_mean

            if ratio_3 > ratio_4 and ratio_3 > 1.3:
                return "3/4"

        return "4/4"
