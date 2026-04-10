"""
Tests for the OpenAI LLM provider adapter.

These tests use mocked httpx to avoid making real API calls.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from app.services.llm.openai import OpenAIProvider
from app.services.llm.base import LLMMessage, LLMResponse, LLMUsage, LLMStreamChunk


class TestOpenAIAdapter:
    """Tests for OpenAIProvider."""

    @pytest.fixture
    def api_key(self):
        """Test API key."""
        return "sk-test-key-12345"

    @pytest.fixture
    def provider(self, api_key):
        """Create an OpenAIProvider instance."""
        return OpenAIProvider(api_key=api_key)

    def test_implements_llm_provider_interface(self, provider):
        """Test that OpenAIProvider implements LLMProvider interface."""
        from app.services.llm.base import LLMProvider
        assert isinstance(provider, LLMProvider)

    def test_name_property_returns_openai(self, provider):
        """Test that name property returns 'openai'."""
        assert provider.name == "openai"

    @pytest.mark.asyncio
    async def test_generate_formats_messages_correctly(self, provider):
        """Test that generate() formats messages into OpenAI API format."""
        messages = [
            LLMMessage(role="user", content="Hello"),
            LLMMessage(role="assistant", content="Hi there"),
        ]
        system_prompt = "You are a helpful assistant"

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Response"}}],
                "model": "gpt-4o",
                "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            }
            mock_post.return_value = mock_response

            await provider.generate(
                messages, system_prompt=system_prompt, temperature=0.8, max_tokens=500
            )

            # Verify the call was made
            assert mock_post.called
            call_args = mock_post.call_args
            assert "https://api.openai.com" in call_args[0][0]
            assert "/chat/completions" in call_args[0][0]

            # Verify the request body contains properly formatted messages
            request_data = call_args[1]["json"]
            assert "messages" in request_data
            # Should have system message + 2 user messages
            assert len(request_data["messages"]) == 3
            # First message should be system
            assert request_data["messages"][0]["role"] == "system"
            assert request_data["messages"][0]["content"] == system_prompt
            # Then user messages
            assert request_data["messages"][1]["role"] == "user"
            assert request_data["messages"][1]["content"] == "Hello"

    @pytest.mark.asyncio
    async def test_generate_sends_correct_headers(self, provider):
        """Test that generate() includes correct Authorization header."""
        messages = [LLMMessage(role="user", content="Test")]

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Response"}}],
                "model": "gpt-4o",
                "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            }
            mock_post.return_value = mock_response

            await provider.generate(messages)

            # Verify headers
            call_args = mock_post.call_args
            headers = call_args[1]["headers"]
            assert "Authorization" in headers
            assert headers["Authorization"] == f"Bearer {provider._api_key}"
            assert headers["Content-Type"] == "application/json"

    @pytest.mark.asyncio
    async def test_generate_parses_response_correctly(self, provider):
        """Test that generate() parses API response into LLMResponse."""
        messages = [LLMMessage(role="user", content="Test")]

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Generated response"}}],
                "model": "gpt-4o",
                "usage": {"prompt_tokens": 15, "completion_tokens": 20},
            }
            mock_post.return_value = mock_response

            result = await provider.generate(messages)

            assert isinstance(result, LLMResponse)
            assert result.content == "Generated response"
            assert result.model == "gpt-4o"
            assert result.usage.prompt_tokens == 15
            assert result.usage.completion_tokens == 20

    @pytest.mark.asyncio
    async def test_generate_handles_401_unauthorized(self, provider):
        """Test that generate() raises exception on 401 Unauthorized."""
        messages = [LLMMessage(role="user", content="Test")]

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.json.return_value = {
                "error": {"message": "Unauthorized", "type": "invalid_request_error"}
            }
            mock_post.return_value = mock_response

            with pytest.raises(Exception) as exc_info:
                await provider.generate(messages)

            assert "401" in str(exc_info.value) or "Unauthorized" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_handles_429_rate_limit(self, provider):
        """Test that generate() raises exception on 429 Rate Limit."""
        messages = [LLMMessage(role="user", content="Test")]

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_response.json.return_value = {
                "error": {"message": "Rate limit exceeded", "type": "server_error"}
            }
            mock_post.return_value = mock_response

            with pytest.raises(Exception) as exc_info:
                await provider.generate(messages)

            assert "429" in str(exc_info.value) or "Rate limit" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_handles_500_server_error(self, provider):
        """Test that generate() raises exception on 500 Server Error."""
        messages = [LLMMessage(role="user", content="Test")]

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.json.return_value = {
                "error": {"message": "Internal server error", "type": "server_error"}
            }
            mock_post.return_value = mock_response

            with pytest.raises(Exception) as exc_info:
                await provider.generate(messages)

            assert "500" in str(exc_info.value) or "Server error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_stream_yields_stream_chunks_from_sse(self, provider):
        """Test that stream() yields LLMStreamChunk from SSE."""
        messages = [LLMMessage(role="user", content="Test")]

        # Mock SSE response with OpenAI format
        sse_lines = [
            'data: {"choices":[{"delta":{"content":"Hello"}}]}',
            'data: {"choices":[{"delta":{"content":" "}}]}',
            'data: {"choices":[{"delta":{"content":"world"}}]}',
            'data: [DONE]',
        ]

        with patch("httpx.AsyncClient.stream") as mock_stream:
            mock_response = MagicMock()
            mock_response.status_code = 200

            async def async_lines():
                for line in sse_lines:
                    yield line

            mock_response.aiter_lines.return_value = async_lines()
            mock_stream.return_value.__aenter__.return_value = mock_response

            chunks = []
            async for chunk in provider.stream(messages):
                chunks.append(chunk)

            # Should have 4 chunks (3 content + 1 final)
            assert len(chunks) == 4
            assert all(isinstance(c, LLMStreamChunk) for c in chunks)
            assert chunks[0].content == "Hello"
            assert chunks[1].content == " "
            assert chunks[2].content == "world"

    @pytest.mark.asyncio
    async def test_stream_marks_final_chunk_correctly(self, provider):
        """Test that stream() marks final chunk correctly."""
        messages = [LLMMessage(role="user", content="Test")]

        sse_lines = [
            'data: {"choices":[{"delta":{"content":"Part 1"}}]}',
            'data: {"choices":[{"delta":{"content":"Part 2"}}]}',
            'data: [DONE]',
        ]

        with patch("httpx.AsyncClient.stream") as mock_stream:
            mock_response = MagicMock()
            mock_response.status_code = 200

            async def async_lines():
                for line in sse_lines:
                    yield line

            mock_response.aiter_lines.return_value = async_lines()
            mock_stream.return_value.__aenter__.return_value = mock_response

            chunks = []
            async for chunk in provider.stream(messages):
                chunks.append(chunk)

            # Last chunk should be marked as final
            if chunks:
                assert chunks[-1].is_final is True
                # All others should not be final
                for chunk in chunks[:-1]:
                    assert chunk.is_final is False

    @pytest.mark.asyncio
    async def test_generate_includes_temperature_and_max_tokens(self, provider):
        """Test that generate() includes temperature and max_tokens in request."""
        messages = [LLMMessage(role="user", content="Test")]

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Response"}}],
                "model": "gpt-4o",
                "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            }
            mock_post.return_value = mock_response

            await provider.generate(messages, temperature=0.5, max_tokens=256)

            call_args = mock_post.call_args
            request_data = call_args[1]["json"]
            assert request_data["temperature"] == 0.5
            assert request_data["max_tokens"] == 256

    @pytest.mark.asyncio
    async def test_stream_includes_temperature_and_max_tokens(self, provider):
        """Test that stream() includes temperature and max_tokens in request."""
        messages = [LLMMessage(role="user", content="Test")]

        sse_lines = ['data: [DONE]']

        with patch("httpx.AsyncClient.stream") as mock_stream:
            mock_response = MagicMock()
            mock_response.status_code = 200

            async def async_lines():
                for line in sse_lines:
                    yield line

            mock_response.aiter_lines.return_value = async_lines()
            mock_stream.return_value.__aenter__.return_value = mock_response

            async for _ in provider.stream(messages, temperature=0.3, max_tokens=512):
                pass

            call_args = mock_stream.call_args
            request_data = call_args[1]["json"]
            assert request_data["temperature"] == 0.3
            assert request_data["max_tokens"] == 512
