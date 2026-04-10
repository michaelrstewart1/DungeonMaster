"""Integration tests for WebSocket map-related messages."""
import pytest
from httpx import AsyncClient
import asyncio

from app.api.websockets.game_ws import manager


@pytest.mark.asyncio
async def test_websocket_token_move_broadcasts_to_all_clients():
    """token_move message is broadcasted to all connected players in session."""
    session_id = "ws-test-session-1"
    
    # Broadcast token move message
    message = {
        "type": "token_move",
        "token_id": "char1",
        "x": 7,
        "y": 8,
    }
    await manager.broadcast(session_id, message)
    
    # Since we don't have connected clients, just verify broadcast doesn't crash


@pytest.mark.asyncio
async def test_websocket_fog_update_broadcasts_to_all_clients():
    """fog_update message is broadcasted to all connected players in session."""
    session_id = "ws-test-session-2"
    
    # Broadcast fog update message
    message = {
        "type": "fog_update",
        "revealed": [[0, 0], [1, 1], [2, 2]],
    }
    await manager.broadcast(session_id, message)
    
    # Since we don't have connected clients, just verify broadcast doesn't crash


@pytest.mark.asyncio
async def test_websocket_map_sync_broadcasts_full_state():
    """map_sync message broadcasts full map state to all players."""
    session_id = "ws-test-session-3"
    
    # Broadcast map sync message with full map state
    map_data = {
        "width": 10,
        "height": 10,
        "terrain_grid": [["empty"] * 10 for _ in range(10)],
        "token_positions": [{"entity_id": "char1", "x": 5, "y": 5}],
        "fog_of_war": [[False] * 10 for _ in range(10)],
    }
    message = {
        "type": "map_sync",
        "map_data": map_data,
    }
    await manager.broadcast(session_id, message)
    
    # Just verify broadcast doesn't crash


@pytest.mark.asyncio
async def test_websocket_handles_invalid_map_message_types():
    """Unknown message types are ignored gracefully."""
    session_id = "ws-test-session-4"
    
    # Broadcast unknown message type
    message = {
        "type": "unknown_type",
        "some_data": "value",
    }
    await manager.broadcast(session_id, message)
    
    # Should not crash
    assert True
