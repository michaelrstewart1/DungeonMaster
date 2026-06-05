"""Inventory item actions: use, equip, unequip.

These are session-scoped because we broadcast WS notifications so the DM and
other players see when someone uses or equips an item.

Item shape (in `character.structured_inventory`):
    {
      id: str,
      name: str,
      quantity: int,
      rarity: str | None,
      item_type: str | None,         # 'potion', 'weapon', 'armor', 'shield', 'accessory', etc.
      description: str | None,
      effect: {type: str, value: str | int} | None,
                                     # Currently supported types:
                                     #   'heal'   value=dice notation (e.g. '2d4+2')
      equipped: bool,                # only meaningful for equippable item_types
    }
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

import app.repository as repo
from app.api import storage
from app.db import get_db
from app.services.dice import DiceRoller

router = APIRouter(prefix="/game", tags=["items"])

EQUIPPABLE_TYPES = {"weapon", "armor", "shield", "accessory"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_item_ids(character: dict) -> bool:
    """Mirror of trade._ensure_item_ids — keeps both modules independent."""
    inv = character.get("structured_inventory") or []
    mutated = False
    for entry in inv:
        if not isinstance(entry, dict):
            continue
        if not entry.get("id"):
            entry["id"] = str(uuid.uuid4())
            mutated = True
    character["structured_inventory"] = inv
    return mutated


def _find_item(character: dict, item_id: str) -> tuple[int, dict] | None:
    inv = character.get("structured_inventory") or []
    for idx, entry in enumerate(inv):
        if isinstance(entry, dict) and entry.get("id") == item_id:
            return idx, entry
    return None


def _player_owns_character(session_id: str, player_id: str, character_id: str) -> bool:
    for p in storage.session_players.get(session_id, []):
        if p.get("id") == player_id and p.get("character_id") == character_id:
            return True
    return False


class ItemActionRequest(BaseModel):
    """Body shared by use/equip/unequip; identifies the actor."""
    player_id: str = Field(..., description="Player performing the action")


class UseResult(BaseModel):
    character_id: str
    item_id: str
    item_name: str
    consumed: bool
    effect_summary: Optional[str] = None
    hp_before: Optional[int] = None
    hp_after: Optional[int] = None


def _apply_effect(character: dict, effect: dict) -> tuple[Optional[str], int, int]:
    """Apply effect dict to character. Returns (summary, hp_before, hp_after).

    Unknown effect types return ("<no effect>", hp, hp).
    """
    hp_before = int(character.get("hp") or 0)
    max_hp = int(character.get("max_hp") or hp_before)
    effect_type = effect.get("type")
    value = effect.get("value")

    if effect_type == "heal":
        if isinstance(value, int):
            healed = value
            notation = str(value)
        else:
            try:
                result = DiceRoller().roll(str(value))
                healed = max(0, result.total)
                notation = f"{value} → {healed}"
            except Exception:
                return (f"Bad heal effect: {value}", hp_before, hp_before)
        hp_after = min(max_hp, hp_before + healed)
        character["hp"] = hp_after
        return (f"Healed {hp_after - hp_before} HP ({notation})", hp_before, hp_after)

    return (f"No effect handler for '{effect_type}'", hp_before, hp_before)


@router.post(
    "/sessions/{session_id}/characters/{character_id}/items/{item_id}/use",
    response_model=UseResult,
)
async def use_item(
    session_id: str,
    character_id: str,
    item_id: str,
    body: ItemActionRequest,
    db: AsyncSession = Depends(get_db),
) -> UseResult:
    """Use (consume) one unit of an item; apply its effect if any.

    Decrements quantity by 1; removes the stack entirely when it hits 0.
    """
    session = await repo.get_game_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if not _player_owns_character(session_id, body.player_id, character_id):
        raise HTTPException(status_code=403, detail="That isn't your character")

    character = await repo.get_character(db, character_id)
    if character is None:
        raise HTTPException(status_code=404, detail="Character not found")
    _ensure_item_ids(character)

    found = _find_item(character, item_id)
    if found is None:
        raise HTTPException(status_code=404, detail="Item not found")
    idx, item = found

    effect = item.get("effect")
    summary: Optional[str] = None
    hp_before = hp_after = int(character.get("hp") or 0)
    if isinstance(effect, dict) and effect.get("type"):
        summary, hp_before, hp_after = _apply_effect(character, effect)

    qty = int(item.get("quantity", 1))
    consumed = False
    if qty <= 1:
        character["structured_inventory"].pop(idx)
        consumed = True
    else:
        item["quantity"] = qty - 1

    await repo.save_character(db, character)

    from app.api.websockets.game_ws import manager
    await manager.broadcast(session_id, {
        "type": "item_used",
        "character_id": character_id,
        "character_name": character.get("name", ""),
        "item_name": item.get("name", ""),
        "effect_summary": summary,
        "hp_before": hp_before,
        "hp_after": hp_after,
        "timestamp": _now(),
    })

    return UseResult(
        character_id=character_id,
        item_id=item_id,
        item_name=item.get("name", ""),
        consumed=consumed,
        effect_summary=summary,
        hp_before=hp_before,
        hp_after=hp_after,
    )


async def _toggle_equipped(
    session_id: str,
    character_id: str,
    item_id: str,
    body: ItemActionRequest,
    db: AsyncSession,
    target: bool,
) -> dict:
    session = await repo.get_game_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if not _player_owns_character(session_id, body.player_id, character_id):
        raise HTTPException(status_code=403, detail="That isn't your character")

    character = await repo.get_character(db, character_id)
    if character is None:
        raise HTTPException(status_code=404, detail="Character not found")
    _ensure_item_ids(character)

    found = _find_item(character, item_id)
    if found is None:
        raise HTTPException(status_code=404, detail="Item not found")
    _, item = found

    itype = (item.get("item_type") or "").lower()
    if itype not in EQUIPPABLE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Item type '{itype or 'unknown'}' is not equippable",
        )
    item["equipped"] = target
    await repo.save_character(db, character)

    from app.api.websockets.game_ws import manager
    event = "item_equipped" if target else "item_unequipped"
    await manager.broadcast(session_id, {
        "type": event,
        "character_id": character_id,
        "character_name": character.get("name", ""),
        "item_id": item_id,
        "item_name": item.get("name", ""),
        "timestamp": _now(),
    })
    return {"character_id": character_id, "item_id": item_id, "equipped": target}


@router.post("/sessions/{session_id}/characters/{character_id}/items/{item_id}/equip")
async def equip_item(
    session_id: str,
    character_id: str,
    item_id: str,
    body: ItemActionRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await _toggle_equipped(session_id, character_id, item_id, body, db, True)


@router.post("/sessions/{session_id}/characters/{character_id}/items/{item_id}/unequip")
async def unequip_item(
    session_id: str,
    character_id: str,
    item_id: str,
    body: ItemActionRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await _toggle_equipped(session_id, character_id, item_id, body, db, False)
