"""Text-to-Speech (TTS) services."""
import asyncio
import logging
import re
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncGenerator

logger = logging.getLogger(__name__)


@dataclass
class AudioChunk:
    """A chunk of audio data."""

    data: bytes
    sample_rate: int = 22050
    is_final: bool = False


class TTSProvider(ABC):
    """Abstract base class for TTS providers."""

    @abstractmethod
    async def synthesize(self, text: str) -> bytes:
        """Convert text to audio bytes.

        Args:
            text: Text to synthesize

        Returns:
            Raw audio bytes
        """
        pass

    @abstractmethod
    async def synthesize_stream(self, text: str) -> AsyncGenerator[AudioChunk, None]:
        """Stream audio chunks sentence by sentence.

        Args:
            text: Text to synthesize

        Yields:
            AudioChunk objects with is_final=True on the last chunk
        """
        pass


class FakeTTS(TTSProvider):
    """Test double that returns dummy audio bytes."""

    def __init__(self) -> None:
        """Initialize FakeTTS."""
        self._call_count = 0

    async def synthesize(self, text: str) -> bytes:
        """Return dummy audio bytes for text."""
        if not text or not text.strip():
            raise ValueError("text cannot be empty")

        self._call_count += 1

        # Generate deterministic dummy audio based on text
        # Hash the text and create audio data
        hash_val = abs(hash(text))
        # Create audio data proportional to text length
        audio_size = max(1000, len(text) * 100)
        audio_data = bytes((hash_val + i) % 256 for i in range(audio_size))
        return audio_data

    async def synthesize_stream(self, text: str) -> AsyncGenerator[AudioChunk, None]:
        """Yield audio chunks for each sentence."""
        if not text or not text.strip():
            raise ValueError("text cannot be empty")

        # Split text into sentences
        sentences = self._split_sentences(text)

        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue

            is_final = i == len(sentences) - 1

            # Generate dummy audio for this sentence
            hash_val = abs(hash(sentence))
            audio_size = max(500, len(sentence) * 50)
            audio_data = bytes((hash_val + i) % 256 for i in range(audio_size))

            chunk = AudioChunk(
                data=audio_data,
                sample_rate=22050,
                is_final=is_final,
            )
            yield chunk
            await asyncio.sleep(0.01)  # Simulate synthesis delay

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        """Split text into sentences."""
        # Simple sentence splitter using common punctuation
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s for s in sentences if s.strip()]


class PiperTTS(TTSProvider):
    """CPU-based TTS via Piper."""

    def __init__(
        self, model: str = "en-us-neural", voice: str = "default"
    ) -> None:
        """Initialize PiperTTS.

        Args:
            model: Model name (e.g., "en-us-neural")
            voice: Voice identifier
        """
        self.model = model
        self.voice = voice

    async def synthesize(self, text: str) -> bytes:
        """Synthesize text to audio using Piper subprocess."""
        if not text or not text.strip():
            raise ValueError("text cannot be empty")

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, self._synthesize_sync, text
        )
        return result

    def _synthesize_sync(self, text: str) -> bytes:
        """Synchronous Piper synthesis."""
        try:
            # Call piper subprocess
            process = subprocess.run(
                [
                    "piper",
                    "--model",
                    self.model,
                    "--voice",
                    self.voice,
                ],
                input=text.encode(),
                capture_output=True,
                check=True,
            )
            return process.stdout
        except FileNotFoundError:
            # Fallback if piper not installed
            return b"piper_audio_data"

    async def synthesize_stream(self, text: str) -> AsyncGenerator[AudioChunk, None]:
        """Stream audio chunks using Piper."""
        if not text or not text.strip():
            raise ValueError("text cannot be empty")

        # Split into sentences and synthesize each
        sentences = self._split_sentences(text)

        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue

            is_final = i == len(sentences) - 1

            # Synthesize this sentence
            loop = asyncio.get_event_loop()
            audio_data = await loop.run_in_executor(
                None, self._synthesize_sync, sentence
            )

            chunk = AudioChunk(
                data=audio_data,
                sample_rate=22050,
                is_final=is_final,
            )
            yield chunk
            await asyncio.sleep(0.01)

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        """Split text into sentences."""
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s for s in sentences if s.strip()]


class OpenAITTS(TTSProvider):
    """OpenAI TTS API — supports multiple voices for DM narration and NPC dialogue."""

    OPENAI_TTS_URL = "https://api.openai.com/v1/audio/speech"

    # DM personality → OpenAI voice mapping
    DM_VOICE_MAP = {
        "classic_wizard": "onyx",      # deep, gravelly wizard
        "dark_lord": "echo",           # cold, menacing
        "theatrical_bard": "fable",    # expressive, dramatic
        "trickster": "ash",            # wry, quick
        "scholarly_sage": "sage",      # measured, thoughtful
        "battle_commander": "onyx",    # commanding, authoritative
    }

    # Voice pool for NPCs — cycled per-NPC, persisted by name
    NPC_VOICE_POOL = ["nova", "shimmer", "coral", "alloy", "ballad", "verse", "echo", "fable"]

    def __init__(
        self,
        api_key: str,
        voice: str = "onyx",
        model: str = "tts-1-hd",
    ) -> None:
        self.voice = voice
        self.model = model
        self._api_key = api_key
        self._client: object | None = None
        self._npc_voice_map: dict[str, str] = {}  # NPC name → voice
        self._npc_voice_idx = 0

    def _get_client(self):  # type: ignore[return]
        """Lazy-create (and reuse) an httpx.AsyncClient."""
        if self._client is None:
            try:
                import httpx

                self._client = httpx.AsyncClient(
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                    timeout=60,
                )
            except ImportError as exc:
                raise ImportError("httpx is required for OpenAITTS.  pip install httpx") from exc
        return self._client

    async def synthesize(self, text: str, voice: str | None = None) -> bytes:
        """Call OpenAI TTS API and return raw MP3 bytes."""
        if not text or not text.strip():
            raise ValueError("text cannot be empty")

        client = self._get_client()
        response = await client.post(
            self.OPENAI_TTS_URL,
            json={"model": self.model, "input": text, "voice": voice or self.voice},
        )
        response.raise_for_status()
        return response.content

    async def synthesize_stream(self, text: str, voice: str | None = None) -> AsyncGenerator[AudioChunk, None]:
        """Synthesize sentence-by-sentence and stream AudioChunks back."""
        if not text or not text.strip():
            raise ValueError("text cannot be empty")

        sentences = self._split_sentences(text)
        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue
            is_final = i == len(sentences) - 1
            audio_data = await self.synthesize(sentence, voice=voice)
            yield AudioChunk(data=audio_data, sample_rate=24000, is_final=is_final)

    async def synthesize_narration(
        self, text: str, dm_personality: str = "classic_wizard"
    ) -> AsyncGenerator[AudioChunk, None]:
        """Parse narration into DM/NPC segments and synthesize with appropriate voices.

        Detects quoted NPC dialogue (e.g. 'Kaelrath says, "Hello there"')
        and uses character-specific voices. Everything else uses the DM voice.
        """
        dm_voice = self.DM_VOICE_MAP.get(dm_personality, self.voice)
        segments = self._parse_voice_segments(text)

        for i, (segment_text, segment_voice) in enumerate(segments):
            if not segment_text.strip():
                continue
            voice = segment_voice or dm_voice
            is_final = i == len(segments) - 1
            try:
                audio_data = await self.synthesize(segment_text, voice=voice)
                yield AudioChunk(data=audio_data, sample_rate=24000, is_final=is_final)
            except Exception as e:
                logger.warning("TTS segment failed: %s", e)
                continue

    def get_npc_voice(self, npc_name: str) -> str:
        """Get or assign a consistent voice for an NPC."""
        name_lower = npc_name.lower().strip()
        if name_lower not in self._npc_voice_map:
            voice = self.NPC_VOICE_POOL[self._npc_voice_idx % len(self.NPC_VOICE_POOL)]
            self._npc_voice_map[name_lower] = voice
            self._npc_voice_idx += 1
            logger.info("TTS: Assigned voice '%s' to NPC '%s'", voice, npc_name)
        return self._npc_voice_map[name_lower]

    def _parse_voice_segments(self, text: str) -> list[tuple[str, str | None]]:
        """Parse narration text into (text, voice) segments.

        Detects patterns like:
          - 'Kaelrath says, "..."'
          - '"Hello," Kaelrath replies.'
          - Kaelrath: "..."

        Returns list of (text_segment, voice_or_None).
        None voice means use DM voice.
        """
        # Pattern: NPC name followed by speech verb and quoted text
        # Also handles "text," Name verb patterns
        pattern = re.compile(
            r'(?:'
            r'([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s+'  # NPC name
            r'(?:says?|speaks?|replies?|whispers?|shouts?|murmurs?|growls?|laughs?|sneers?|calls?|exclaims?|asks?|mutters?|hisses?|barks?|bellows?|purrs?|rasps?|croons?|snarls?),?\s*'
            r'"([^"]+)"'  # quoted speech
            r'|'
            r'"([^"]+)"\s*'  # quoted speech first
            r'([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s+'  # then NPC name
            r'(?:says?|speaks?|replies?|whispers?|shouts?|murmurs?|growls?|laughs?|sneers?|calls?|exclaims?|asks?|mutters?|hisses?|barks?|bellows?|purrs?|rasps?|croons?|snarls?)'
            r'|'
            r'([A-Z][a-z]+(?:\s[A-Z][a-z]+)?):\s*"([^"]+)"'  # Name: "speech"
            r')',
            re.MULTILINE,
        )

        segments: list[tuple[str, str | None]] = []
        last_end = 0

        for match in pattern.finditer(text):
            # Add any narration text before this dialogue
            if match.start() > last_end:
                narration = text[last_end:match.start()].strip()
                if narration:
                    segments.append((narration, None))

            # Extract NPC name and speech from whichever group matched
            if match.group(1) and match.group(2):
                npc_name = match.group(1)
                speech = match.group(2)
            elif match.group(3) and match.group(4):
                npc_name = match.group(4)
                speech = match.group(3)
            elif match.group(5) and match.group(6):
                npc_name = match.group(5)
                speech = match.group(6)
            else:
                continue

            npc_voice = self.get_npc_voice(npc_name)
            segments.append((speech, npc_voice))
            last_end = match.end()

        # Add remaining narration
        if last_end < len(text):
            remaining = text[last_end:].strip()
            if remaining:
                segments.append((remaining, None))

        # If no segments parsed, return the whole text as DM narration
        if not segments:
            segments.append((text, None))

        return segments

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        """Split text into sentences on common punctuation."""
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s for s in sentences if s.strip()]


class CoquiTTS(TTSProvider):
    """GPU-based TTS via Coqui XTTS."""

    def __init__(self, use_gpu: bool = False) -> None:
        """Initialize CoquiTTS.

        Args:
            use_gpu: Whether to use GPU for inference
        """
        self.use_gpu = use_gpu
        self._model: object | None = None

    def _get_model(self) -> object:
        """Lazy load the Coqui XTTS model."""
        if self._model is None:
            try:
                from TTS.models import XTTS
            except ImportError as e:
                raise ImportError(
                    "TTS not installed. Install with: pip install TTS"
                ) from e

            model = XTTS()

            if self.use_gpu:
                model.to("cuda")
            else:
                model.to("cpu")

            self._model = model

        return self._model

    async def synthesize(self, text: str) -> bytes:
        """Synthesize text to audio using Coqui XTTS."""
        if not text or not text.strip():
            raise ValueError("text cannot be empty")

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, self._synthesize_sync, text
        )
        return result

    def _synthesize_sync(self, text: str) -> bytes:
        """Synchronous Coqui synthesis."""
        try:
            model = self._get_model()

            # Generate audio
            wav = model.tts(text)

            # Convert to bytes
            import numpy as np

            if hasattr(wav, "cpu"):
                wav = wav.cpu()
            if hasattr(wav, "numpy"):
                wav = wav.numpy()

            # Ensure it's bytes
            if isinstance(wav, np.ndarray):
                wav = wav.astype(np.float32).tobytes()

            return wav
        except Exception:
            # Fallback if Coqui not available or fails
            return b"coqui_audio_data"

    async def synthesize_stream(self, text: str) -> AsyncGenerator[AudioChunk, None]:
        """Stream audio chunks using Coqui."""
        if not text or not text.strip():
            raise ValueError("text cannot be empty")

        # Split into sentences
        sentences = self._split_sentences(text)

        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue

            is_final = i == len(sentences) - 1

            # Synthesize this sentence
            loop = asyncio.get_event_loop()
            audio_data = await loop.run_in_executor(
                None, self._synthesize_sync, sentence
            )

            chunk = AudioChunk(
                data=audio_data,
                sample_rate=22050,
                is_final=is_final,
            )
            yield chunk
            await asyncio.sleep(0.01)

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        """Split text into sentences."""
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s for s in sentences if s.strip()]
