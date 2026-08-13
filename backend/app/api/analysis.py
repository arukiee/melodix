import wave
import io
import numpy as np
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.music_engine.base_analyzer import AnalysisRequest, AnalysisResult
from app.services.music_engine.analyzer import AutocorrelationAnalyzer

router = APIRouter(prefix="/practice", tags=["analysis"])

@router.post("/analyze", response_model=AnalysisResult)
async def analyze_recording(
    file: UploadFile = File(...),
    target_bpm: int = Form(60),
    expected_notes: List[str] = Form([]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Validates uploaded WAV performance file, extracts musical values using AutocorrelationAnalyzer,
    and returns evaluation scores.
    """
    contents = await file.read()
    
    # Try parsing WAV contents
    try:
        with wave.open(io.BytesIO(contents), "rb") as wav_file:
            n_channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            framerate = wav_file.getframerate()
            n_frames = wav_file.getnframes()
            
            raw_frames = wav_file.readframes(n_frames)
            
            # Convert bytes to numpy float array
            if sample_width == 2:
                data = np.frombuffer(raw_frames, dtype=np.int16).astype(np.float32) / 32768.0
            else:
                data = np.frombuffer(raw_frames, dtype=np.uint8).astype(np.float32) / 128.0 - 1.0

            # If stereo, mix to mono
            if n_channels > 1:
                data = data.reshape(-1, n_channels)
                data = data.mean(axis=1)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid WAV file layout: {str(e)}")

    # Coordinate through pluggable AutocorrelationAnalyzer
    analyzer = AutocorrelationAnalyzer()
    request_data = AnalysisRequest(
        audio_data=data,
        sample_rate=framerate,
        expected_notes=expected_notes,
        target_bpm=target_bpm
    )

    try:
        result = analyzer.analyze(request_data)
        
        # Dispatch to AI coaching service
        from app.services.ai_coach.coaching_service import AICoachingService
        ai_feedback = await AICoachingService.generate_coaching(
            song_title="Piano Song",
            scores=result.scores,
            tempo_metrics=result.tempo_metrics,
            mistakes=result.mistakes,
            measure_scores=result.measure_scores
        )
        result.ai_coach_feedback = ai_feedback
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis pipeline failed: {str(e)}")
