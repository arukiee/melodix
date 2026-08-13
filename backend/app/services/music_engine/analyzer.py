import numpy as np
from typing import List, Tuple, Optional, Dict
from app.services.music_engine.base_analyzer import (
    BaseAudioAnalyzer, AnalysisRequest, AnalysisResult, AnalysisMistake,
    PerformanceEvent, ExpectedEvent, ScoreBreakdown, TempoMetrics,
    NoteComparisonEvent
)


# ─────────────────────────────────────────────────────────────────────────────
# Pitch utilities
# ─────────────────────────────────────────────────────────────────────────────

def hz_to_note_and_cents(hz: float) -> Tuple[str, float]:
    """Converts a frequency in Hz to a MIDI note name and cents deviation."""
    if hz <= 0:
        return "Silence", 0.0
    midi = 12 * np.log2(hz / 440.0) + 69
    midi_round = int(round(midi))
    cents_off = (midi - midi_round) * 100.0
    note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    octave = (midi_round // 12) - 1
    note_idx = midi_round % 12
    return f"{note_names[note_idx]}{octave}", cents_off


def detect_pitch_autocorrelation(signal: np.ndarray, sr: int) -> float:
    """Estimates fundamental frequency (F0) using normalized autocorrelation (YIN-lite)."""
    rms = np.sqrt(np.mean(signal ** 2))
    if rms < 0.005:
        return 0.0

    n = len(signal)
    corr = np.correlate(signal, signal, mode='full')
    corr = corr[n - 1:]

    # Normalize by autocorrelation at lag 0 to avoid bias toward lower pitches
    if corr[0] < 1e-10:
        return 0.0
    corr_norm = corr / corr[0]

    # Skip the initial falling edge to find the first real peak (the fundamental period)
    diff = np.diff(corr_norm)
    valleys = np.where(diff > 0)[0]
    if len(valleys) == 0:
        return 0.0
    start_search = valleys[0]

    # Clamp search range to piano frequency range (A0=27.5 Hz → C8=4186 Hz)
    min_lag = max(1, int(sr / 4200))
    max_lag = int(sr / 27)
    start_search = max(start_search, min_lag)

    search_region = corr_norm[start_search:max_lag]
    if len(search_region) == 0:
        return 0.0

    peak_offset = int(np.argmax(search_region)) + start_search
    if peak_offset == 0 or corr_norm[peak_offset] < 0.4:
        return 0.0

    f0 = sr / peak_offset
    return float(f0) if 27.0 <= f0 <= 4200.0 else 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Onset detection
# ─────────────────────────────────────────────────────────────────────────────

def detect_onsets(audio: np.ndarray, sr: int, hop_ms: int = 10) -> List[float]:
    """
    Energy-transient onset detector using RMS delta.
    Returns list of onset times in seconds.

    Approach:
    1. Compute RMS in small overlapping windows.
    2. Calculate the first difference (delta RMS).
    3. Peaks in delta RMS above a threshold indicate note attacks.
    """
    hop = int(sr * hop_ms / 1000)
    win = hop * 4

    rms_values = []
    for i in range(0, len(audio) - win, hop):
        frame = audio[i: i + win]
        rms_values.append(float(np.sqrt(np.mean(frame ** 2))))

    if len(rms_values) < 3:
        return []

    rms_arr = np.array(rms_values)
    # Spectral flux: positive delta only (note attacks go up, not down)
    delta = np.diff(rms_arr, prepend=rms_arr[0])
    delta = np.maximum(delta, 0)

    # Adaptive threshold: mean + 1.5 × std of positive deltas
    pos_delta = delta[delta > 0]
    if len(pos_delta) == 0:
        return []
    threshold = np.mean(pos_delta) + 1.5 * np.std(pos_delta)
    threshold = max(threshold, 0.005)  # floor to avoid noise triggering

    onset_times = []
    min_gap_frames = int(100 / hop_ms)  # minimum 100ms between onsets
    last_onset = -min_gap_frames

    for i, d in enumerate(delta):
        if d >= threshold and (i - last_onset) >= min_gap_frames:
            onset_times.append(i * hop / sr)
            last_onset = i

    return onset_times


# ─────────────────────────────────────────────────────────────────────────────
# Note segmentation using onsets + pitch estimation per segment
# ─────────────────────────────────────────────────────────────────────────────

def segment_notes_by_onset(
    audio: np.ndarray,
    sr: int,
    onset_times: List[float],
    silence_threshold: float = 0.008
) -> List[PerformanceEvent]:
    """
    For each onset, estimates the pitch in the attack window (30–100ms after onset)
    and tracks the note until the next onset or silence.
    Returns a list of PerformanceEvent objects.
    """
    events: List[PerformanceEvent] = []

    # Add a virtual final boundary
    boundaries = onset_times + [len(audio) / sr]

    for i, onset in enumerate(onset_times):
        end = boundaries[i + 1]
        onset_sample = int(onset * sr)
        end_sample = min(int(end * sr), len(audio))

        # Pitch estimation window: 30ms after onset, 100ms long
        pitch_start = onset_sample + int(0.03 * sr)
        pitch_end = min(pitch_start + int(0.10 * sr), end_sample)

        if pitch_end - pitch_start < 64:
            continue

        pitch_segment = audio[pitch_start:pitch_end]
        f0 = detect_pitch_autocorrelation(pitch_segment, sr)
        note, cents = hz_to_note_and_cents(f0)

        if note == "Silence" or f0 <= 0:
            continue

        # Determine actual note end: look for silence within the segment
        actual_end_sample = end_sample
        check_hop = int(0.02 * sr)  # 20ms windows
        for j in range(onset_sample, end_sample - check_hop, check_hop):
            chunk = audio[j: j + check_hop]
            if np.sqrt(np.mean(chunk ** 2)) < silence_threshold:
                actual_end_sample = j
                break

        start_time = float(onset)
        end_time = float(actual_end_sample / sr)
        duration = end_time - start_time

        if duration < 0.04:  # skip very short transients (< 40ms)
            continue

        segment = audio[onset_sample:actual_end_sample]
        mean_rms = float(np.sqrt(np.mean(segment ** 2))) if len(segment) > 0 else 0.0
        dyn = "soft" if mean_rms < 0.015 else "loud" if mean_rms >= 0.06 else "medium"

        events.append(PerformanceEvent(
            note=note,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            confidence=0.9,
            cents_off=float(cents),
            dynamic_level=dyn,
        ))

    return events


# ─────────────────────────────────────────────────────────────────────────────
# Performance scoring engine
# ─────────────────────────────────────────────────────────────────────────────

class PerformanceScoringEngine:
    """
    Compares the detected performance against the expected performance.
    Produces:
      - ScoreBreakdown (pitch, rhythm, tempo, duration, overall)
      - TempoMetrics
      - List[AnalysisMistake] (named, timestamped feedback items)
      - List[NoteComparisonEvent] (per-note comparison table for the UI)
      - Counts: correct / wrong / missed / extra
    """

    @staticmethod
    def calculate_scores(
        detected_events: List[PerformanceEvent],
        expected: List[ExpectedEvent],
        target_bpm: int
    ) -> Tuple[ScoreBreakdown, TempoMetrics, List[AnalysisMistake], Dict[int, float], List[NoteComparisonEvent], Dict]:
        mistakes: List[AnalysisMistake] = []
        comparison_table: List[NoteComparisonEvent] = []
        pitch_score = 100.0
        rhythm_score = 100.0
        duration_score = 100.0
        tempo_score = 100.0
        correct_count = 0
        wrong_count = 0
        missed_count = 0

        # ── 1. Tempo metrics ──────────────────────────────────────────────────
        detected_bpms = []
        if len(detected_events) > 1:
            for idx in range(len(detected_events) - 1):
                interval = detected_events[idx + 1].start_time - detected_events[idx].start_time
                if interval > 0.01:
                    detected_bpms.append(60.0 / interval)

        avg_bpm = float(np.mean(detected_bpms)) if detected_bpms else float(target_bpm)
        bpm_variance = float(np.std(detected_bpms)) if len(detected_bpms) > 1 else 0.0
        drift = avg_bpm - target_bpm
        stability = max(0.0, 100.0 - (bpm_variance * 5.0))
        tempo_score = max(30.0, stability - min(30.0, abs(drift) * 2.0))

        # ── 2. Note-level matching ────────────────────────────────────────────
        matched_det_indices: set = set()

        for exp in expected:
            best_idx = -1
            best_score = -1.0

            for i, det in enumerate(detected_events):
                if i in matched_det_indices:
                    continue
                # Consider it a candidate if note matches OR it's within timing window
                note_match = (det.note == exp.note)
                time_diff = abs(det.start_time - exp.relative_time)
                if time_diff > 2.0:  # too far away to be this note
                    continue
                # Score candidates: prefer exact note + close timing
                candidate_score = (1.0 if note_match else 0.0) + (1.0 / (1.0 + time_diff))
                if candidate_score > best_score:
                    best_score = candidate_score
                    best_idx = i

            if best_idx == -1:
                # Missed note — no detected event matched at all
                missed_count += 1
                pitch_score = max(20.0, pitch_score - 25.0)
                mistakes.append(AnalysisMistake(
                    timestamp=exp.relative_time,
                    type="missed_note",
                    details=f"Missed {exp.note} (expected at {exp.relative_time:.2f}s)"
                ))
                comparison_table.append(NoteComparisonEvent(
                    expected_note=exp.note,
                    played_note=None,
                    result="missed",
                    expected_time=exp.relative_time,
                    played_time=None,
                    timing_delta_ms=None,
                    expected_duration=exp.duration,
                    played_duration=None,
                    duration_delta_ms=None,
                    cents_off=None,
                ))
                continue

            matched_det_indices.add(best_idx)
            det = detected_events[best_idx]

            # ── Pitch check ──
            if det.note != exp.note:
                wrong_count += 1
                pitch_score = max(20.0, pitch_score - 20.0)
                mistakes.append(AnalysisMistake(
                    timestamp=det.start_time,
                    type="wrong_note",
                    details=f"Expected {exp.note}, played {det.note} at {det.start_time:.2f}s"
                ))
                comparison_table.append(NoteComparisonEvent(
                    expected_note=exp.note,
                    played_note=det.note,
                    result="wrong",
                    expected_time=exp.relative_time,
                    played_time=det.start_time,
                    timing_delta_ms=round((det.start_time - exp.relative_time) * 1000),
                    expected_duration=exp.duration,
                    played_duration=det.duration,
                    duration_delta_ms=round((det.duration - exp.duration) * 1000),
                    cents_off=round(det.cents_off, 1),
                ))
                continue

            correct_count += 1

            # ── Cents intonation ──
            if abs(det.cents_off) > 15.0:
                direction = "sharp" if det.cents_off > 0 else "flat"
                mistakes.append(AnalysisMistake(
                    timestamp=det.start_time,
                    type=direction,
                    details=f"{det.note} was {direction} by {abs(det.cents_off):.1f} cents"
                ))
                pitch_score = max(30.0, pitch_score - 8.0)

            # ── Timing ──
            time_offset = det.start_time - exp.relative_time
            timing_delta_ms = round(time_offset * 1000)
            if abs(time_offset) > 0.15:
                direction = "late" if time_offset > 0 else "early"
                mistakes.append(AnalysisMistake(
                    timestamp=det.start_time,
                    type=direction,
                    details=f"{det.note} played {direction} by {abs(timing_delta_ms)}ms"
                ))
                rhythm_score = max(30.0, rhythm_score - 15.0)

            # ── Duration ──
            dur_delta = det.duration - exp.duration
            dur_delta_ms = round(dur_delta * 1000)
            if abs(dur_delta) > 0.20:  # more than 200ms off
                direction = "too long" if dur_delta > 0 else "too short"
                mistakes.append(AnalysisMistake(
                    timestamp=det.start_time,
                    type="duration",
                    details=f"{det.note} held {direction} ({abs(dur_delta_ms)}ms off)"
                ))
                duration_score = max(30.0, duration_score - 10.0)

            comparison_table.append(NoteComparisonEvent(
                expected_note=exp.note,
                played_note=det.note,
                result="correct",
                expected_time=exp.relative_time,
                played_time=det.start_time,
                timing_delta_ms=timing_delta_ms,
                expected_duration=exp.duration,
                played_duration=det.duration,
                duration_delta_ms=dur_delta_ms,
                cents_off=round(det.cents_off, 1),
            ))

        # ── 3. Extra notes (played but not expected) ──────────────────────────
        extra_count = 0
        for i, det in enumerate(detected_events):
            if i not in matched_det_indices:
                extra_count += 1
                pitch_score = max(20.0, pitch_score - 10.0)
                mistakes.append(AnalysisMistake(
                    timestamp=det.start_time,
                    type="extra_note",
                    details=f"Extra note {det.note} played at {det.start_time:.2f}s (not expected)"
                ))
                comparison_table.append(NoteComparisonEvent(
                    expected_note="—",
                    played_note=det.note,
                    result="extra",
                    expected_time=0.0,
                    played_time=det.start_time,
                    timing_delta_ms=None,
                    expected_duration=None,
                    played_duration=det.duration,
                    duration_delta_ms=None,
                    cents_off=round(det.cents_off, 1),
                ))

        # ── 4. Overall score — weighted average ───────────────────────────────
        overall = (pitch_score * 0.35 + rhythm_score * 0.30 + tempo_score * 0.20 + duration_score * 0.15)

        # ── 5. Per-measure scores ─────────────────────────────────────────────
        measure_scores: Dict[int, float] = {}
        for m_idx in range(max(1, (len(expected) + 3) // 4)):
            start_exp = m_idx * 4
            end_exp = min(len(expected), start_exp + 4)
            m_expected = expected[start_exp:end_exp]
            if not m_expected:
                continue
            m_points = 0.0
            for exp_e in m_expected:
                has_mistake = any(
                    m.timestamp >= exp_e.relative_time and m.timestamp < exp_e.relative_time + exp_e.duration
                    for m in mistakes
                )
                m_points += 100.0 if not has_mistake else 50.0
            measure_scores[m_idx] = float(m_points / len(m_expected))

        counts = {
            "correct": correct_count,
            "wrong": wrong_count,
            "missed": missed_count,
            "extra": extra_count,
        }

        return (
            ScoreBreakdown(
                pitchScore=round(pitch_score, 1),
                rhythmScore=round(rhythm_score, 1),
                tempoScore=round(tempo_score, 1),
                durationScore=round(duration_score, 1),
                overallScore=round(overall, 1),
            ),
            TempoMetrics(
                targetBpm=float(target_bpm),
                averageBpm=round(avg_bpm, 1),
                bpmVariance=round(bpm_variance, 2),
                driftBpm=round(drift, 1),
                stabilityScore=round(stability, 1),
            ),
            mistakes,
            measure_scores,
            comparison_table,
            counts,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Main analyzer — orchestrates onset detection + segmentation + scoring
# ─────────────────────────────────────────────────────────────────────────────

class AutocorrelationAnalyzer(BaseAudioAnalyzer):
    def analyze(self, request: AnalysisRequest) -> AnalysisResult:
        audio = request.audio_data
        sr = request.sample_rate
        duration_ms = (len(audio) / sr) * 1000.0

        empty_scores = ScoreBreakdown(pitchScore=0.0, rhythmScore=0.0, tempoScore=0.0, durationScore=0.0, overallScore=0.0)
        empty_tempo = TempoMetrics(targetBpm=float(request.target_bpm), averageBpm=0.0, bpmVariance=0.0, driftBpm=0.0, stabilityScore=0.0)

        # ── Validation ────────────────────────────────────────────────────────
        rms = np.sqrt(np.mean(audio ** 2))
        if len(audio) < sr * 0.5:
            return AnalysisResult(
                noteAccuracy=0, rhythmAccuracy=0, tempoAccuracy=0, overallScore=0, detectedBpm=0,
                durationMs=duration_ms, scores=empty_scores, tempo_metrics=empty_tempo,
                mistakes=[AnalysisMistake(timestamp=0.0, type="short", details="Recording is too short (< 0.5s)")]
            )
        if rms < 0.001:
            return AnalysisResult(
                noteAccuracy=0, rhythmAccuracy=0, tempoAccuracy=0, overallScore=0, detectedBpm=0,
                durationMs=duration_ms, scores=empty_scores, tempo_metrics=empty_tempo,
                mistakes=[AnalysisMistake(timestamp=0.0, type="silent", details="No audio volume detected. Is the microphone working?")]
            )

        # ── Stage 1: Onset detection ──────────────────────────────────────────
        onset_times = detect_onsets(audio, sr, hop_ms=10)

        # ── Stage 2: Note segmentation ────────────────────────────────────────
        # Use onset-based segmentation if we found onsets; fall back to frame-based
        if onset_times:
            detected_events = segment_notes_by_onset(audio, sr, onset_times)
        else:
            # Fallback: 50ms frame-based pitch tracking (original approach)
            detected_events = self._frame_based_fallback(audio, sr)

        # ── Stage 3: Build expected events ───────────────────────────────────
        expected = request.expected_events
        if not expected and request.expected_notes:
            # BPM-aware timing: each note occupies one beat = 60/bpm seconds
            beat_duration = 60.0 / max(request.target_bpm, 1)
            expected = [
                ExpectedEvent(
                    note=n,
                    relative_time=round(i * beat_duration, 4),
                    duration=round(beat_duration * 0.85, 4)  # 85% of beat = staccato headroom
                )
                for i, n in enumerate(request.expected_notes)
            ]

        # ── Stage 4: Score ────────────────────────────────────────────────────
        scores_data, tempo_data, mistakes, measure_scores, comparison_table, counts = \
            PerformanceScoringEngine.calculate_scores(detected_events, expected, request.target_bpm)

        # ── Stage 5: Measure dynamics ─────────────────────────────────────────
        measure_dynamics: Dict[int, str] = {}
        for m_idx in measure_scores.keys():
            m_start = m_idx * (4 * (60.0 / max(request.target_bpm, 1)))
            m_end = m_start + 4 * (60.0 / max(request.target_bpm, 1))
            m_notes = [
                det.dynamic_level for det in detected_events
                if m_start <= det.start_time < m_end
            ]
            measure_dynamics[m_idx] = max(set(m_notes), key=m_notes.count) if m_notes else "medium"

        return AnalysisResult(
            version=2,
            noteAccuracy=scores_data.pitchScore,
            rhythmAccuracy=scores_data.rhythmScore,
            tempoAccuracy=scores_data.tempoScore,
            overallScore=scores_data.overallScore,
            detectedBpm=tempo_data.averageBpm,
            durationMs=duration_ms,
            mistakes=mistakes,
            detected_events=detected_events,
            scores=scores_data,
            tempo_metrics=tempo_data,
            measure_scores=measure_scores,
            measure_dynamics=measure_dynamics,
            note_comparison=comparison_table,
            correct_notes=counts["correct"],
            wrong_notes=counts["wrong"],
            missed_notes=counts["missed"],
            extra_notes=counts["extra"],
        )

    def _frame_based_fallback(self, audio: np.ndarray, sr: int) -> List[PerformanceEvent]:
        """Original 50ms frame-based segmentation — used when onset detection finds nothing."""
        frame_len = int(sr * 0.05)
        detected_events: List[PerformanceEvent] = []
        current_note: Optional[str] = None
        start_frame_idx = 0
        cents_accumulator: List[float] = []
        rms_accumulator: List[float] = []

        for idx in range(0, len(audio) - frame_len, frame_len):
            frame = audio[idx: idx + frame_len]
            f0 = detect_pitch_autocorrelation(frame, sr)
            note, cents = hz_to_note_and_cents(f0)
            frame_rms = float(np.sqrt(np.mean(frame ** 2)))

            if note != current_note:
                if current_note and current_note != "Silence":
                    start_time = (start_frame_idx * frame_len) / sr
                    end_time = (idx * frame_len) / sr
                    dur = end_time - start_time
                    mean_cents = float(np.mean(cents_accumulator)) if cents_accumulator else 0.0
                    mean_rms = float(np.mean(rms_accumulator)) if rms_accumulator else 0.0
                    dyn = "soft" if mean_rms < 0.015 else "loud" if mean_rms >= 0.06 else "medium"
                    if dur >= 0.04:
                        detected_events.append(PerformanceEvent(
                            note=current_note,
                            start_time=start_time,
                            end_time=end_time,
                            duration=dur,
                            confidence=0.85,
                            cents_off=mean_cents,
                            dynamic_level=dyn,
                        ))
                current_note = note
                start_frame_idx = idx // frame_len
                cents_accumulator = [cents]
                rms_accumulator = [frame_rms]
            else:
                cents_accumulator.append(cents)
                rms_accumulator.append(frame_rms)

        if current_note and current_note != "Silence":
            start_time = (start_frame_idx * frame_len) / sr
            end_time = len(audio) / sr
            mean_rms = float(np.mean(rms_accumulator)) if rms_accumulator else 0.0
            dyn = "soft" if mean_rms < 0.015 else "loud" if mean_rms >= 0.06 else "medium"
            detected_events.append(PerformanceEvent(
                note=current_note,
                start_time=start_time,
                end_time=end_time,
                duration=end_time - start_time,
                confidence=0.85,
                cents_off=float(np.mean(cents_accumulator)) if cents_accumulator else 0.0,
                dynamic_level=dyn,
            ))

        return detected_events
