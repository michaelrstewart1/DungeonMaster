"""WebSocket endpoint for real-time game session updates."""
import uuid
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

import app.repository as repo

router = APIRouter(prefix="/ws", tags=["websocket"])


class ConnectionManager:
    """Manager for WebSocket connections grouped by session."""

    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: dict[str, list[WebSocket]] = {}

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
                action = message.get("action")

                narrator = getattr(websocket.app.state, "narrator", None)
                if narrator is not None:
                    try:
                        from app.services.llm.narrator import _strip_action_echo
                        db_factory = getattr(websocket.app.state, "db_factory", None)
                        if db_factory:
                            async with db_factory() as db:
                                session_data = await repo.get_game_session(db, session_id) or {}
                                campaign_id = session_data.get("campaign_id", "")
                                campaign = await repo.get_campaign(db, campaign_id) or {}
                                world_context = campaign.get("world_state", {}).get("context", "A perilous realm.")
                                characters = []
                                for cid in campaign.get("character_ids", []):
                                    c = await repo.get_character(db, cid)
                                    if c:
                                        characters.append(c)
                                scene = {
                                    "name": "Current Scene",
                                    "description": session_data.get("current_scene", ""),
                                }
                                story_bible = await repo.get_campaign_story_bible(db, campaign_id) or ""
                                player_text = f"{character_id}: {action}" if character_id else (action or "")
                                narration = await narrator.narrate_exploration(
                                    scene=scene,
                                    player_action=player_text,
                                    characters=characters,
                                    world_context=world_context,
                                    story_bible=story_bible,
                                )
                                # Safety: strip any echoed action
                                narration = _strip_action_echo(narration, action or "")
                        else:
                            narration = f"Character {character_id} {action}. The DM responds..."
                    except Exception:
                        narration = f"Character {character_id} {action}. The DM responds..."
                else:
                    narration = f"Character {character_id} {action}. The DM responds..."

                turn_result = {
                    "type": "turn_result",
                    "character_id": character_id,
                    "action": action,
                    "narration": narration,
                    "timestamp": datetime.now().isoformat(),
                }
                await manager.broadcast(session_id, turn_result)

                # Update session state in DB
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
                                await repo.save_game_session(db, session_data)
                                await db.commit()
                    except Exception:
                        pass
            
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
                await manager.broadcast(session_id, {
                    "type": "player_update",
                    "players": _storage.session_players[session_id],
                    "connection_count": manager.get_connection_count(session_id),
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
