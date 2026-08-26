from typing import List, Dict, Any, Tuple, Optional

# Pitch class maps
NOTE_PITCH_CLASSES = {
    "C": 0, "C#": 1, "DB": 1,
    "D": 2, "D#": 3, "EB": 3,
    "E": 4, "F": 5, "F#": 6, "GB": 6,
    "G": 7, "G#": 8, "AB": 8,
    "A": 9, "A#": 10, "BB": 10,
    "B": 11
}

PITCH_CLASS_NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]

# Standard chord templates (pitch class intervals from root)
CHORD_TEMPLATES = {
    "Major Triad": ([0, 4, 7], ""),
    "Minor Triad": ([0, 3, 7], "m"),
    "Diminished Triad": ([0, 3, 6], "dim"),
    "Augmented Triad": ([0, 4, 8], "aug"),
    "Sus2": ([0, 2, 7], "sus2"),
    "Sus4": ([0, 5, 7], "sus4"),
    "Major 7th": ([0, 4, 7, 11], "Maj7"),
    "Minor 7th": ([0, 3, 7, 10], "m7"),
    "Dominant 7th": ([0, 4, 7, 10], "7"),
    "Diminished 7th": ([0, 3, 6, 9], "dim7"),
    "Half-Diminished 7th": ([0, 3, 6, 10], "m7b5"),
    "Major 6th": ([0, 4, 7, 9], "6"),
    "Minor 6th": ([0, 3, 7, 9], "m6"),
}


def parse_pitch_class(note_name: str) -> Tuple[Optional[str], Optional[int], int]:
    """
    Parses a note string (e.g. 'C#4', 'Eb3', 'G4') into (pitch_name, pitch_class, octave).
    Correctly preserves accidentals (# and b).
    """
    if not note_name:
        return None, None, 4

    clean = note_name.strip().upper()
    octave = 4
    # Extract trailing digits for octave
    digits = []
    i = len(clean) - 1
    while i >= 0 and (clean[i].isdigit() or clean[i] == '-'):
        digits.insert(0, clean[i])
        i -= 1

    if digits:
        try:
            octave = int("".join(digits))
        except ValueError:
            octave = 4
        pitch_str = clean[:i+1]
    else:
        pitch_str = clean

    pc = NOTE_PITCH_CLASSES.get(pitch_str)
    if pc is not None:
        display_name = PITCH_CLASS_NAMES[pc]
        return display_name, pc, octave

    # Fallback heuristic
    if pitch_str and pitch_str[0] in NOTE_PITCH_CLASSES:
        first_pc = NOTE_PITCH_CLASSES[pitch_str[0]]
        return PITCH_CLASS_NAMES[first_pc], first_pc, octave

    return None, None, octave


class ChordExtractor:
    @staticmethod
    def extract_chords(notes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Groups notes sharing the same onset measure/timestamp and labels chords using pitch class matching.
        Preserves accidentals and detects inversions.
        """
        measure_groups: Dict[int, List[Dict[str, Any]]] = {}
        for note in notes:
            m_idx = note.get("measure", 0)
            measure_groups.setdefault(m_idx, []).append(note)

        chords = []
        for m_idx, group_notes in measure_groups.items():
            parsed_notes = []
            for n in group_notes:
                n_str = n.get("note", "C4")
                p_name, pc, octave = parse_pitch_class(n_str)
                if pc is not None:
                    midi = pc + (octave + 1) * 12
                    parsed_notes.append({"name": p_name, "pc": pc, "midi": midi})

            if not parsed_notes:
                continue

            unique_pcs = sorted(list(set(n["pc"] for n in parsed_notes)))
            unique_names = sorted(list(set(n["name"] for n in parsed_notes)))

            # Find bass note (lowest MIDI pitch)
            sorted_by_pitch = sorted(parsed_notes, key=lambda x: x["midi"])
            bass_pc = sorted_by_pitch[0]["pc"]
            bass_name = sorted_by_pitch[0]["name"]

            detected_chord = "Unknown Chord"
            best_score = 0.0

            if len(unique_pcs) >= 3:
                # Try matching all candidate roots
                for root_pc in unique_pcs:
                    root_name = PITCH_CLASS_NAMES[root_pc]
                    shifted_pcs = set((pc - root_pc) % 12 for pc in unique_pcs)

                    for full_name, (template_pcs, suffix) in CHORD_TEMPLATES.items():
                        t_set = set(template_pcs)
                        match_count = len(shifted_pcs.intersection(t_set))
                        extra_count = len(shifted_pcs - t_set)
                        score = (match_count / len(t_set)) - (extra_count * 0.25)

                        if score > best_score and match_count >= 3:
                            best_score = score
                            base_label = f"{root_name} {full_name}" if not suffix else f"{root_name}{suffix} ({full_name})"
                            if root_pc != bass_pc:
                                base_label += f"/{bass_name}"
                            detected_chord = base_label

            elif len(unique_pcs) == 2:
                detected_chord = f"Dyad ({'-'.join(unique_names)})"

            chords.append({
                "measure": m_idx,
                "pitches": unique_names,
                "detected_chord": detected_chord if best_score >= 0.70 or len(unique_pcs) == 2 else f"Dyad ({'-'.join(unique_names)})"
            })

        return chords

