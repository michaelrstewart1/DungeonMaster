"""Real STT wiring — audio WS must use the app-state voice pipeline."""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.voice.pipeline import VoicePipeline
from app.services.voice.stt import FakeSTT, OpenAIWhisperSTT
from app.services.voice.tts import FakeTTS
from app.services.voice.vad import VADProcessor


class RecordingSTT(FakeSTT):
    def __init__(self):
        super().__init__(responses=["I attack the goblin"])
        self.received: list[bytes] = []

    async def transcribe(self, audio_bytes, language="en"):
        self.received.append(audio_bytes)
        return await super().transcribe(audio_bytes, language)


def test_audio_ws_uses_app_state_pipeline():
    stt = RecordingSTT()
    try:
        with TestClient(app) as client:
            # Set after startup — lifespan wires its own pipeline
            app.state.voice_pipeline = VoicePipeline(stt=stt, tts=FakeTTS(), vad=VADProcessor())
            with client.websocket_connect("/ws/audio/test-session") as ws:
                ws.send_bytes(b"\x00\x01fake-webm-audio")
                msg = ws.receive_json()
                assert msg["type"] == "transcription"
                assert msg["text"] == "I attack the goblin"
        assert stt.received and stt.received[0].endswith(b"fake-webm-audio")
    finally:
        if hasattr(app.state, "voice_pipeline"):
            del app.state.voice_pipeline


def test_audio_ws_falls_back_to_module_pipeline_without_state():
    if hasattr(app.state, "voice_pipeline"):
        del app.state.voice_pipeline
    with TestClient(app) as client:
        with client.websocket_connect("/ws/audio/test-session") as ws:
            ws.send_bytes(b"\x00\x01audio")
            msg = ws.receive_json()
            assert msg["type"] == "transcription"


class TestOpenAIWhisperSTT:
    @pytest.mark.asyncio
    async def test_rejects_empty_audio(self):
        stt = OpenAIWhisperSTT(api_key="sk-test")
        with pytest.raises(ValueError):
            await stt.transcribe(b"")

    @pytest.mark.asyncio
    async def test_transcribe_posts_multipart(self, monkeypatch):
        stt = OpenAIWhisperSTT(api_key="sk-test")
        captured = {}

        class FakeResponse:
            def raise_for_status(self):
                pass

            def json(self):
                return {"text": " Hello adventurer ", "duration": 1.5}

        class FakeClient:
            async def post(self, url, data=None, files=None):
                captured.update(url=url, data=data, files=files)
                return FakeResponse()

        stt._client = FakeClient()
        result = await stt.transcribe(b"webm-bytes", language="en")

        assert result.text == "Hello adventurer"
        assert result.duration_seconds == 1.5
        assert captured["data"]["model"] == "whisper-1"
        assert captured["files"]["file"][1] == b"webm-bytes"
