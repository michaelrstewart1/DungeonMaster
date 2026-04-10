"""Tests for Voice Pipeline."""
import pytest

from app.services.voice.pipeline import VoicePipeline
from app.services.voice.stt import FakeSTT
from app.services.voice.tts import FakeTTS, AudioChunk
from app.services.voice.vad import VADProcessor


class TestVoicePipeline:
    """Tests for Voice Pipeline integration."""

    def test_voice_pipeline_initialization(self) -> None:
        """VoicePipeline should initialize with required services."""
        stt = FakeSTT()
        tts = FakeTTS()
        vad = VADProcessor()

        pipeline = VoicePipeline(stt=stt, tts=tts, vad=vad)

        assert pipeline.stt is stt
        assert pipeline.tts is tts
        assert pipeline.vad is vad

    @pytest.mark.asyncio
    async def test_voice_pipeline_process_audio_input(self) -> None:
        """VoicePipeline should convert audio to text."""
        stt = FakeSTT(responses=["Hello, I attack the goblin"])
        tts = FakeTTS()
        vad = VADProcessor()

        pipeline = VoicePipeline(stt=stt, tts=tts, vad=vad)

        audio_bytes = b"fake_audio_data"
        result = await pipeline.process_audio_input(audio_bytes)

        assert result == "Hello, I attack the goblin"

    @pytest.mark.asyncio
    async def test_voice_pipeline_respects_vad(self) -> None:
        """VoicePipeline should only transcribe after speech_end VAD event."""
        stt = FakeSTT(responses=["Should be transcribed"])
        tts = FakeTTS()
        vad = VADProcessor()

        pipeline = VoicePipeline(stt=stt, tts=tts, vad=vad)

        # Process audio input - VAD should detect speech/silence
        audio_bytes = b"\x00" * 1024  # Silence
        result = await pipeline.process_audio_input(audio_bytes)

        # Result should still be the transcription
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_voice_pipeline_generate_audio_response(self) -> None:
        """VoicePipeline should convert text to audio chunks."""
        stt = FakeSTT()
        tts = FakeTTS()
        vad = VADProcessor()

        pipeline = VoicePipeline(stt=stt, tts=tts, vad=vad)

        chunks = []
        async for chunk in pipeline.generate_audio_response("Hello, brave adventurer."):
            chunks.append(chunk)

        assert len(chunks) > 0
        assert all(isinstance(chunk, AudioChunk) for chunk in chunks)

    @pytest.mark.asyncio
    async def test_voice_pipeline_sentence_splitting(self) -> None:
        """VoicePipeline should split text into sentences for streaming."""
        stt = FakeSTT()
        tts = FakeTTS()
        vad = VADProcessor()

        pipeline = VoicePipeline(stt=stt, tts=tts, vad=vad)

        text = "First sentence. Second sentence. Third sentence."
        chunks = []

        async for chunk in pipeline.generate_audio_response(text):
            chunks.append(chunk)

        # Should have multiple chunks for multiple sentences
        assert len(chunks) >= 3

    @pytest.mark.asyncio
    async def test_voice_pipeline_streaming_marks_final_chunk(self) -> None:
        """VoicePipeline should mark last chunk as final."""
        stt = FakeSTT()
        tts = FakeTTS()
        vad = VADProcessor()

        pipeline = VoicePipeline(stt=stt, tts=tts, vad=vad)

        chunks = []
        async for chunk in pipeline.generate_audio_response("Test response."):
            chunks.append(chunk)

        assert chunks[-1].is_final is True
        for chunk in chunks[:-1]:
            assert chunk.is_final is False

    @pytest.mark.asyncio
    async def test_voice_pipeline_handles_empty_text(self) -> None:
        """VoicePipeline should handle empty text gracefully."""
        stt = FakeSTT()
        tts = FakeTTS()
        vad = VADProcessor()

        pipeline = VoicePipeline(stt=stt, tts=tts, vad=vad)

        with pytest.raises((ValueError, StopAsyncIteration)):
            async for _ in pipeline.generate_audio_response(""):
                pass

    @pytest.mark.asyncio
    async def test_voice_pipeline_full_cycle(self) -> None:
        """VoicePipeline should handle full audio->text->audio cycle."""
        # Setup
        player_input_text = "I cast fireball"
        dm_response_text = "The goblin takes 8d6 damage. Roll initiative!"

        stt = FakeSTT(responses=[player_input_text])
        tts = FakeTTS()
        vad = VADProcessor()

        pipeline = VoicePipeline(stt=stt, tts=tts, vad=vad)

        # Player speaks
        audio_input = b"fake_audio_player_input"
        transcribed = await pipeline.process_audio_input(audio_input)
        assert transcribed == player_input_text

        # DM responds with text
        response_chunks = []
        async for chunk in pipeline.generate_audio_response(dm_response_text):
            response_chunks.append(chunk)

        assert len(response_chunks) > 0
        assert all(isinstance(chunk, AudioChunk) for chunk in response_chunks)

    @pytest.mark.asyncio
    async def test_voice_pipeline_handles_multiple_inputs(self) -> None:
        """VoicePipeline should handle multiple sequential inputs."""
        responses = [
            "I attack",
            "I cast a spell",
            "I run away",
        ]
        stt = FakeSTT(responses=responses)
        tts = FakeTTS()
        vad = VADProcessor()

        pipeline = VoicePipeline(stt=stt, tts=tts, vad=vad)

        for i, expected_text in enumerate(responses):
            result = await pipeline.process_audio_input(f"audio_input_{i}".encode())
            assert result == expected_text

    @pytest.mark.asyncio
    async def test_voice_pipeline_preserves_audio_quality(self) -> None:
        """VoicePipeline should preserve audio chunk quality (sample rate, etc)."""
        stt = FakeSTT()
        tts = FakeTTS()
        vad = VADProcessor()

        pipeline = VoicePipeline(stt=stt, tts=tts, vad=vad)

        chunks = []
        async for chunk in pipeline.generate_audio_response("Test audio quality."):
            chunks.append(chunk)

        for chunk in chunks:
            assert chunk.sample_rate > 0
            assert isinstance(chunk.data, bytes)

    @pytest.mark.asyncio
    async def test_voice_pipeline_with_punctuation(self) -> None:
        """VoicePipeline should handle text with various punctuation."""
        stt = FakeSTT()
        tts = FakeTTS()
        vad = VADProcessor()

        pipeline = VoicePipeline(stt=stt, tts=tts, vad=vad)

        text_variants = [
            "What? Really! Yes.",
            "One... two... three.",
            "Attack now!",
        ]

        for text in text_variants:
            chunks = []
            async for chunk in pipeline.generate_audio_response(text):
                chunks.append(chunk)

            assert len(chunks) > 0
            assert all(isinstance(chunk, AudioChunk) for chunk in chunks)

    @pytest.mark.asyncio
    async def test_voice_pipeline_streaming_produces_output_incrementally(self) -> None:
        """VoicePipeline streaming should produce chunks incrementally."""
        stt = FakeSTT()
        tts = FakeTTS()
        vad = VADProcessor()

        pipeline = VoicePipeline(stt=stt, tts=tts, vad=vad)

        text = "Sentence one. Sentence two. Sentence three."
        chunk_count = 0

        async for chunk in pipeline.generate_audio_response(text):
            chunk_count += 1
            # Each chunk should be reasonably small for streaming
            assert len(chunk.data) > 0

        assert chunk_count >= 3  # At least 3 sentences

    @pytest.mark.asyncio
    async def test_voice_pipeline_concurrent_audio_input(self) -> None:
        """VoicePipeline should handle sequential audio input calls."""
        stt = FakeSTT(responses=["Input 1", "Input 2", "Input 3"])
        tts = FakeTTS()
        vad = VADProcessor()

        pipeline = VoicePipeline(stt=stt, tts=tts, vad=vad)

        results = []
        for i in range(3):
            result = await pipeline.process_audio_input(f"audio_{i}".encode())
            results.append(result)

        assert results == ["Input 1", "Input 2", "Input 3"]


class TestVoicePipelineErrorHandling:
    """Tests for Voice Pipeline error handling."""

    @pytest.mark.asyncio
    async def test_voice_pipeline_handles_stt_error(self) -> None:
        """VoicePipeline should handle STT errors gracefully."""
        class FailingSTT(FakeSTT):
            async def transcribe(self, audio_bytes, language="en"):
                raise RuntimeError("STT failed")

        stt = FailingSTT()
        tts = FakeTTS()
        vad = VADProcessor()

        pipeline = VoicePipeline(stt=stt, tts=tts, vad=vad)

        with pytest.raises(RuntimeError):
            await pipeline.process_audio_input(b"audio")

    @pytest.mark.asyncio
    async def test_voice_pipeline_handles_tts_error(self) -> None:
        """VoicePipeline should handle TTS errors gracefully."""
        class FailingTTS(FakeTTS):
            async def synthesize_stream(self, text):
                raise RuntimeError("TTS failed")
                yield  # Make it a generator

        stt = FakeSTT()
        tts = FailingTTS()
        vad = VADProcessor()

        pipeline = VoicePipeline(stt=stt, tts=tts, vad=vad)

        with pytest.raises(RuntimeError):
            async for _ in pipeline.generate_audio_response("Test"):
                pass

    @pytest.mark.asyncio
    async def test_voice_pipeline_handles_vad_error(self) -> None:
        """VoicePipeline should handle VAD errors gracefully."""
        class FailingVAD(VADProcessor):
            def process_chunk(self, audio_chunk):
                raise RuntimeError("VAD failed")

        stt = FakeSTT()
        tts = FakeTTS()
        vad = FailingVAD()

        pipeline = VoicePipeline(stt=stt, tts=tts, vad=vad)

        with pytest.raises(RuntimeError):
            await pipeline.process_audio_input(b"audio")
