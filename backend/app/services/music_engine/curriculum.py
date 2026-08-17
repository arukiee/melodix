from typing import List, Dict, Any
import uuid

class LearningPlanGenerator:
    @staticmethod
    def generate_curriculum(sections: List[Dict[str, Any]], bpm: float) -> Dict[str, Any]:
        """
        Takes analyzed musical sections and generates a step-by-step curriculum
        consisting of practice phases and missions.
        """
        phases = []
        
        # We will create a Phase for each Section
        for s_idx, section in enumerate(sections):
            display_label = section["display_label"]
            
            missions = []
            
            # Step 1: Right Hand (Melody focus)
            missions.append({
                "id": str(uuid.uuid4()),
                "title": f"Right Hand - {display_label}",
                "type": "right_hand",
                "status": "available" if s_idx == 0 else "locked",
                "progress": 0,
                "bpm": max(40.0, bpm * 0.75), # 75% speed
                "learningGoal": f"Focus on the right hand melody for the {display_label}.",
                "xpReward": 50,
                "expectedEvents": [
                    {
                        "note": n.note_name,
                        "relative_time": n.start_time - section["start_time"],
                        "duration": n.duration
                    }
                    for n in section["notes"]
                    if getattr(n, 'hand', 'RIGHT') in ['RIGHT', 'UNASSIGNED']
                ]
            })

            # Step 2: Left Hand (Bass/Chords focus)
            missions.append({
                "id": str(uuid.uuid4()),
                "title": f"Left Hand - {display_label}",
                "type": "left_hand",
                "status": "locked",
                "progress": 0,
                "bpm": max(40.0, bpm * 0.75), # 75% speed
                "learningGoal": f"Focus on the left hand accompaniment for the {display_label}.",
                "xpReward": 50,
                "expectedEvents": [
                    {
                        "note": n.note_name,
                        "relative_time": n.start_time - section["start_time"],
                        "duration": n.duration
                    }
                    for n in section["notes"]
                    if getattr(n, 'hand', 'RIGHT') == 'LEFT'
                ]
            })
            
            # Step 3: Both Hands together (Slow)
            missions.append({
                "id": str(uuid.uuid4()),
                "title": f"Hands Together (Slow) - {display_label}",
                "type": "both_hands",
                "status": "locked",
                "progress": 0,
                "bpm": max(40.0, bpm * 0.85), # 85% speed
                "learningGoal": f"Combine both hands slowly for the {display_label}.",
                "xpReward": 75,
                "expectedEvents": [
                    {
                        "note": n.note_name,
                        "relative_time": n.start_time - section["start_time"],
                        "duration": n.duration
                    }
                    for n in section["notes"]
                ]
            })
            
            # Step 4: Full Speed Performance
            missions.append({
                "id": str(uuid.uuid4()),
                "title": f"Mastery - {display_label}",
                "type": "performance",
                "status": "locked",
                "progress": 0,
                "bpm": bpm, # 100% speed
                "learningGoal": f"Play the {display_label} at full speed.",
                "xpReward": 100,
                "expectedEvents": [
                    {
                        "note": n.note_name,
                        "relative_time": n.start_time - section["start_time"],
                        "duration": n.duration
                    }
                    for n in section["notes"]
                ]
            })

            phases.append({
                "id": str(uuid.uuid4()),
                "title": f"Phase {s_idx + 1}: {display_label}",
                "missions": missions
            })

        # Add a final Full Song phase
        all_notes = []
        for s in sections:
            all_notes.extend(s["notes"])
            
        full_song_phase = {
            "id": str(uuid.uuid4()),
            "title": f"Phase {len(sections) + 1}: Full Song Performance",
            "missions": [
                {
                    "id": str(uuid.uuid4()),
                    "title": "Full Song Mastery",
                    "type": "performance",
                    "status": "locked",
                    "progress": 0,
                    "bpm": bpm,
                    "learningGoal": "Perform the entire song from start to finish.",
                    "xpReward": 500,
                    "expectedEvents": [
                        {
                            "note": n.note_name,
                            "relative_time": n.start_time, # Absolute time relative to start of song
                            "duration": n.duration
                        }
                        for n in all_notes
                    ]
                }
            ]
        }
        phases.append(full_song_phase)

        return {
            "lesson_id": str(uuid.uuid4()),
            "overall_progress": 0,
            "phases": phases
        }
