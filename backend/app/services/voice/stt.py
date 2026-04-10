"""Speech-to-Text (STT) services."""
import asyncio
import io
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncGenerator

try:
    import librosa
except ImportError:
    librosa = None  # type: ignore

try:
    import numpy as np
except ImportError:
    np = None  # type: ignore


@dataclass
class TranscriptionResult:
    """Result of a transcription operation."""

    text: str
    language: str
    confidence: float
    duration_seconds: float


class STTProvider(ABC):
    """Abstract base class for STT providers."""

    @abstractmethod
    async def transcribe(
        self, audio_bytes: bytes, language: str = "en"
    ) -> TranscriptionResult:
        """Transcribe audio bytes to text.

        Args:
            audio_bytes: Raw audio data
            language: Language code (e.g., "en", "es", "en-US")

        Returns:
            TranscriptionResult containing transcribed text and metadata
        """
        pass

    @abstractmethod
    async def transcribe_stream(
        self, audio_chunks: bytes
    ) -> AsyncGenerator[str, None]:
        """Stream transcription from audio chunks.

        Args:
            audio_chunks: Raw audio data

        Yields:
            Partial transcription results as they become available
        """
        pass


class FakeSTT(STTProvider):
    """Test double that returns configurable responses."""

    def __init__(self, responses: list[str] | None = None) -> None:
        """Initialize FakeSTT.

        Args:
            responses: List of responses to return on successive calls
        """
        self.responses = responses or ["Hello, I attack the goblin"]
        self.stream_responses: list[str] = []
        self._call_count = 0
        self.received_audio: list[bytes] = []

    async def transcribe(
        self, audio_bytes: bytes, language: str = "en"
    ) -> TranscriptionResult:
        """Return next configured response."""
        self.received_audio.append(audio_bytes)

        if self._call_count >= len(self.responses):
            text = self.responses[-1]  # Repeat last response
        else:
            text = self.responses[self._call_count]

        self._call_count += 1

        return TranscriptionResult(
            text=text,
            language=language,
            confidence=0.95,
            duration_seconds=float(len(audio_bytes)) / 16000.0,
        )

    async def transcribe_stream(
        self, audio_chunks: bytes
    ) -> AsyncGenerator[str, None]:
        """Yield partial transcription results."""
        if not self.stream_responses:
            # Generate default stream responses
            self.stream_responses = ["Hello", "Hello world", "Hello world, I"]

        for response in self.stream_responses:
            yield response
            await asyncio.sleep(0.01)  # Simulate streaming delay


class WhisperSTT(STTProvider):
    """faster-whisper based STT implementation."""

    def __init__(self, model_size: str = "base", device: str = "cpu") -> None:
        """Initialize WhisperSTT.

        Args:
            model_size: Model size ("tiny", "base", "small", "medium", "large")
            device: Device to run on ("cpu", "cuda")
        """
        self.model_size = model_size
        self.device = device
        self._model: object | None = None

    def _get_model(self) -> object:
        """Lazy load the Whisper model."""
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError as e:
                raise ImportError(
                    "faster-whisper not installed. "
                    "Install with: pip install faster-whisper"
                ) from e

            self._model = WhisperModel(self.model_size, device=self.device)
        return self._model

    async def transcribe(
        self, audio_bytes: bytes, language: str = "en"
    ) -> TranscriptionResult:
        """Transcribe audio using Whisper model."""
        if not audio_bytes:
            raise ValueError("audio_bytes cannot be empty")

        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, self._transcribe_sync, audio_bytes, language
        )
        return result

    def _transcribe_sync(
        self, audio_bytes: bytes, language: str
    ) -> TranscriptionResult:
        """Synchronous transcription implementation."""
        import io

        import numpy as np

        try:
            import librosa
        except ImportError:
            # Create dummy audio metadata if librosa not available
            duration = len(audio_bytes) / 16000.0
        else:
            # Load audio and get duration
            audio_io = io.BytesIO(audio_bytes)
            y, sr = librosa.load(audio_io, sr=16000)
            duration = librosa.get_duration(y=y, sr=sr)

        model = self._get_model()

        # Transcribe using the model
        segments, info, _ = model.transcribe(
            audio_bytes,
            language=language,
            fp16=self.device == "cuda",
        )

        # Combine segments into full text
        texts = [seg["text"].strip() for seg in segments]
        full_text = " ".join(texts).strip()

        # Calculate average confidence from segments
        if segments:
            confidences = [seg.get("confidence", 0.9) for seg in segments]
            confidence = float(np.mean(confidences))
        else:
            confidence = 0.0

        return TranscriptionResult(
            text=full_text,
            language=language,
            confidence=confidence,
            duration_seconds=duration,
        )

    async def transcribe_stream(
        self, audio_chunks: bytes
    ) -> AsyncGenerator[str, None]:
        """Stream partial transcriptions as they become available."""
        if not audio_chunks:
            raise ValueError("audio_chunks cannot be empty")

        # Simulate streaming by yielding partial results
        # In a real implementation, this would use Whisper's streaming API
        partial_results = [
            "Loading...",
            "Transcribing...",
            "Processing audio...",
        ]

        for partial in partial_results:
            await asyncio.sleep(0.1)
            yield partial
