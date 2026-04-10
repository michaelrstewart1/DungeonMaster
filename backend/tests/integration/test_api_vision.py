"""Integration tests for vision API endpoints."""
import pytest
from httpx import AsyncClient

from app.services.vision.analyzer import TokenDetection


class TestVisionCapture:
    """Tests for POST /api/vision/{session_id}/capture"""

    async def test_capture_returns_200_with_analysis(self, client: AsyncClient):
        """Capturing should return 200 with grid analysis."""
        response = await client.post("/api/vision/session1/capture")

        assert response.status_code == 200
        data = response.json()
        assert "grid_width" in data
        assert "grid_height" in data
        assert "tokens" in data
        assert "confidence" in data

    async def test_capture_returns_grid_analysis_data(self, client: AsyncClient):
        """Capture should return board grid analysis."""
        response = await client.post("/api/vision/session1/capture")

        assert response.status_code == 200
        data = response.json()
        assert data["grid_width"] == 10
        assert data["grid_height"] == 10
        assert isinstance(data["tokens"], list)
        assert data["confidence"] == 0.95

    async def test_capture_stores_result_in_memory(self, client: AsyncClient):
        """Capture should store result in memory storage."""
        session_id = "session1"

        # First capture
        response = await client.post(f"/api/vision/{session_id}/capture")
        assert response.status_code == 200

        # Should be retrievable with GET latest
        latest_response = await client.get(f"/api/vision/{session_id}/latest")
        assert latest_response.status_code == 200
        assert latest_response.json()["grid_width"] == 10

    async def test_capture_different_sessions_independent(self, client: AsyncClient):
        """Different sessions should have independent capture results."""
        response1 = await client.post("/api/vision/session1/capture")
        response2 = await client.post("/api/vision/session2/capture")

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Both should be retrievable separately
        latest1 = await client.get("/api/vision/session1/latest")
        latest2 = await client.get("/api/vision/session2/latest")

        assert latest1.status_code == 200
        assert latest2.status_code == 200


class TestVisionUpload:
    """Tests for POST /api/vision/{session_id}/upload"""

    async def test_upload_image_returns_200_with_analysis(self, client: AsyncClient):
        """Uploading an image should return 200 with analysis."""
        response = await client.post(
            "/api/vision/session1/upload",
            files={"file": ("board.png", b"fake-image-data", "image/png")},
        )

        assert response.status_code == 200
        data = response.json()
        assert "grid_width" in data
        assert "grid_height" in data
        assert "tokens" in data
        assert "confidence" in data

    async def test_upload_without_file_returns_422(self, client: AsyncClient):
        """Uploading without a file should return 422."""
        response = await client.post("/api/vision/session1/upload")

        assert response.status_code == 422

    async def test_upload_stores_result_in_memory(self, client: AsyncClient):
        """Upload should store result in memory storage."""
        session_id = "session3"

        # Upload an image
        response = await client.post(
            f"/api/vision/{session_id}/upload",
            files={"file": ("board.png", b"fake-image-data", "image/png")},
        )
        assert response.status_code == 200

        # Should be retrievable with GET latest
        latest_response = await client.get(f"/api/vision/{session_id}/latest")
        assert latest_response.status_code == 200
        assert latest_response.json()["grid_width"] == 10

    async def test_upload_analyzes_image(self, client: AsyncClient):
        """Upload should pass image through BoardAnalyzer."""
        image_data = b"test-image-bytes"

        response = await client.post(
            "/api/vision/session1/upload",
            files={"file": ("board.png", image_data, "image/png")},
        )

        assert response.status_code == 200
        data = response.json()
        # FakeBoardAnalyzer returns empty tokens list by default
        assert isinstance(data["tokens"], list)


class TestVisionLatest:
    """Tests for GET /api/vision/{session_id}/latest"""

    async def test_latest_returns_404_for_unknown_session(self, client: AsyncClient):
        """Getting latest for unknown session should return 404."""
        response = await client.get("/api/vision/unknown_session/latest")

        assert response.status_code == 404

    async def test_latest_returns_most_recent_analysis(self, client: AsyncClient):
        """Getting latest should return most recent analysis."""
        session_id = "session2"

        # First capture
        response1 = await client.post(f"/api/vision/{session_id}/capture")
        assert response1.status_code == 200

        # Get latest
        latest_response = await client.get(f"/api/vision/{session_id}/latest")

        assert latest_response.status_code == 200
        data = latest_response.json()
        assert data["grid_width"] == 10
        assert data["grid_height"] == 10

    async def test_latest_after_upload(self, client: AsyncClient):
        """Latest should return the uploaded image analysis."""
        session_id = "session4"

        # Upload an image
        response = await client.post(
            f"/api/vision/{session_id}/upload",
            files={"file": ("board.png", b"image-data", "image/png")},
        )
        assert response.status_code == 200

        # Get latest - should be the same as the upload response
        latest_response = await client.get(f"/api/vision/{session_id}/latest")
        assert latest_response.status_code == 200
        assert latest_response.json() == response.json()

    async def test_latest_multiple_captures_returns_last(self, client: AsyncClient):
        """After multiple captures, latest should return the last one."""
        session_id = "session5"

        # Multiple captures
        await client.post(f"/api/vision/{session_id}/capture")
        await client.post(f"/api/vision/{session_id}/capture")
        response3 = await client.post(f"/api/vision/{session_id}/capture")

        # Get latest
        latest_response = await client.get(f"/api/vision/{session_id}/latest")

        assert latest_response.status_code == 200
        # Should be consistent with the last capture
        assert latest_response.json() == response3.json()
