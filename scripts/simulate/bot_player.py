"""One bot player = one WebSocket connection + one action policy.

The default policy is a scripted iterator (for deterministic smoke tests).
Phase 2 will introduce an LLM-backed policy (AutoGen `AssistantAgent`) that
plugs into the same `ActionPolicy` interface.
"""
from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import AsyncIterator, Awaitable, Callable, Iterable, Optional, Protocol

import websockets
from websockets.asyncio.client import ClientConnection

from .api_client import ApiClient, JoinedSession

logger = logging.getLogger(__name__)


PolicyFn = Callable[["BotPlayer", Optional[dict]], Awaitable[Optional[str]]]


class ActionPolicy(Protocol):
    """Strategy used by a bot to decide its next action."""

    async def next_action(
        self, bot: "BotPlayer", incoming: Optional[dict]
    ) -> Optional[str]:
        ...


class ScriptedPolicy:
    """Yields a fixed sequence of actions, one per turn. Stops when exhausted."""

    def __init__(self, actions: Iterable[str]):
        self._actions = list(actions)
        self._idx = 0

    async def next_action(
        self, bot: "BotPlayer", incoming: Optional[dict]
    ) -> Optional[str]:
        if self._idx >= len(self._actions):
            return None
        action = self._actions[self._idx]
        self._idx += 1
        return action

    @property
    def remaining(self) -> int:
        return max(0, len(self._actions) - self._idx)


@dataclass
class BotConfig:
    """Static identity of a bot."""

    name: str
    character_id: Optional[str] = None
    policy: Optional[ActionPolicy] = None


@dataclass
class TranscriptEntry:
    """One event recorded by the harness."""

    bot: str
    direction: str  # "sent" | "recv"
    message: dict
    ts: float = field(default_factory=lambda: asyncio.get_event_loop().time())

    def to_jsonable(self) -> dict:
        return {
            "bot": self.bot,
            "direction": self.direction,
            "message": self.message,
            "ts": round(self.ts, 6),
        }


class BotPlayer:
    """A single bot player driving one WS connection against the backend."""

    def __init__(
        self,
        config: BotConfig,
        api: ApiClient,
        ws_base_url: str,
        *,
        transcript: Optional[list[TranscriptEntry]] = None,
        turn_owner: Optional["TurnOwner"] = None,
    ):
        self.config = config
        self.api = api
        self.ws_base_url = ws_base_url.rstrip("/")
        self.transcript = transcript if transcript is not None else []
        self.turn_owner = turn_owner
        self.joined: Optional[JoinedSession] = None
        self._ws: Optional[ClientConnection] = None
        self._stopped = False
        self._turns_taken = 0

    # ---- lifecycle --------------------------------------------------------

    async def join(self, room_code: str) -> JoinedSession:
        self.joined = await self.api.join(
            room_code, self.config.name, self.config.character_id
        )
        return self.joined

    async def connect(self) -> None:
        assert self.joined is not None, "must join() before connect()"
        url = f"{self.ws_base_url}/ws/game/{self.joined.session_id}"
        self._ws = await websockets.connect(url, ping_interval=20, ping_timeout=10)
        logger.debug("%s connected to %s", self.config.name, url)

    async def announce(self) -> None:
        """Send player_join and player_ready over the WS."""
        await self._send({
            "type": "player_join",
            "name": self.config.name,
            "character_id": self.config.character_id,
            # Phase 3 will server-side honor this; today it's ignored.
            "player_id": self.joined.player_id if self.joined else None,
        })
        await self._send({"type": "player_ready", "ready": True})

    async def close(self) -> None:
        self._stopped = True
        if self._ws is not None:
            try:
                await self._ws.close()
            except Exception:
                pass
            self._ws = None

    # ---- I/O --------------------------------------------------------------

    async def _send(self, message: dict) -> None:
        assert self._ws is not None
        payload = json.dumps(message)
        await self._ws.send(payload)
        self.transcript.append(
            TranscriptEntry(bot=self.config.name, direction="sent", message=message)
        )

    # ---- driver loop ------------------------------------------------------

    async def take_initial_turn(self) -> None:
        """Send the first action without waiting for incoming messages."""
        policy = self.config.policy
        if policy is None:
            return
        if self.turn_owner is not None and not self.turn_owner.is_my_turn(self):
            return
        action = await policy.next_action(self, None)
        if action is None:
            return
        await self._send_action(action)

    async def run(
        self,
        *,
        max_turns: int,
        idle_timeout: float = 2.0,
        max_consecutive_idles: int = 4,
    ) -> None:
        """Receive loop: on each `turn_result` (or `chat`), maybe respond.

        Exits when (a) policy returns None for us, (b) max_turns reached,
        (c) we've been idle for `max_consecutive_idles × idle_timeout` seconds
        with no actionable message (the scenario has wound down).
        """
        assert self._ws is not None
        policy = self.config.policy
        idle_count = 0

        while not self._stopped and self._turns_taken < max_turns:
            try:
                raw = await asyncio.wait_for(self._ws.recv(), timeout=idle_timeout)
            except asyncio.TimeoutError:
                # If a TurnOwner is gating us and it's not our turn, don't age
                # out — another bot may be mid-LLM-call. Only true global idle
                # (no messages for everyone) should exit; we detect that via
                # the OTHER bots eventually advancing turn_owner past us, OR
                # via the runner's wall-clock timeout.
                if self.turn_owner is not None and not self.turn_owner.is_my_turn(self):
                    continue
                idle_count += 1
                if idle_count >= max_consecutive_idles:
                    logger.debug("%s exiting after %d idle ticks", self.config.name, idle_count)
                    return
                if policy is None:
                    continue
                action = await policy.next_action(self, None)
                if action is None:
                    if self.turn_owner is not None:
                        self.turn_owner.remove(self)
                    return
                await self._send_action(action)
                idle_count = 0
                continue
            except websockets.ConnectionClosed:
                logger.debug("%s ws closed", self.config.name)
                return

            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue
            self.transcript.append(
                TranscriptEntry(bot=self.config.name, direction="recv", message=msg)
            )

            # Don't count chatter/player_update broadcasts as idle progress —
            # only true wall-clock timeouts should age the bot out.
            if not await self._should_react(msg):
                continue
            idle_count = 0

            if policy is None:
                continue
            action = await policy.next_action(self, msg)
            if action is None:
                # Policy exhausted — drop from turn rotation so peers don't
                # block waiting for our turn that will never come.
                if self.turn_owner is not None:
                    self.turn_owner.remove(self)
                return
            await self._send_action(action)

    async def _should_react(self, msg: dict) -> bool:
        """Default filter: react to turn_result/chat from others when it's our turn."""
        mtype = msg.get("type")
        if mtype not in ("turn_result", "chat"):
            return False
        # Don't reply to our own narration (only meaningful when we have an id).
        if mtype == "turn_result":
            cid = msg.get("character_id")
            if cid is not None and cid == self.config.character_id:
                return False
        if self.turn_owner is not None and not self.turn_owner.is_my_turn(self):
            return False
        return True

    async def _send_action(self, action: str) -> None:
        await self._send({
            "type": "action",
            "character_id": self.config.character_id,
            "action": action,
        })
        self._turns_taken += 1
        if self.turn_owner is not None:
            self.turn_owner.advance()


class TurnOwner:
    """Harness-side round-robin gate.

    Phase 3 will replace this with the server-broadcast `current_speaker_id`.
    """

    def __init__(self, bots: list[BotPlayer]):
        self._bots = bots
        self._idx = 0

    def is_my_turn(self, bot: BotPlayer) -> bool:
        if not self._bots:
            return False
        return self._bots[self._idx % len(self._bots)] is bot

    def advance(self) -> None:
        self._idx += 1

    def remove(self, bot: BotPlayer) -> None:
        """Drop a bot from the rotation when its policy is exhausted.

        Without this, the round-robin gate would keep waiting for a turn
        that the exhausted bot will never take, leaving other bots blocked
        until the wall-clock timeout fires.
        """
        if bot in self._bots:
            i = self._bots.index(bot)
            self._bots.remove(bot)
            # Keep _idx pointing at the same logical "next" bot.
            if self._bots and i < (self._idx % (len(self._bots) + 1)):
                self._idx = max(0, self._idx - 1)
