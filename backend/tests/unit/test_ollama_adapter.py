"""
Tests for the Ollama LLM provider adapter.

These tests use mocked httpx to avoid making real API calls.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from app.services.llm.ollama import OllamaProvider
from app.services.llm.base import LLMMessage, LLMResponse, LLMUsage, LLMStreamChunk


class TestOllamaAdapter:
    """Tests for OllamaProvider."""

    @pytest.fixture
    def provider(self):
        """Create an OllamaProvider instance."""
        return OllamaProvider(base_url="http://localhost:11434", model="llama3.1:8b")

    def test_implements_llm_provider_interface(self, provider):
        """Test that OllamaProvider implements LLMProvider interface."""
        from app.services.llm.base import LLMProvider
        assert isinstance(provider, LLMProvider)

    def test_name_property_returns_ollama(self, provider):
        """Test that name property returns 'ollama'."""
        assert provider.name == "ollama"

    def test_constructor_sets_model(self):
        """Test that constructor properly sets the model."""
        provider = OllamaProvider(model="mistral:7b")
        assert provider._model == "mistral:7b"

    def test_constructor_sets_base_url(self):
        """Test that constructor properly sets the base URL."""
        provider = OllamaProvider(base_url="http://192.168.1.100:11434")
        assert provider._base_url == "http://192.168.1.100:11434"

    @pytest.mark.asyncio
    async def test_generate_sends_post_to_api_chat(self, provider):
        """Test that generate() sends POST to {base_url}/api/chat."""
        messages = [LLMMessage(role="user", content="Hello")]

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "model": "llama3.1:8b",
                "message": {"role": "assistant", "content": "Hi there"},
                "done": True,
            }
            mock_post.return_value = mock_response

            await provider.generate(messages)

            # Verify the endpoint
            assert mock_post.called
            call_args = mock_post.call_args
            assert "api/chat" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_generate_formats_messages_correctly(self, provider):
        """Test that generate() formats messages correctly for Ollama."""
        messages = [
            LLMMessage(role="user", content="Hello"),
            LLMMessage(role="assistant", content="Hi"),
        ]

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "model": "llama3.1:8b",
                "message": {"role": "assistant", "content": "Response"},
                "done": True,
            }
            mock_post.return_value = mock_response

            await provider.generate(messages)

            call_args = mock_post.call_args
            request_data = call_args[1]["json"]
            assert "messages" in request_data
            assert len(request_data["messages"]) == 2
            assert request_data["messages"][0]["role"] == "user"
            assert request_data["messages"][0]["content"] == "Hello"

    @pytest.mark.asyncio
    async def test_generate_includes_system_message_if_provided(self, provider):
        """Test that generate() includes system message if provided."""
        messages = [LLMMessage(role="user", content="Tell me a story")]
        system_prompt = "You are a storyteller"

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "model": "llama3.1:8b",
                "message": {"role": "assistant", "content": "Once upon a time..."},
                "done": True,
            }
            mock_post.return_value = mock_response

            await provider.generate(messages, system_prompt=system_prompt)

            call_args = mock_post.call_args
            request_data = call_args[1]["json"]
            # System prompt is now passed as first message with role "system"
            assert request_data["messages"][0]["role"] == "system"
            assert request_data["messages"][0]["content"] == system_prompt

    @pytest.mark.asyncio
    async def test_generate_parses_ollama_response_format(self, provider):
        """Test that generate() parses Ollama response format correctly."""
        messages = [LLMMessage(role="user", content="Test")]

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "model": "llama3.1:8b",
                "message": {"role": "assistant", "content": "Test response content"},
                "done": True,
                "total_duration": 1234567890,
                "load_duration": 123456,
                "prompt_eval_count": 42,
                "prompt_eval_duration": 456789,
                "eval_count": 28,
                "eval_duration": 789012,
            }
            mock_post.return_value = mock_response

            result = await provider.generate(messages)

            assert isinstance(result, LLMResponse)
            assert result.content == "Test response content"
            assert result.model == "llama3.1:8b"

    @pytest.mark.asyncio
    async def test_generate_handles_connection_errors(self, provider):
        """Test that generate() handles connection errors (Ollama not running)."""
        messages = [LLMMessage(role="user", content="Test")]

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.side_effect = httpx.ConnectError("Connection refused")

            with pytest.raises(Exception) as exc_info:
                await provider.generate(messages)

            assert "Connection" in str(exc_info.value) or "connect" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_stream_yields_chunks_from_streaming_response(self, provider):
        """Test that stream() yields chunks from Ollama streaming response."""
        messages = [LLMMessage(role="user", content="Test")]

        # Ollama sends line-by-line JSON
        response_lines = [
            '{"model":"llama3.1:8b","message":{"role":"assistant","content":"Hello"},"done":false}',
            '{"model":"llama3.1:8b","message":{"role":"assistant","content":" "},"done":false}',
            '{"model":"llama3.1:8b","message":{"role":"assistant","content":"world"},"done":false}',
            '{"model":"llama3.1:8b","message":{"role":"assistant","content":""},"done":true,"total_duration":1000000,"load_duration":100000}',
        ]

        with patch("httpx.AsyncClient.stream") as mock_stream:
            mock_response = MagicMock()
            mock_response.status_code = 200

            async def async_lines():
                for line in response_lines:
                    yield line

            mock_response.aiter_lines.return_value = async_lines()
            mock_stream.return_value.__aenter__.return_value = mock_response

            chunks = []
            async for chunk in provider.stream(messages):
                chunks.append(chunk)

            # Should have 4 chunks
            assert len(chunks) == 4
            assert all(isinstance(c, LLMStreamChunk) for c in chunks)
            assert chunks[0].content == "Hello"
            assert chunks[1].content == " "
            assert chunks[2].content == "world"

    @pytest.mark.asyncio
    async def test_stream_marks_final_chunk_when_done_true(self, provider):
        """Test that stream() marks final chunk when "done": true."""
        messages = [LLMMessage(role="user", content="Test")]

        response_lines = [
            '{"model":"llama3.1:8b","message":{"role":"assistant","content":"Part 1"},"done":false}',
            '{"model":"llama3.1:8b","message":{"role":"assistant","content":"Part 2"},"done":false}',
            '{"model":"llama3.1:8b","message":{"role":"assistant","content":""},"done":true}',
        ]

        with patch("httpx.AsyncClient.stream") as mock_stream:
            mock_response = MagicMock()
            mock_response.status_code = 200

            async def async_lines():
                for line in response_lines:
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
    async def test_generate_includes_model_in_request(self, provider):
        """Test that generate() includes model in request."""
        messages = [LLMMessage(role="user", content="Test")]

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "model": "llama3.1:8b",
                "message": {"role": "assistant", "content": "Response"},
                "done": True,
            }
            mock_post.return_value = mock_response

            await provider.generate(messages)

            call_args = mock_post.call_args
            request_data = call_args[1]["json"]
            assert request_data["model"] == "llama3.1:8b"

    @pytest.mark.asyncio
    async def test_stream_includes_model_in_request(self, provider):
        """Test that stream() includes model in request."""
        messages = [LLMMessage(role="user", content="Test")]

        response_lines = [
            '{"model":"llama3.1:8b","message":{"role":"assistant","content":""},"done":true}',
        ]

        with patch("httpx.AsyncClient.stream") as mock_stream:
            mock_response = MagicMock()
            mock_response.status_code = 200

            async def async_lines():
                for line in response_lines:
                    yield line

            mock_response.aiter_lines.return_value = async_lines()
            mock_stream.return_value.__aenter__.return_value = mock_response

            async for _ in provider.stream(messages):
                pass

            call_args = mock_stream.call_args
            request_data = call_args[1]["json"]
            assert request_data["model"] == "llama3.1:8b"

    @pytest.mark.asyncio
    async def test_generate_includes_temperature_and_options(self, provider):
        """Test that generate() includes temperature in request."""
        messages = [LLMMessage(role="user", content="Test")]

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "model": "llama3.1:8b",
                "message": {"role": "assistant", "content": "Response"},
                "done": True,
            }
            mock_post.return_value = mock_response

            await provider.generate(messages, temperature=0.5)

            call_args = mock_post.call_args
            request_data = call_args[1]["json"]
            assert "options" in request_data
            assert request_data["options"]["temperature"] == 0.5

    @pytest.mark.asyncio
    async def test_stream_handles_connection_errors(self, provider):
        """Test that stream() handles connection errors."""
        messages = [LLMMessage(role="user", content="Test")]

        with patch("httpx.AsyncClient.stream") as mock_stream:
            mock_stream.side_effect = httpx.ConnectError("Connection refused")

            with pytest.raises(Exception) as exc_info:
                async for _ in provider.stream(messages):
                    pass

            assert "Connection" in str(exc_info.value) or "connect" in str(exc_info.value).lower()
