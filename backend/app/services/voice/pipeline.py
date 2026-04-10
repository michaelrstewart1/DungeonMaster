"""Voice Pipeline integration."""
import re
from typing import AsyncGenerator

from app.services.voice.stt import STTProvider
from app.services.voice.tts import TTSProvider, AudioChunk
from app.services.voice.vad import VADProcessor


class VoicePipeline:
    """Integrates STT, TTS, and VAD services."""

    def __init__(
        self,
        stt: STTProvider,
        tts: TTSProvider,
        vad: VADProcessor,
    ) -> None:
        """Initialize Voice Pipeline.

        Args:
            stt: Speech-to-Text provider
            tts: Text-to-Speech provider
            vad: Voice Activity Detection processor
        """
        self.stt = stt
        self.tts = tts
        self.vad = vad

    async def process_audio_input(self, audio_bytes: bytes) -> str:
        """Process audio input through VAD and STT.

        Pipeline:
        1. Run audio through VAD to detect speech boundaries
        2. Transcribe audio to text using STT
        3. Return the transcribed text

        Args:
            audio_bytes: Raw audio data

        Returns:
            Transcribed text
        """
        # Process through VAD to detect speech activity
        vad_events = self.vad.process_chunk(audio_bytes)

        # Always transcribe - VAD is just for tracking boundaries
        transcription = await self.stt.transcribe(audio_bytes)

        return transcription.text

    async def generate_audio_response(
        self, text: str
    ) -> AsyncGenerator[AudioChunk, None]:
        """Generate streaming audio response from text.

        Pipeline:
        1. Split text into sentences
        2. Stream audio chunks using TTS
        3. Mark final chunk appropriately

        Args:
            text: Response text to synthesize

        Yields:
            AudioChunk objects with streaming audio
        """
        if not text or not text.strip():
            raise ValueError("text cannot be empty")

        # Use TTS streaming capability
        chunk_count = 0
        async for chunk in self.tts.synthesize_stream(text):
            chunk_count += 1
            yield chunk

        if chunk_count == 0:
            raise StopAsyncIteration("No audio chunks generated")

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        """Split text into sentences.

        Args:
            text: Text to split

        Returns:
            List of sentences
        """
        # Split on common sentence endings
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s for s in sentences if s.strip()]
