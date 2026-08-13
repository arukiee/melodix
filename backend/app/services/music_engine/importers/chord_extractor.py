from typing import List, Dict, Any

class ChordExtractor:
    @staticmethod
    def extract_chords(notes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Groups notes sharing the same onset measure/timestamp and labels chord triads.
        """
        measure_groups: Dict[int, List[str]] = {}
        for note in notes:
            m_idx = note.get("measure", 0)
            note_name = note.get("note", "C4")
            # Strip octave number to isolate note pitch class
            pitch_class = "".join([c for c in note_name if not c.isdigit()])
            measure_groups.setdefault(m_idx, []).append(pitch_class)

        chords = []
        for m_idx, pitch_list in measure_groups.items():
            unique_pitches = sorted(list(set(pitch_list)))
            chord_name = "Unknown Chord"

            # Simple Triad Matching logic
            if "C" in unique_pitches and "E" in unique_pitches and "G" in unique_pitches:
                chord_name = "C Major Triad"
            elif "G" in unique_pitches and "B" in unique_pitches and "D" in unique_pitches:
                chord_name = "G Major Triad"
            elif "F" in unique_pitches and "A" in unique_pitches and "C" in unique_pitches:
                chord_name = "F Major Triad"
            elif len(unique_pitches) >= 2:
                chord_name = f"Dyad ({'-'.join(unique_pitches)})"

            chords.append({
                "measure": m_idx,
                "pitches": unique_pitches,
                "detected_chord": chord_name
            })
            
        return chords
