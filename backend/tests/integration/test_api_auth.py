"""Tests for simple token-based auth — TDD red phase first."""
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import create_app
from app.api import storage


@pytest.fixture(autouse=True)
def _reset_storage():
    storage.reset()
    yield
    storage.reset()


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ── Registration ──


class TestRegister:
    async def test_register_player(self, client: AsyncClient):
        resp = await client.post("/api/auth/register", json={
            "username": "gandalf",
            "password": "youshallnotpass",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "gandalf"
        assert "id" in data
        assert "password" not in data

    async def test_register_duplicate_username(self, client: AsyncClient):
        await client.post("/api/auth/register", json={
            "username": "gandalf",
            "password": "pw1",
        })
        resp = await client.post("/api/auth/register", json={
            "username": "gandalf",
            "password": "pw2",
        })
        assert resp.status_code == 409
        assert "already exists" in resp.json()["detail"].lower()

    async def test_register_missing_fields(self, client: AsyncClient):
        resp = await client.post("/api/auth/register", json={"username": "gandalf"})
        assert resp.status_code == 422

    async def test_register_short_password(self, client: AsyncClient):
        resp = await client.post("/api/auth/register", json={
            "username": "gandalf",
            "password": "ab",
        })
        assert resp.status_code == 422


# ── Login ──


class TestLogin:
    async def test_login_success(self, client: AsyncClient):
        await client.post("/api/auth/register", json={
            "username": "gandalf",
            "password": "youshallnotpass",
        })
        resp = await client.post("/api/auth/login", json={
            "username": "gandalf",
            "password": "youshallnotpass",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data
        assert data["username"] == "gandalf"

    async def test_login_wrong_password(self, client: AsyncClient):
        await client.post("/api/auth/register", json={
            "username": "gandalf",
            "password": "youshallnotpass",
        })
        resp = await client.post("/api/auth/login", json={
            "username": "gandalf",
            "password": "wrong",
        })
        assert resp.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        resp = await client.post("/api/auth/login", json={
            "username": "nobody",
            "password": "pw",
        })
        assert resp.status_code == 401


# ── Token Verification / Protected Endpoints ──


class TestProtectedEndpoints:
    async def _register_and_login(self, client: AsyncClient) -> str:
        await client.post("/api/auth/register", json={
            "username": "gandalf",
            "password": "youshallnotpass",
        })
        resp = await client.post("/api/auth/login", json={
            "username": "gandalf",
            "password": "youshallnotpass",
        })
        return resp.json()["token"]

    async def test_get_me_with_token(self, client: AsyncClient):
        token = await self._register_and_login(client)
        resp = await client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {token}",
        })
        assert resp.status_code == 200
        assert resp.json()["username"] == "gandalf"

    async def test_get_me_no_token(self, client: AsyncClient):
        resp = await client.get("/api/auth/me")
        assert resp.status_code == 401

    async def test_get_me_invalid_token(self, client: AsyncClient):
        resp = await client.get("/api/auth/me", headers={
            "Authorization": "Bearer invalidtoken123",
        })
        assert resp.status_code == 401

    async def test_get_me_malformed_header(self, client: AsyncClient):
        resp = await client.get("/api/auth/me", headers={
            "Authorization": "NotBearer token",
        })
        assert resp.status_code == 401


# ── Token Management ──


class TestTokenManagement:
    async def test_multiple_logins_produce_different_tokens(self, client: AsyncClient):
        await client.post("/api/auth/register", json={
            "username": "gandalf",
            "password": "youshallnotpass",
        })
        resp1 = await client.post("/api/auth/login", json={
            "username": "gandalf",
            "password": "youshallnotpass",
        })
        resp2 = await client.post("/api/auth/login", json={
            "username": "gandalf",
            "password": "youshallnotpass",
        })
        assert resp1.json()["token"] != resp2.json()["token"]

    async def test_old_token_still_valid_after_new_login(self, client: AsyncClient):
        await client.post("/api/auth/register", json={
            "username": "gandalf",
            "password": "youshallnotpass",
        })
        resp1 = await client.post("/api/auth/login", json={
            "username": "gandalf",
            "password": "youshallnotpass",
        })
        token1 = resp1.json()["token"]
        # Log in again
        await client.post("/api/auth/login", json={
            "username": "gandalf",
            "password": "youshallnotpass",
        })
        # First token still works
        resp = await client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {token1}",
        })
        assert resp.status_code == 200
