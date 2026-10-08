"""Deterministic online matcher used as the keyboard/MIDI research baseline."""

from dataclasses import replace
from statistics import pstdev

from .contracts import MatchStatus, NoteMatch, PlayedNoteEvent, ScoreResult, TargetNote


DEFAULT_TOLERANCES_MS = {"beginner": 250.0, "intermediate": 150.0, "advanced": 100.0}


def match_notes(
    targets: list[TargetNote],
    played: list[PlayedNoteEvent],
    target_bpm: float,
    timing_tolerance_ms: float,
    start_time_ms: int = 0,
) -> list[NoteMatch]:
    """Match each target to one nearest, still-unmatched played event."""
    unmatched = set(range(len(played)))
    matches: list[NoteMatch] = []
    target_times = [start_time_ms + target.start_beat * 60_000 / target_bpm for target in targets]

    for target, target_time in zip(targets, target_times):
        candidates = [
            (abs(played[index].onset_time_ms - target_time), index)
            for index in unmatched
            if abs(played[index].onset_time_ms - target_time) <= timing_tolerance_ms
        ]
        if not candidates:
            matches.append(NoteMatch(None, target.note_id, MatchStatus.MISSED, None, target.midi_pitch, target.section_id))
            continue

        _, played_index = min(candidates)
        unmatched.remove(played_index)
        event = played[played_index]
        error = event.onset_time_ms - target_time
        if event.midi_pitch != target.midi_pitch:
            status = MatchStatus.WRONG_PITCH
        elif error < 0:
            status = MatchStatus.EARLY
        elif error > 0:
            status = MatchStatus.LATE
        else:
            status = MatchStatus.CORRECT
        matches.append(NoteMatch(played_index, target.note_id, status, error, event.midi_pitch, target.section_id))

    matches.extend(
        NoteMatch(index, None, MatchStatus.EXTRA, None, event.midi_pitch, None)
        for index, event in enumerate(played)
        if index in unmatched
    )
    return matches


def score_matches(
    targets: list[TargetNote],
    played: list[PlayedNoteEvent],
    matches: list[NoteMatch],
    target_bpm: float,
    timing_tolerance_ms: float,
) -> ScoreResult:
    target_count = len(targets)
    matched_targets = [match for match in matches if match.target_note_id is not None]
    correct_pitch = [match for match in matched_targets if match.status in {MatchStatus.CORRECT, MatchStatus.EARLY, MatchStatus.LATE}]
    timing_errors = [abs(match.timing_error_ms or 0.0) for match in correct_pitch]
    extras = sum(match.status == MatchStatus.EXTRA for match in matches)

    pitch_accuracy = len(correct_pitch) / target_count if target_count else 0.0
    timing_accuracy = max(0.0, 1.0 - (sum(timing_errors) / len(timing_errors)) / timing_tolerance_ms) if timing_errors else 0.0
    completion_score = len(matched_targets) / target_count if target_count else 0.0
    extra_rate = extras / len(played) if played else 0.0

    onsets = sorted(event.onset_time_ms for event in played)
    intervals = [(right - left) for left, right in zip(onsets, onsets[1:]) if right > left]
    expected_interval = 60_000 / target_bpm if target_bpm else 0.0
    tempo_stability = max(0.0, 1.0 - (pstdev(intervals) / expected_interval if len(intervals) > 1 and expected_interval else 1.0))
    overall = 0.45 * pitch_accuracy + 0.35 * timing_accuracy + 0.10 * completion_score + 0.10 * tempo_stability

    section_scores: dict[str, float] = {}
    for section_id in {target.section_id for target in targets}:
        section_target_ids = {target.note_id for target in targets if target.section_id == section_id}
        section_matches = [match for match in matched_targets if match.target_note_id in section_target_ids]
        section_scores[section_id] = len([m for m in section_matches if m.status != MatchStatus.WRONG_PITCH]) / len(section_target_ids)

    return ScoreResult(pitch_accuracy, timing_accuracy, completion_score, extra_rate, tempo_stability, overall, matches, section_scores)


def evaluate(
    targets: list[TargetNote],
    played: list[PlayedNoteEvent],
    target_bpm: float,
    level: str = "beginner",
    start_time_ms: int = 0,
) -> ScoreResult:
    tolerance = DEFAULT_TOLERANCES_MS.get(level.lower(), DEFAULT_TOLERANCES_MS["beginner"])
    matches = match_notes(targets, played, target_bpm, tolerance, start_time_ms)
    return score_matches(targets, played, matches, target_bpm, tolerance)
