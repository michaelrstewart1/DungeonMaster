"""WebSocket endpoint for audio streaming and processing."""
import json
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.voice.pipeline import VoicePipeline
from app.services.voice.stt import FakeSTT
from app.services.voice.tts import FakeTTS
from app.services.voice.vad import VADProcessor

router = APIRouter(prefix="/ws", tags=["websocket"])

# Initialize voice services (with Fake implementations for now)
_stt = FakeSTT()
_tts = FakeTTS()
_vad = VADProcessor()
_pipeline = VoicePipeline(stt=_stt, tts=_tts, vad=_vad)


@router.websocket("/audio/{session_id}")
async def websocket_audio_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for audio streaming.

    Handles:
    - Binary frames: Raw audio data from client mic
      → Processed through VAD → STT pipeline
      → Returns JSON: {"type": "transcription", "text": str}
    - JSON messages:
      - {"type": "ping"} → {"type": "pong"}
      - {"type": "synthesize", "text": str} → Binary audio frames
    """
    await websocket.accept()

    try:
        while True:
            # Receive data - can be either text (JSON) or binary
            message = await websocket.receive()

            # Handle binary frames (audio data)
            if "bytes" in message:
                audio_bytes = message["bytes"]
                # Process audio through VAD + STT pipeline (even if empty)
                try:
                    transcription = await _pipeline.process_audio_input(audio_bytes)
                    await websocket.send_json(
                        {
                            "type": "transcription",
                            "text": transcription,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                except Exception:
                    # On error, still send a message to keep connection alive
                    await websocket.send_json(
                        {
                            "type": "transcription",
                            "text": "",
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

            # Handle JSON messages
            elif "text" in message:
                try:
                    text_data = message.get("text", "")
                    data = json.loads(text_data)

                    msg_type = data.get("type")

                    # Handle ping
                    if msg_type == "ping":
                        await websocket.send_json(
                            {"type": "pong", "timestamp": datetime.now().isoformat()}
                        )

                    # Handle synthesize
                    elif msg_type == "synthesize":
                        text = data.get("text", "")
                        if text:
                            # Use real TTS from app state when available
                            tts_provider = getattr(websocket.app.state, "tts", _tts)
                            # Stream audio chunks
                            async for chunk in tts_provider.synthesize_stream(text):
                                await websocket.send_bytes(chunk.data)
                            # Signal end of audio stream so client can play it
                            await websocket.send_json({"type": "audio_done"})

                except (json.JSONDecodeError, ValueError):
                    # Ignore malformed messages
                    pass

    except WebSocketDisconnect:
        pass
    except Exception:
        # Silently close on any other error
        pass



