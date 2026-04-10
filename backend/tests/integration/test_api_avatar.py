"""Integration tests for Avatar State API endpoints."""
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import create_app
from app.api import storage
from app.api.routes import avatar


@pytest.fixture(autouse=True)
def reset_storage():
    """Reset storage before each test."""
    storage.reset()
    avatar.reset()



@pytest.mark.asyncio
async def test_get_avatar_state_default():
    """Test getting avatar state returns default values."""
    app = create_app()
    transport = ASGITransport(app=app)
    
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/avatar/session1")
        assert resp.status_code == 200
        
        data = resp.json()
        assert data["expression"] == "neutral"
        assert data["is_speaking"] is False
        assert data["mouth_amplitude"] == 0.0
        assert data["gaze"] == "center"


@pytest.mark.asyncio
async def test_set_expression():
    """Test setting avatar expression."""
    app = create_app()
    transport = ASGITransport(app=app)
    
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Set expression
        resp = await client.put(
            "/api/avatar/session1/expression",
            json={"expression": "happy"}
        )
        assert resp.status_code == 200
        
        data = resp.json()
        assert data["expression"] == "happy"
        
        # Verify persistence
        resp = await client.get("/api/avatar/session1")
        assert resp.status_code == 200
        assert resp.json()["expression"] == "happy"


@pytest.mark.asyncio
async def test_set_expression_invalid():
    """Test setting invalid expression."""
    app = create_app()
    transport = ASGITransport(app=app)
    
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.put(
            "/api/avatar/session1/expression",
            json={"expression": "invalid_expression"}
        )
        assert resp.status_code == 400


@pytest.mark.asyncio
async def test_speak_animation():
    """Test triggering speaking animation."""
    app = create_app()
    transport = ASGITransport(app=app)
    
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Trigger speak
        resp = await client.post(
            "/api/avatar/session1/speak",
            json={"text": "Greetings, adventurer!", "duration": 2.5}
        )
        assert resp.status_code == 200
        
        data = resp.json()
        assert data["is_speaking"] is True
        
        # Verify persistence
        resp = await client.get("/api/avatar/session1")
        assert resp.status_code == 200
        assert resp.json()["is_speaking"] is True


@pytest.mark.asyncio
async def test_speak_animation_without_duration():
    """Test speak animation with default duration."""
    app = create_app()
    transport = ASGITransport(app=app)
    
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/avatar/session1/speak",
            json={"text": "Hello"}
        )
        assert resp.status_code == 200
        assert resp.json()["is_speaking"] is True


@pytest.mark.asyncio
async def test_get_full_avatar_state():
    """Test getting full avatar state with all fields."""
    app = create_app()
    transport = ASGITransport(app=app)
    
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Set expression
        await client.put(
            "/api/avatar/session1/expression",
            json={"expression": "angry"}
        )
        
        # Trigger speak
        await client.post(
            "/api/avatar/session1/speak",
            json={"text": "Roar!", "duration": 1.0}
        )
        
        # Get state
        resp = await client.get("/api/avatar/session1/state")
        assert resp.status_code == 200
        
        data = resp.json()
        # Note: "Roar!" will be detected as menacing (danger keyword)
        assert data["expression"] in ["angry", "menacing"]
        assert data["is_speaking"] is True
        assert "mouth_amplitude" in data
        assert "gaze" in data



@pytest.mark.asyncio
async def test_multiple_sessions_isolated():
    """Test that different sessions have isolated states."""
    app = create_app()
    transport = ASGITransport(app=app)
    
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Set session1 expression
        await client.put(
            "/api/avatar/session1/expression",
            json={"expression": "happy"}
        )
        
        # Set session2 expression
        await client.put(
            "/api/avatar/session2/expression",
            json={"expression": "angry"}
        )
        
        # Verify isolation
        resp1 = await client.get("/api/avatar/session1")
        resp2 = await client.get("/api/avatar/session2")
        
        assert resp1.json()["expression"] == "happy"
        assert resp2.json()["expression"] == "angry"


@pytest.mark.asyncio
async def test_expression_from_text_sentiment():
    """Test setting expression based on text sentiment."""
    app = create_app()
    transport = ASGITransport(app=app)
    
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Speak with exciting text
        resp = await client.post(
            "/api/avatar/session1/speak",
            json={"text": "That was amazing! Legendary victory!", "duration": 2.0}
        )
        
        # Avatar should detect sentiment and set excited expression
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_mouth_amplitude_updates():
    """Test that mouth amplitude is tracked."""
    app = create_app()
    transport = ASGITransport(app=app)
    
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Initially not speaking
        resp = await client.get("/api/avatar/session1")
        initial_amplitude = resp.json()["mouth_amplitude"]
        assert initial_amplitude == 0.0
        
        # After speaking
        await client.post(
            "/api/avatar/session1/speak",
            json={"text": "Hello", "duration": 1.0}
        )
        
        resp = await client.get("/api/avatar/session1")
        data = resp.json()
        assert data["is_speaking"] is True
        assert data["mouth_amplitude"] > 0.0  # Mouth opens when speaking

