from typing import Dict, Any, List
from app.services.music_engine.base_analyzer import ExpectedEvent

class TimelineBuilder:
    @staticmethod
    def build_expected_events(parsed_data: Dict[str, Any]) -> List[ExpectedEvent]:
        """
        Translates raw parsed notes into expected timeline events with start times and durations.
        """
        expected_events = []
        current_time = 0.0
        
        # Mapping duration factor based on tempo bpm
        tempo_bpm = parsed_data.get("bpm", 60)
        beat_duration = 60.0 / tempo_bpm
        
        for note_data in parsed_data.get("notes", []):
            duration_sec = note_data["duration"] * beat_duration
            expected_events.append(
                ExpectedEvent(
                    note=note_data["note"],
                    relative_time=current_time,
                    duration=duration_sec
                )
            )
            current_time += duration_sec
            
        return expected_events
