"""AutoGen-backed `ActionPolicy` for bot players (Phase 2).

Each `LLMPolicy` wraps a single AutoGen `AssistantAgent` whose persona is
defined in `PERSONAS`. The policy:

  - Reads the latest DM narration / chat / `None` (when nudged by a timeout).
  - Calls the agent with a buffered context (last 15 messages).
  - Injects a reminder system message every 5 turns.
  - Guards the output against common LLM tells ("As an AI…", out-of-character
    asides, narrating other PCs). On guard failure: retry up to 2 times, else
    fall back to a canned, in-character idle line.

If Ollama is not reachable, `LLMPolicy.try_create()` returns None and the
caller can substitute a `ScriptedPolicy` (graceful CI degradation).
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Iterable, Optional

from .bot_player import ActionPolicy, BotPlayer

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Personas (mirror the 4 mock characters in
# `frontend/tests/e2e/multiplayer-simulation.spec.ts:16-53`).
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Persona:
    """Static persona definition consumed by the LLM policy."""

    name: str
    system_prompt: str
    idle_fallback: str = "*pauses thoughtfully, watching the others*"


def _build_prompt(identity: str, sheet: str) -> str:
    """Build a short structured system prompt (target ≤300 tokens)."""
    return (
        f"IDENTITY: {identity}\n\n"
        f"CHARACTER SHEET: {sheet}\n\n"
        "RULES:\n"
        "- Always speak and act in first person as your character.\n"
        "- Never narrate what other player characters do, think, or say.\n"
        "- Never break the fourth wall or refer to yourself as an AI.\n"
        "- Keep responses to 1-3 short sentences describing only your own action or speech.\n"
        "- If you want to roll, describe the intent (e.g. 'I try to sneak…'); the DM rolls.\n"
        "- Do not invent NPCs or scene elements the DM has not introduced.\n"
    )


PERSONAS: dict[str, Persona] = {
    "Lyra Moonwhisper": Persona(
        name="Lyra Moonwhisper",
        system_prompt=_build_prompt(
            identity="A half-elf wizard, scholarly and cautious, fascinated by ancient lore.",
            sheet="Wizard 5, HP 28, AC 13, INT-focused. Spells: detect magic, mage armor, magic missile, misty step.",
        ),
        idle_fallback="*Lyra adjusts her spectacles and studies the room in silence.*",
    ),
    "Thorin Ironforge": Persona(
        name="Thorin Ironforge",
        system_prompt=_build_prompt(
            identity="A dwarf fighter, gruff and protective, quick to defend allies.",
            sheet="Fighter 5, HP 48, AC 18, STR-focused. Greataxe, plate armor, second wind.",
        ),
        idle_fallback="*Thorin grunts and tightens his grip on his axe haft.*",
    ),
    "Zephyr Quickfoot": Persona(
        name="Zephyr Quickfoot",
        system_prompt=_build_prompt(
            identity="A halfling rogue, sly and curious, always scouting for advantage.",
            sheet="Rogue 5, HP 30, AC 15, DEX-focused. Sneak attack 3d6, thieves' tools, shortbow.",
        ),
        idle_fallback="*Zephyr melts back into the shadows, eyes scanning.*",
    ),
    "Grimshaw Stormblade": Persona(
        name="Grimshaw Stormblade",
        system_prompt=_build_prompt(
            identity="A human paladin, righteous and stern, sworn to protect the innocent.",
            sheet="Paladin 5, HP 44, AC 18, CHA-focused. Lay on hands, divine smite, longsword, shield.",
        ),
        idle_fallback="*Grimshaw murmurs a quiet prayer to his god.*",
    ),
}


# ---------------------------------------------------------------------------
# Output guard
# ---------------------------------------------------------------------------

_OOC_PATTERNS = [
    re.compile(r"\bas an ai\b", re.I),
    re.compile(r"\bi (?:cannot|can't) (?:do|help|assist)\b", re.I),
    re.compile(r"\*?\bOOC\b\*?", re.I),
    re.compile(r"\blanguage model\b", re.I),
]


def _violates_guard(text: str, *, other_names: Iterable[str]) -> str | None:
    if not text or not text.strip():
        return "empty response"
    for pat in _OOC_PATTERNS:
        if pat.search(text):
            return f"matched OOC pattern: {pat.pattern}"
    lower = text.lower()
    for other in other_names:
        if not other:
            continue
        # Narrating another PC by name + an action verb is a soft signal of
        # god-modding. We only flag if the other name appears at the start of
        # a sentence followed by a verb-like word.
        pat = re.compile(rf"\b{re.escape(other.split()[0])}\b\s+(?:draws|strikes|casts|says|shouts|moves|jumps|runs|attacks|grabs|opens)", re.I)
        if pat.search(text):
            return f"narrates another PC: {other}"
    return None


# ---------------------------------------------------------------------------
# LLM-backed policy
# ---------------------------------------------------------------------------

@dataclass
class LLMPolicy:
    """An `ActionPolicy` that delegates to an AutoGen `AssistantAgent`."""

    persona: Persona
    other_persona_names: list[str] = field(default_factory=list)
    reminder_every: int = 5
    max_retries: int = 2
    _agent: object = field(default=None, init=False, repr=False)
    _turn_count: int = field(default=0, init=False, repr=False)

    @classmethod
    async def try_create(
        cls,
        persona: Persona,
        *,
        other_persona_names: list[str],
        ollama_host: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Optional["LLMPolicy"]:
        """Construct an LLMPolicy; return None if Ollama isn't reachable.

        `ollama_host` defaults to env `SIMULATE_OLLAMA_HOST` else
        `http://127.0.0.1:11434`. `model` defaults to `SIMULATE_OLLAMA_MODEL`
        else `llama3.1:8b`.
        """
        import os

        ollama_host = ollama_host or os.environ.get(
            "SIMULATE_OLLAMA_HOST", "http://127.0.0.1:11434"
        )
        model = model or os.environ.get("SIMULATE_OLLAMA_MODEL", "llama3.1:8b")
        try:
            from autogen_agentchat.agents import AssistantAgent
            from autogen_core.model_context import BufferedChatCompletionContext
            from autogen_ext.models.ollama import OllamaChatCompletionClient
        except ImportError as exc:
            logger.warning("autogen not installed: %s", exc)
            return None

        # Reachability probe — avoids a long stall if Ollama is down.
        try:
            import httpx

            async with httpx.AsyncClient(timeout=2.0) as client:
                r = await client.get(f"{ollama_host}/api/tags")
                if r.status_code != 200:
                    logger.warning("Ollama at %s returned %d", ollama_host, r.status_code)
                    return None
        except Exception as exc:
            logger.warning("Ollama at %s unreachable: %s", ollama_host, exc)
            return None

        client = OllamaChatCompletionClient(
            model=model,
            host=ollama_host,
            options={"seed": 42, "temperature": 0.0, "num_ctx": 4096},
        )
        agent = AssistantAgent(
            name=re.sub(r"\W+", "_", persona.name),
            model_client=client,
            system_message=persona.system_prompt,
            model_context=BufferedChatCompletionContext(buffer_size=15),
        )
        return cls(persona=persona, other_persona_names=other_persona_names, _agent=agent)

    # -- ActionPolicy --------------------------------------------------------

    async def next_action(
        self, bot: BotPlayer, incoming: Optional[dict]
    ) -> Optional[str]:
        if self._agent is None:
            return self.persona.idle_fallback

        from autogen_agentchat.messages import TextMessage
        from autogen_core import CancellationToken

        self._turn_count += 1

        # Build the DM-facing message text.
        if incoming is None:
            user_text = "[DM]: (silence — the table waits on you)"
        elif incoming.get("type") == "turn_result":
            narration = incoming.get("narration", "") or ""
            user_text = f"[DM]: {narration.strip()}"
        elif incoming.get("type") == "chat":
            sender = incoming.get("sender", "Someone")
            user_text = f"[{sender}]: {incoming.get('message', '').strip()}"
        else:
            user_text = "[DM]: (an indistinct rustling)"

        # Reminder injection every N turns (kept terse to spare token budget).
        if self._turn_count % self.reminder_every == 0:
            user_text = (
                f"[REMINDER: You are {self.persona.name}. Stay in character.]\n"
                + user_text
            )

        # Try up to max_retries+1 times to get a guard-clean response.
        last_violation: str | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = await self._agent.on_messages(
                    [TextMessage(content=user_text, source="DM")],
                    cancellation_token=CancellationToken(),
                )
            except Exception as exc:
                logger.warning("%s: agent call failed (%s)", self.persona.name, exc)
                return self.persona.idle_fallback

            text = ""
            msg = getattr(response, "chat_message", None)
            if msg is not None:
                text = getattr(msg, "content", "") or ""
            text = text.strip()

            violation = _violates_guard(text, other_names=self.other_persona_names)
            if violation is None:
                return text
            last_violation = violation
            logger.debug(
                "%s: guard violation (%s) on attempt %d; retrying",
                self.persona.name,
                violation,
                attempt + 1,
            )

        logger.info(
            "%s: falling back to idle line after guard violations: %s",
            self.persona.name,
            last_violation,
        )
        return self.persona.idle_fallback
