"""Smoke tests to verify the test infrastructure works."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app


class TestSmoke:
    """Verify the application boots and basic infrastructure works."""

    def test_app_creates_successfully(self):
        """The FastAPI app should be created without errors."""
        app = create_app()
        assert app is not None
        assert app.title == "AI Dungeon Master"

    @pytest.mark.asyncio
    async def test_health_endpoint_returns_200(self):
        """The health check endpoint should return 200 with status info."""
        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "0.1.0"

    @pytest.mark.asyncio
    async def test_health_endpoint_via_fixture(self, client):
        """Test health endpoint using the shared client fixture."""
        response = await client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
