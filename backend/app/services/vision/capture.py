"""Camera capture service — abstracts frame capture from camera devices."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class CaptureResult:
    image_bytes: bytes
    width: int
    height: int
    format: str = "jpeg"


class CameraCapture(ABC):
    @abstractmethod
    async def capture(self) -> CaptureResult:
        """Capture a single frame and return image bytes."""

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if camera is available."""


class FakeCamera(CameraCapture):
    """Test double for camera capture."""

    def __init__(self, image_bytes: bytes | None = None, width: int = 640, height: int = 480):
        self._image_bytes = image_bytes or b"\x89PNG\r\n\x1a\nfake_image_data"
        self._width = width
        self._height = height
        self.capture_count = 0

    async def capture(self) -> CaptureResult:
        self.capture_count += 1
        return CaptureResult(
            image_bytes=self._image_bytes,
            width=self._width,
            height=self._height,
            format="png",
        )

    async def is_available(self) -> bool:
        return True
