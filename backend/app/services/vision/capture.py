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


class OpenCVCamera(CameraCapture):
    """USB/webcam capture via OpenCV — for a camera pointed at the physical
    battle map. Frames are JPEG-encoded for the vision analyzer."""

    def __init__(self, device_index: int = 0, width: int = 1280, height: int = 720):
        self.device_index = device_index
        self.width = width
        self.height = height

    def _capture_sync(self) -> CaptureResult:
        try:
            import cv2
        except ImportError as exc:
            raise RuntimeError(
                "opencv-python is required for OpenCVCamera. pip install opencv-python-headless"
            ) from exc

        cap = cv2.VideoCapture(self.device_index)
        try:
            if not cap.isOpened():
                raise RuntimeError(f"Camera device {self.device_index} could not be opened")
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            ok, frame = cap.read()
            if not ok or frame is None:
                raise RuntimeError(f"Camera device {self.device_index} returned no frame")
            ok, buf = cv2.imencode(".jpg", frame)
            if not ok:
                raise RuntimeError("Failed to JPEG-encode camera frame")
            h, w = frame.shape[:2]
            return CaptureResult(image_bytes=buf.tobytes(), width=w, height=h, format="jpeg")
        finally:
            cap.release()

    async def capture(self) -> CaptureResult:
        import asyncio
        return await asyncio.get_event_loop().run_in_executor(None, self._capture_sync)

    async def is_available(self) -> bool:
        try:
            import asyncio

            def _check() -> bool:
                import cv2
                cap = cv2.VideoCapture(self.device_index)
                try:
                    return cap.isOpened()
                finally:
                    cap.release()

            return await asyncio.get_event_loop().run_in_executor(None, _check)
        except Exception:
            return False
