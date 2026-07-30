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

class OllamaLike(FakeLLM):
    """FakeLLM that quacks like the Ollama adapter (has _base_url)."""
    _base_url = "http://localhost:11434"

    @property
    def name(self) -> str:
        return "ollama-like"


@pytest.mark.asyncio
async def test_serving_locally_tracks_breaker_state():
    """Compact-prompt detection must follow WHICH provider will serve next."""
    cloud = ExplodingLLM(default_response="cloud")
    local = OllamaLike(default_response="local narration")
    provider = FallbackLLMProvider(cloud, local, cooldown_seconds=60)

    # Breaker closed: cloud primary serves -> rich prompts
    assert provider.serving_locally() is False

    # Primary fails -> breaker trips -> local serves -> compact prompts
    resp = await provider.generate(messages=[LLMMessage(role="user", content="hi")])
    assert resp.content == "local narration"
    assert provider.serving_locally() is True

    # Breaker expiry restores cloud detection
    provider._primary_down_until = 0.0
    assert provider.serving_locally() is False


def test_serving_locally_local_primary():
    provider = FallbackLLMProvider(OllamaLike(), FakeLLM())
    assert provider.serving_locally() is True
