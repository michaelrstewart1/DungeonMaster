"""
OpenAI LLM provider adapter for D&D 5e AI Dungeon Master.

This module provides integration with the OpenAI Chat Completions API.
"""

import httpx
import json
from typing import AsyncIterator, Optional
import logging

from .base import LLMProvider, LLMMessage, LLMResponse, LLMUsage, LLMStreamChunk

logger = logging.getLogger(__name__)


class OpenAIError(Exception):
    """Base exception for OpenAI API errors."""
    pass


class OpenAIAuthError(OpenAIError):
    """Exception for authentication errors (401)."""
    pass


class OpenAIRateLimitError(OpenAIError):
    """Exception for rate limit errors (429)."""
    pass


class OpenAIServerError(OpenAIError):
    """Exception for server errors (5xx)."""
    pass


class OpenAIProvider(LLMProvider):
    """OpenAI Chat Completions LLM provider.

    Implements the LLMProvider interface for OpenAI models via the Chat Completions API.
    Includes support for both standard generation and streaming responses.
    """

    API_BASE = "https://api.openai.com/v1"
    DEFAULT_MODEL = "gpt-4o"

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        """Initialize the OpenAI provider.

        Args:
            api_key: Your OpenAI API key
            model: The model to use (default: gpt-4o)
        """
        self._api_key = api_key
        self._model = model
        self._client = httpx.AsyncClient(timeout=60.0)

    @property
    def name(self) -> str:
        """Return the name of this LLM provider."""
        return "openai"

    async def generate(
        self,
        messages: list[LLMMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        """Generate a response from OpenAI.

        Args:
            messages: List of message objects with role and content
            system_prompt: Optional system prompt to guide the LLM
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens in the response

        Returns:
            LLMResponse containing the generated content and metadata

        Raises:
            OpenAIAuthError: If API key is invalid (401)
            OpenAIRateLimitError: If rate limited (429)
            OpenAIServerError: If server error (5xx)
            OpenAIError: For other API errors
        """
        # Format messages for OpenAI API
        formatted_messages = self._format_messages(messages, system_prompt)

        # Build request payload
        payload = {
            "model": self._model,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        # Prepare headers
        headers = self._get_headers()

        try:
            response = await self._client.post(
                f"{self.API_BASE}/chat/completions",
                json=payload,
                headers=headers,
            )

            # Check for errors
            if response.status_code == 401:
                raise OpenAIAuthError(
                    f"Authentication failed (401): Invalid API key"
                )
            elif response.status_code == 429:
                raise OpenAIRateLimitError(
                    f"Rate limit exceeded (429): Too many requests"
                )
            elif response.status_code >= 500:
                raise OpenAIServerError(
                    f"Server error ({response.status_code}): {response.text}"
                )
            elif response.status_code >= 400:
                error_data = response.json()
                raise OpenAIError(
                    f"API error ({response.status_code}): "
                    f"{error_data.get('error', {}).get('message', 'Unknown error')}"
                )

            # Parse successful response
            data = response.json()
            content = self._extract_content(data)
            usage = self._extract_usage(data)

            return LLMResponse(
                content=content,
                model=data.get("model", self._model),
                usage=usage,
            )

        except (OpenAIAuthError, OpenAIRateLimitError, OpenAIServerError, OpenAIError):
            raise
        except httpx.ConnectError as e:
            raise OpenAIError(f"Connection error: {str(e)}")
        except Exception as e:
            raise OpenAIError(f"Unexpected error: {str(e)}")

    async def stream(
        self,
        messages: list[LLMMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> AsyncIterator[LLMStreamChunk]:
        """Stream a response from OpenAI.

        Args:
            messages: List of message objects with role and content
            system_prompt: Optional system prompt to guide the LLM
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens in the response

        Yields:
            LLMStreamChunk objects representing partial responses

        Raises:
            OpenAIAuthError: If API key is invalid (401)
            OpenAIRateLimitError: If rate limited (429)
            OpenAIServerError: If server error (5xx)
            OpenAIError: For other API errors
        """
        # Format messages for OpenAI API
        formatted_messages = self._format_messages(messages, system_prompt)

        # Build request payload
        payload = {
            "model": self._model,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        # Prepare headers
        headers = self._get_headers()

        async with self._client.stream(
            "POST",
            f"{self.API_BASE}/chat/completions",
            json=payload,
            headers=headers,
        ) as response:
            if response.status_code == 401:
                raise OpenAIAuthError(
                    f"Authentication failed (401): Invalid API key"
                )
            elif response.status_code == 429:
                raise OpenAIRateLimitError(
                    f"Rate limit exceeded (429): Too many requests"
                )
            elif response.status_code >= 500:
                raise OpenAIServerError(
                    f"Server error ({response.status_code})"
                )
            elif response.status_code >= 400:
                raise OpenAIError(f"API error ({response.status_code})")

            # Process streaming response
            async for line in response.aiter_lines():
                # Skip empty lines
                if not line or line.isspace():
                    continue

                # Handle Server-Sent Events format
                if line.startswith("data: "):
                    json_str = line[6:]  # Remove "data: " prefix

                    # Check for end marker
                    if json_str == "[DONE]":
                        # Yield final chunk to mark completion
                        yield LLMStreamChunk(content="", is_final=True)
                        continue

                    try:
                        event_data = json.loads(json_str)
                        choices = event_data.get("choices", [])

                        # Extract content from delta
                        if choices:
                            delta = choices[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield LLMStreamChunk(content=content, is_final=False)

                    except json.JSONDecodeError:
                        logger.debug(f"Failed to parse JSON: {json_str}")
                        continue

    def _format_messages(
        self,
        messages: list[LLMMessage],
        system_prompt: Optional[str] = None,
    ) -> list[dict]:
        """Format messages for OpenAI API format.

        OpenAI API expects system message first (role: "system"),
        then other messages in conversation order.

        Args:
            messages: List of LLMMessage objects
            system_prompt: Optional system prompt to add at the beginning

        Returns:
            List of dicts formatted for OpenAI API
        """
        formatted = []

        # Add system message first if provided
        if system_prompt:
            formatted.append({"role": "system", "content": system_prompt})

        # Add all other messages, filtering out system messages from input
        for msg in messages:
            if msg.role != "system":
                formatted.append({"role": msg.role, "content": msg.content})

        return formatted

    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers for OpenAI API requests.

        Returns:
            Dict of headers with API key and content type
        """
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    def _extract_content(self, response_data: dict) -> str:
        """Extract text content from OpenAI API response.

        Args:
            response_data: The JSON response from the API

        Returns:
            The extracted text content
        """
        choices = response_data.get("choices", [])
        if choices:
            message = choices[0].get("message", {})
            return message.get("content", "")
        return ""

    def _extract_usage(self, response_data: dict) -> LLMUsage:
        """Extract token usage from OpenAI API response.

        Args:
            response_data: The JSON response from the API

        Returns:
            LLMUsage object with prompt and completion tokens
        """
        usage_data = response_data.get("usage", {})
        return LLMUsage(
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
        )

    async def __aenter__(self):
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup client."""
        await self._client.aclose()

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()
