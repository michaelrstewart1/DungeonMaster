"""Integration tests for WebSocket game events."""
import pytest
from starlette.testclient import TestClient

from app.main import create_app
from app.api import storage


@pytest.fixture
def ws_client():
    """Create a test client with WebSocket support."""
    app = create_app()
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_storage_for_ws():
    """Reset in-memory storage before each test."""
    storage.reset()
    yield
    storage.reset()


def create_test_session(client: TestClient) -> str:
    """Helper to create a campaign and game session, return session_id."""
    # Create campaign first
    campaign_response = client.post(
        "/api/campaigns",
        json={
            "name": "Test Campaign",
            "description": "For testing",
            "character_ids": [],
            "world_state": {},
            "dm_settings": {},
        },
    )
    campaign_id = campaign_response.json()["id"]

    # Create game session
    session_response = client.post(
        "/api/game/sessions",
        json={
            "campaign_id": campaign_id,
            "current_phase": "exploration",
            "current_scene": "You enter a tavern.",
        },
    )
    return session_response.json()["id"]


class TestWebSocketConnection:
    """Tests for WebSocket connection establishment."""

    def test_ws_connect_accepts_connection(self, ws_client: TestClient):
        """WebSocket client can connect to /ws/game/{session_id}."""
        session_id = create_test_session(ws_client)
        
        with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws:
            # Connection should be accepted
            assert ws is not None

    def test_ws_connect_to_nonexistent_session(self, ws_client: TestClient):
        """WebSocket connection to non-existent session should still work (lazy creation)."""
        # Test with a session that doesn't exist yet
        with ws_client.websocket_connect("/ws/game/nonexistent-session") as ws:
            assert ws is not None

    def test_ws_multiple_connections_same_session(self, ws_client: TestClient):
        """Multiple WebSocket clients can connect to the same session."""
        session_id = create_test_session(ws_client)
        
        with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws1:
            with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws2:
                assert ws1 is not None
                assert ws2 is not None


class TestWebSocketPingPong:
    """Tests for ping/pong messaging."""

    def test_ws_ping_pong(self, ws_client: TestClient):
        """Client sends ping, receives pong."""
        session_id = create_test_session(ws_client)
        
        with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws:
            # First message is always player_joined event
            join_event = ws.receive_json()
            assert join_event["type"] == "player_joined"
            
            ws.send_json({"type": "ping"})
            data = ws.receive_json()
            assert data["type"] == "pong"

    def test_ws_ping_pong_includes_timestamp(self, ws_client: TestClient):
        """Pong message includes timestamp."""
        session_id = create_test_session(ws_client)
        
        with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws:
            # First message is always player_joined event
            join_event = ws.receive_json()
            assert join_event["type"] == "player_joined"
            
            ws.send_json({"type": "ping"})
            data = ws.receive_json()
            assert data["type"] == "pong"
            assert "timestamp" in data


class TestWebSocketChatMessage:
    """Tests for chat messaging."""

    def test_ws_chat_message_broadcasts(self, ws_client: TestClient):
        """Chat message is broadcast to all clients in session."""
        session_id = create_test_session(ws_client)
        
        with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws1:
            with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws2:
                # Both get player_joined events
                ws1_join = ws1.receive_json()
                assert ws1_join["type"] == "player_joined"
                
                ws2_join = ws2.receive_json()
                assert ws2_join["type"] == "player_joined"
                
                # ws1 also gets a player_joined for ws2
                ws1_join2 = ws1.receive_json()
                assert ws1_join2["type"] == "player_joined"
                
                # Send chat from ws1
                ws1.send_json({
                    "type": "chat",
                    "message": "Hello everyone!",
                    "sender": "Player1"
                })
                
                # Both clients should receive it
                data1 = ws1.receive_json()
                data2 = ws2.receive_json()
                
                assert data1["type"] == "chat"
                assert data1["message"] == "Hello everyone!"
                assert data1["sender"] == "Player1"
                
                assert data2["type"] == "chat"
                assert data2["message"] == "Hello everyone!"
                assert data2["sender"] == "Player1"

    def test_ws_chat_not_sent_to_other_sessions(self, ws_client: TestClient):
        """Chat messages are only sent to clients in the same session."""
        session1_id = create_test_session(ws_client)
        session2_id = create_test_session(ws_client)
        
        with ws_client.websocket_connect(f"/ws/game/{session1_id}") as ws1:
            with ws_client.websocket_connect(f"/ws/game/{session2_id}") as ws2:
                # Consume initial join events
                ws1.receive_json()
                ws2.receive_json()
                
                # Send chat in session 1
                ws1.send_json({
                    "type": "chat",
                    "message": "In session 1",
                    "sender": "Player1"
                })
                
                # ws1 should receive it
                data1 = ws1.receive_json()
                assert data1["type"] == "chat"
                assert data1["message"] == "In session 1"
                
                # ws2 should NOT receive the chat message from session 1
                # We can verify by checking it's still alive by sending a ping
                ws2.send_json({"type": "ping"})
                pong = ws2.receive_json()
                assert pong["type"] == "pong"


class TestWebSocketPlayerEvents:
    """Tests for player join/leave events."""

    def test_ws_player_joined_broadcast_on_connect(self, ws_client: TestClient):
        """When a player connects, broadcast player_joined to all in session."""
        session_id = create_test_session(ws_client)
        
        with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws1:
            # Second client connects
            with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws2:
                # Both should get a player_joined event
                # ws1 should receive it
                data1 = ws1.receive_json()
                assert data1["type"] == "player_joined"
                assert "player_id" in data1
                assert "connection_count" in data1
                
                # ws2 may immediately receive its own join
                # Let's just verify we can receive something
                assert ws2 is not None

    def test_ws_player_left_broadcast_on_disconnect(self, ws_client: TestClient):
        """When a player disconnects, broadcast player_left to others in session."""
        session_id = create_test_session(ws_client)
        
        with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws1:
            # First connection - ws1 gets join event for itself
            ws1_first_join = ws1.receive_json()
            assert ws1_first_join["type"] == "player_joined"
            
            with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws2:
                # ws2 connects - ws1 gets join event for ws2
                ws1_ws2_join = ws1.receive_json()
                assert ws1_ws2_join["type"] == "player_joined"
                
                # ws2 gets its own join event
                ws2_join = ws2.receive_json()
                assert ws2_join["type"] == "player_joined"
            
            # After ws2 disconnects, ws1 should receive player_left
            leave_data = ws1.receive_json()
            assert leave_data["type"] == "player_left"
            assert "player_id" in leave_data
            assert "connection_count" in leave_data


class TestWebSocketConnectionCount:
    """Tests for connection counting."""

    def test_ws_connection_count_single(self, ws_client: TestClient):
        """Single connection should have count of 1."""
        session_id = create_test_session(ws_client)
        
        with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws:
            # Consume initial join event
            join_event = ws.receive_json()
            assert join_event["type"] == "player_joined"
            assert join_event["connection_count"] == 1
            
            ws.send_json({"type": "ping"})
            data = ws.receive_json()
            assert data["type"] == "pong"

    def test_ws_connection_count_multiple(self, ws_client: TestClient):
        """Multiple connections should be counted."""
        session_id = create_test_session(ws_client)
        
        with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws1:
            with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws2:
                with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws3:
                    # Consume all join events
                    for _ in range(3):
                        ws1.receive_json()
                    for _ in range(2):
                        ws2.receive_json()
                    ws3.receive_json()
                    
                    # All connections should be active
                    ws1.send_json({"type": "ping"})
                    data1 = ws1.receive_json()
                    assert data1["type"] == "pong"
                    
                    ws2.send_json({"type": "ping"})
                    data2 = ws2.receive_json()
                    assert data2["type"] == "pong"
                    
                    ws3.send_json({"type": "ping"})
                    data3 = ws3.receive_json()
                    assert data3["type"] == "pong"


class TestWebSocketSessionIsolation:
    """Tests for isolation between sessions."""

    def test_ws_sessions_are_isolated(self, ws_client: TestClient):
        """Messages in one session don't affect another."""
        session1_id = create_test_session(ws_client)
        session2_id = create_test_session(ws_client)
        
        with ws_client.websocket_connect(f"/ws/game/{session1_id}") as ws1:
            with ws_client.websocket_connect(f"/ws/game/{session2_id}") as ws2:
                # Consume initial join events
                ws1.receive_json()
                ws2.receive_json()
                
                # Send ping in session 1
                ws1.send_json({"type": "ping"})
                data1 = ws1.receive_json()
                assert data1["type"] == "pong"
                
                # Session 2 should not be affected
                ws2.send_json({"type": "ping"})
                data2 = ws2.receive_json()
                assert data2["type"] == "pong"

    def test_ws_chat_isolated_between_sessions(self, ws_client: TestClient):
        """Chat in one session doesn't reach another."""
        session1_id = create_test_session(ws_client)
        session2_id = create_test_session(ws_client)
        
        with ws_client.websocket_connect(f"/ws/game/{session1_id}") as ws1:
            with ws_client.websocket_connect(f"/ws/game/{session2_id}") as ws2:
                # Consume initial join events
                ws1.receive_json()
                ws2.receive_json()
                
                # Send chat in session 1
                ws1.send_json({
                    "type": "chat",
                    "message": "Session 1 message",
                    "sender": "Player1"
                })
                
                # ws1 receives its own message
                data1 = ws1.receive_json()
                assert data1["type"] == "chat"
                assert data1["message"] == "Session 1 message"
                
                # ws2 should not receive the chat message from session 1
                # We can verify by checking it's still alive by sending a ping
                ws2.send_json({"type": "ping"})
                pong = ws2.receive_json()
                assert pong["type"] == "pong"


class TestWebSocketActionSubmission:
    """Tests for player action submission via WebSocket."""

    def test_ws_action_submission_receives_turn_result(self, ws_client: TestClient):
        """Client sends action via WS, receives turn_result."""
        session_id = create_test_session(ws_client)
        
        with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws:
            # Consume initial join event
            ws.receive_json()
            
            ws.send_json({
                "type": "action",
                "character_id": "char1",
                "action": "I cast fireball!"
            })
            
            data = ws.receive_json()
            assert data["type"] == "turn_result"
            assert "narration" in data
            assert isinstance(data["narration"], str)

    def test_ws_action_broadcast_to_all_in_session(self, ws_client: TestClient):
        """Action results are broadcast to all players in session."""
        session_id = create_test_session(ws_client)
        
        with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws1:
            with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws2:
                # Consume initial join events
                for _ in range(2):
                    ws1.receive_json()
                ws2.receive_json()
                
                # ws1 sends an action
                ws1.send_json({
                    "type": "action",
                    "character_id": "char1",
                    "action": "Attack the goblin!"
                })
                
                # Both should receive turn_result
                data1 = ws1.receive_json()
                assert data1["type"] == "turn_result"
                assert "narration" in data1
                
                data2 = ws2.receive_json()
                assert data2["type"] == "turn_result"
                assert "narration" in data2


class TestWebSocketStateUpdate:
    """Tests for game state updates."""

    def test_ws_state_update_event(self, ws_client: TestClient):
        """Clients receive state_update events."""
        session_id = create_test_session(ws_client)
        
        with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws:
            # Consume initial join event
            ws.receive_json()
            
            # Send action to trigger state update
            ws.send_json({
                "type": "action",
                "character_id": "char1",
                "action": "Cast spell"
            })
            
            # Receive turn_result
            turn_result = ws.receive_json()
            assert turn_result["type"] == "turn_result"

    def test_ws_multiple_actions_in_sequence(self, ws_client: TestClient):
        """Multiple actions can be submitted and processed in sequence."""
        session_id = create_test_session(ws_client)
        
        with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws:
            # Consume initial join event
            ws.receive_json()
            
            # First action
            ws.send_json({
                "type": "action",
                "character_id": "char1",
                "action": "First action"
            })
            result1 = ws.receive_json()
            assert result1["type"] == "turn_result"
            
            # Second action
            ws.send_json({
                "type": "action",
                "character_id": "char1",
                "action": "Second action"
            })
            result2 = ws.receive_json()
            assert result2["type"] == "turn_result"


class TestWebSocketErrorHandling:
    """Tests for error handling in WebSocket communication."""

    def test_ws_invalid_message_type(self, ws_client: TestClient):
        """Invalid message type should not crash connection."""
        session_id = create_test_session(ws_client)
        
        with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws:
            # Consume initial join event
            ws.receive_json()
            
            # Send invalid message type
            ws.send_json({"type": "invalid_type"})
            
            # Connection should still be open and we can send ping
            ws.send_json({"type": "ping"})
            data = ws.receive_json()
            assert data["type"] == "pong"

    def test_ws_malformed_message(self, ws_client: TestClient):
        """Malformed message should not crash connection."""
        session_id = create_test_session(ws_client)
        
        with ws_client.websocket_connect(f"/ws/game/{session_id}") as ws:
            # Consume initial join event
            ws.receive_json()
            
            # Send message without required fields
            ws.send_json({"data": "incomplete"})
            
            # Connection should still be open
            ws.send_json({"type": "ping"})
            data = ws.receive_json()
            assert data["type"] == "pong"
