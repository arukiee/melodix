import json
import logging
from typing import Dict, Any, List
from app.services.music_engine.importers.base_importer import BaseImporter
from app.services.ai_coach.ollama import generate_ollama_completion

logger = logging.getLogger("melodix.youtube_importer")

class YouTubeImporter(BaseImporter):
    """
    Parses YouTube metadata, queries the local Ollama LLM to analyze the song's musical structure,
    and procedurally constructs a playable piano arrangement (melody + accompaniment) matching the song's chords/tempo.
    """

    def parse(self, file_content: bytes) -> Dict[str, Any]:
        try:
            meta = json.loads(file_content.decode('utf-8'))
        except Exception:
            meta = {"title": "YouTube Song", "artist": "Traditional", "duration": 120}

        title = meta.get("title", "YouTube Song")
        artist = meta.get("artist", "Unknown Artist")
        
        # 1. Query Ollama for musical analysis
        analysis = self._query_ai_analysis(title, artist)
        
        # 2. Build chord mappings
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
        sections_out = []
        
        # 3. Procedurally generate piano arrangement matching structural sections
        for section in analysis["sections"]:
            sec_start = measure
            # Generate 4 measures for each structural section using the chord progression
            for _ in range(4):
                for chord_name in analysis["chords"]:
                    # Clean chord name
                    base_chord = chord_name.replace("7", "").replace("9", "").strip()
                    mapping = chord_mappings.get(base_chord, (["C4", "E4", "G4"], "C3"))
                    rh_notes, lh_root = mapping
                    
                    # Beat 0: Left Hand Bass Note
                    notes.append({"note": lh_root, "duration": 4.0, "measure": measure})
                    
                    # Beat 0,1,2,3: Right Hand Melody Arpeggio
                    notes.append({"note": rh_notes[0], "duration": 1.0, "measure": measure})
                    notes.append({"note": rh_notes[1], "duration": 1.0, "measure": measure})
                    notes.append({"note": rh_notes[2], "duration": 1.0, "measure": measure})
                    notes.append({"note": rh_notes[1], "duration": 1.0, "measure": measure})
                    
                    measure += 1
            
            sections_out.append({
                "id": f"sec-{section.lower()}",
                "title": section,
                "start_measure": sec_start,
                "end_measure": measure - 1
            })

        steps = self._generate_12_stage_steps(sections_out)

        return {
            "title": title,
            "composer": artist,
            "key_signature": analysis["key_signature"],
            "time_signature": analysis["time_signature"],
            "bpm": analysis["bpm"],
            "notes": notes,
            "sections": sections_out,
            "steps": steps
        }

    def _query_ai_analysis(self, title: str, artist: str) -> Dict[str, Any]:
        """Queries local Ollama to analyze song structure, key, and chords."""
        prompt = f"""
        Analyze this song and provide its typical musical structure:
        Title: {title}
        Artist: {artist}

        Provide your output ONLY as a single JSON object with this exact structure:
        {{
          "bpm": 100,
          "key_signature": "G Major",
          "time_signature": "4/4",
          "sections": ["Intro", "Verse", "Chorus"],
          "chords": ["G", "D", "Em", "C"]
        }}
        Do not add any Markdown fences or explanations. Return raw JSON text only.
        """
        
        fallback = {
            "bpm": 90,
            "key_signature": "C Major",
            "time_signature": "4/4",
            "sections": ["Intro", "Verse", "Chorus", "Ending"],
            "chords": ["C", "G", "Am", "F"]
        }

        # Run synchronously in current loop using run_until_complete or just running task
        try:
            # We run the async Ollama completion call synchronously
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is already running, run it as a future task
                response_txt = loop.run_until_complete(generate_ollama_completion(prompt))
            else:
                response_txt = asyncio.run(generate_ollama_completion(prompt))

            if response_txt:
                parsed = json.loads(response_txt)
                return {
                    "bpm": int(parsed.get("bpm", fallback["bpm"])),
                    "key_signature": str(parsed.get("key_signature", fallback["key_signature"])),
                    "time_signature": str(parsed.get("time_signature", fallback["time_signature"])),
                    "sections": list(parsed.get("sections", fallback["sections"])),
                    "chords": list(parsed.get("chords", fallback["chords"]))
                }
        except Exception as e:
            logger.error(f"Ollama YouTube music analysis failed, using fallback: {e}")

        return fallback

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
