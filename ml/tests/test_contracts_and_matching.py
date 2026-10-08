from ml.data.contracts import InputMode, MatchStatus, PlayedNoteEvent, TargetNote, pitch_name
from ml.data.matching import evaluate


def test_pitch_name_and_event_contract():
    assert pitch_name(60) == "C4"
    event = PlayedNoteEvent("session", InputMode.MIDI, 60, 100, 250, 0.8, 1.0)
    assert event.pitch_name == "C4"


def test_perfect_and_extra_note_matching():
    targets = [TargetNote("n1", 60, 0, 1, "bar1"), TargetNote("n2", 62, 1, 1, "bar1")]
    played = [
        PlayedNoteEvent("session", InputMode.KEYBOARD, 60, 0),
        PlayedNoteEvent("session", InputMode.KEYBOARD, 62, 600),
        PlayedNoteEvent("session", InputMode.KEYBOARD, 70, 700),
    ]
    result = evaluate(targets, played, 100)
    assert result.pitch_accuracy == 1.0
    assert result.completion_score == 1.0
    assert any(match.status == MatchStatus.EXTRA for match in result.matches)


def test_wrong_pitch_and_missed_note_are_distinguished():
    targets = [TargetNote("n1", 60, 0, 1, "bar1"), TargetNote("n2", 62, 1, 1, "bar1")]
    played = [PlayedNoteEvent("session", InputMode.MIDI, 61, 0)]
    result = evaluate(targets, played, 100)
    statuses = {match.status for match in result.matches}
    assert MatchStatus.WRONG_PITCH in statuses
    assert MatchStatus.MISSED in statuses
