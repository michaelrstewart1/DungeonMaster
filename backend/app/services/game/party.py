"""Who is actually at the table tonight.

Campaign rows outlive a session: Lyra can still be on the campaign after her
player went home. The DM prompt and the narration may only treat a hero as
present when a connected player has claimed them.
"""
from __future__ import annotations

import re


def absent_party_notice(absent: list[dict]) -> str:
    """Instruction block naming heroes who must not be narrated as acting."""
    names = [" ".join(str(c.get("name") or "").split()) for c in absent]
    names = [name for name in names if name]
    if not names:
        return ""
    listed = ", ".join(names)
    return (
        "## Not at the table\n"
        f"These heroes are absent and have no player tonight: {listed}. "
        "Do not narrate them as acting, observing, detecting, speaking, or "
        "making discoveries. Do not credit them with findings. "
        "Only heroes listed as player characters are here.\n"
    )


def party_for_table(characters: list[dict], session_id: str) -> tuple[list[dict], list[dict]]:
    """Split campaign heroes into (present, absent).

    When nobody has a live seat, the whole campaign stays the party — solo
    play and tests have no phone to claim a hero. Once any seat is connected,
    only heroes that seat has claimed are present. Everyone else is absent.
    """
    from app.api.roster import present_character_ids

    claimed = present_character_ids(session_id)
    if claimed is None:
        return list(characters), []
    present = [c for c in characters if c.get("id") in claimed]
    absent = [c for c in characters if c.get("id") not in claimed]
    return present, absent


def uncredit_absent_heroes(text: str, absent_names: list[str]) -> str:
    """Remove an absent hero's name so the line cannot credit them with an action.

    Possessives ("Lyra's findings") become "the earlier" so a present hero's
    sentence still reads. A bare name in front of a verb ("Lyra detected")
    is dropped, leaving the rest of the sentence.
    """
    if not text or not absent_names:
        return text
    names: list[str] = []
    for raw in absent_names:
        full = " ".join(str(raw).split())
        if len(full) < 2:
            continue
        names.append(full)
        first = full.split()[0]
        if first.casefold() != full.casefold() and len(first) >= 3:
            names.append(first)
    # Longer names first so "Lyra Moonwhisper" is removed before "Lyra".
    names.sort(key=len, reverse=True)
    cleaned = text
    for name in names:
        cleaned = re.sub(
            rf"\b{re.escape(name)}'s\b",
            "the earlier",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(rf"\b{re.escape(name)}\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r" +([,.;:!?])", r"\1", cleaned)
    cleaned = re.sub(r"\(\s*\)", "", cleaned)
    return cleaned.strip()
