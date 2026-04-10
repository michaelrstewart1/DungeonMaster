"""
Anthropic Claude LLM provider adapter for D&D 5e AI Dungeon Master.

This module provides integration with the Anthropic Claude API.
"""

import asyncio
import httpx
import json
from typing import AsyncIterator, Optional
import logging

from .base import LLMProvider, LLMMessage, LLMResponse, LLMUsage, LLMStreamChunk

logger = logging.getLogger(__name__)


class AnthropicError(Exception):
    """Base exception for Anthropic API errors."""
    pass


class AnthropicAuthError(AnthropicError):
    """Exception for authentication errors (401)."""
    pass


class AnthropicRateLimitError(AnthropicError):
    """Exception for rate limit errors (429)."""
    pass


class AnthropicServerError(AnthropicError):
    """Exception for server errors (5xx)."""
    pass


class AnthropicProvider(LLMProvider):
    """Anthropic Claude LLM provider.
    
    Implements the LLMProvider interface for Claude models via the Anthropic API.
    Includes support for both standard generation and streaming responses.
    """

    API_BASE = "https://api.anthropic.com/v1"
    API_VERSION = "2024-06-01"
    DEFAULT_MODEL = "claude-sonnet-4-20250514"
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        """Initialize the Anthropic provider.
        
        Args:
            api_key: Your Anthropic API key
            model: The model to use (default: claude-sonnet-4-20250514)
        """
        self._api_key = api_key
        self._model = model
        self._client = httpx.AsyncClient(timeout=60.0)

    @property
    def name(self) -> str:
        """Return the name of this LLM provider."""
        return "anthropic"

    async def generate(
        self,
        messages: list[LLMMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> LLMResponse:
        """Generate a response from Claude.
        
        Args:
            messages: List of message objects with role and content
            system_prompt: Optional system prompt to guide the LLM
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens in the response
            
        Returns:
            LLMResponse containing the generated content and metadata
            
        Raises:
            AnthropicAuthError: If API key is invalid (401)
            AnthropicRateLimitError: If rate limited (429)
            AnthropicServerError: If server error (5xx)
            AnthropicError: For other API errors
        """
        # Format messages for Anthropic API
        formatted_messages = self._format_messages(messages)

        # Build request payload
        payload = {
            "model": self._model,
            "messages": formatted_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        # Add system prompt if provided
        if system_prompt:
            payload["system"] = system_prompt

        # Prepare headers
        headers = self._get_headers()

        # Retry logic for rate limits
        for attempt in range(self.MAX_RETRIES):
            try:
                response = await self._client.post(
                    f"{self.API_BASE}/messages",
                    json=payload,
                    headers=headers,
                )

                # Check for errors
                if response.status_code == 401:
                    raise AnthropicAuthError(
                        f"Authentication failed (401): Invalid API key"
                    )
                elif response.status_code == 429:
                    if attempt < self.MAX_RETRIES - 1:
                        # Retry with exponential backoff
                        delay = self.RETRY_DELAY * (2 ** attempt)
                        logger.warning(
                            f"Rate limited (429). Retrying in {delay}s "
                            f"(attempt {attempt + 1}/{self.MAX_RETRIES})"
                        )
                        await asyncio.sleep(delay)
                        continue
                    else:
                        raise AnthropicRateLimitError(
                            f"Rate limit exceeded (429): Too many requests"
                        )
                elif response.status_code >= 500:
                    raise AnthropicServerError(
                        f"Server error ({response.status_code}): {response.text}"
                    )
                elif response.status_code >= 400:
                    error_data = response.json()
                    raise AnthropicError(
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

            except (AnthropicRateLimitError, asyncio.TimeoutError) as e:
                if attempt < self.MAX_RETRIES - 1:
                    delay = self.RETRY_DELAY * (2 ** attempt)
                    await asyncio.sleep(delay)
                    continue
                raise

    async def stream(
        self,
        messages: list[LLMMessage],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> AsyncIterator[LLMStreamChunk]:
        """Stream a response from Claude.
        
        Args:
            messages: List of message objects with role and content
            system_prompt: Optional system prompt to guide the LLM
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens in the response
            
        Yields:
            LLMStreamChunk objects representing partial responses
            
        Raises:
            AnthropicAuthError: If API key is invalid (401)
            AnthropicRateLimitError: If rate limited (429)
            AnthropicServerError: If server error (5xx)
            AnthropicError: For other API errors
        """
        # Format messages for Anthropic API
        formatted_messages = self._format_messages(messages)

        # Build request payload
        payload = {
            "model": self._model,
            "messages": formatted_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }

        # Add system prompt if provided
        if system_prompt:
            payload["system"] = system_prompt

        # Prepare headers
        headers = self._get_headers()

        async with self._client.stream(
            "POST",
            f"{self.API_BASE}/messages",
            json=payload,
            headers=headers,
        ) as response:
            if response.status_code == 401:
                raise AnthropicAuthError(
                    f"Authentication failed (401): Invalid API key"
                )
            elif response.status_code == 429:
                raise AnthropicRateLimitError(
                    f"Rate limit exceeded (429): Too many requests"
                )
            elif response.status_code >= 500:
                raise AnthropicServerError(
                    f"Server error ({response.status_code})"
                )
            elif response.status_code >= 400:
                raise AnthropicError(f"API error ({response.status_code})")

            # Process streaming response
            is_final = False
            line_buffer = ""

            async for byte_line in response.aiter_lines():
                # Handle Server-Sent Events format
                if byte_line.startswith("data: "):
                    json_str = byte_line[6:]  # Remove "data: " prefix

                    try:
                        event_data = json.loads(json_str)
                        event_type = event_data.get("type")

                        # Extract content from delta events
                        if event_type == "content_block_delta":
                            delta = event_data.get("delta", {})
                            if delta.get("type") == "text_delta":
                                text = delta.get("text", "")
                                yield LLMStreamChunk(content=text, is_final=False)

                        # Mark final when message stop event
                        elif event_type == "message_stop":
                            is_final = True

                    except json.JSONDecodeError:
                        logger.debug(f"Failed to parse JSON: {json_str}")
                        continue

            # Yield final chunk to mark completion
            yield LLMStreamChunk(content="", is_final=True)

    def _format_messages(self, messages: list[LLMMessage]) -> list[dict]:
        """Format messages for Anthropic API format.
        
        Anthropic API expects a list of message objects with role and content.
        System prompts are passed separately in the payload.
        
        Args:
            messages: List of LLMMessage objects
            
        Returns:
            List of dicts formatted for Anthropic API
        """
        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
            if msg.role != "system"  # System role is handled separately
        ]

    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers for Anthropic API requests.
        
        Returns:
            Dict of headers with API key and required fields
        """
        return {
            "x-api-key": self._api_key,
            "anthropic-version": self.API_VERSION,
            "content-type": "application/json",
        }

    def _extract_content(self, response_data: dict) -> str:
        """Extract text content from Anthropic API response.
        
        Args:
            response_data: The JSON response from the API
            
        Returns:
            The extracted text content
        """
        content_blocks = response_data.get("content", [])
        texts = [
            block.get("text", "")
            for block in content_blocks
            if block.get("type") == "text"
        ]
        return "".join(texts)

    def _extract_usage(self, response_data: dict) -> LLMUsage:
        """Extract token usage from Anthropic API response.
        
        Args:
            response_data: The JSON response from the API
            
        Returns:
            LLMUsage object with prompt and completion tokens
        """
        usage_data = response_data.get("usage", {})
        return LLMUsage(
            prompt_tokens=usage_data.get("input_tokens", 0),
            completion_tokens=usage_data.get("output_tokens", 0),
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
