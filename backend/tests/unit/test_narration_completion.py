"""DM replies that hit the token cap, or whose stream dies, must finish.

Playtest: the skeletons' turn stopped mid-sentence on the phone and at a
different cutoff on the TV, and the DM was left on Waiting.
"""
import pytest

from app.services.llm.base import LLMResponse, LLMStreamChunk, finish_needs_continuation
from app.services.llm.narrator import DMNarrator


class LengthThenContinue:
    """First call stops on length; the next call finishes the sentence."""

    def __init__(self):
        self.stream_calls = 0
        self.max_tokens: list[int] = []

    @property
    def name(self) -> str:
        return "length-then-continue"

    async def generate(self, messages, system_prompt=None, temperature=0.7, max_tokens=2000):
        self.max_tokens.append(max_tokens)
        return LLMResponse(content="SHOULD NOT GENERATE", model=self.name, finish_reason="stop")

    async def stream(self, messages, system_prompt=None, temperature=0.7, max_tokens=2000):
        self.stream_calls += 1
        self.max_tokens.append(max_tokens)
        if self.stream_calls == 1:
            yield LLMStreamChunk(
                content="The remaining three skeletons clatter past Thorne, their ",
                finish_reason=None,
            )
            yield LLMStreamChunk(content="", is_final=True, finish_reason="length")
        else:
            yield LLMStreamChunk(
                content="bones knock against the door. It is Ashara's turn.",
                is_final=True,
                finish_reason="stop",
            )


class DieAfterPartial:
    """Stream dies after a partial sentence. Generate finishes it."""

    def __init__(self, generate_also_fails: bool = False):
        self.generate_also_fails = generate_also_fails
        self.generate_calls = 0

    @property
    def name(self) -> str:
        return "die-after-partial"

    async def generate(self, messages, system_prompt=None, temperature=0.7, max_tokens=2000):
        self.generate_calls += 1
        if self.generate_also_fails:
            raise RuntimeError("generate down")
        return LLMResponse(
            content="AC 15 and the blow goes wide.",
            model=self.name,
            finish_reason="stop",
        )

    async def stream(self, messages, system_prompt=None, temperature=0.7, max_tokens=2000):
        yield LLMStreamChunk(content="Skeleton 1 (damaged) attacks Thorne: Attack Roll: (d20 + 4) vs ")
        raise RuntimeError("connection reset")


def test_length_and_max_tokens_need_continuation():
    assert finish_needs_continuation("length")
    assert finish_needs_continuation("MAX_TOKENS")
    assert finish_needs_continuation("error")
    assert not finish_needs_continuation("stop")
    assert not finish_needs_continuation(None)


@pytest.mark.asyncio
async def test_length_cutoff_is_continued_and_streamed_in_full():
    llm = LengthThenContinue()
    narrator = DMNarrator(llm=llm)
    chunks: list[str] = []

    async def on_chunk(text: str) -> None:
        chunks.append(text)

    result = await narrator.narrate_exploration(
        scene={"name": "Crypt", "description": "Bones on the floor"},
        player_action="Kael shoots the leader",
        characters=[{"name": "Kael"}],
        world_context="A crypt",
        on_chunk=on_chunk,
    )

    assert "clatter past Thorne, their bones knock against the door" in result
    assert "Ashara's turn" in result
    assert "".join(chunks) == result
    assert llm.stream_calls == 2
    assert llm.max_tokens[0] >= 800
    assert "SHOULD NOT GENERATE" not in result


@pytest.mark.asyncio
async def test_stream_error_keeps_the_partial_and_finishes_it():
    llm = DieAfterPartial()
    narrator = DMNarrator(llm=llm)
    chunks: list[str] = []

    async def on_chunk(text: str) -> None:
        chunks.append(text)

    result = await narrator.narrate_exploration(
        scene={"name": "Crypt", "description": "Bones"},
        player_action="Kael shoots",
        characters=[],
        world_context="A crypt",
        on_chunk=on_chunk,
    )

    assert result.startswith("Skeleton 1 (damaged) attacks Thorne: Attack Roll: (d20 + 4) vs ")
    assert result.endswith("the blow goes wide.")
    assert "".join(chunks) == result
    assert llm.generate_calls == 1


@pytest.mark.asyncio
async def test_stream_error_without_a_backup_still_returns_the_partial():
    """The turn must be able to close on the text already shown, not hang."""
    llm = DieAfterPartial(generate_also_fails=True)
    narrator = DMNarrator(llm=llm)
    chunks: list[str] = []

    async def on_chunk(text: str) -> None:
        chunks.append(text)

    result = await narrator.narrate_exploration(
        scene={"name": "Crypt", "description": "Bones"},
        player_action="Kael shoots",
        characters=[],
        world_context="A crypt",
        on_chunk=on_chunk,
    )

    assert result == "Skeleton 1 (damaged) attacks Thorne: Attack Roll: (d20 + 4) vs "
    assert "".join(chunks) == result
    assert llm.generate_calls == 1


@pytest.mark.asyncio
async def test_combat_narration_continues_past_max_tokens():
    class LengthGenerate:
        def __init__(self):
            self.calls = 0

        async def generate(self, messages, system_prompt=None, temperature=0.7, max_tokens=2000):
            self.calls += 1
            if self.calls == 1:
                return LLMResponse(
                    content="The remaining three skeletons clatter past Thorne, their ",
                    model="fake",
                    finish_reason="length",
                )
            return LLMResponse(
                content="bones stop at the door. Ashara is next.",
                model="fake",
                finish_reason="stop",
            )

        async def stream(self, **kwargs):
            raise AssertionError("combat narration should not stream")
            yield  # pragma: no cover

    llm = LengthGenerate()
    narrator = DMNarrator(llm=llm)
    result = await narrator.narrate_combat_action(
        {"round_number": 1, "combatants": [], "initiative_order": []},
        {"description": "Kael hits the skeleton"},
        [],
    )
    assert "clatter past Thorne, their bones stop at the door" in result
    assert llm.calls == 2
