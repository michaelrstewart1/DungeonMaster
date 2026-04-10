"""
Ollama LLM provider adapter for D&D 5e AI Dungeon Master.

This module provides integration with the Ollama API for local LLM inference.
"""

import httpx
import json
from typing import AsyncIterator, Optional
import logging

from .base import LLMProvider, LLMMessage, LLMResponse, LLMUsage, LLMStreamChunk

logger = logging.getLogger(__name__)


class OllamaError(Exception):
    """Base exception for Ollama API errors."""
    pass


class OllamaConnectionError(OllamaError):
    """Exception for connection errors (Ollama not running)."""
    pass


class OllamaProvider(LLMProvider):
    """Ollama LLM provider.

    Implements the LLMProvider interface for local models via the Ollama API.
    Includes support for both standard generation and streaming responses.
    """

    DEFAULT_BASE_URL = "http://localhost:11434"
    DEFAULT_MODEL = "llama3.1:8b"

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        model: str = DEFAULT_MODEL,
    ):
        """Initialize the Ollama provider.

        Args:
            base_url: The base URL for the Ollama API (default: http://localhost:11434)
            model: The model to use (default: llama3.1:8b)
        """
        self._base_url = base_url
        self._model = model
        self._client = httpx.AsyncClient(timeout=120.0)

    @property
    def name(self) -> str:
        """Return the name of this LLM provider."""
        return "ollama"

    async def generate(
        self,
        messages: list[LLMMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        """Generate a response from Ollama.

        Args:
            messages: List of message objects with role and content
            system_prompt: Optional system prompt to guide the LLM
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens in the response

        Returns:
            LLMResponse containing the generated content and metadata

        Raises:
            OllamaConnectionError: If Ollama is not running
            OllamaError: For other API errors
        """
        # Format messages for Ollama API
        formatted_messages = self._format_messages(messages)

        # Build request payload
        payload = {
            "model": self._model,
            "messages": formatted_messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        # Add system message if provided
        if system_prompt:
            payload["system"] = system_prompt

        try:
            response = await self._client.post(
                f"{self._base_url}/api/chat",
                json=payload,
            )

            # Check for errors
            if response.status_code >= 400:
                raise OllamaError(
                    f"Ollama API error ({response.status_code}): {response.text}"
                )

            # Parse successful response
            data = response.json()
            content = data.get("response", "")

            return LLMResponse(
                content=content,
                model=data.get("model", self._model),
                usage=LLMUsage(),  # Ollama doesn't provide token counts in non-streaming
            )

        except httpx.ConnectError as e:
            raise OllamaConnectionError(
                f"Failed to connect to Ollama at {self._base_url}: {str(e)}"
            )
        except OllamaError:
            raise
        except Exception as e:
            raise OllamaError(f"Unexpected error: {str(e)}")

    async def stream(
        self,
        messages: list[LLMMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> AsyncIterator[LLMStreamChunk]:
        """Stream a response from Ollama.

        Args:
            messages: List of message objects with role and content
            system_prompt: Optional system prompt to guide the LLM
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens in the response

        Yields:
            LLMStreamChunk objects representing partial responses

        Raises:
            OllamaConnectionError: If Ollama is not running
            OllamaError: For other API errors
        """
        # Format messages for Ollama API
        formatted_messages = self._format_messages(messages)

        # Build request payload
        payload = {
            "model": self._model,
            "messages": formatted_messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        # Add system message if provided
        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with self._client.stream(
                "POST",
                f"{self._base_url}/api/chat",
                json=payload,
            ) as response:
                if response.status_code >= 400:
                    raise OllamaError(
                        f"Ollama API error ({response.status_code})"
                    )

                # Process streaming response
                async for line in response.aiter_lines():
                    # Skip empty lines
                    if not line or line.isspace():
                        continue

                    try:
                        event_data = json.loads(line)
                        content = event_data.get("response", "")
                        is_done = event_data.get("done", False)

                        # Yield content chunk if present
                        if content:
                            yield LLMStreamChunk(
                                content=content,
                                is_final=is_done,
                            )
                        elif is_done:
                            # Yield empty final chunk to mark completion
                            yield LLMStreamChunk(content="", is_final=True)

                    except json.JSONDecodeError:
                        logger.debug(f"Failed to parse JSON: {line}")
                        continue

        except httpx.ConnectError as e:
            raise OllamaConnectionError(
                f"Failed to connect to Ollama at {self._base_url}: {str(e)}"
            )
        except OllamaError:
            raise
        except Exception as e:
            raise OllamaError(f"Unexpected error: {str(e)}")

    def _format_messages(self, messages: list[LLMMessage]) -> list[dict]:
        """Format messages for Ollama API format.

        Ollama API expects a list of message objects with role and content.
        System prompts are passed separately in the payload.

        Args:
            messages: List of LLMMessage objects

        Returns:
            List of dicts formatted for Ollama API
        """
        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
            if msg.role != "system"  # System role is handled separately
        ]

    async def __aenter__(self):
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup client."""
        await self._client.aclose()

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()
