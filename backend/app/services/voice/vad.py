"""Voice Activity Detection (VAD) service."""
from dataclasses import dataclass
from typing import Literal

try:
    import numpy as np
except ImportError:
    np = None  # type: ignore


@dataclass
class VADEvent:
    """Event indicating a change in voice activity."""

    type: Literal["speech_start", "speech_end"]
    timestamp: float


class VADProcessor:
    """Voice Activity Detection processor."""

    def __init__(
        self,
        silence_threshold_ms: int = 500,
        energy_threshold: float = 0.01,
    ) -> None:
        """Initialize VAD processor.

        Args:
            silence_threshold_ms: Duration of silence (ms) to trigger speech_end
            energy_threshold: Energy threshold for speech detection (0.0 to 1.0)
        """
        self.silence_threshold_ms = silence_threshold_ms
        self.energy_threshold = energy_threshold

        self._is_speaking = False
        self._silence_duration_ms = 0.0
        self._current_timestamp = 0.0
        self._sample_rate = 16000

    def process_chunk(self, audio_chunk: bytes) -> list[VADEvent]:
        """Process audio chunk and detect voice activity.

        Args:
            audio_chunk: Raw audio bytes (16-bit PCM assumed)

        Returns:
            List of VADEvent indicating activity changes
        """
        if np is None:
            raise ImportError("numpy is required for VAD processing")

        events: list[VADEvent] = []

        if not audio_chunk:
            return events

        # Convert bytes to audio samples
        try:
            audio_data = np.frombuffer(audio_chunk, dtype=np.int16)
        except (ValueError, TypeError):
            return events

        if len(audio_data) == 0:
            return events

        # Calculate chunk duration in milliseconds
        chunk_duration_ms = (len(audio_data) / self._sample_rate) * 1000

        # Calculate RMS energy
        energy = self._calculate_energy(audio_data)

        # Check if speech is detected
        speech_detected = energy >= self.energy_threshold

        if speech_detected and not self._is_speaking:
            # Speech start detected
            self._is_speaking = True
            self._silence_duration_ms = 0.0
            events.append(VADEvent(type="speech_start", timestamp=self._current_timestamp))

        elif not speech_detected and self._is_speaking:
            # In potential silence
            self._silence_duration_ms += chunk_duration_ms

            if self._silence_duration_ms >= self.silence_threshold_ms:
                # Speech end detected
                self._is_speaking = False
                self._silence_duration_ms = 0.0
                events.append(VADEvent(type="speech_end", timestamp=self._current_timestamp))

        elif speech_detected and self._is_speaking:
            # Still speaking, reset silence counter
            self._silence_duration_ms = 0.0

        # Update timestamp
        self._current_timestamp += chunk_duration_ms / 1000.0

        return events

    def reset(self) -> None:
        """Reset VAD state for a new utterance."""
        self._is_speaking = False
        self._silence_duration_ms = 0.0
        self._current_timestamp = 0.0

    @staticmethod
    def _calculate_energy(audio_data) -> float:  # type: ignore
        """Calculate RMS energy of audio chunk.

        Args:
            audio_data: Audio samples

        Returns:
            Normalized energy value (0.0 to 1.0)
        """
        if np is None:
            raise ImportError("numpy is required for VAD processing")

        # Calculate RMS
        rms = np.sqrt(np.mean(audio_data.astype(float) ** 2))

        # Normalize to 0-1 range (assuming 16-bit audio max is 32767)
        normalized_rms = rms / 32767.0

        return float(normalized_rms)
