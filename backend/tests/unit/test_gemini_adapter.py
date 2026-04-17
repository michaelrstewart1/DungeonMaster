"""
Tests for the Google Gemini LLM provider adapter.

These tests use mocked httpx to avoid making real API calls.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from app.services.llm.gemini import (
    GeminiProvider,
    GeminiError,
    GeminiAuthError,
    GeminiRateLimitError,
    GeminiServerError,
)
from app.services.llm.base import LLMMessage, LLMResponse, LLMUsage, LLMStreamChunk


class TestGeminiAdapter:
    """Tests for GeminiProvider."""

    @pytest.fixture
    def api_key(self):
        return "test-gemini-key-12345"

    @pytest.fixture
    def provider(self, api_key):
        return GeminiProvider(api_key=api_key)

    def test_implements_llm_provider_interface(self, provider):
        from app.services.llm.base import LLMProvider
        assert isinstance(provider, LLMProvider)

    def test_name_property(self, provider):
        assert provider.name == "gemini"

    def test_default_model(self, provider):
        assert provider._model == "gemini-2.5-flash"

    def test_custom_model(self, api_key):
        p = GeminiProvider(api_key=api_key, model="gemini-2.0-flash")
        assert p._model == "gemini-2.0-flash"

    @pytest.mark.asyncio
    async def test_generate_success(self, provider):
        messages = [
            LLMMessage(role="user", content="Hello"),
            LLMMessage(role="assistant", content="Hi there"),
            LLMMessage(role="user", content="Tell me a story"),
        ]

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{"text": "Once upon a time..."}],
                    "role": "model",
                }
            }],
            "usageMetadata": {
                "promptTokenCount": 20,
                "candidatesTokenCount": 50,
            },
        }

        with patch("httpx.AsyncClient.post", return_value=mock_resp) as mock_post:
            result = await provider.generate(
                messages, system_prompt="You are a DM", temperature=0.8
            )

        assert isinstance(result, LLMResponse)
        assert result.content == "Once upon a time..."
        assert result.usage.prompt_tokens == 20
        assert result.usage.completion_tokens == 50

        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        # System prompt goes to systemInstruction
        assert "systemInstruction" in payload
        assert payload["systemInstruction"]["parts"][0]["text"] == "You are a DM"
        # Messages mapped: assistant -> model
        roles = [c["role"] for c in payload["contents"]]
        assert roles == ["user", "model", "user"]

    @pytest.mark.asyncio
    async def test_generate_filters_system_messages(self, provider):
        messages = [
            LLMMessage(role="system", content="System msg"),
            LLMMessage(role="user", content="Hello"),
        ]

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "Hi"}], "role": "model"}}],
            "usageMetadata": {},
        }

        with patch("httpx.AsyncClient.post", return_value=mock_resp) as mock_post:
            await provider.generate(messages)

        payload = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1].get("json")
        roles = [c["role"] for c in payload["contents"]]
        assert "system" not in roles

    @pytest.mark.asyncio
    async def test_generate_auth_error(self, provider):
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_resp.text = "Forbidden"

        with patch("httpx.AsyncClient.post", return_value=mock_resp):
            with pytest.raises(GeminiAuthError):
                await provider.generate([LLMMessage(role="user", content="Hi")])

    @pytest.mark.asyncio
    async def test_generate_rate_limit_retries(self, provider):
        mock_429 = MagicMock()
        mock_429.status_code = 429
        mock_429.text = "Rate limited"

        mock_ok = MagicMock()
        mock_ok.status_code = 200
        mock_ok.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "OK"}], "role": "model"}}],
            "usageMetadata": {},
        }

        with patch("httpx.AsyncClient.post", side_effect=[mock_429, mock_ok]):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await provider.generate(
                    [LLMMessage(role="user", content="Hi")]
                )
        assert result.content == "OK"

    @pytest.mark.asyncio
    async def test_generate_rate_limit_exhausted(self, provider):
        mock_429 = MagicMock()
        mock_429.status_code = 429
        mock_429.text = "Rate limited"

        with patch("httpx.AsyncClient.post", return_value=mock_429):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(GeminiRateLimitError):
                    await provider.generate(
                        [LLMMessage(role="user", content="Hi")]
                    )

    @pytest.mark.asyncio
    async def test_generate_server_error(self, provider):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal server error"

        with patch("httpx.AsyncClient.post", return_value=mock_resp):
            with pytest.raises(GeminiServerError):
                await provider.generate([LLMMessage(role="user", content="Hi")])

    @pytest.mark.asyncio
    async def test_generate_empty_candidates(self, provider):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"candidates": [], "usageMetadata": {}}

        with patch("httpx.AsyncClient.post", return_value=mock_resp):
            result = await provider.generate(
                [LLMMessage(role="user", content="Hi")]
            )
        assert result.content == ""

    def test_format_messages(self, provider):
        messages = [
            LLMMessage(role="system", content="Sys"),
            LLMMessage(role="user", content="Hello"),
            LLMMessage(role="assistant", content="Hi"),
        ]
        formatted = provider._format_messages(messages)
        assert len(formatted) == 2
        assert formatted[0]["role"] == "user"
        assert formatted[1]["role"] == "model"

    def test_extract_content(self, provider):
        data = {
            "candidates": [{
                "content": {
                    "parts": [
                        {"text": "Part 1 "},
                        {"text": "Part 2"},
                    ]
                }
            }]
        }
        assert provider._extract_content(data) == "Part 1 Part 2"

    def test_extract_usage(self, provider):
        data = {"usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 25}}
        usage = provider._extract_usage(data)
        assert usage.prompt_tokens == 10
        assert usage.completion_tokens == 25

    def test_extract_usage_missing(self, provider):
        usage = provider._extract_usage({})
        assert usage.prompt_tokens == 0
        assert usage.completion_tokens == 0
