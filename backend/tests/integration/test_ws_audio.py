"""Integration tests for audio WebSocket endpoint."""
import json
from starlette.testclient import TestClient

from app.main import create_app
from app.services.voice.stt import FakeSTT
from app.services.voice.tts import FakeTTS
from app.services.voice.vad import VADProcessor
from app.services.voice.pipeline import VoicePipeline


def test_audio_ws_ping_pong():
    """Test ping/pong message handling."""
    app = create_app()
    client = TestClient(app)
    
    with client.websocket_connect("/ws/audio/session1") as ws:
        ws.send_json({"type": "ping"})
        data = ws.receive_json()
        assert data["type"] == "pong"


def test_audio_ws_transcription():
    """Test audio data reception and transcription response."""
    app = create_app()
    client = TestClient(app)
    
    # Fake audio data (16-bit PCM, 1 second of silence)
    audio_data = b"\x00\x00" * 16000  # 16kHz * 2 bytes per sample
    
    with client.websocket_connect("/ws/audio/session1") as ws:
        # Send audio data as binary frame
        ws.send_bytes(audio_data)
        
        # Receive transcription response
        data = ws.receive_json()
        assert data["type"] == "transcription"
        assert isinstance(data["text"], str)


def test_audio_ws_synthesize():
    """Test text synthesis request."""
    app = create_app()
    client = TestClient(app)
    
    with client.websocket_connect("/ws/audio/session1") as ws:
        # Send synthesize request
        ws.send_json({"type": "synthesize", "text": "Test"})
        
        # Receive first audio chunk as binary frame
        audio_response = ws.receive_bytes()
        assert isinstance(audio_response, bytes)
        assert len(audio_response) > 0




def test_audio_ws_multiple_messages():
    """Test sequence of different message types."""
    app = create_app()
    client = TestClient(app)
    
    audio_data = b"\x00\x00" * 16000
    
    with client.websocket_connect("/ws/audio/session1") as ws:
        # Ping
        ws.send_json({"type": "ping"})
        pong = ws.receive_json()
        assert pong["type"] == "pong"
        
        # Audio
        ws.send_bytes(audio_data)
        transcription = ws.receive_json()
        assert transcription["type"] == "transcription"
        
        # Synthesize
        ws.send_json({"type": "synthesize", "text": "Test"})
        audio_response = ws.receive_bytes()
        assert len(audio_response) > 0


def test_audio_ws_empty_audio():
    """Test handling of empty audio data."""
    app = create_app()
    client = TestClient(app)
    
    with client.websocket_connect("/ws/audio/session1") as ws:
        # Send empty audio
        ws.send_bytes(b"")
        
        # Should still receive transcription (from FakeSTT default)
        data = ws.receive_json()
        assert data["type"] == "transcription"


def test_audio_ws_invalid_json():
    """Test handling of invalid JSON messages."""
    app = create_app()
    client = TestClient(app)
    
    with client.websocket_connect("/ws/audio/session1") as ws:
        # Send JSON without type field - should be ignored
        ws.send_json({"no_type": "here"})
        
        # Connection should still be alive
        ws.send_json({"type": "ping"})
        pong = ws.receive_json()
        assert pong["type"] == "pong"


def test_audio_ws_multiple_sessions():
    """Test that different sessions are isolated."""
    app = create_app()
    client = TestClient(app)
    
    with client.websocket_connect("/ws/audio/session1") as ws1:
        with client.websocket_connect("/ws/audio/session2") as ws2:
            # Send to session1
            ws1.send_json({"type": "ping"})
            pong1 = ws1.receive_json()
            assert pong1["type"] == "pong"
            
            # Send to session2
            ws2.send_json({"type": "ping"})
            pong2 = ws2.receive_json()
            assert pong2["type"] == "pong"
