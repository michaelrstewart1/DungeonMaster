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


class CountingExplodingLLM(ExplodingLLM):
    def __init__(self):
        super().__init__()
        self.attempts = 0

    async def generate(self, **kwargs):
        self.attempts += 1
        raise RuntimeError("api down")


@pytest.mark.asyncio
async def test_cooldown_skips_primary_after_failure():
    """After a primary failure the breaker trips: subsequent calls go straight
    to the fallback without touching the primary until the cooldown expires."""
    primary = CountingExplodingLLM()
    fallback = FakeLLM(default_response="fallback narration")
    provider = FallbackLLMProvider(primary, fallback, cooldown_seconds=60.0)

    await provider.generate(messages=[LLMMessage(role="user", content="one")])
    await provider.generate(messages=[LLMMessage(role="user", content="two")])
    await provider.generate(messages=[LLMMessage(role="user", content="three")])

    assert primary.attempts == 1
    assert len(fallback.call_history) == 3


@pytest.mark.asyncio
async def test_cooldown_expiry_retries_primary():
    primary = CountingExplodingLLM()
    fallback = FakeLLM(default_response="fallback narration")
    provider = FallbackLLMProvider(primary, fallback, cooldown_seconds=0.0)

    await provider.generate(messages=[LLMMessage(role="user", content="one")])
    await provider.generate(messages=[LLMMessage(role="user", content="two")])

    # cooldown of 0 means the primary is retried every call
    assert primary.attempts == 2
