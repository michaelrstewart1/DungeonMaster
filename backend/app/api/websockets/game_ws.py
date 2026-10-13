"""WebSocket endpoint for real-time game session updates."""
import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

import app.repository as repo
from app.api import storage
from app.api.routes.game import (
    _advance_time,
    _apply_xp_award,
    _detect_scene_type,
    _extract_npcs_from_narration,
    _generate_dm_response,
    _merge_detected_npcs,
    _sync_combatant_hp,
    _sync_combatants_to_characters,
    apply_reported_hp,
)
from app.api.routes.items import _player_owns_character
from app.services.dice import notation_modifier, roll_broadcast_total
from app.services.game.combat_loop import (
    announce_current_player,
    classify_combat_text,
    current_combatant,
    format_initiative_summary,
    hp_updates_from_state,
    note_current_player_acted,
    prepare_player_facing_narration,
    resolve_player_action,
    resolve_waiting_monster_turn,
    run_pending_monster_turns,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


class ConnectionManager:
    """Manager for WebSocket connections grouped by session."""

    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: dict[str, list[WebSocket]] = {}
        # session_id -> set of connections that joined as read-only observers.
        # Observers receive every broadcast but are excluded from player
        # counts and never trigger join/leave broadcasts.
        self.observer_connections: dict[str, set[WebSocket]] = {}
        # session_id -> {player_id: WebSocket} for targeted (private) sends.
        # A player's id is the one reconciled after `player_join` (the HTTP
        # join id when supplied, otherwise the WS-generated id).
        self.player_connections: dict[str, dict[str, WebSocket]] = {}

    async def connect(self, session_id: str, websocket: WebSocket, observer: bool = False):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)
        if observer:
            self.observer_connections.setdefault(session_id, set()).add(websocket)

    def disconnect(self, session_id: str, websocket: WebSocket):
        """Remove a WebSocket connection from the session."""
        if session_id in self.active_connections:
            self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        observers = self.observer_connections.get(session_id)
        if observers:
            observers.discard(websocket)
            if not observers:
                del self.observer_connections[session_id]
        # Forget any player_id -> websocket mappings for this connection.
        players = self.player_connections.get(session_id)
        if players:
            stale = [pid for pid, ws in players.items() if ws is websocket]
            for pid in stale:
                del players[pid]
            if not players:
                del self.player_connections[session_id]

    def register_player(self, session_id: str, player_id: str, websocket: WebSocket):
        """Bind a player_id to a specific connection for private sends."""
        if not player_id:
            return
        self.player_connections.setdefault(session_id, {})[player_id] = websocket

    async def send_to_player(self, session_id: str, player_id: str, message: dict) -> bool:
        """Send a message to a single player_id. Returns True if delivered."""
        ws = self.player_connections.get(session_id, {}).get(player_id)
        if ws is None:
            return False
        try:
            await ws.send_json(message)
            return True
        except Exception:
            return False

    async def broadcast(self, session_id: str, message: dict):
        """Send a message to all connections in a session."""
        if session_id not in self.active_connections:
            return

        # Iterate over a snapshot — sends can yield to the loop, during which
        # connections may disconnect and mutate the list.
        for connection in list(self.active_connections[session_id]):
            try:
                if connection.client_state != WebSocketState.CONNECTED:
                    continue
                await connection.send_json(message)
            except Exception:
                pass

    def get_connection_count(self, session_id: str) -> int:
        """Get the number of active PLAYER connections in a session.

        Observers are intentionally excluded — a spectator connecting or
        leaving must never change what players and displays see.
        """
        total = len(self.active_connections.get(session_id, []))
        observers = len(self.observer_connections.get(session_id, set()))
        return max(total - observers, 0)

    def get_observer_count(self, session_id: str) -> int:
        """Get the number of read-only observer connections in a session."""
        return len(self.observer_connections.get(session_id, set()))


# Global connection manager instance
manager = ConnectionManager()


def _owner_player_id(session_id: str, character_id: str | None, *candidates: str | None) -> str | None:
    """First candidate seat that actually owns ``character_id``, if any."""
    if not character_id:
        return None
    for pid in candidates:
        if isinstance(pid, str) and pid and _player_owns_character(session_id, pid, character_id):
            return pid
    return None


async def _handle_combat_ws_action(
    websocket: WebSocket,
    session_id: str,
    player_id: str,
    message: dict,
) -> bool:
    """Resolve a combat-phase action without waiting on the language model.

    Returns True when the session is in engine combat and this message was
    answered (rules result, initiative acknowledgement, ownership error, or
    an immediate fallback). Exploration messages return False so the caller
    keeps the existing narration path.

    A dice report or a typed attack used to block this socket inside a 90s
    model call, which left the phone on "DM is composing…" with every combat
    button disabled. The rules engine already owns initiative and attacks.
    """
    db_factory = getattr(websocket.app.state, "db_factory", None)
    if db_factory is None:
        return False

    character_id = message.get("character_id")
    action = message.get("action") or ""
    claimed_player = message.get("player_id") if isinstance(message.get("player_id"), str) else None

    try:
        async with db_factory() as db:
            session = await repo.get_game_session(db, session_id) or {}
            combat_state = session.get("combat_state") or {}
            if session.get("current_phase") != "combat" or not combat_state.get("combatants"):
                return False

            # A monster left on the initiative index is resolved before any
            # player message is considered. Combat never waits on the table
            # for an enemy or NPC turn — not even for one exchange.
            stuck_events: list[str] = []
            if current_combatant(combat_state) and not current_combatant(combat_state).get("is_player"):
                stuck = run_pending_monster_turns(combat_state)
                stuck_events = list(stuck.get("events") or [])
                note = announce_current_player(combat_state)
                if note:
                    stuck_events.append(note)
                if stuck.get("combat_over"):
                    session["current_phase"] = "exploration"
                    await _sync_combatants_to_characters(db, combat_state)
                    session["combat_state"] = None
                else:
                    await _sync_combatant_hp(db, combat_state)
                    session["combat_state"] = combat_state
                await repo.save_game_session(db, session)
                await db.commit()
                if stuck_events:
                    await manager.broadcast(session_id, {
                        "type": "combat_update",
                        "events": stuck_events,
                        "narration": " ".join(stuck_events),
                        "combat_state": session.get("combat_state"),
                        "phase": session["current_phase"],
                        "combat_over": bool(stuck.get("combat_over")),
                        "hp_updates": hp_updates_from_state(combat_state),
                    })
                if stuck.get("combat_over"):
                    return True

            kind = classify_combat_text(action)
            if kind == "roll":
                summary = format_initiative_summary(combat_state)
                narration = f"{summary}. That roll is noted and does not change the turn order."
                session.setdefault("narrative_history", []).append(f"Player: {action}")
                session["narrative_history"].append(f"DM: {narration}")
                await repo.save_game_session(db, session)
                await db.commit()
                await manager.broadcast(session_id, {
                    "type": "turn_result",
                    "character_id": character_id,
                    "action": action,
                    "narration": narration,
                    "timestamp": datetime.now().isoformat(),
                })
                return True

            if kind in ("attack", "dodge", "heal"):
                registered = storage.session_players.get(session_id) or []
                owner = _owner_player_id(session_id, character_id, claimed_player, player_id)
                if registered and owner is None:
                    await websocket.send_json({
                        "type": "error",
                        "message": "That isn't your character",
                    })
                    return True

                result = resolve_player_action(combat_state, character_id, kind, None)
                if result.get("error"):
                    await websocket.send_json({"type": "error", "message": result["error"]})
                    return True

                for ev in result.get("events") or []:
                    session.setdefault("narrative_history", []).append(f"DM: {ev}")
                if result.get("combat_over"):
                    session["current_phase"] = "exploration"
                    await _sync_combatants_to_characters(db, combat_state)
                    if result.get("victory") and result.get("xp_awarded"):
                        player_ids = [
                            c["id"] for c in combat_state.get("combatants", []) if c.get("is_player")
                        ]
                        if player_ids:
                            await _apply_xp_award(db, player_ids, result["xp_awarded"])
                    session["combat_state"] = None
                else:
                    session["combat_state"] = combat_state
                    await _sync_combatant_hp(db, combat_state)
                await repo.save_game_session(db, session)
                await db.commit()
                await manager.broadcast(session_id, {
                    "type": "combat_update",
                    **result,
                    "narration": " ".join(result.get("events") or []),
                    "combat_state": session.get("combat_state"),
                    "phase": session["current_phase"],
                    "hp_updates": hp_updates_from_state(combat_state),
                })
                return True

            # Anything else said during a fight still gets an immediate reply.
            # Waiting on the model here is what deadlocked round 1.
            # The narrator used to be passed as None, so this branch always
            # took the keyword mock. Keep that: a live model call here is what
            # stalled the table. Monster turns are still resolved below from
            # the reply text and the initiative index.
            narration = await _generate_dm_response(action, session, narrator=None, db=None)
            monster_events: list[str] = []
            ran_engine_monster = False
            if session.get("combat_state"):
                note_current_player_acted(session["combat_state"], character_id)
                resolved = resolve_waiting_monster_turn(session["combat_state"], narration)
                monster_events = list(resolved.get("events") or [])
                ran_engine_monster = bool(monster_events) or bool(resolved.get("combat_over"))
                if resolved.get("combat_over"):
                    session["current_phase"] = "exploration"
                    await _sync_combatants_to_characters(db, session["combat_state"])
                    session["combat_state"] = None
                elif monster_events:
                    await _sync_combatant_hp(db, session["combat_state"])
            # Spoken damage updates the sheet. Skip the DM's own damage
            # sentence when the engine just applied a monster attack, so the
            # same hit cannot land twice.
            hp_source = action if ran_engine_monster else f"{action}\n{narration}"
            hp_updates = await apply_reported_hp(db, session, hp_source, actor_id=character_id)
            if ran_engine_monster and session.get("combat_state"):
                hp_updates = hp_updates_from_state(session["combat_state"]) or hp_updates
            narration = prepare_player_facing_narration(narration, session.get("combat_state"))
            if monster_events:
                narration = f"{' '.join(monster_events)} {narration}".strip()
            note = announce_current_player(session.get("combat_state") or {})
            if note and note not in narration:
                narration = f"{narration} {note}".strip()
            actor = character_id or "Player"
            session.setdefault("narrative_history", []).append(f"Player: {actor}: {action}")
            session["narrative_history"].append(f"DM: {narration}")
            await repo.save_game_session(db, session)
            await db.commit()
            await manager.broadcast(session_id, {
                "type": "turn_result",
                "character_id": character_id,
                "action": action,
                "narration": narration,
                "timestamp": datetime.now().isoformat(),
                "hp_updates": hp_updates,
                "combat_state": session.get("combat_state"),
                "phase": session.get("current_phase"),
            })
            return True
    except Exception:
        logger.exception("Combat action failed for session %s", session_id)
        try:
            await websocket.send_json({
                "type": "error",
                "message": "The action could not be resolved. Try again.",
            })
        except Exception:
            pass
        return True


@router.websocket("/game/{session_id}")
async def websocket_game_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time game session updates.

    Connect with `?role=observer` for a read-only spectator connection:
    observers receive every broadcast but cannot send game-mutating
    messages, never appear in rosters or connection counts, and their
    join/leave is invisible to players.
    """
    player_id = str(uuid.uuid4())
    is_observer = websocket.query_params.get("role") == "observer"

    await manager.connect(session_id, websocket, observer=is_observer)

    try:
        if is_observer:
            # Private ack only — players must never notice an observer.
            await websocket.send_json({
                "type": "observer_ack",
                "observer_count": manager.get_observer_count(session_id),
                "timestamp": datetime.now().isoformat(),
            })
        else:
            # Notify other players that someone joined
            connection_count = manager.get_connection_count(session_id)
            await manager.broadcast(session_id, {
                "type": "player_joined",
                "player_id": player_id,
                "connection_count": connection_count,
            })

        # A reconnecting phone asks for this. Push the row that is stored
        # now — not whatever snapshot the browser cached for GET /state.
        if websocket.query_params.get("resync") == "1":
            db_factory = getattr(websocket.app.state, "db_factory", None)
            if db_factory is not None:
                try:
                    async with db_factory() as db:
                        live = await repo.get_game_session(db, session_id)
                    if live:
                        await websocket.send_json({"type": "game_state", **live})
                except Exception:
                    logger.exception("Failed to push resync state for %s", session_id)

        # Main message loop
        while True:
            message = await websocket.receive_json()
            
            if not isinstance(message, dict):
                continue
            
            message_type = message.get("type")
            
            if message_type == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat(),
                })
                continue

            if is_observer:
                # Server-enforced read-only: ignore every game-mutating
                # message from observers, whatever the client claims to be.
                await websocket.send_json({
                    "type": "error",
                    "message": "Observers are read-only and cannot interact with the game.",
                })
                continue

            if message_type == "chat":
                chat_message = {
                    "type": "chat",
                    "message": message.get("message", ""),
                    "sender": message.get("sender", "Unknown"),
                    "timestamp": datetime.now().isoformat(),
                }
                await manager.broadcast(session_id, chat_message)
            
            elif message_type == "action":
                if await _handle_combat_ws_action(websocket, session_id, player_id, message):
                    continue
                character_id = message.get("character_id")
                action = message.get("action") or ""
                session_data: dict | None = None

                # Use the unified narrator helper so the WS path graceful-falls
                # back to the keyword-mock narration when no LLM provider is
                # configured — same behavior as POST /api/game/sessions/{id}/action.
                # Previously this branch produced a useless stub echo string
                # ("Character X <action>. The DM responds...") for any session
                # running without an LLM key, which made multiplayer unusable.
                narrator = getattr(websocket.app.state, "narrator", None)
                db_factory = getattr(websocket.app.state, "db_factory", None)

                # Resolve the character's NAME — raw UUIDs must never leak
                # into the LLM prompt, narrative history, or player feeds.
                actor_name = None
                if character_id and db_factory is not None:
                    try:
                        async with db_factory() as db:
                            character = await repo.get_character(db, character_id)
                            if character:
                                actor_name = character.get("name")
                    except Exception:
                        actor_name = None
                actor_label = actor_name or character_id
                player_text = f"{actor_label}: {action}" if actor_label else action

                baseline_version: int | None = None
                if db_factory is not None:
                    # Stream LLM tokens live to all clients so the DM display
                    # renders narration as it is generated instead of blocking.
                    chunk_seq = 0

                    async def _broadcast_chunk(text: str) -> None:
                        nonlocal chunk_seq
                        chunk_seq += 1
                        await manager.broadcast(session_id, {
                            "type": "narration_chunk",
                            "character_id": character_id,
                            "chunk": text,
                            "seq": chunk_seq,
                        })

                    try:
                        async with db_factory() as db:
                            session_data = await repo.get_game_session(db, session_id) or {}
                            baseline_version = repo.session_version(session_data)
                            narration = await _generate_dm_response(
                                player_text,
                                session_data,
                                narrator=narrator,
                                db=db,
                                on_chunk=_broadcast_chunk,
                            )
                    except Exception:
                        narration = await _generate_dm_response(player_text, {}, narrator=None, db=None)
                        baseline_version = None
                else:
                    narration = await _generate_dm_response(player_text, {}, narrator=None, db=None)

                # Narrated fights (no initiative snapshot yet) still cannot
                # stall on a monster, and a stated HP change has to hit the sheet.
                hp_updates: list[dict] = []
                if db_factory is not None:
                    try:
                        async with db_factory() as db:
                            session_data = await repo.get_game_session(db, session_id) or session_data or {}
                            # The model answered from the snapshot taken before
                            # the call. If the table moved on, drop that reply
                            # and hand this phone the current row instead of
                            # writing the old scene back.
                            if (
                                baseline_version is not None
                                and repo.session_version(session_data) != baseline_version
                            ):
                                await websocket.send_json({"type": "game_state", **session_data})
                                continue
                            combat_state = session_data.get("combat_state") or {}
                            ran_engine_monster = False
                            if combat_state.get("combatants"):
                                note_current_player_acted(combat_state, character_id)
                                resolved = resolve_waiting_monster_turn(combat_state, narration)
                                ran_engine_monster = bool(resolved.get("events")) or bool(resolved.get("combat_over"))
                                if resolved.get("events"):
                                    narration = f"{' '.join(resolved['events'])} {narration}".strip()
                                if resolved.get("combat_over"):
                                    session_data["current_phase"] = "exploration"
                                    await _sync_combatants_to_characters(db, combat_state)
                                    session_data["combat_state"] = None
                                elif resolved.get("events"):
                                    session_data["combat_state"] = combat_state
                            else:
                                campaign = await repo.get_campaign(db, session_data.get("campaign_id", "")) or {}
                                party = []
                                for cid in campaign.get("character_ids", []):
                                    character = await repo.get_character(db, cid)
                                    if character:
                                        party.append(character)
                                from app.services.game.combat_loop import settle_narrated_monster_turn
                                narration = settle_narrated_monster_turn(
                                    narration, party, actor_id=character_id,
                                )
                            narration = prepare_player_facing_narration(
                                narration, session_data.get("combat_state"),
                            )
                            # Engine attack text is already reflected on the
                            # combatants. Parsing it again would subtract twice.
                            # A player's own "now at 20 of 34 HP" still applies.
                            hp_source = action if ran_engine_monster else f"{action}\n{narration}"
                            hp_updates = await apply_reported_hp(
                                db, session_data, hp_source, actor_id=character_id,
                            )
                            if ran_engine_monster and session_data.get("combat_state"):
                                await _sync_combatant_hp(db, session_data["combat_state"])
                                hp_updates = hp_updates_from_state(session_data["combat_state"]) or hp_updates
                            note = announce_current_player(session_data.get("combat_state") or {})
                            if note and note not in narration:
                                narration = f"{narration} {note}".strip()
                            saved = await repo.save_game_session(db, session_data)
                            if not saved.applied:
                                await websocket.send_json({"type": "game_state", **saved})
                                continue
                            session_data = saved
                            await db.commit()
                    except Exception:
                        logger.exception("Failed to settle narration for session %s", session_id)

                turn_result = {
                    "type": "turn_result",
                    "character_id": character_id,
                    "character_name": actor_name,
                    "action": action,
                    "narration": narration,
                    "timestamp": datetime.now().isoformat(),
                    "environment": session_data.get("environment") if session_data else None,
                    "detected_scene": _detect_scene_type(narration),
                    "detected_npcs": _extract_npcs_from_narration(narration),
                    "hp_updates": hp_updates,
                    "combat_state": (session_data or {}).get("combat_state"),
                    "phase": (session_data or {}).get("current_phase"),
                }

                # Update session state in DB BEFORE broadcasting.
                # Order matters: if we broadcast first, the client may close before
                # the async DB write finishes, leaving the connection in a half-closed
                # state that deadlocks the SQLAlchemy aiosqlite pool on cancellation.
                db_factory = getattr(websocket.app.state, "db_factory", None)
                if db_factory:
                    try:
                        async with db_factory() as db:
                            session_data = await repo.get_game_session(db, session_id)
                            if session_data:
                                session_data.setdefault("narrative_history", []).append(f"Player: {player_text}")
                                session_data["narrative_history"].append(f"DM: {narration}")
                                session_data["turn_count"] = session_data.get("turn_count", 0) + 1
                                # Auto-detect and merge NPCs
                                detected = _extract_npcs_from_narration(narration)
                                _merge_detected_npcs(session_data, detected)
                                # Detect and store scene type
                                scene_type = _detect_scene_type(narration)
                                if scene_type:
                                    session_data["detected_scene"] = scene_type
                                # Advance environment
                                _advance_time(session_data)
                                await repo.save_game_session(db, session_data)
                                await db.commit()
                    except Exception:
                        pass

                # Animate the DM avatar on the TV display for this narration
                from app.api.routes.avatar import trigger_speaking
                trigger_speaking(session_id, narration)

                if session_data:
                    turn_result["state_version"] = repo.session_version(session_data)
                    turn_result["phase"] = session_data.get("current_phase")
                    # An exploration scene must not carry an earlier fight.
                    if session_data.get("current_phase") != "combat":
                        turn_result["combat_state"] = None
                    else:
                        turn_result["combat_state"] = session_data.get("combat_state")

                await manager.broadcast(session_id, turn_result)
            
            elif message_type == "token_move":
                token_move_msg = {
                    "type": "token_move",
                    "token_id": message.get("token_id"),
                    "x": message.get("x"),
                    "y": message.get("y"),
                    "timestamp": datetime.now().isoformat(),
                }
                await manager.broadcast(session_id, token_move_msg)
            
            elif message_type == "fog_update":
                fog_update_msg = {
                    "type": "fog_update",
                    "revealed": message.get("revealed", []),
                    "timestamp": datetime.now().isoformat(),
                }
                await manager.broadcast(session_id, fog_update_msg)
            
            elif message_type == "map_sync":
                map_sync_msg = {
                    "type": "map_sync",
                    "map_data": message.get("map_data", {}),
                    "timestamp": datetime.now().isoformat(),
                }
                await manager.broadcast(session_id, map_sync_msg)

            elif message_type == "player_join":
                name = message.get("name") or "Unknown"
                character_id = message.get("character_id") or None
                supplied_id = message.get("player_id")
                if session_id not in storage.session_players:
                    storage.session_players[session_id] = []
                players = storage.session_players[session_id]

                # Rebind this socket to the existing seat. A phone reload or a
                # QR rejoin opens a new connection (new id) but the player is
                # the same: prefer the id they already joined with, then the
                # same display name. Never wipe a claimed character when the
                # new socket doesn't repeat it, and never steal one.
                existing = None
                if isinstance(supplied_id, str) and supplied_id:
                    existing = next((p for p in players if p.get("id") == supplied_id), None)
                if existing is None and name and name != "Unknown":
                    existing = next(
                        (p for p in players if str(p.get("name", "")).lower() == name.lower()),
                        None,
                    )

                if existing is not None:
                    player_id = existing["id"]
                    bound = existing.get("character_id")
                    if bound:
                        # Keep the claimed hero. A phone that woke up holding
                        # an older session's character id must not overwrite it.
                        character_id = bound
                    elif character_id and any(
                        p.get("character_id") == character_id and p.get("id") != existing["id"]
                        for p in players
                    ):
                        character_id = None
                    existing["name"] = name
                    existing["character_id"] = character_id
                    existing["rejoined_at"] = datetime.now().isoformat()
                else:
                    if character_id and any(p.get("character_id") == character_id for p in players):
                        character_id = None
                    players.append({
                        "id": player_id,
                        "name": name,
                        "character_id": character_id,
                        "is_ready": False,
                        "joined_at": datetime.now().isoformat(),
                    })
                storage.flush("session_players")
                # Bind player_id -> this websocket so the server can send
                # private messages (e.g. trade offers) to a specific player.
                manager.register_player(session_id, player_id, websocket)
                await manager.broadcast(session_id, {
                    "type": "player_update",
                    "players": storage.session_players[session_id],
                    "connection_count": manager.get_connection_count(session_id),
                })

            elif message_type == "dice_roll":
                # The phone used to total the dice and drop the modifier.
                # When the individual faces are present, the broadcast total
                # is sum(faces) + the modifier written on the notation.
                notation = message.get("notation") or ""
                result = message.get("result")
                rolls = message.get("rolls")
                modifier = notation_modifier(notation) if isinstance(notation, str) else 0
                if isinstance(rolls, list) and rolls and isinstance(notation, str):
                    try:
                        result = roll_broadcast_total(notation, rolls)
                    except (TypeError, ValueError):
                        result = message.get("result")
                await manager.broadcast(session_id, {
                    "type": "dice_roll",
                    "player_id": player_id,
                    "character_id": message.get("character_id"),
                    "character_name": message.get("character_name"),
                    "notation": notation,
                    "result": result,
                    "rolls": rolls if isinstance(rolls, list) else None,
                    "modifier": modifier,
                    "breakdown": message.get("breakdown"),
                    "note": message.get("note"),
                    "purpose": message.get("purpose"),
                    "timestamp": datetime.now().isoformat(),
                })

            elif message_type == "player_ready":
                from app.api import storage as _storage
                ready = message.get("ready", True)
                players = _storage.session_players.get(session_id, [])
                for p in players:
                    if p["id"] == player_id:
                        p["is_ready"] = ready
                        break
                _storage.flush("session_players")
                await manager.broadcast(session_id, {
                    "type": "player_update",
                    "players": players,
                    "connection_count": manager.get_connection_count(session_id),
                })

    except WebSocketDisconnect:
        pass
    
    finally:
        manager.disconnect(session_id, websocket)

        if not is_observer:
            connection_count = manager.get_connection_count(session_id)
            try:
                await manager.broadcast(session_id, {
                    "type": "player_left",
                    "player_id": player_id,
                    "connection_count": connection_count,
                })
            except Exception:
                # Never let a farewell broadcast raise through the ASGI stack
                # (e.g. racing sends against sockets that closed simultaneously).
                pass
