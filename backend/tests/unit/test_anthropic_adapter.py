"""
Tests for the Anthropic Claude LLM provider adapter.

These tests use mocked httpx to avoid making real API calls.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from app.services.llm.anthropic import AnthropicProvider
from app.services.llm.base import LLMMessage, LLMResponse, LLMUsage, LLMStreamChunk


class TestAnthropicAdapter:
    """Tests for AnthropicProvider."""

    @pytest.fixture
    def api_key(self):
        """Test API key."""
        return "sk-ant-test-key-12345"

    @pytest.fixture
    def provider(self, api_key):
        """Create an AnthropicProvider instance."""
        return AnthropicProvider(api_key=api_key)

    def test_implements_llm_provider_interface(self, provider):
        """Test that AnthropicProvider implements LLMProvider interface."""
        from app.services.llm.base import LLMProvider
        assert isinstance(provider, LLMProvider)

    def test_name_property_returns_anthropic(self, provider):
        """Test that name property returns 'anthropic'."""
        assert provider.name == "anthropic"

    @pytest.mark.asyncio
    async def test_generate_formats_messages_correctly(self, provider):
        """Test that generate() formats messages into Anthropic API format."""
        messages = [
            LLMMessage(role="user", content="Hello"),
            LLMMessage(role="assistant", content="Hi there"),
        ]
        system_prompt = "You are helpful"

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "content": [{"type": "text", "text": "Response"}],
                "model": "claude-sonnet-4-20250514",
                "usage": {"input_tokens": 10, "output_tokens": 5},
            }
            mock_post.return_value = mock_response

            await provider.generate(
                messages, system_prompt=system_prompt, temperature=0.8, max_tokens=500
            )

            # Verify the call was made
            assert mock_post.called
            call_args = mock_post.call_args
            assert call_args[0][0] == "https://api.anthropic.com/v1/messages"

            # Verify the request body contains properly formatted messages
            request_data = call_args[1]["json"]
            assert "messages" in request_data
            assert len(request_data["messages"]) == 2
            assert request_data["messages"][0]["role"] == "user"
            assert request_data["messages"][0]["content"] == "Hello"
            assert request_data["system"] == system_prompt

    @pytest.mark.asyncio
    async def test_generate_sends_correct_headers(self, provider):
        """Test that generate() includes correct headers."""
        messages = [LLMMessage(role="user", content="Test")]

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "content": [{"type": "text", "text": "Response"}],
                "model": "claude-sonnet-4-20250514",
                "usage": {"input_tokens": 10, "output_tokens": 5},
            }
            mock_post.return_value = mock_response

            await provider.generate(messages)

            # Verify headers
            call_args = mock_post.call_args
            headers = call_args[1]["headers"]
            assert "x-api-key" in headers
            assert headers["x-api-key"] == provider._api_key
            assert "anthropic-version" in headers
            assert headers["content-type"] == "application/json"

    @pytest.mark.asyncio
    async def test_generate_parses_response_correctly(self, provider):
        """Test that generate() parses API response into LLMResponse."""
        messages = [LLMMessage(role="user", content="Test")]

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "content": [{"type": "text", "text": "Generated response"}],
                "model": "claude-sonnet-4-20250514",
                "usage": {"input_tokens": 15, "output_tokens": 20},
            }
            mock_post.return_value = mock_response

            result = await provider.generate(messages)

            assert isinstance(result, LLMResponse)
            assert result.content == "Generated response"
            assert result.model == "claude-sonnet-4-20250514"
            assert result.usage.prompt_tokens == 15
            assert result.usage.completion_tokens == 20

    @pytest.mark.asyncio
    async def test_generate_handles_401_unauthorized(self, provider):
        """Test that generate() raises exception on 401 Unauthorized."""
        messages = [LLMMessage(role="user", content="Test")]

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.json.return_value = {"error": {"message": "Unauthorized"}}
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
            mock_response.json.return_value = {"error": {"message": "Rate limit exceeded"}}
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
            mock_response.json.return_value = {"error": {"message": "Internal server error"}}
            mock_post.return_value = mock_response

            with pytest.raises(Exception) as exc_info:
                await provider.generate(messages)

            assert "500" in str(exc_info.value) or "Server error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_retries_on_rate_limit(self, provider):
        """Test that generate() retries on 429 rate limit."""
        messages = [LLMMessage(role="user", content="Test")]

        with patch("httpx.AsyncClient.post") as mock_post:
            # First call returns 429, second call succeeds
            rate_limit_response = MagicMock()
            rate_limit_response.status_code = 429
            rate_limit_response.json.return_value = {"error": {"message": "Rate limit"}}

            success_response = MagicMock()
            success_response.status_code = 200
            success_response.json.return_value = {
                "content": [{"type": "text", "text": "Success"}],
                "model": "claude-sonnet-4-20250514",
                "usage": {"input_tokens": 10, "output_tokens": 5},
            }

            mock_post.side_effect = [rate_limit_response, success_response]

            # Should retry and succeed
            result = await provider.generate(messages)

            assert result.content == "Success"
            assert mock_post.call_count == 2

    @pytest.mark.asyncio
    async def test_stream_yields_stream_chunks(self, provider):
        """Test that stream() yields LLMStreamChunk objects."""
        messages = [LLMMessage(role="user", content="Test")]

        # Mock SSE response
        sse_content = (
            b"event: content_block_start\ndata: {}\n\n"
            b"event: content_block_delta\ndata: {\"delta\": {\"type\": \"text_delta\", \"text\": \"Hello\"}}\n\n"
            b"event: content_block_delta\ndata: {\"delta\": {\"type\": \"text_delta\", \"text\": \" world\"}}\n\n"
            b"event: message_stop\ndata: {}\n\n"
        )

        with patch("httpx.AsyncClient.stream") as mock_stream:
            mock_response = MagicMock()
            mock_response.status_code = 200

            async def async_lines():
                for line in sse_content.split(b"\n\n"):
                    if line:
                        yield line.decode("utf-8")

            mock_response.aiter_lines.return_value = async_lines()
            mock_stream.return_value.__aenter__.return_value = mock_response

            chunks = []
            async for chunk in provider.stream(messages):
                chunks.append(chunk)

            assert len(chunks) > 0
            assert all(isinstance(c, LLMStreamChunk) for c in chunks)

    @pytest.mark.asyncio
    async def test_stream_marks_final_chunk_correctly(self, provider):
        """Test that stream() marks the final chunk correctly."""
        messages = [LLMMessage(role="user", content="Test")]

        # Create a simple mock response
        chunks_data = [
            "event: content_block_delta\ndata: {\"delta\": {\"type\": \"text_delta\", \"text\": \"Part 1\"}}",
            "event: content_block_delta\ndata: {\"delta\": {\"type\": \"text_delta\", \"text\": \"Part 2\"}}",
            "event: message_stop\ndata: {}",
        ]

        with patch("httpx.AsyncClient.stream") as mock_stream:
            mock_response = MagicMock()
            mock_response.status_code = 200

            async def async_lines():
                for chunk_data in chunks_data:
                    yield chunk_data

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
