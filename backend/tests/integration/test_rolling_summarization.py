"""Rolling narrative summarization — old history folds into a summary."""
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app import repository as repo
from app.models.database import Base
from app.services.game.summarizer import (
    CHUNK_MIN,
    KEEP_RECENT,
    maybe_roll_up,
    summarize_chunk,
)
from app.services.llm.base import LLMResponse


class FakeLLM:
    def __init__(self, reply="The party rescued Mira and swore vengeance on the Ashen Hand."):
        self.reply = reply
        self.calls = []

    async def generate(self, messages, system_prompt="", temperature=0.7, max_tokens=500):
        self.calls.append({"messages": messages, "system_prompt": system_prompt})
        return LLMResponse(content=self.reply, model="fake", usage={})


class FailingLLM:
    async def generate(self, **kwargs):
        raise RuntimeError("llm down")


@pytest.fixture
async def db_factory():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield factory
    await engine.dispose()


async def _make_session(db_factory, entries: int) -> str:
    history = []
    for i in range(entries // 2):
        history.append(f"Player: action number {i}")
        history.append(f"DM: outcome number {i}")
    session = {
        "id": "sess-roll",
        "campaign_id": "camp-1",
        "narrative_history": history,
        "current_scene": "A dark forest",
    }
    async with db_factory() as db:
        await repo.save_game_session(db, session)
        await db.commit()
    return "sess-roll"


@pytest.mark.asyncio
async def test_roll_up_summarizes_old_entries(db_factory):
    session_id = await _make_session(db_factory, entries=80)
    llm = FakeLLM()

    assert await maybe_roll_up(db_factory, llm, session_id) is True

    async with db_factory() as db:
        session = await repo.get_game_session(db, session_id)
    assert "Mira" in session["history_summary"]
    assert session["summarized_upto"] == 80 - KEEP_RECENT
    # Full history preserved — summary augments, never deletes
    assert len(session["narrative_history"]) == 80


@pytest.mark.asyncio
async def test_no_roll_up_for_short_history(db_factory):
    session_id = await _make_session(db_factory, entries=KEEP_RECENT + CHUNK_MIN - 2)
    llm = FakeLLM()

    assert await maybe_roll_up(db_factory, llm, session_id) is False
    assert llm.calls == []


@pytest.mark.asyncio
async def test_incremental_roll_up_carries_previous_summary(db_factory):
    session_id = await _make_session(db_factory, entries=80)
    llm = FakeLLM()
    await maybe_roll_up(db_factory, llm, session_id)

    # Session grows; next pass must include the previous summary as input
    async with db_factory() as db:
        session = await repo.get_game_session(db, session_id)
        for i in range(40, 55):
            session["narrative_history"].append(f"Player: later action {i}")
            session["narrative_history"].append(f"DM: later outcome {i}")
        await repo.save_game_session(db, session)
        await db.commit()

    llm.reply = "Updated saga: the Ashen Hand struck back at Duskhollow."
    assert await maybe_roll_up(db_factory, llm, session_id) is True
    prompt_text = llm.calls[-1]["messages"][0].content
    assert "PREVIOUS SUMMARY" in prompt_text
    assert "Mira" in prompt_text

    async with db_factory() as db:
        session = await repo.get_game_session(db, session_id)
    assert "Ashen Hand struck back" in session["history_summary"]
    assert session["summarized_upto"] == 110 - KEEP_RECENT


@pytest.mark.asyncio
async def test_llm_failure_leaves_session_untouched(db_factory):
    session_id = await _make_session(db_factory, entries=80)

    assert await maybe_roll_up(db_factory, FailingLLM(), session_id) is False
    async with db_factory() as db:
        session = await repo.get_game_session(db, session_id)
    assert session.get("history_summary") in (None, "")


@pytest.mark.asyncio
async def test_missing_session_is_noop(db_factory):
    assert await maybe_roll_up(db_factory, FakeLLM(), "nope") is False


@pytest.mark.asyncio
async def test_summarize_chunk_prompt_contains_transcript():
    llm = FakeLLM()
    result = await summarize_chunk(llm, "", ["Player: hello", "DM: the door creaks"])
    assert result == llm.reply
    assert "the door creaks" in llm.calls[0]["messages"][0].content
