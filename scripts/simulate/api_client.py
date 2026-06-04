"""Thin async HTTP client for the DungeonMaster REST surface used by bots.

Only covers endpoints a bot player needs: create/list/get sessions, fetch room
code, join via room code, list campaigns/characters. Everything else routes
through the WebSocket.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import httpx


@dataclass
class JoinedSession:
    """Result of joining a session via room code."""

    session_id: str
    player_id: str
    campaign_id: str
    room_code: str


class ApiClient:
    """Async HTTP client targeting the FastAPI backend's `/api` surface."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000", *, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        # Disable HTTP keep-alive: the backend's SQLAlchemy session pool has a
        # write-then-read visibility race when two POSTs reuse the same TCP
        # connection (campaign create → session create returns 404 because the
        # second handler picks up a stale session). Forcing a fresh connection
        # per request avoids it without touching backend internals.
        limits = httpx.Limits(max_keepalive_connections=0, max_connections=20)
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=timeout, limits=limits)

    async def __aenter__(self) -> "ApiClient":
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.close()

    async def close(self) -> None:
        await self._client.aclose()

    # ---- Campaigns --------------------------------------------------------

    async def list_campaigns(self) -> list[dict]:
        r = await self._client.get("/api/campaigns")
        r.raise_for_status()
        return r.json()

    async def get_campaign(self, campaign_id: str) -> dict:
        r = await self._client.get(f"/api/campaigns/{campaign_id}")
        r.raise_for_status()
        return r.json()

    async def create_minimal_campaign(self, name: str = "Bot Playtest") -> dict:
        """Create a barebones campaign suitable for bot smoke tests."""
        payload = {
            "name": name,
            "description": "Auto-created by scripts/simulate for bot harness runs.",
            "character_ids": [],
            "world_state": {"context": "A nondescript tavern on a quiet evening."},
            "dm_settings": {},
        }
        r = await self._client.post("/api/campaigns", json=payload)
        r.raise_for_status()
        return r.json()

    # ---- Game sessions ----------------------------------------------------

    async def _post_with_404_retry(self, path: str, payload: dict, *, attempts: int = 4) -> httpx.Response:
        """POST with retry on 404 — the backend commits its DB transaction
        in the dependency cleanup, which runs *after* the response is sent,
        so a follow-up request can race the previous write.
        """
        import asyncio

        last: httpx.Response | None = None
        for i in range(attempts):
            r = await self._client.post(path, json=payload)
            if r.status_code != 404:
                return r
            last = r
            await asyncio.sleep(0.05 * (i + 1))
        assert last is not None
        return last

    async def create_session(
        self,
        campaign_id: str,
        *,
        current_phase: str = "exploration",
        current_scene: str = (
            "You stand in the common room of the Wayfarer's Rest. "
            "A warm fire crackles; a hooded stranger eyes you from a corner booth."
        ),
    ) -> dict:
        payload = {
            "campaign_id": campaign_id,
            "current_phase": current_phase,
            "current_scene": current_scene,
        }
        r = await self._post_with_404_retry("/api/game/sessions", payload)
        r.raise_for_status()
        return r.json()

    async def get_room_code(self, session_id: str) -> str:
        import asyncio

        for i in range(4):
            r = await self._client.get(f"/api/game/sessions/{session_id}/room-code")
            if r.status_code != 404:
                r.raise_for_status()
                return r.json()["room_code"]
            await asyncio.sleep(0.05 * (i + 1))
        r.raise_for_status()
        return r.json()["room_code"]  # unreachable

    async def join(
        self,
        room_code: str,
        player_name: str,
        character_id: Optional[str] = None,
    ) -> JoinedSession:
        payload: dict[str, Any] = {"room_code": room_code, "player_name": player_name}
        if character_id:
            payload["character_id"] = character_id
        r = await self._post_with_404_retry("/api/game/join", payload)
        r.raise_for_status()
        body = r.json()
        return JoinedSession(
            session_id=body["session_id"],
            player_id=body["player_id"],
            campaign_id=body.get("campaign_id", ""),
            room_code=room_code.upper(),
        )

    async def list_players(self, session_id: str) -> list[dict]:
        r = await self._client.get(f"/api/game/sessions/{session_id}/players")
        r.raise_for_status()
        return r.json().get("players", [])

    # ---- Characters -------------------------------------------------------

    async def create_character(self, character: dict) -> dict:
        r = await self._client.post("/api/characters", json=character)
        r.raise_for_status()
        return r.json()

    async def health(self) -> bool:
        try:
            r = await self._client.get("/api/health")
            return r.status_code == 200
        except httpx.HTTPError:
            return False
