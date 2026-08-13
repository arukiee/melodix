from typing import Dict, Any, List

class MissionBuilder:
    @staticmethod
    def generate_missions(parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Creates learning path mission blocks for the imported song package.
        """
        song_notes = [n["note"] for n in parsed_data.get("notes", [])]
        target_bpm = parsed_data.get("bpm", 60)
        
        return [
            {
                "id": "auto-m1",
                "title": "Listen & Clapping Rhythm",
                "type": "listen",
                "bpm": target_bpm,
                "learningGoal": "Develop timing stability by clapping along.",
                "xpReward": 10
            },
            {
                "id": "auto-m2",
                "title": "Right Hand Practice",
                "type": "right_hand",
                "bpm": target_bpm - 10,
                "learningGoal": "Learn step intervals separately.",
                "xpReward": 25,
                "expectedNotes": song_notes[:8] if len(song_notes) >= 8 else song_notes
            },
            {
                "id": "auto-m3",
                "title": "Complete Song Rehearsal",
                "type": "both_hands",
                "bpm": target_bpm,
                "learningGoal": "Perform the full piece with expression and steady dynamics.",
                "xpReward": 50,
                "expectedNotes": song_notes
            }
        ]
