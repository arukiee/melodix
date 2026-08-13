import xml.etree.ElementTree as ET
from typing import Dict, Any, List
from fastapi import HTTPException
from app.services.music_engine.importers.base_importer import BaseImporter

class MusicXMLImporter(BaseImporter):
    def parse(self, file_content: bytes) -> Dict[str, Any]:
        """
        Parses standard MusicXML files extracting title, composer, key, meter, and notes.
        """
        try:
            root = ET.fromstring(file_content)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid or corrupted MusicXML file.")

        title = "Unknown Song"
        composer = "Traditional"
        work_title = root.find(".//work/work-title")
        if work_title is not None and work_title.text:
            title = work_title.text

        creator = root.find(".//identification/creator[@type='composer']")
        if creator is not None and creator.text:
            composer = creator.text

        # Extract basic musical attributes
        beats = 4
        beat_type = 4
        key_sig = "C"
        
        time_node = root.find(".//attributes/time")
        if time_node is not None:
            b = time_node.find("beats")
            bt = time_node.find("beat-type")
            if b is not None and b.text: beats = int(b.text)
            if bt is not None and bt.text: beat_type = int(bt.text)

        key_node = root.find(".//attributes/key")
        if key_node is not None:
            fifths = key_node.find("fifths")
            if fifths is not None and fifths.text:
                f_val = int(fifths.text)
                keys_map = {0: "C", 1: "G", 2: "D", 3: "A", 4: "E", -1: "F", -2: "Bb", -3: "Eb"}
                key_sig = keys_map.get(f_val, "C")

        notes: List[Dict[str, Any]] = []
        measure_idx = 0

        for measure in root.findall(".//measure"):
            for note in measure.findall("note"):
                pitch = note.find("pitch")
                duration = note.find("duration")
                
                # Check for pitch presence (skips rests)
                if pitch is not None:
                    step = pitch.find("step")
                    octave = pitch.find("octave")
                    alter = pitch.find("alter")
                    
                    step_str = step.text if step is not None else "C"
                    octave_str = octave.text if octave is not None else "4"
                    alter_val = int(alter.text) if alter is not None else 0
                    
                    alter_suffix = "#" if alter_val > 0 else "b" if alter_val < 0 else ""
                    note_name = f"{step_str}{alter_suffix}{octave_str}"
                    
                    dur_val = float(duration.text) / 4.0 if duration is not None else 1.0
                    notes.append({
                        "note": note_name,
                        "duration": dur_val,
                        "measure": measure_idx
                    })
            measure_idx += 1

        return {
            "title": title,
            "composer": composer,
            "key_signature": f"{key_sig} Major",
            "time_signature": f"{beats}/{beat_type}",
            "bpm": 60,
            "notes": notes
        }
