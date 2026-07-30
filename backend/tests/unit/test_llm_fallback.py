"""FallbackLLMProvider — primary failure must transparently use fallback."""
import pytest

from app.services.llm.base import FakeLLM, LLMMessage, LLMStreamChunk
from app.services.llm.fallback import FallbackLLMProvider


class ExplodingLLM(FakeLLM):
    @property
    def name(self) -> str:
        return "exploding"

    async def generate(self, **kwargs):
        raise RuntimeError("api down")

    async def stream(self, **kwargs):
        raise RuntimeError("api down")
        yield  # pragma: no cover


class SlowLLM(FakeLLM):
    @property
    def name(self) -> str:
        return "slow"

    async def generate(self, **kwargs):
        import asyncio
        await asyncio.sleep(10)
        return await super().generate(**kwargs)


@pytest.mark.asyncio
async def test_primary_success_used_directly():
    primary = FakeLLM(default_response="primary says hi")
    fallback = FakeLLM(default_response="fallback says hi")
    provider = FallbackLLMProvider(primary, fallback)

    resp = await provider.generate(messages=[LLMMessage(role="user", content="hi")])
    assert resp.content == "primary says hi"
    assert fallback.call_history == []


@pytest.mark.asyncio
async def test_primary_error_falls_back():
    fallback = FakeLLM(default_response="fallback narration")
    provider = FallbackLLMProvider(ExplodingLLM(), fallback)

    resp = await provider.generate(messages=[LLMMessage(role="user", content="hi")])
    assert resp.content == "fallback narration"
    assert len(fallback.call_history) == 1


@pytest.mark.asyncio
async def test_primary_timeout_falls_back():
    fallback = FakeLLM(default_response="fast fallback")
    provider = FallbackLLMProvider(SlowLLM(), fallback, primary_timeout=0.05)

    resp = await provider.generate(messages=[LLMMessage(role="user", content="hi")])
    assert resp.content == "fast fallback"


@pytest.mark.asyncio
async def test_stream_falls_back_when_primary_dies_before_output():
    fallback = FakeLLM(default_chunks=["fall", "back"])
    provider = FallbackLLMProvider(ExplodingLLM(), fallback)

    chunks = [c.content async for c in provider.stream(messages=[LLMMessage(role="user", content="hi")])]
    assert chunks == ["fall", "back"]


@pytest.mark.asyncio
async def test_name_reflects_chain():
    provider = FallbackLLMProvider(FakeLLM(), FakeLLM())
    assert "fallback" in provider.name
