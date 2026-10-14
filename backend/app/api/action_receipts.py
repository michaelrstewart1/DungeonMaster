"""Remember player-line ids so a retry does not apply the same action twice.

A phone shows a line as sent only after the server has accepted it. If that
ack is lost, the phone retries with the same id. The first accept wins.
"""
from __future__ import annotations

_seen: dict[str, set[str]] = {}
_CAP = 300


def claim_client_action(session_id: str, client_id: str | None) -> bool:
    """Return True when this id is new and should be processed.

    Missing ids are always processed (older clients, dice, tests).
    """
    if not client_id:
        return True
    seen = _seen.setdefault(session_id, set())
    if client_id in seen:
        return False
    if len(seen) >= _CAP:
        seen.clear()
    seen.add(client_id)
    return True


def release_client_action(session_id: str, client_id: str | None) -> None:
    """Drop an id that was rejected so the player can retry it."""
    if not client_id:
        return
    seen = _seen.get(session_id)
    if seen is not None:
        seen.discard(client_id)


def reset_client_actions() -> None:
    _seen.clear()
