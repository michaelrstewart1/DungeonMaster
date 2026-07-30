"""Rolling narrative summarization.

Long campaigns overflow the LLM context: the narrator only sees the last
~30 narrative entries. Instead of losing older history, this service
compresses it into a running "story so far" summary stored on the session
(`history_summary` + `summarized_upto`), which the narrator injects as a
context layer above recent history.

Runs fire-and-forget after turns — never blocks play.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# Keep this many recent entries verbatim (matches narrator max_history).
KEEP_RECENT = 30
# Only summarize once at least this many un-summarized old entries pile up.
CHUNK_MIN = 20
# Hard cap on how many entries to fold in per pass (token budget).
CHUNK_MAX = 60

SUMMARY_PROMPT = (
    "You are the memory-keeper for a D&D campaign. Merge the previous summary "
    "and the new transcript excerpt into ONE updated 'story so far' summary.\n"
    "Rules:\n"
    "- Past tense, third person, max 250 words.\n"
    "- Preserve: named NPCs and their fates, promises, items gained/lost, "
    "quest progress, deaths, unresolved threads.\n"
    "- Drop flavor descriptions and blow-by-blow dialogue.\n"
    "- Never invent events that are not in the input.\n"
    "Respond with ONLY the summary text."
)


async def summarize_chunk(llm, previous_summary: str, entries: list[str]) -> str:
    """Fold a chunk of narrative entries into the running summary."""
    from app.services.llm.base import LLMMessage

    transcript = "\n".join(entries)
    parts = []
    if previous_summary:
        parts.append(f"PREVIOUS SUMMARY:\n{previous_summary}")
    parts.append(f"NEW TRANSCRIPT:\n{transcript}")
    try:
        response = await llm.generate(
            messages=[LLMMessage(role="user", content="\n\n".join(parts))],
            system_prompt=SUMMARY_PROMPT,
            temperature=0.2,
            max_tokens=400,
        )
        return response.content.strip()
    except Exception as exc:
        logger.warning("History summarization failed: %s", exc)
        return ""


async def maybe_roll_up(db_factory, llm, session_id: str) -> bool:
    """Summarize old narrative entries if enough have scrolled out of the
    narrator's recent-history window. Returns True if a summary was written."""
    from app import repository as repo

    try:
        async with db_factory() as db:
            session = await repo.get_game_session(db, session_id)
        if not session:
            return False

        history = session.get("narrative_history", []) or []
        upto = int(session.get("summarized_upto", 0) or 0)
        boundary = len(history) - KEEP_RECENT
        if boundary - upto < CHUNK_MIN:
            return False

        chunk_end = min(boundary, upto + CHUNK_MAX)
        chunk = history[upto:chunk_end]
        summary = await summarize_chunk(llm, session.get("history_summary", "") or "", chunk)
        if not summary:
            return False

        # Re-fetch and mutate only summary fields to minimize clobbering
        # concurrent turn writes.
        async with db_factory() as db:
            fresh = await repo.get_game_session(db, session_id)
            if not fresh:
                return False
            fresh["history_summary"] = summary
            fresh["summarized_upto"] = chunk_end
            await repo.save_game_session(db, fresh)
            await db.commit()
        logger.info(
            "Rolled up narrative history for session %s (entries %d-%d)",
            session_id, upto, chunk_end,
        )
        return True
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("History roll-up failed for session %s: %s", session_id, exc)
        return False
