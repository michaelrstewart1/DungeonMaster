"""
Google Gemini LLM provider adapter for D&D 5e AI Dungeon Master.

Uses the Gemini REST API (generativelanguage.googleapis.com).
Recommended model: gemini-2.5-flash — fast, cheap, creative.
"""

import asyncio
import httpx
import json
from typing import AsyncIterator, Optional
import logging

from .base import LLMProvider, LLMMessage, LLMResponse, LLMUsage, LLMStreamChunk

logger = logging.getLogger(__name__)


class GeminiError(Exception):
    """Base exception for Gemini API errors."""
    pass


class GeminiAuthError(GeminiError):
    """Exception for authentication errors (401/403)."""
    pass


class GeminiRateLimitError(GeminiError):
    """Exception for rate limit errors (429)."""
    pass


class GeminiServerError(GeminiError):
    """Exception for server errors (5xx)."""
    pass


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider.

    Implements the LLMProvider interface for Gemini models via the
    Google AI generativelanguage REST API.
    """

    API_BASE = "https://generativelanguage.googleapis.com/v1beta"
    DEFAULT_MODEL = "gemini-2.5-flash"
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        self._api_key = api_key
        self._model = model
        self._client = httpx.AsyncClient(timeout=90.0)

    @property
    def name(self) -> str:
        return "gemini"

    async def generate(
        self,
        messages: list[LLMMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        payload = self._build_payload(messages, system_prompt, temperature, max_tokens)
        url = f"{self.API_BASE}/models/{self._model}:generateContent?key={self._api_key}"

        for attempt in range(self.MAX_RETRIES):
            try:
                response = await self._client.post(url, json=payload)
                self._check_errors(response, attempt)

                data = response.json()
                content = self._extract_content(data)
                usage = self._extract_usage(data)

                return LLMResponse(
                    content=content,
                    model=self._model,
                    usage=usage,
                )

            except GeminiRateLimitError:
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_DELAY * (2 ** attempt)
                    logger.warning(
                        "Gemini rate limited. Retrying in %.1fs (attempt %d/%d)",
                        delay, attempt + 1, self.MAX_RETRIES,
                    )
                    await asyncio.sleep(delay)
                    continue
                raise
            except (GeminiAuthError, GeminiServerError, GeminiError):
                raise

        # Should not reach here, but satisfy type checker
        raise GeminiError("Max retries exceeded")  # pragma: no cover

    async def stream(
        self,
        messages: list[LLMMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> AsyncIterator[LLMStreamChunk]:
        payload = self._build_payload(messages, system_prompt, temperature, max_tokens)
        url = (
            f"{self.API_BASE}/models/{self._model}:streamGenerateContent"
            f"?alt=sse&key={self._api_key}"
        )

        async with self._client.stream("POST", url, json=payload) as response:
            if response.status_code in (401, 403):
                raise GeminiAuthError(f"Authentication failed ({response.status_code})")
            elif response.status_code == 429:
                raise GeminiRateLimitError("Rate limit exceeded (429)")
            elif response.status_code >= 500:
                raise GeminiServerError(f"Server error ({response.status_code})")
            elif response.status_code >= 400:
                raise GeminiError(f"API error ({response.status_code})")

            async for line in response.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue

                json_str = line[6:]
                try:
                    event_data = json.loads(json_str)
                    candidates = event_data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        for part in parts:
                            text = part.get("text", "")
                            if text:
                                yield LLMStreamChunk(content=text, is_final=False)
                except json.JSONDecodeError:
                    logger.debug("Failed to parse Gemini SSE: %s", json_str)
                    continue

            yield LLMStreamChunk(content="", is_final=True)

    # --- internal helpers ---

    def _build_payload(
        self,
        messages: list[LLMMessage],
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
    ) -> dict:
        """Build the Gemini API request payload."""
        payload: dict = {
            "contents": self._format_messages(messages),
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        if system_prompt:
            payload["systemInstruction"] = {
                "parts": [{"text": system_prompt}]
            }

        return payload

    def _format_messages(self, messages: list[LLMMessage]) -> list[dict]:
        """Convert LLMMessage list to Gemini contents format.

        Gemini uses 'user' and 'model' roles (not 'assistant').
        System messages are handled via systemInstruction, not contents.
        """
        contents = []
        for msg in messages:
            if msg.role == "system":
                continue
            role = "model" if msg.role == "assistant" else "user"
            contents.append({
                "role": role,
                "parts": [{"text": msg.content}],
            })
        return contents

    def _check_errors(self, response: httpx.Response, attempt: int) -> None:
        """Raise typed exceptions for HTTP error codes."""
        status = response.status_code
        if status in (401, 403):
            raise GeminiAuthError(f"Authentication failed ({status}): check your API key")
        elif status == 429:
            raise GeminiRateLimitError("Rate limit exceeded (429)")
        elif status >= 500:
            raise GeminiServerError(f"Server error ({status}): {response.text[:200]}")
        elif status >= 400:
            try:
                err = response.json().get("error", {}).get("message", response.text[:200])
            except Exception:
                err = response.text[:200]
            raise GeminiError(f"API error ({status}): {err}")

    def _extract_content(self, data: dict) -> str:
        """Extract text from Gemini generateContent response."""
        candidates = data.get("candidates", [])
        if not candidates:
            return ""
        parts = candidates[0].get("content", {}).get("parts", [])
        return "".join(p.get("text", "") for p in parts)

    def _extract_usage(self, data: dict) -> LLMUsage:
        """Extract token usage from Gemini response metadata."""
        usage = data.get("usageMetadata", {})
        return LLMUsage(
            prompt_tokens=usage.get("promptTokenCount", 0),
            completion_tokens=usage.get("candidatesTokenCount", 0),
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._client.aclose()

    async def close(self):
        await self._client.aclose()
