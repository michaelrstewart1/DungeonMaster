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
    """OpenAI TTS API — gpt-4o-mini-tts with dramatic instructions for fantasy narration."""

    OPENAI_TTS_URL = "https://api.openai.com/v1/audio/speech"

    # DM personality → (voice, dramatic instructions)
    DM_VOICE_MAP: dict[str, tuple[str, str]] = {
        "classic_wizard": ("ash", (
            "You are the voice of an ancient, powerful wizard narrating a Dungeons & Dragons adventure. "
            "Speak with deep gravitas and theatrical weight. Use dramatic pauses before revealing key details. "
            "Let wonder and mystery drip from every word. When describing danger, lower your voice to a near-whisper. "
            "When describing triumph, let your voice swell with pride. You are telling an epic tale by firelight."
        )),
        "dark_lord": ("echo", (
            "You are a menacing, cold narrator — like a dark lord recounting events with cruel amusement. "
            "Speak slowly and deliberately, savoring each word. Your tone is sinister and foreboding. "
            "Pause before threats. Let malice seep into descriptions of danger. "
            "Even mundane descriptions carry an undertone of dread."
        )),
        "theatrical_bard": ("fable", (
            "You are a flamboyant, theatrical bard performing a grand tale for a captivated audience. "
            "Your voice is rich, expressive, and full of emotion — you go big on every moment. "
            "Gasp at surprises, whisper conspiracies, boom with heroic declarations. "
            "Every sentence is a performance. You live for the drama."
        )),
        "trickster": ("ash", (
            "You are a wry, mischievous trickster narrating with sly amusement. "
            "Your pacing is quick and playful, with unexpected pauses for comic timing. "
            "You find everything slightly amusing. Lean into irony and wit. "
            "Even danger gets a sardonic twist."
        )),
        "scholarly_sage": ("sage", (
            "You are a wise, ancient sage recounting events with measured gravitas. "
            "Speak thoughtfully, as if choosing each word with great care. "
            "Your tone carries the weight of centuries of knowledge. "
            "Pause to let important revelations land. Convey awe when describing the arcane or divine."
        )),
        "battle_commander": ("onyx", (
            "You are a grizzled battle commander narrating with commanding authority. "
            "Your voice is powerful and decisive. Descriptions of combat are sharp and intense. "
            "You bark out action sequences with urgency. In quiet moments, your voice carries "
            "the weariness and resolve of a veteran who has seen too many wars."
        )),
    }

    # Default dramatic instructions when no personality matches
    DEFAULT_DM_INSTRUCTIONS = (
        "You are a dramatic fantasy narrator for a Dungeons & Dragons game. "
        "Speak with theatrical gravitas. Use dramatic pacing — pause before reveals, "
        "whisper in moments of tension, swell with energy during action and triumph. "
        "You are telling an epic tale. Make every word count."
    )

    # NPC voice pool with character archetypes for varied delivery
    NPC_VOICE_POOL: list[tuple[str, str]] = [
        ("nova", "Speak as a confident, warm female character in a fantasy world. Be expressive and natural."),
        ("shimmer", "Speak as a mysterious, ethereal character. Your voice carries otherworldly elegance."),
        ("coral", "Speak as a bold, passionate character. You feel deeply and express yourself with fire."),
        ("alloy", "Speak as a gruff, no-nonsense character. Short sentences, direct, and rough around the edges."),
        ("ballad", "Speak as a gentle, wise character. Your words carry calm authority and kindness."),
        ("verse", "Speak as a young, eager character. You are enthusiastic and full of wonder."),
        ("echo", "Speak as a cold, calculating character. Every word is measured and deliberate."),
        ("fable", "Speak as a theatrical, larger-than-life character. You love being the center of attention."),
    ]

    def __init__(
        self,
        api_key: str,
        voice: str = "onyx",
        model: str = "gpt-4o-mini-tts",
        speed: float = 0.9,
    ) -> None:
        self.voice = voice
        self.model = model
        self.speed = speed
        self._api_key = api_key
        self._client: object | None = None
        self._npc_voice_map: dict[str, tuple[str, str]] = {}  # NPC name → (voice, instructions)
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

    async def synthesize(
        self,
        text: str,
        voice: str | None = None,
        instructions: str | None = None,
        speed: float | None = None,
    ) -> bytes:
        """Call OpenAI TTS API and return raw MP3 bytes."""
        if not text or not text.strip():
            raise ValueError("text cannot be empty")

        payload: dict = {
            "model": self.model,
            "input": text,
            "voice": voice or self.voice,
            "speed": speed or self.speed,
        }
        # gpt-4o-mini-tts supports instructions for style control
        if instructions and "gpt-4o" in self.model:
            payload["instructions"] = instructions

        client = self._get_client()
        response = await client.post(self.OPENAI_TTS_URL, json=payload)
        response.raise_for_status()
        return response.content

    async def synthesize_stream(
        self,
        text: str,
        voice: str | None = None,
        instructions: str | None = None,
    ) -> AsyncGenerator[AudioChunk, None]:
        """Synthesize sentence-by-sentence and stream AudioChunks back."""
        if not text or not text.strip():
            raise ValueError("text cannot be empty")

        sentences = self._split_sentences(text)
        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue
            is_final = i == len(sentences) - 1
            audio_data = await self.synthesize(sentence, voice=voice, instructions=instructions)
            yield AudioChunk(data=audio_data, sample_rate=24000, is_final=is_final)

    async def synthesize_narration(
        self, text: str, dm_personality: str = "classic_wizard"
    ) -> AsyncGenerator[AudioChunk, None]:
        """Parse narration into DM/NPC segments and synthesize with dramatic voices.

        DM narration uses personality-specific voice + instructions.
        NPC dialogue uses character-specific voice + archetype instructions.
        """
        dm_voice, dm_instructions = self.DM_VOICE_MAP.get(
            dm_personality, (self.voice, self.DEFAULT_DM_INSTRUCTIONS)
        )
        segments = self._parse_voice_segments(text)

        for i, (segment_text, segment_npc) in enumerate(segments):
            if not segment_text.strip():
                continue
            is_final = i == len(segments) - 1

            if segment_npc:
                # NPC dialogue — use character voice + archetype instructions
                npc_voice, npc_instructions = self.get_npc_voice(segment_npc)
                voice = npc_voice
                instructions = npc_instructions
            else:
                # DM narration
                voice = dm_voice
                instructions = dm_instructions

            try:
                audio_data = await self.synthesize(segment_text, voice=voice, instructions=instructions)
                yield AudioChunk(data=audio_data, sample_rate=24000, is_final=is_final)
            except Exception as e:
                logger.warning("TTS segment failed: %s", e)
                continue

    def get_npc_voice(self, npc_name: str) -> tuple[str, str]:
        """Get or assign a consistent voice + instructions for an NPC."""
        name_lower = npc_name.lower().strip()
        if name_lower not in self._npc_voice_map:
            voice, instructions = self.NPC_VOICE_POOL[self._npc_voice_idx % len(self.NPC_VOICE_POOL)]
            self._npc_voice_map[name_lower] = (voice, instructions)
            self._npc_voice_idx += 1
            logger.info("TTS: Assigned voice '%s' to NPC '%s'", voice, npc_name)
        return self._npc_voice_map[name_lower]

    def _parse_voice_segments(self, text: str) -> list[tuple[str, str | None]]:
        """Parse narration text into (text, npc_name_or_None) segments.

        Detects patterns like:
          - 'Kaelrath says, "..."'
          - '"Hello," Kaelrath replies.'
          - Kaelrath: "..."

        Returns list of (text_segment, npc_name_or_None).
        None means DM narration.
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

            segments.append((speech, npc_name))
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
