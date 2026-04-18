"""Tests for Text-to-Speech (TTS) services."""
import pytest
from typing import AsyncGenerator

from app.services.voice.tts import (
    TTSProvider,
    AudioChunk,
    FakeTTS,
    PiperTTS,
    CoquiTTS,
)


class TestAudioChunk:
    """Tests for AudioChunk dataclass."""

    def test_create_audio_chunk_with_defaults(self) -> None:
        """Should create AudioChunk with default sample rate."""
        chunk = AudioChunk(data=b"audio_data")
        assert chunk.data == b"audio_data"
        assert chunk.sample_rate == 22050
        assert chunk.is_final is False

    def test_create_audio_chunk_with_custom_values(self) -> None:
        """Should create AudioChunk with custom values."""
        chunk = AudioChunk(
            data=b"audio_data",
            sample_rate=44100,
            is_final=True,
        )
        assert chunk.data == b"audio_data"
        assert chunk.sample_rate == 44100
        assert chunk.is_final is True


class TestFakeTTS:
    """Tests for FakeTTS mock implementation."""

    @pytest.mark.asyncio
    async def test_fake_tts_synthesize_returns_bytes(self) -> None:
        """FakeTTS.synthesize should return audio bytes."""
        tts = FakeTTS()
        result = await tts.synthesize("Hello, this is a test.")
        assert isinstance(result, bytes)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_fake_tts_synthesize_consistent_output(self) -> None:
        """FakeTTS.synthesize should return consistent output for same input."""
        tts = FakeTTS()
        text = "Hello, this is a test."

        result1 = await tts.synthesize(text)
        result2 = await tts.synthesize(text)

        assert result1 == result2

    @pytest.mark.asyncio
    async def test_fake_tts_synthesize_empty_text_error(self) -> None:
        """FakeTTS.synthesize should handle empty text gracefully."""
        tts = FakeTTS()

        with pytest.raises((ValueError, Exception)):
            await tts.synthesize("")

    @pytest.mark.asyncio
    async def test_fake_tts_streaming_yields_chunks(self) -> None:
        """FakeTTS.synthesize_stream should yield AudioChunk objects."""
        tts = FakeTTS()
        chunks = []

        async for chunk in tts.synthesize_stream("Hello. How are you?"):
            chunks.append(chunk)

        assert len(chunks) > 0
        assert all(isinstance(chunk, AudioChunk) for chunk in chunks)

    @pytest.mark.asyncio
    async def test_fake_tts_streaming_final_chunk(self) -> None:
        """FakeTTS.synthesize_stream should mark last chunk as final."""
        tts = FakeTTS()
        chunks = []

        async for chunk in tts.synthesize_stream("Hello. How are you?"):
            chunks.append(chunk)

        assert chunks[-1].is_final is True
        for chunk in chunks[:-1]:
            assert chunk.is_final is False

    @pytest.mark.asyncio
    async def test_fake_tts_streaming_audio_data(self) -> None:
        """FakeTTS.synthesize_stream chunks should contain audio data."""
        tts = FakeTTS()

        async for chunk in tts.synthesize_stream("Test audio"):
            assert isinstance(chunk.data, bytes)
            assert len(chunk.data) > 0
            assert chunk.sample_rate > 0

    @pytest.mark.asyncio
    async def test_fake_tts_streaming_sentence_splitting(self) -> None:
        """FakeTTS.synthesize_stream should split by sentences."""
        tts = FakeTTS()
        chunks = []

        async for chunk in tts.synthesize_stream("First sentence. Second sentence. Third."):
            chunks.append(chunk)

        # Should have at least 3 chunks for 3 sentences
        assert len(chunks) >= 3

    @pytest.mark.asyncio
    async def test_fake_tts_tracks_call_count(self) -> None:
        """FakeTTS should track number of calls."""
        tts = FakeTTS()
        assert tts._call_count == 0

        await tts.synthesize("Test 1")
        assert tts._call_count == 1

        await tts.synthesize("Test 2")
        assert tts._call_count == 2


class TestPiperTTS:
    """Tests for PiperTTS implementation."""

    def test_piper_tts_initialization(self) -> None:
        """PiperTTS should initialize with model and voice."""
        tts = PiperTTS(model="en-us-neural", voice="default")
        assert tts.model == "en-us-neural"
        assert tts.voice == "default"

    def test_piper_tts_initialization_defaults(self) -> None:
        """PiperTTS should have sensible defaults."""
        tts = PiperTTS()
        assert tts.model is not None
        assert tts.voice is not None

    @pytest.mark.asyncio
    async def test_piper_tts_synthesize_returns_bytes(self) -> None:
        """PiperTTS.synthesize should return audio bytes or fallback."""
        tts = PiperTTS()
        result = await tts.synthesize("Hello, world.")
        assert isinstance(result, bytes)

    @pytest.mark.asyncio
    async def test_piper_tts_streaming_interface(self) -> None:
        """PiperTTS should support streaming."""
        tts = PiperTTS()
        chunks = []

        async for chunk in tts.synthesize_stream("Hello. World."):
            chunks.append(chunk)

        assert len(chunks) > 0
        assert all(isinstance(chunk, AudioChunk) for chunk in chunks)

    @pytest.mark.asyncio
    async def test_piper_tts_empty_text_error(self) -> None:
        """PiperTTS should handle empty text gracefully."""
        tts = PiperTTS()

        with pytest.raises(ValueError):
            await tts.synthesize("")


class TestCoquiTTS:
    """Tests for CoquiTTS implementation."""

    def test_coqui_tts_initialization(self) -> None:
        """CoquiTTS should initialize with GPU flag."""
        tts = CoquiTTS(use_gpu=True)
        assert tts.use_gpu is True

    def test_coqui_tts_initialization_defaults(self) -> None:
        """CoquiTTS should have sensible defaults."""
        tts = CoquiTTS()
        assert isinstance(tts.use_gpu, bool)

    @pytest.mark.asyncio
    async def test_coqui_tts_empty_text_error(self) -> None:
        """CoquiTTS should handle empty text gracefully."""
        tts = CoquiTTS()

        with pytest.raises(ValueError):
            await tts.synthesize("")


class TestTTSProviderInterface:
    """Tests for TTSProvider abstract interface."""

    def test_tts_provider_is_abstract(self) -> None:
        """TTSProvider should be an abstract base class."""
        with pytest.raises(TypeError):
            TTSProvider()  # type: ignore

    @pytest.mark.asyncio
    async def test_fake_tts_implements_tts_provider(self) -> None:
        """FakeTTS should implement TTSProvider interface."""
        tts = FakeTTS()
        assert isinstance(tts, TTSProvider)

    @pytest.mark.asyncio
    async def test_piper_tts_implements_tts_provider(self) -> None:
        """PiperTTS should implement TTSProvider interface."""
        tts = PiperTTS()
        assert isinstance(tts, TTSProvider)

    @pytest.mark.asyncio
    async def test_coqui_tts_implements_tts_provider(self) -> None:
        """CoquiTTS should implement TTSProvider interface."""
        tts = CoquiTTS()
        assert isinstance(tts, TTSProvider)


class TestOpenAITTSMultiVoice:
    """Tests for OpenAITTS multi-voice features (no API calls)."""

    def test_dm_voice_map_has_all_personalities(self) -> None:
        """DM_VOICE_MAP should cover all known DM personalities."""
        from app.services.voice.tts import OpenAITTS
        expected = {"classic_wizard", "dark_lord", "theatrical_bard", "trickster", "scholarly_sage", "battle_commander"}
        assert expected == set(OpenAITTS.DM_VOICE_MAP.keys())

    def test_npc_voice_pool_is_nonempty(self) -> None:
        """NPC_VOICE_POOL should have voices for assignment."""
        from app.services.voice.tts import OpenAITTS
        assert len(OpenAITTS.NPC_VOICE_POOL) >= 6

    def test_get_npc_voice_consistency(self) -> None:
        """Same NPC name should always get the same voice."""
        from app.services.voice.tts import OpenAITTS
        tts = OpenAITTS(api_key="test-key")
        result1 = tts.get_npc_voice("Kaelrath")
        result2 = tts.get_npc_voice("Kaelrath")
        assert result1 == result2
        assert isinstance(result1, tuple) and len(result1) == 2

    def test_get_npc_voice_case_insensitive(self) -> None:
        """NPC voice assignment should be case-insensitive."""
        from app.services.voice.tts import OpenAITTS
        tts = OpenAITTS(api_key="test-key")
        result1 = tts.get_npc_voice("Kaelrath")
        result2 = tts.get_npc_voice("kaelrath")
        assert result1 == result2

    def test_different_npcs_get_different_voices(self) -> None:
        """Different NPCs should get different voices (until pool wraps)."""
        from app.services.voice.tts import OpenAITTS
        tts = OpenAITTS(api_key="test-key")
        voice1, _ = tts.get_npc_voice("Kaelrath")
        voice2, _ = tts.get_npc_voice("Mira")
        assert voice1 != voice2

    def test_parse_voice_segments_simple_narration(self) -> None:
        """Pure narration should return one segment with None."""
        from app.services.voice.tts import OpenAITTS
        tts = OpenAITTS(api_key="test-key")
        segments = tts._parse_voice_segments("The tavern is dark and smoky.")
        assert len(segments) == 1
        assert segments[0][1] is None

    def test_parse_voice_segments_npc_says(self) -> None:
        """'NPC says' pattern should extract NPC name."""
        from app.services.voice.tts import OpenAITTS
        tts = OpenAITTS(api_key="test-key")
        text = 'The old man turns to you. Kaelrath says, "Welcome to my shop, adventurer."'
        segments = tts._parse_voice_segments(text)
        assert len(segments) >= 2
        npc_segments = [(t, v) for t, v in segments if v is not None]
        assert len(npc_segments) == 1
        assert "Welcome to my shop" in npc_segments[0][0]
        assert npc_segments[0][1] == "Kaelrath"

    def test_parse_voice_segments_colon_pattern(self) -> None:
        """'NPC: "speech"' pattern should be detected."""
        from app.services.voice.tts import OpenAITTS
        tts = OpenAITTS(api_key="test-key")
        text = 'Mira: "Follow me, quickly!"'
        segments = tts._parse_voice_segments(text)
        npc_segments = [(t, v) for t, v in segments if v is not None]
        assert len(npc_segments) == 1
        assert "Follow me" in npc_segments[0][0]
        assert npc_segments[0][1] == "Mira"

    def test_parse_voice_segments_multiple_npcs(self) -> None:
        """Multiple NPCs should return different NPC names."""
        from app.services.voice.tts import OpenAITTS
        tts = OpenAITTS(api_key="test-key")
        text = 'Kaelrath says, "Hello." Mira whispers, "Be careful."'
        segments = tts._parse_voice_segments(text)
        npc_segments = [(t, v) for t, v in segments if v is not None]
        assert len(npc_segments) == 2
        assert npc_segments[0][1] != npc_segments[1][1]

    def test_parse_voice_segments_persistent_npc_name(self) -> None:
        """Same NPC in multiple utterances should return same NPC name."""
        from app.services.voice.tts import OpenAITTS
        tts = OpenAITTS(api_key="test-key")
        text = 'Kaelrath says, "Hello." He pauses. Kaelrath says, "Goodbye."'
        segments = tts._parse_voice_segments(text)
        npc_segments = [(t, v) for t, v in segments if v is not None]
        assert len(npc_segments) == 2
        assert npc_segments[0][1] == npc_segments[1][1] == "Kaelrath"

    def test_dm_voice_map_returns_valid_voices(self) -> None:
        """All DM voice mappings should contain valid OpenAI voice names."""
        from app.services.voice.tts import OpenAITTS
        valid_voices = {"alloy", "ash", "ballad", "coral", "echo", "fable", "onyx", "nova", "sage", "shimmer", "verse"}
        for voice, instructions in OpenAITTS.DM_VOICE_MAP.values():
            assert voice in valid_voices, f"{voice} is not a valid OpenAI voice"
            assert len(instructions) > 20, "Instructions should be meaningful"

    def test_npc_voice_pool_valid_voices(self) -> None:
        """All NPC pool voices should be valid OpenAI voice names."""
        from app.services.voice.tts import OpenAITTS
        valid_voices = {"alloy", "ash", "ballad", "coral", "echo", "fable", "onyx", "nova", "sage", "shimmer", "verse"}
        for voice, instructions in OpenAITTS.NPC_VOICE_POOL:
            assert voice in valid_voices, f"{voice} is not a valid OpenAI voice"
            assert len(instructions) > 10, "Instructions should be meaningful"
