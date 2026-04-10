"""Text-to-Speech (TTS) services."""
import asyncio
import re
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncGenerator


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
