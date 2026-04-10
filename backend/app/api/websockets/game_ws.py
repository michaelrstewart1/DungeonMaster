"""WebSocket endpoint for real-time game session updates."""
import uuid
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

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
                # Connection may have been closed, skip it
                pass

    def get_connection_count(self, session_id: str) -> int:
        """Get the number of active connections in a session."""
        return len(self.active_connections.get(session_id, []))


# Global connection manager instance
manager = ConnectionManager()


@router.websocket("/game/{session_id}")
async def websocket_game_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time game session updates.
    
    Handles:
    - ping/pong: {"type": "ping"} -> {"type": "pong", "timestamp": "..."}
    - chat: {"type": "chat", "message": "...", "sender": "..."} 
    - action: {"type": "action", "character_id": "...", "action": "..."}
    - player_joined/left events on connect/disconnect
    """
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
                # Respond to ping with pong
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat(),
                })
            
            elif message_type == "chat":
                # Broadcast chat message to all in session
                chat_message = {
                    "type": "chat",
                    "message": message.get("message", ""),
                    "sender": message.get("sender", "Unknown"),
                    "timestamp": datetime.now().isoformat(),
                }
                await manager.broadcast(session_id, chat_message)
            
            elif message_type == "action":
                # Process player action and broadcast result
                character_id = message.get("character_id")
                action = message.get("action")
                
                # Generate narration (mock for now)
                narration = f"Character {character_id} {action}. The DM responds..."
                
                turn_result = {
                    "type": "turn_result",
                    "character_id": character_id,
                    "action": action,
                    "narration": narration,
                    "timestamp": datetime.now().isoformat(),
                }
                await manager.broadcast(session_id, turn_result)
            
            # Other message types are ignored gracefully
    
    except WebSocketDisconnect:
        pass
    
    finally:
        # Cleanup and notify others
        manager.disconnect(session_id, websocket)
        connection_count = manager.get_connection_count(session_id)
        
        await manager.broadcast(session_id, {
            "type": "player_left",
            "player_id": player_id,
            "connection_count": connection_count,
        })
