"""Player-to-player item trading.

Trades live in volatile in-memory storage (`storage.trades`) — they represent
short-lived offers that resolve quickly. On accept, items move between the
two characters' `structured_inventory` lists atomically; on
decline/cancel/expiry the offer is simply removed.

WebSocket notifications:
- `trade_offer`   — sent privately to the recipient when an offer is created.
- `trade_resolved` — broadcast to the whole session when an offer is
  accepted/declined/cancelled, so both endpoints (and any open trade list
  UIs) can update.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

import app.repository as repo
from app.api import storage
from app.db import get_db

router = APIRouter(prefix="/game", tags=["trade"])


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class TradeItemRef(BaseModel):
    """A reference to an item the sender wants to trade.

    `item_id` identifies a specific entry in the character's
    `structured_inventory`. If `quantity` is less than the stack size the
    item is split on accept.
    """

    item_id: str = Field(..., description="Item id from the character's structured_inventory")
    quantity: int = Field(default=1, ge=1, description="Number of units to transfer")


class TradeCreate(BaseModel):
    from_player_id: str = Field(..., description="Initiating player_id")
    from_character_id: str = Field(..., description="Character whose inventory to debit")
    to_player_id: str = Field(..., description="Recipient player_id")
    to_character_id: Optional[str] = Field(
        default=None,
        description="Recipient's character_id; if omitted the trade is rejected on accept",
    )
    offered_items: List[TradeItemRef] = Field(default_factory=list)
    requested_items: List[TradeItemRef] = Field(default_factory=list)
    offered_gold: int = Field(default=0, ge=0)
    requested_gold: int = Field(default=0, ge=0)
    note: str = Field(default="", max_length=280)


class TradeResponse(BaseModel):
    action: str = Field(..., description="'accept' or 'decline'")
    player_id: str = Field(..., description="Responding player; must be the recipient")


class TradeCancel(BaseModel):
    player_id: str = Field(..., description="Cancelling player; must be the initiator")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_item_ids(character: dict) -> bool:
    """Ensure every entry in structured_inventory has an `id`. Returns True
    if the character was mutated and needs to be saved."""
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


def _find_item(inv: list, item_id: str) -> Optional[dict]:
    for entry in inv:
        if isinstance(entry, dict) and entry.get("id") == item_id:
            return entry
    return None


def _player_in_session(session_id: str, player_id: str) -> Optional[dict]:
    for p in storage.session_players.get(session_id, []):
        if p.get("id") == player_id:
            return p
    return None


def _trade_summary(trade: dict) -> dict:
    """Shape returned to clients — same as the stored dict today."""
    return dict(trade)


async def _debit_items(character: dict, refs: List[TradeItemRef]) -> list[dict]:
    """Remove `refs` from character's structured_inventory, returning the
    detached item dicts (with quantity = requested). Raises on insufficient
    quantity or missing item; caller wraps in HTTPException."""
    inv = character.setdefault("structured_inventory", [])
    detached: list[dict] = []
    for ref in refs:
        entry = _find_item(inv, ref.item_id)
        if entry is None:
            raise ValueError(f"item {ref.item_id} not found")
        have = int(entry.get("quantity", 1))
        if have < ref.quantity:
            raise ValueError(
                f"item {entry.get('name', ref.item_id)} has {have}, needs {ref.quantity}"
            )
        if have == ref.quantity:
            inv.remove(entry)
            detached.append(dict(entry))
        else:
            entry["quantity"] = have - ref.quantity
            split = dict(entry)
            split["quantity"] = ref.quantity
            # The split-off stack needs its own id so it doesn't shadow the
            # remaining stack in the recipient's inventory.
            split["id"] = str(uuid.uuid4())
            detached.append(split)
    return detached


def _credit_items(character: dict, items: list[dict]) -> None:
    inv = character.setdefault("structured_inventory", [])
    for item in items:
        # Merge stacks of the same name+rarity to keep inventories tidy.
        merged = False
        for entry in inv:
            if (
                isinstance(entry, dict)
                and entry.get("name") == item.get("name")
                and entry.get("rarity") == item.get("rarity")
                and entry.get("item_type") == item.get("item_type")
            ):
                entry["quantity"] = int(entry.get("quantity", 1)) + int(item.get("quantity", 1))
                merged = True
                break
        if not merged:
            inv.append(dict(item))


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/sessions/{session_id}/trades", status_code=status.HTTP_201_CREATED)
async def create_trade(
    session_id: str,
    body: TradeCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a trade offer. The recipient is notified via WS `trade_offer`."""
    session = await repo.get_game_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Game session not found")

    # Validate players are in the session.
    sender = _player_in_session(session_id, body.from_player_id)
    recipient = _player_in_session(session_id, body.to_player_id)
    if sender is None or recipient is None:
        raise HTTPException(
            status_code=400,
            detail="Both players must be joined to the session",
        )
    if body.from_player_id == body.to_player_id:
        raise HTTPException(status_code=400, detail="Cannot trade with yourself")
    if not body.offered_items and not body.requested_items and body.offered_gold == 0 and body.requested_gold == 0:
        raise HTTPException(status_code=400, detail="Trade must offer or request something")

    # Validate sender owns the offered items (eagerly — they may still race
    # before accept, which we recheck atomically there).
    sender_char = await repo.get_character(db, body.from_character_id)
    if sender_char is None:
        raise HTTPException(status_code=404, detail="Sender character not found")
    if _ensure_item_ids(sender_char):
        await repo.save_character(db, sender_char)
    inv = sender_char.get("structured_inventory") or []
    for ref in body.offered_items:
        entry = _find_item(inv, ref.item_id)
        if entry is None:
            raise HTTPException(status_code=400, detail=f"Item {ref.item_id} not in sender inventory")
        if int(entry.get("quantity", 1)) < ref.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Item {entry.get('name', ref.item_id)} insufficient quantity",
            )

    # If the recipient character is supplied, make sure their items exist
    # (only a soft check; recheck atomically on accept).
    if body.to_character_id and body.requested_items:
        recipient_char = await repo.get_character(db, body.to_character_id)
        if recipient_char is None:
            raise HTTPException(status_code=404, detail="Recipient character not found")
        if _ensure_item_ids(recipient_char):
            await repo.save_character(db, recipient_char)
        rinv = recipient_char.get("structured_inventory") or []
        for ref in body.requested_items:
            entry = _find_item(rinv, ref.item_id)
            if entry is None:
                raise HTTPException(status_code=400, detail=f"Requested item {ref.item_id} not in recipient inventory")
            if int(entry.get("quantity", 1)) < ref.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Requested item {entry.get('name', ref.item_id)} insufficient quantity",
                )

    trade_id = str(uuid.uuid4())
    trade: dict[str, Any] = {
        "id": trade_id,
        "session_id": session_id,
        "from_player_id": body.from_player_id,
        "from_player_name": sender.get("name", ""),
        "from_character_id": body.from_character_id,
        "to_player_id": body.to_player_id,
        "to_player_name": recipient.get("name", ""),
        "to_character_id": body.to_character_id,
        "offered_items": [ref.model_dump() for ref in body.offered_items],
        "requested_items": [ref.model_dump() for ref in body.requested_items],
        "offered_gold": body.offered_gold,
        "requested_gold": body.requested_gold,
        "note": body.note,
        "status": "pending",
        "created_at": _now(),
        "resolved_at": None,
    }
    # Snapshot a human-readable label for each offered/requested item so the
    # recipient's UI can render the offer even if the items move later.
    def _label_refs(refs: list[dict], from_inv: list) -> list[dict]:
        out = []
        for r in refs:
            entry = _find_item(from_inv, r["item_id"])
            label = entry.get("name", r["item_id"]) if entry else r["item_id"]
            out.append({**r, "name": label})
        return out

    trade["offered_items"] = _label_refs(trade["offered_items"], inv)
    if body.to_character_id:
        try:
            rinv = (await repo.get_character(db, body.to_character_id) or {}).get(
                "structured_inventory", []
            )
        except Exception:
            rinv = []
        trade["requested_items"] = _label_refs(trade["requested_items"], rinv)

    storage.trades[trade_id] = trade

    # Notify the recipient privately if they're connected.
    from app.api.websockets.game_ws import manager

    delivered = await manager.send_to_player(
        session_id,
        body.to_player_id,
        {"type": "trade_offer", "trade": _trade_summary(trade), "timestamp": _now()},
    )
    return {"trade": _trade_summary(trade), "delivered": delivered}


@router.get("/sessions/{session_id}/trades")
async def list_trades(
    session_id: str,
    player_id: Optional[str] = None,
    status_filter: Optional[str] = None,
) -> dict:
    """List trades for a session. Filter by player or status when provided."""
    result = []
    for tid, t in storage.trades.items():
        if t.get("session_id") != session_id:
            continue
        if player_id is not None and t.get("from_player_id") != player_id and t.get("to_player_id") != player_id:
            continue
        if status_filter is not None and t.get("status") != status_filter:
            continue
        result.append(_trade_summary(t))
    return {"trades": result}


@router.post("/sessions/{session_id}/trades/{trade_id}/respond")
async def respond_trade(
    session_id: str,
    trade_id: str,
    body: TradeResponse,
    db: AsyncSession = Depends(get_db),
) -> dict:
    trade = storage.trades.get(trade_id)
    if trade is None or trade.get("session_id") != session_id:
        raise HTTPException(status_code=404, detail="Trade not found")
    if trade.get("status") != "pending":
        raise HTTPException(status_code=409, detail=f"Trade already {trade['status']}")
    if body.player_id != trade.get("to_player_id"):
        raise HTTPException(status_code=403, detail="Only the recipient can respond")
    if body.action not in ("accept", "decline"):
        raise HTTPException(status_code=400, detail="action must be 'accept' or 'decline'")

    if body.action == "decline":
        trade["status"] = "declined"
        trade["resolved_at"] = _now()
        from app.api.websockets.game_ws import manager

        await manager.broadcast(
            session_id,
            {"type": "trade_resolved", "trade": _trade_summary(trade), "timestamp": _now()},
        )
        return {"trade": _trade_summary(trade)}

    # accept: atomic two-sided transfer.
    sender_char = await repo.get_character(db, trade["from_character_id"])
    if sender_char is None:
        trade["status"] = "cancelled"
        trade["resolved_at"] = _now()
        raise HTTPException(status_code=410, detail="Sender character missing; trade cancelled")
    _ensure_item_ids(sender_char)

    recipient_char_id = trade.get("to_character_id")
    if not recipient_char_id:
        raise HTTPException(
            status_code=400,
            detail="Recipient has no character selected; cannot complete trade",
        )
    recipient_char = await repo.get_character(db, recipient_char_id)
    if recipient_char is None:
        raise HTTPException(status_code=404, detail="Recipient character not found")
    _ensure_item_ids(recipient_char)

    # Detach items from both sides first (raises if anything is missing),
    # only then credit. This keeps the operation effectively atomic from
    # the client's perspective: either both inventories change or neither.
    offered_refs = [TradeItemRef(**r) for r in trade.get("offered_items", [])]
    requested_refs = [TradeItemRef(**r) for r in trade.get("requested_items", [])]
    try:
        offered_items = await _debit_items(sender_char, offered_refs)
        requested_items = await _debit_items(recipient_char, requested_refs)
    except ValueError as exc:
        # Partial debit happened on sender if recipient debit fails — undo it.
        if "offered_items" in locals():
            _credit_items(sender_char, offered_items)  # type: ignore[has-type]
        trade["status"] = "cancelled"
        trade["resolved_at"] = _now()
        raise HTTPException(status_code=409, detail=str(exc))

    _credit_items(recipient_char, offered_items)
    _credit_items(sender_char, requested_items)

    await repo.save_character(db, sender_char)
    await repo.save_character(db, recipient_char)

    trade["status"] = "accepted"
    trade["resolved_at"] = _now()

    from app.api.websockets.game_ws import manager

    await manager.broadcast(
        session_id,
        {"type": "trade_resolved", "trade": _trade_summary(trade), "timestamp": _now()},
    )
    return {"trade": _trade_summary(trade)}


@router.post("/sessions/{session_id}/trades/{trade_id}/cancel")
async def cancel_trade(session_id: str, trade_id: str, body: TradeCancel) -> dict:
    trade = storage.trades.get(trade_id)
    if trade is None or trade.get("session_id") != session_id:
        raise HTTPException(status_code=404, detail="Trade not found")
    if trade.get("status") != "pending":
        raise HTTPException(status_code=409, detail=f"Trade already {trade['status']}")
    if body.player_id != trade.get("from_player_id"):
        raise HTTPException(status_code=403, detail="Only the initiator can cancel")
    trade["status"] = "cancelled"
    trade["resolved_at"] = _now()

    from app.api.websockets.game_ws import manager

    await manager.broadcast(
        session_id,
        {"type": "trade_resolved", "trade": _trade_summary(trade), "timestamp": _now()},
    )
    return {"trade": _trade_summary(trade)}
