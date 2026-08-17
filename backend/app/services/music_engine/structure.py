import math
from typing import List, Dict, Any

class MusicStructureEngine:
    @staticmethod
    def analyze_structure(notes: List[Any], bpm: float, time_signature: str = "4/4") -> List[Dict[str, Any]]:
        """
        Groups a flat list of notes into distinct musical sections (Intro, Verse, Chorus, etc.)
        based on measures and rhythmic density.
        """
        if not notes:
            return []

        # Calculate measure duration in seconds
        # For 4/4 time, there are 4 quarter notes per measure
        beats_per_measure = int(time_signature.split('/')[0])
        beat_duration = 60.0 / max(bpm, 1.0)
        measure_duration = beats_per_measure * beat_duration

        # Sort notes by start time just in case
        sorted_notes = sorted(notes, key=lambda n: n.start_time)
        song_duration = max(n.end_time for n in sorted_notes)
        total_measures = math.ceil(song_duration / measure_duration)

        # 1. Bucket notes into measures
        measures = [[] for _ in range(total_measures)]
        for note in sorted_notes:
            m_idx = int(note.start_time // measure_duration)
            if m_idx < total_measures:
                measures[m_idx].append(note)

        # 2. Group measures into 8-bar phrases (common pop structure)
        phrases = []
        phrase_length = 8
        
        for p_idx in range(math.ceil(total_measures / phrase_length)):
            start_m = p_idx * phrase_length
            end_m = min(start_m + phrase_length, total_measures)
            
            phrase_notes = []
            for m_idx in range(start_m, end_m):
                phrase_notes.extend(measures[m_idx])
                
            if not phrase_notes:
                continue
                
            # Density is notes per measure in this phrase
            density = len(phrase_notes) / (end_m - start_m)
            
            phrases.append({
                "phrase_index": p_idx,
                "start_measure": start_m,
                "end_measure": end_m,
                "start_time": start_m * measure_duration,
                "end_time": end_m * measure_duration,
                "notes": phrase_notes,
                "density": density
            })

        if not phrases:
            return []

        # 3. Classify sections based on relative density
        # Identify the max density to find the "Chorus"
        max_density = max(p["density"] for p in phrases)
        
        sections = []
        for i, p in enumerate(phrases):
            label = "Verse"
            
            if i == 0:
                label = "Intro"
            elif i == len(phrases) - 1:
                label = "Outro"
            elif p["density"] >= max_density * 0.8:
                label = "Chorus"
            elif p["density"] < max_density * 0.5:
                label = "Bridge"
                
            # Deduplicate sequential labels (e.g., Verse 1, Verse 2)
            existing = sum(1 for s in sections if s["base_label"] == label)
            display_label = f"{label} {existing + 1}" if existing > 0 and label not in ["Intro", "Outro"] else label
            
            sections.append({
                "id": f"section_{i}",
                "base_label": label,
                "display_label": display_label,
                "start_measure": p["start_measure"],
                "end_measure": p["end_measure"],
                "start_time": p["start_time"],
                "end_time": p["end_time"],
                "note_count": len(p["notes"]),
                "notes": p["notes"]
            })

        return sections
