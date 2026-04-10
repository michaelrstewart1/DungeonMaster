"""Tests for Speech-to-Text (STT) services."""
import pytest
from typing import AsyncGenerator

from app.services.voice.stt import (
    STTProvider,
    TranscriptionResult,
    FakeSTT,
    WhisperSTT,
)


class TestTranscriptionResult:
    """Tests for TranscriptionResult dataclass."""

    def test_create_transcription_result(self) -> None:
        """Should create a TranscriptionResult with all fields."""
        result = TranscriptionResult(
            text="Hello, I attack the goblin",
            language="en",
            confidence=0.95,
            duration_seconds=2.5,
        )
        assert result.text == "Hello, I attack the goblin"
        assert result.language == "en"
        assert result.confidence == 0.95
        assert result.duration_seconds == 2.5


class TestFakeSTT:
    """Tests for FakeSTT mock implementation."""

    @pytest.mark.asyncio
    async def test_fake_stt_returns_configured_responses(self) -> None:
        """FakeSTT should return configured responses in order."""
        responses = ["Hello", "World"]
        stt = FakeSTT(responses=responses)

        result1 = await stt.transcribe(b"audio_data_1")
        assert result1.text == "Hello"

        result2 = await stt.transcribe(b"audio_data_2")
        assert result2.text == "World"

    @pytest.mark.asyncio
    async def test_fake_stt_default_response(self) -> None:
        """FakeSTT should return default response when not configured."""
        stt = FakeSTT()
        result = await stt.transcribe(b"audio_data")
        assert result.text == "Hello, I attack the goblin"

    @pytest.mark.asyncio
    async def test_fake_stt_tracks_received_audio(self) -> None:
        """FakeSTT should track all received audio bytes."""
        stt = FakeSTT()
        audio1 = b"audio_chunk_1"
        audio2 = b"audio_chunk_2"

        await stt.transcribe(audio1)
        await stt.transcribe(audio2)

        assert len(stt.received_audio) == 2
        assert stt.received_audio[0] == audio1
        assert stt.received_audio[1] == audio2

    @pytest.mark.asyncio
    async def test_fake_stt_returns_valid_transcription_result(self) -> None:
        """FakeSTT.transcribe should return valid TranscriptionResult."""
        stt = FakeSTT(responses=["Test transcription"])
        result = await stt.transcribe(b"audio_data", language="en-US")

        assert isinstance(result, TranscriptionResult)
        assert result.text == "Test transcription"
        assert result.language == "en-US"
        assert isinstance(result.confidence, float)
        assert 0.0 <= result.confidence <= 1.0
        assert isinstance(result.duration_seconds, float)
        assert result.duration_seconds >= 0.0

    @pytest.mark.asyncio
    async def test_fake_stt_respects_language_parameter(self) -> None:
        """FakeSTT should accept language parameter."""
        stt = FakeSTT()
        result = await stt.transcribe(b"audio_data", language="es")
        assert result.language == "es"

    @pytest.mark.asyncio
    async def test_fake_stt_streaming_transcription(self) -> None:
        """FakeSTT should support streaming transcription."""
        partial_results = ["Hello", "Hello world", "Hello world,", "Hello world, I"]
        stt = FakeSTT()
        stt.stream_responses = partial_results

        chunks = []
        async for chunk in stt.transcribe_stream(b"audio_data"):
            chunks.append(chunk)

        assert len(chunks) == len(partial_results)
        assert chunks == partial_results

    @pytest.mark.asyncio
    async def test_fake_stt_call_count(self) -> None:
        """FakeSTT should track number of transcribe calls."""
        stt = FakeSTT()
        assert stt._call_count == 0

        await stt.transcribe(b"audio_data_1")
        assert stt._call_count == 1

        await stt.transcribe(b"audio_data_2")
        assert stt._call_count == 2


class TestWhisperSTT:
    """Tests for WhisperSTT implementation."""

    def test_whisper_stt_initialization_with_defaults(self) -> None:
        """WhisperSTT should initialize with default parameters."""
        stt = WhisperSTT()
        assert stt.model_size == "base"
        assert stt.device == "cpu"

    def test_whisper_stt_initialization_with_custom_params(self) -> None:
        """WhisperSTT should accept custom model size and device."""
        stt = WhisperSTT(model_size="small", device="cuda")
        assert stt.model_size == "small"
        assert stt.device == "cuda"

    @pytest.mark.asyncio
    async def test_whisper_stt_empty_audio_error_handling(self) -> None:
        """WhisperSTT should handle empty audio gracefully."""
        stt = WhisperSTT()

        with pytest.raises(ValueError):
            await stt.transcribe(b"")

    @pytest.mark.asyncio
    async def test_whisper_stt_streaming_transcription(self) -> None:
        """WhisperSTT should support streaming transcription."""
        stt = WhisperSTT()
        chunks = []

        async for chunk in stt.transcribe_stream(b"audio_data"):
            chunks.append(chunk)
            if len(chunks) >= 3:  # Prevent infinite loop
                break

        assert len(chunks) > 0
        assert all(isinstance(chunk, str) for chunk in chunks)


class TestSTTProviderInterface:
    """Tests for STTProvider abstract interface."""

    def test_stt_provider_is_abstract(self) -> None:
        """STTProvider should be an abstract base class."""
        with pytest.raises(TypeError):
            STTProvider()  # type: ignore

    @pytest.mark.asyncio
    async def test_fake_stt_implements_stt_provider(self) -> None:
        """FakeSTT should implement STTProvider interface."""
        stt = FakeSTT()
        assert isinstance(stt, STTProvider)

    @pytest.mark.asyncio
    async def test_whisper_stt_implements_stt_provider(self) -> None:
        """WhisperSTT should implement STTProvider interface."""
        stt = WhisperSTT()
        assert isinstance(stt, STTProvider)
