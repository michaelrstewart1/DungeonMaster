"""Seat roster for a multiplayer table.

A phone that comes back the next night must reclaim the stale row for that
name or device, not add a second one. A hero held by a seat that is not
here tonight is released so the picker can offer it again.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.api import storage


def _norm_name(name: str | None) -> str:
    return " ".join((name or "").split()).casefold()


def _clean_name(name: str | None) -> str:
    return " ".join((name or "").split())


def connected_player_ids(session_id: str) -> set[str]:
    """Player ids with a live socket. Host and TV sockets are not seats."""
    try:
        from app.api.websockets.game_ws import manager
    except Exception:
        return set()
    sockets = manager.player_connections.get(session_id) or {}
    return {pid for pid in sockets if pid}


def present_character_ids(session_id: str) -> set[str] | None:
    """Character ids claimed by a connected seat.

    ``None`` means no seat is connected, so callers should keep using the
    whole campaign. A set — even an empty one — means the table is live and
    only these claims are in play.
    """
    live = connected_player_ids(session_id)
    if not live:
        return None
    claimed: set[str] = set()
    for player in storage.session_players.get(session_id, []):
        character_id = player.get("character_id")
        if player.get("id") in live and character_id:
            claimed.add(character_id)
    return claimed


def _score(player: dict, live: set[str]) -> tuple[int, int, int]:
    return (
        1 if player.get("id") in live else 0,
        1 if player.get("character_id") else 0,
        1 if player.get("present") is not False else 0,
    )


def _fold(donor: dict, into: dict) -> None:
    """Copy the bits a duplicate row might be the only copy of."""
    if not into.get("character_id") and donor.get("character_id"):
        into["character_id"] = donor["character_id"]
    if not into.get("previous_character_id") and donor.get("previous_character_id"):
        into["previous_character_id"] = donor["previous_character_id"]
    if not into.get("device_id") and donor.get("device_id"):
        into["device_id"] = donor["device_id"]
    if donor.get("present") is not False:
        into["present"] = True


def collapse_duplicate_seats(session_id: str) -> None:
    """One row per device, and one row per name.

    Prefer a connected seat, then one that still holds a hero. The lobby
    cannot list the same player twice after this.
    """
    players = list(storage.session_players.get(session_id) or [])
    if len(players) < 2:
        return
    live = connected_player_ids(session_id)
    kept: list[dict] = []
    by_device: dict[str, dict] = {}
    by_name: dict[str, dict] = {}

    def remember(row: dict) -> None:
        device = (row.get("device_id") or "").strip()
        name = _norm_name(row.get("name"))
        if device:
            by_device[device] = row
        if name and name != "unknown":
            by_name[name] = row

    def forget(row: dict) -> None:
        device = (row.get("device_id") or "").strip()
        name = _norm_name(row.get("name"))
        if device and by_device.get(device) is row:
            del by_device[device]
        if name and by_name.get(name) is row:
            del by_name[name]

    for row in players:
        device = (row.get("device_id") or "").strip()
        name = _norm_name(row.get("name"))
        target = None
        if device and device in by_device:
            target = by_device[device]
        elif name and name != "unknown" and name in by_name:
            target = by_name[name]
        if target is None:
            kept.append(row)
            remember(row)
            continue
        if _score(row, live) > _score(target, live):
            _fold(target, row)
            kept[kept.index(target)] = row
            forget(target)
            remember(row)
        else:
            _fold(row, target)
    storage.session_players[session_id] = kept


def release_stale_heroes(session_id: str) -> None:
    """A new night: seats with no socket let go of last night's hero.

    The hero id is kept as ``previous_character_id`` so the same player can
    be offered that card again. A seat that is connected right now keeps
    its claim — resuming the table must not unseat someone still in the room.
    """
    live = connected_player_ids(session_id)
    for player in storage.session_players.get(session_id, []):
        if player.get("id") in live:
            player["present"] = True
            continue
        player["present"] = False
        character_id = player.get("character_id")
        if character_id:
            player["previous_character_id"] = character_id
            player["character_id"] = None


def prepare_rejoin_roster(session_id: str) -> None:
    """Collapse duplicates and release heroes before anyone rejoins."""
    if session_id not in storage.session_players:
        storage.session_players[session_id] = []
    collapse_duplicate_seats(session_id)
    release_stale_heroes(session_id)
    storage.flush("session_players")


def visible_players(session_id: str) -> list[dict]:
    """Rows the lobby and the claim picker should see.

    A seat from last night stays in storage so a rejoin can reclaim it, but
    it is not listed until that player comes back (``present`` is not false).
    """
    return [
        player
        for player in storage.session_players.get(session_id, [])
        if player.get("present") is not False
    ]


def _held_by_present(players: list[dict], character_id: str, except_id: str) -> bool:
    return any(
        player.get("character_id") == character_id
        and player.get("id") != except_id
        and player.get("present") is not False
        for player in players
    )


def _find_seat(
    players: list[dict],
    *,
    player_id: str | None,
    device_id: str | None,
    name: str | None,
) -> dict | None:
    if player_id:
        found = next((player for player in players if player.get("id") == player_id), None)
        if found is not None:
            return found
    device = (device_id or "").strip()
    if device:
        found = next(
            (player for player in players if (player.get("device_id") or "").strip() == device),
            None,
        )
        if found is not None:
            return found
    norm = _norm_name(name)
    if norm and norm != "unknown":
        return next(
            (player for player in players if _norm_name(player.get("name")) == norm),
            None,
        )
    return None


def reconcile_seat(
    session_id: str,
    *,
    name: str,
    player_id: str | None = None,
    device_id: str | None = None,
    character_id: str | None = None,
    assign_id: str | None = None,
) -> tuple[dict, bool]:
    """Reclaim a stale seat or create one. Returns ``(seat, rejoined)``.

    Match order is the id the phone already joined with, then the device,
    then the display name. An existing claim is never replaced here — picking
    a different hero goes through select-character. A hero held by someone
    who is still at the table is not taken.
    """
    if session_id not in storage.session_players:
        storage.session_players[session_id] = []
    collapse_duplicate_seats(session_id)
    players = storage.session_players[session_id]
    existing = _find_seat(players, player_id=player_id, device_id=device_id, name=name)
    rejoined = existing is not None
    clean_name = _clean_name(name) or "Unknown"
    device = (device_id or "").strip() or None
    now = datetime.now(timezone.utc).isoformat()

    if existing is None:
        seat_id = assign_id or storage.generate_id()
        seat = {
            "id": seat_id,
            "name": clean_name,
            "character_id": None,
            "device_id": device,
            "present": True,
            "is_ready": False,
            "joined_at": now,
        }
        if character_id and not _held_by_present(players, character_id, seat_id):
            seat["character_id"] = character_id
        players.append(seat)
    else:
        seat = existing
        if clean_name and clean_name != "Unknown":
            seat["name"] = clean_name
        if device:
            seat["device_id"] = device
        seat["present"] = True
        seat["rejoined_at"] = now
        if (
            not seat.get("character_id")
            and character_id
            and not _held_by_present(players, character_id, seat["id"])
        ):
            seat["character_id"] = character_id

    collapse_duplicate_seats(session_id)
    found = _find_seat(
        storage.session_players[session_id],
        player_id=seat.get("id"),
        device_id=seat.get("device_id"),
        name=seat.get("name"),
    )
    storage.flush("session_players")
    return found or seat, rejoined


def release_character_from_absent(session_id: str, character_id: str, keeper_id: str) -> None:
    """A claim from a seat that is not at the table does not block a new one."""
    for player in storage.session_players.get(session_id, []):
        if player.get("id") == keeper_id:
            continue
        if player.get("character_id") != character_id:
            continue
        if player.get("present") is False:
            player["previous_character_id"] = character_id
            player["character_id"] = None
