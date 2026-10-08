"""Convert onset/frame/offset probabilities into polyphonic note events."""


def probabilities_to_notes(predictions, hop_ms: float, onset_threshold: float = 0.5, frame_threshold: float = 0.5, offset_threshold: float = 0.5) -> list[dict]:
    notes = []
    active = {}
    onset, frame, offset, velocity = (prediction.detach().cpu().numpy() for prediction in predictions)
    for time_index in range(onset.shape[0]):
        for key in range(88):
            if key not in active and onset[time_index, key] >= onset_threshold:
                active[key] = (time_index, float(velocity[time_index, key]), float(onset[time_index, key]))
            if key in active and (offset[time_index, key] >= offset_threshold or frame[time_index, key] < frame_threshold):
                start, dynamics, confidence = active.pop(key)
                notes.append({"midi_pitch": key + 21, "onset_time_ms": start * hop_ms, "offset_time_ms": time_index * hop_ms, "velocity": dynamics, "confidence": confidence})
    for key, (start, dynamics, confidence) in active.items():
        notes.append({"midi_pitch": key + 21, "onset_time_ms": start * hop_ms, "offset_time_ms": onset.shape[0] * hop_ms, "velocity": dynamics, "confidence": confidence})
    return notes
