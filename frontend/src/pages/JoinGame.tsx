/** Join Game page — enter a room code or scan QR to join a multiplayer session. */
import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

export function JoinGame() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [roomCode, setRoomCode] = useState(searchParams.get('code') || '');
  const [playerName, setPlayerName] = useState('');
  const [error, setError] = useState('');
  const [joining, setJoining] = useState(false);

  // Auto-join if code is in URL
  useEffect(() => {
    const code = searchParams.get('code');
    const name = searchParams.get('name');
    if (code && name) {
      handleJoin(code, name);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleJoin(code?: string, name?: string) {
    const finalCode = (code || roomCode).trim().toUpperCase();
    const finalName = (name || playerName).trim();

    if (!finalCode) { setError('Enter a room code'); return; }
    if (!finalName) { setError('Enter your name'); return; }

    setJoining(true);
    setError('');

    try {
      const res = await fetch(`${API_BASE}/game/join`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ room_code: finalCode, player_name: finalName }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({ detail: 'Failed to join' }));
        throw new Error(data.detail || 'Failed to join');
      }

      const data = await res.json();
      // Store player info in sessionStorage for the player view
      sessionStorage.setItem('playerName', finalName);
      sessionStorage.setItem('playerId', data.player_id);
      sessionStorage.setItem('sessionId', data.session_id);

      navigate(`/play/${data.session_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to join');
    } finally {
      setJoining(false);
    }
  }

  return (
    <div className="join-game-page">
      <div className="join-game-card">
        <div className="join-game-icon">⚔️</div>
        <h1>Join Adventure</h1>
        <p className="join-game-subtitle">Enter the room code shown on the DM screen</p>

        <div className="join-game-form">
          <label className="join-field">
            <span>Your Name</span>
            <input
              type="text"
              value={playerName}
              onChange={(e) => setPlayerName(e.target.value)}
              placeholder="e.g. Cohen, Brody, Kit"
              maxLength={30}
              autoFocus
            />
          </label>

          <label className="join-field">
            <span>Room Code</span>
            <input
              type="text"
              className="join-room-code-input"
              value={roomCode}
              onChange={(e) => setRoomCode(e.target.value.toUpperCase())}
              placeholder="ABCD"
              maxLength={6}
            />
          </label>

          {error && <div className="join-error">{error}</div>}

          <button
            className="join-game-btn"
            onClick={() => handleJoin()}
            disabled={joining || !roomCode.trim() || !playerName.trim()}
          >
            {joining ? 'Joining...' : '🗡️ Enter the Dungeon'}
          </button>
        </div>
      </div>
    </div>
  );
}
