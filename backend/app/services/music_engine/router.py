# backend/app/services/music_engine/router.py

import json
from typing import List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from .engine import audio_stream, NoteEvent

router = APIRouter()

@router.websocket("/ws/music")
async def music_ws(websocket: WebSocket):
    await websocket.accept()
    try:
        async for note in audio_stream():
            await websocket.send_text(note.json())
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.close(code=1011)
