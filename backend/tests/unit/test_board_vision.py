"""Tests for board vision — camera capture & analysis. TDD: tests first."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.vision.capture import CameraCapture, FakeCamera, CaptureResult
from app.services.vision.analyzer import BoardAnalyzer, FakeBoardAnalyzer, BoardAnalysis, TokenDetection


class TestCaptureResult:
    def test_has_image_data(self):
        result = CaptureResult(image_bytes=b"\x89PNG", width=640, height=480, format="png")
        assert result.image_bytes == b"\x89PNG"
        assert result.width == 640
        assert result.height == 480

    def test_format_default(self):
        result = CaptureResult(image_bytes=b"data", width=100, height=100)
        assert result.format == "jpeg"


class TestFakeCamera:
    @pytest.mark.asyncio
    async def test_capture_returns_result(self):
        camera = FakeCamera()
        result = await camera.capture()
        assert isinstance(result, CaptureResult)
        assert len(result.image_bytes) > 0

    @pytest.mark.asyncio
    async def test_capture_increments_count(self):
        camera = FakeCamera()
        await camera.capture()
        await camera.capture()
        assert camera.capture_count == 2

    @pytest.mark.asyncio
    async def test_custom_image_data(self):
        camera = FakeCamera(image_bytes=b"custom_image")
        result = await camera.capture()
        assert result.image_bytes == b"custom_image"


class TestCameraCapture:
    def test_is_abstract(self):
        with pytest.raises(TypeError):
            CameraCapture()

    def test_fake_camera_is_subclass(self):
        assert issubclass(FakeCamera, CameraCapture)


class TestTokenDetection:
    def test_has_fields(self):
        token = TokenDetection(entity_id="goblin1", x=3, y=5, confidence=0.95)
        assert token.entity_id == "goblin1"
        assert token.x == 3
        assert token.y == 5
        assert token.confidence == 0.95


class TestBoardAnalysis:
    def test_has_grid_and_tokens(self):
        analysis = BoardAnalysis(
            grid_width=10,
            grid_height=10,
            tokens=[TokenDetection("hero", 1, 1, 0.99)],
            confidence=0.9,
            raw_description="A 10x10 dungeon grid with a hero at position 1,1",
        )
        assert analysis.grid_width == 10
        assert len(analysis.tokens) == 1
        assert analysis.confidence == 0.9

    def test_empty_tokens_list(self):
        analysis = BoardAnalysis(grid_width=5, grid_height=5, tokens=[], confidence=0.8)
        assert analysis.tokens == []


class TestFakeBoardAnalyzer:
    @pytest.mark.asyncio
    async def test_returns_configured_analysis(self):
        tokens = [TokenDetection("elf", 2, 3, 0.9)]
        analyzer = FakeBoardAnalyzer(
            grid_size=(8, 8),
            tokens=tokens,
        )
        result = await analyzer.analyze(b"image_data")
        assert isinstance(result, BoardAnalysis)
        assert result.grid_width == 8
        assert result.grid_height == 8
        assert len(result.tokens) == 1
        assert result.tokens[0].entity_id == "elf"

    @pytest.mark.asyncio
    async def test_tracks_calls(self):
        analyzer = FakeBoardAnalyzer()
        await analyzer.analyze(b"img1")
        await analyzer.analyze(b"img2")
        assert analyzer.call_count == 2
        assert analyzer.received_images == [b"img1", b"img2"]

    @pytest.mark.asyncio
    async def test_default_analysis(self):
        analyzer = FakeBoardAnalyzer()
        result = await analyzer.analyze(b"data")
        assert result.grid_width == 10
        assert result.grid_height == 10
        assert result.tokens == []


class TestBoardAnalyzer:
    def test_is_abstract(self):
        with pytest.raises(TypeError):
            BoardAnalyzer()

    def test_fake_is_subclass(self):
        assert issubclass(FakeBoardAnalyzer, BoardAnalyzer)
