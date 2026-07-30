"""Resilient LLM provider — primary with automatic fallback.

Makes cloud narration first-class for consistency (e.g. Anthropic/OpenAI)
while keeping local Ollama as a safety net (or vice versa): if the primary
provider errors or times out, the request is retried on the fallback so
the table never stalls on a dead API.
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import AsyncIterator, Optional

from app.services.llm.base import (
    LLMMessage,
    LLMProvider,
    LLMResponse,
    LLMStreamChunk,
)

logger = logging.getLogger(__name__)


class FallbackLLMProvider(LLMProvider):
    """Try the primary provider; on error or timeout, use the fallback."""

    def __init__(
        self,
        primary: LLMProvider,
        fallback: LLMProvider,
        primary_timeout: float = 30.0,
        cooldown_seconds: float = 120.0,
    ):
        self._primary = primary
        self._fallback = fallback
        self._primary_timeout = primary_timeout
        # Circuit breaker: after a primary failure, route straight to the
        # fallback for this long instead of paying the primary's retry/timeout
        # tax on every request (e.g. Gemini 429 storms added 3-9s per call).
        self._cooldown_seconds = cooldown_seconds
        self._primary_down_until = 0.0

    def serving_locally(self) -> bool:
        """True when the provider that will serve the NEXT request is a
        local model (Ollama). DMNarrator uses this per-request to pick
        compact prompts/token budgets for the GPU and rich ones for the
        cloud — a static decision at startup mislabeled Gemini as local
        (or vice versa) and truncated cloud narrations at 200 tokens."""
        active = self._primary if self._primary_available() else self._fallback
        return hasattr(active, "_base_url")

    @property
    def name(self) -> str:
        return f"{self._primary.name}+fallback:{self._fallback.name}"

    def _primary_available(self) -> bool:
        return time.monotonic() >= self._primary_down_until

    def _trip_breaker(self) -> None:
        self._primary_down_until = time.monotonic() + self._cooldown_seconds

    async def generate(
        self,
        messages: list[LLMMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        if self._primary_available():
            try:
                result = await asyncio.wait_for(
                    self._primary.generate(
                        messages=messages,
                        system_prompt=system_prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    ),
                    timeout=self._primary_timeout,
                )
                self._primary_down_until = 0.0
                return result
            except Exception as exc:
                self._trip_breaker()
                logger.warning(
                    "Primary LLM (%s) failed (%s: %s) — falling back to %s for %.0fs",
                    self._primary.name, type(exc).__name__, exc,
                    self._fallback.name, self._cooldown_seconds,
                )
        return await self._fallback.generate(
            messages=messages,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def stream(
        self,
        messages: list[LLMMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> AsyncIterator[LLMStreamChunk]:
        yielded = False
        if self._primary_available():
            try:
                async for chunk in self._primary.stream(
                    messages=messages,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                ):
                    yielded = True
                    yield chunk
                self._primary_down_until = 0.0
                return
            except Exception as exc:
                if yielded:
                    # Mid-stream failure: can't restart without duplicating output.
                    logger.error(
                        "Primary LLM (%s) died mid-stream (%s) — truncating",
                        self._primary.name, exc,
                    )
                    return
                self._trip_breaker()
                logger.warning(
                    "Primary LLM (%s) stream failed (%s: %s) — falling back to %s for %.0fs",
                    self._primary.name, type(exc).__name__, exc,
                    self._fallback.name, self._cooldown_seconds,
                )
        async for chunk in self._fallback.stream(
            messages=messages,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        ):
            yield chunk
