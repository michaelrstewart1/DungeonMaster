"""WebSocket endpoint for real-time game session updates."""
import uuid
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

import app.repository as repo
from app.api.routes.game import (
    _extract_npcs_from_narration,
    _merge_detected_npcs,
    _detect_scene_type,
    _advance_time,
    _generate_dm_response,
)

router = APIRouter(prefix="/ws", tags=["websocket"])


class ConnectionManager:
    """Manager for WebSocket connections grouped by session."""

    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: dict[str, list[WebSocket]] = {}
        # session_id -> {player_id: WebSocket} for targeted (private) sends.
        # A player's id is the one reconciled after `player_join` (the HTTP
        # join id when supplied, otherwise the WS-generated id).
        self.player_connections: dict[str, dict[str, WebSocket]] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)

    def disconnect(self, session_id: str, websocket: WebSocket):
        """Remove a WebSocket connection from the session."""
        if session_id in self.active_connections:
            self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
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
        
        for connection in self.active_connections[session_id]:
            try:
                await connection.send_json(message)
            except Exception:
                pass

    def get_connection_count(self, session_id: str) -> int:
        """Get the number of active connections in a session."""
        return len(self.active_connections.get(session_id, []))


# Global connection manager instance
manager = ConnectionManager()


@router.websocket("/game/{session_id}")
async def websocket_game_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time game session updates."""
    player_id = str(uuid.uuid4())
    
    await manager.connect(session_id, websocket)
    
    try:
        # Notify other players that someone joined
        connection_count = manager.get_connection_count(session_id)
        await manager.broadcast(session_id, {
            "type": "player_joined",
            "player_id": player_id,
            "connection_count": connection_count,
        })
        
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
            
            elif message_type == "chat":
                chat_message = {
                    "type": "chat",
                    "message": message.get("message", ""),
                    "sender": message.get("sender", "Unknown"),
                    "timestamp": datetime.now().isoformat(),
                }
                await manager.broadcast(session_id, chat_message)
            
            elif message_type == "action":
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
                player_text = f"{character_id}: {action}" if character_id else action

                if db_factory is not None:
                    try:
                        async with db_factory() as db:
                            session_data = await repo.get_game_session(db, session_id) or {}
                            narration = await _generate_dm_response(
                                player_text,
                                session_data,
                                narrator=narrator,
                                db=db,
                            )
                    except Exception:
                        narration = await _generate_dm_response(player_text, {}, narrator=None, db=None)
                else:
                    narration = await _generate_dm_response(player_text, {}, narrator=None, db=None)

                turn_result = {
                    "type": "turn_result",
                    "character_id": character_id,
                    "action": action,
                    "narration": narration,
                    "timestamp": datetime.now().isoformat(),
                    "environment": session_data.get("environment") if session_data else None,
                    "detected_scene": _detect_scene_type(narration),
                    "detected_npcs": _extract_npcs_from_narration(narration),
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
                                player_text = f"{character_id}: {action}" if character_id else (action or "")
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
                from app.api import storage as _storage
                name = message.get("name", "Unknown")
                character_id = message.get("character_id")

                # Phase 3 reconciliation: if the client supplies a player_id
                # (typically the one returned by POST /api/game/join) and that
                # id is already known to session_players, adopt it as THIS
                # connection's id. This collapses the historical HTTP/WS
                # double-id and makes player_update broadcasts coherent.
                supplied_id = message.get("player_id")
                if (
                    isinstance(supplied_id, str)
                    and supplied_id
                    and any(
                        p.get("id") == supplied_id
                        for p in _storage.session_players.get(session_id, [])
                    )
                ):
                    player_id = supplied_id

                player_info = {
                    "id": player_id,
                    "name": name,
                    "character_id": character_id,
                    "is_ready": False,
                    "joined_at": datetime.now().isoformat(),
                }
                if session_id not in _storage.session_players:
                    _storage.session_players[session_id] = []
                existing = [p for p in _storage.session_players[session_id] if p["id"] == player_id]
                if existing:
                    existing[0].update(player_info)
                else:
                    _storage.session_players[session_id].append(player_info)
                # Bind player_id -> this websocket so the server can send
                # private messages (e.g. trade offers) to a specific player.
                manager.register_player(session_id, player_id, websocket)
                await manager.broadcast(session_id, {
                    "type": "player_update",
                    "players": _storage.session_players[session_id],
                    "connection_count": manager.get_connection_count(session_id),
                })

            elif message_type == "dice_roll":
                # Phase 3 additive: broadcast a dice roll to all connections.
                # The roll itself is computed client-side today; a future change
                # may make this server-authoritative.
                await manager.broadcast(session_id, {
                    "type": "dice_roll",
                    "player_id": player_id,
                    "character_id": message.get("character_id"),
                    "notation": message.get("notation", ""),
                    "result": message.get("result"),
                    "breakdown": message.get("breakdown"),
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
                await manager.broadcast(session_id, {
                    "type": "player_update",
                    "players": players,
                    "connection_count": manager.get_connection_count(session_id),
                })

    except WebSocketDisconnect:
        pass
    
    finally:
        manager.disconnect(session_id, websocket)
        connection_count = manager.get_connection_count(session_id)
        
        await manager.broadcast(session_id, {
            "type": "player_left",
            "player_id": player_id,
            "connection_count": connection_count,
        })
