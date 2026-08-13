import re
from typing import Dict, Any, List
from app.services.music_engine.importers.base_importer import BaseImporter

class ChordSheetImporter(BaseImporter):
    """
    Parses Ultimate Guitar chord sheets (which contain lyrics and chords in [ch]Tags[/ch])
    and procedurally arranges them into playable piano notes (melody + simple accompaniment).
    """

    def parse(self, file_content: bytes) -> Dict[str, Any]:
        text = file_content.decode('utf-8', errors='ignore')
        
        # Extract all chords inside [ch]...[/ch] tags
        chords = re.findall(r'\[ch\](.*?)\[/ch\]', text)
        
        # If no chords found, try to extract words that look like chords (e.g. C, G, Am, F)
        if not chords:
            # simple regex for common chords
            chords = re.findall(r'\b([A-G][#b]?(?:m|maj|min|dim|aug|sus)?(?:\d)?)\b', text)

        # Clean duplicates or keep progression structure
        # Limit to first 24 chords for a reasonable length lesson
        progression = chords[:24] if chords else ["C", "G", "Am", "F"]
        
        # Map of chords to piano notes (Root, Third, Fifth)
        chord_mappings = {
            "C":   (["C4", "E4", "G4"], "C3"),
            "C#":  (["C#4", "F4", "G#4"], "C#3"),
            "Db":  (["C#4", "F4", "G#4"], "C#3"),
            "D":   (["D4", "F#4", "A4"], "D3"),
            "D#":  (["D#4", "G4", "A#4"], "D#3"),
            "Eb":  (["D#4", "G4", "A#4"], "D#3"),
            "E":   (["E4", "G#4", "B4"], "E3"),
            "F":   (["F4", "A4", "C5"], "F3"),
            "F#":  (["F#4", "A#4", "C#5"], "F#3"),
            "Gb":  (["F#4", "A#4", "C#5"], "F#3"),
            "G":   (["G4", "B4", "D5"], "G3"),
            "G#":  (["G#4", "C5", "D#5"], "G#3"),
            "Ab":  (["G#4", "C5", "D#5"], "G#3"),
            "A":   (["A4", "C#5", "E5"], "A3"),
            "A#":  (["A#4", "D5", "F5"], "A#3"),
            "Bb":  (["A#4", "D5", "F5"], "A#3"),
            "B":   (["B4", "D#5", "F#5"], "B3"),
            "Cm":  (["C4", "D#4", "G4"], "C3"),
            "Dm":  (["D4", "F4", "A4"], "D3"),
            "Em":  (["E4", "G4", "B4"], "E3"),
            "Fm":  (["F4", "G#4", "C5"], "F3"),
            "Gm":  (["G4", "A#4", "D5"], "G3"),
            "Am":  (["A4", "C5", "E5"], "A3"),
            "Bm":  (["B4", "D5", "F#5"], "B3"),
        }

        notes = []
        measure = 0
        
        # Procedurally build expected note events from the chord progression
        for chord_name in progression:
            # Normalize chord name (strip extensions like 7, sus4, slash chords to find basic mapping)
            base_chord = re.sub(r'(?:7|9|11|13|sus\d?|add\d?|/\w+)', '', chord_name).strip()
            
            mapping = chord_mappings.get(base_chord, (["C4", "E4", "G4"], "C3"))
            right_hand_pitches, left_hand_root = mapping
            
            # Place notes in the measure:
            # Beat 0: Left hand root (held for 4 beats)
            # Beat 0: Right hand pitch 1 (1 beat)
            # Beat 1: Right hand pitch 2 (1 beat)
            # Beat 2: Right hand pitch 3 (1 beat)
            # Beat 3: Right hand pitch 2 (1 beat)
            
            # Left Hand (bass root accompaniment)
            # We prefix bass notes to be played by LH, but for the note sequence
            # we just generate them sequentially or label them
            notes.append({"note": left_hand_root, "duration": 4.0, "measure": measure})
            
            # Right Hand (melody arpeggio)
            notes.append({"note": right_hand_pitches[0], "duration": 1.0, "measure": measure})
            notes.append({"note": right_hand_pitches[1], "duration": 1.0, "measure": measure})
            notes.append({"note": right_hand_pitches[2], "duration": 1.0, "measure": measure})
            notes.append({"note": right_hand_pitches[1], "duration": 1.0, "measure": measure})
            
            measure += 1

        # If no chords were found or generated
        if not notes:
            notes = [
                {"note": "C4", "duration": 1.0, "measure": 0},
                {"note": "E4", "duration": 1.0, "measure": 0},
                {"note": "G4", "duration": 2.0, "measure": 0},
            ]

        sections = self._chunk_into_sections(notes)
        steps = self._generate_12_stage_steps(sections)

        return {
            "title": "Chords Imported Song",
            "composer": "Ultimate Guitar",
            "key_signature": "C Major",
            "time_signature": "4/4",
            "bpm": 80,
            "notes": notes,
            "sections": sections,
            "steps": steps
        }

    def _chunk_into_sections(self, notes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        sections = []
        if not notes:
            return sections
        max_measure = max([n.get("measure", 0) for n in notes])
        for i in range(0, max_measure + 1, 4):
            sections.append({
                "id": f"sec-{i}",
                "title": "Intro" if i == 0 else f"Section {i//4 + 1}",
                "start_measure": i,
                "end_measure": min(max_measure, i + 3)
            })
        return sections

    def _generate_12_stage_steps(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        stages = [
            {"id": 1, "name": "Listen", "type": "listen", "tempo_pct": 50, "hand": "both"},
            {"id": 2, "name": "Watch", "type": "watch", "tempo_pct": 50, "hand": "both"},
            {"id": 3, "name": "Single Notes", "type": "interactive_single", "tempo_pct": 0, "hand": "both"},
            {"id": 4, "name": "Right Hand (Slow)", "type": "practice", "tempo_pct": 40, "hand": "right"},
            {"id": 5, "name": "Right Hand (Target)", "type": "practice", "tempo_pct": 100, "hand": "right"},
            {"id": 6, "name": "Left Hand (Slow)", "type": "practice", "tempo_pct": 40, "hand": "left"},
            {"id": 7, "name": "Left Hand (Target)", "type": "practice", "tempo_pct": 100, "hand": "left"},
            {"id": 8, "name": "Hands Together (Slow)", "type": "practice", "tempo_pct": 40, "hand": "both"},
            {"id": 9, "name": "Hands Together (Mid)", "type": "practice", "tempo_pct": 70, "hand": "both"},
            {"id": 10, "name": "Hands Together (Target)", "type": "practice", "tempo_pct": 100, "hand": "both"},
        ]
        steps = []
        for sec in sections:
            for st in stages:
                steps.append({
                    "id": f"{sec['id']}-stage-{st['id']}",
                    "section_id": sec["id"],
                    "stage_id": st["id"],
                    "name": f"{sec['title']} - {st['name']}",
                    "type": st["type"],
                    "tempo_pct": st["tempo_pct"],
                    "hand": st["hand"]
                })
        return steps
