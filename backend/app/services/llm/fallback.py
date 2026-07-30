"""Resilient LLM provider — primary with automatic fallback.

Makes cloud narration first-class for consistency (e.g. Anthropic/OpenAI)
while keeping local Ollama as a safety net (or vice versa): if the primary
provider errors or times out, the request is retried on the fallback so
the table never stalls on a dead API.
"""
from __future__ import annotations

import asyncio
import logging
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
    ):
        self._primary = primary
        self._fallback = fallback
        self._primary_timeout = primary_timeout
        # Ollama-detection heuristic used by DMNarrator for compact prompts —
        # mirror the primary so prompt sizing matches the model actually used.
        if hasattr(primary, "_base_url"):
            self._base_url = primary._base_url

    @property
    def name(self) -> str:
        return f"{self._primary.name}+fallback:{self._fallback.name}"

    async def generate(
        self,
        messages: list[LLMMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        try:
            return await asyncio.wait_for(
                self._primary.generate(
                    messages=messages,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                ),
                timeout=self._primary_timeout,
            )
        except Exception as exc:
            logger.warning(
                "Primary LLM (%s) failed (%s: %s) — falling back to %s",
                self._primary.name, type(exc).__name__, exc, self._fallback.name,
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
        try:
            async for chunk in self._primary.stream(
                messages=messages,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            ):
                yielded = True
                yield chunk
            return
        except Exception as exc:
            if yielded:
                # Mid-stream failure: can't restart without duplicating output.
                logger.error(
                    "Primary LLM (%s) died mid-stream (%s) — truncating",
                    self._primary.name, exc,
                )
                return
            logger.warning(
                "Primary LLM (%s) stream failed (%s: %s) — falling back to %s",
                self._primary.name, type(exc).__name__, exc, self._fallback.name,
            )
        async for chunk in self._fallback.stream(
            messages=messages,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        ):
            yield chunk
