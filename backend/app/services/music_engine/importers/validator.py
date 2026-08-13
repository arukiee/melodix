import re
from typing import Dict, Any, List

# Time signatures commonly used in Western music
STANDARD_TIME_SIGS = {"2/2", "2/4", "3/4", "4/4", "6/8", "9/8", "12/8", "3/8", "5/4", "6/4"}

class ImportValidator:
    @staticmethod
    def validate(song_data: Dict[str, Any]) -> List[str]:
        """
        Validates parsed song details for timing, tempo, and notes anomalies.
        Returns a list of warning/error messages.
        """
        errors = []

        # 1. Title check
        if not song_data.get("title") or song_data["title"].strip() == "":
            errors.append("Song title is missing or empty.")
        
        # 2. Tempo check
        bpm = song_data.get("bpm", 60)
        if bpm < 30 or bpm > 240:
            errors.append(f"Invalid tempo BPM: {bpm}. Must be between 30 and 240.")

        # 3. Time Signature validation
        time_sig = song_data.get("time_signature", "4/4")
        if not re.match(r"^\d+/\d+$", time_sig):
            errors.append(f"Invalid time signature format: {time_sig}. Expected e.g. 4/4 or 3/4.")
        elif time_sig not in STANDARD_TIME_SIGS:
            errors.append(f"Unusual time signature: {time_sig}. Import will proceed but verify correctness.")

        # 4. Key signature check
        if not song_data.get("key_signature"):
            errors.append("Missing key signature. Defaulting to C Major.")

        # 5. Notes checks
        notes = song_data.get("notes", [])
        if not notes:
            errors.append("Song contains no parsed notes.")
        
        if len(notes) > 500:
            errors.append(f"Large song detected ({len(notes)} notes). Import may take longer.")

        for idx, note in enumerate(notes):
            if "note" not in note:
                errors.append(f"Note entry at index {idx} is missing note name.")
            if "duration" not in note or note["duration"] <= 0:
                errors.append(f"Note entry at index {idx} has invalid duration: {note.get('duration')}.")
            if "measure" not in note or note["measure"] < 0:
                errors.append(f"Note entry at index {idx} has invalid measure index: {note.get('measure')}.")

        return errors

