"""Test configuration for vision tests."""
import pytest
from httpx import ASGITransport, AsyncClient

from app.api import storage


@pytest.fixture
def app():
    """Create a fresh FastAPI app instance for testing."""
    # Import here to avoid the SRD models issue during conftest loading
    from app.main import create_app
    return create_app()


@pytest.fixture
async def client(app):
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
def reset_storage():
    """Reset in-memory storage before and after each test."""
    storage.reset()
    yield
    storage.reset()
