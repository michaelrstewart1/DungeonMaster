/** Game Lobby — host view showing room code, QR, and connected players. */
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useGameSocket } from '../hooks/useGameSocket';
import type { Character } from '../types';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

export function Lobby() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const { connected, players, connectionCount } = useGameSocket(sessionId);
  const [roomCode, setRoomCode] = useState('');
  const [characters, setCharacters] = useState<Character[]>([]);
  const [sessionInfo, setSessionInfo] = useState<{ campaign_id?: string }>({});

  // Fetch session info and room code
  useEffect(() => {
    if (!sessionId) return;

    fetch(`${API_BASE}/game/sessions/${sessionId}/state`)
      .then((r) => r.json())
      .then((data) => {
        setSessionInfo(data);
        if (data.campaign_id) {
          fetch(`${API_BASE}/characters?campaign_id=${data.campaign_id}`)
            .then((r) => r.json())
            .then(setCharacters)
            .catch(() => {});
        }
      })
      .catch(() => {});

    fetch(`${API_BASE}/game/sessions/${sessionId}/room-code`)
      .then((r) => r.json())
      .then((data) => setRoomCode(data.room_code || ''))
      .catch(() => {});
  }, [sessionId]);

  const joinUrl = `${window.location.origin}/join?code=${roomCode}`;

  function launchDMDisplay() {
    navigate(`/dm/${sessionId}`);
  }

  function launchGame() {
    navigate(`/game/${sessionId}`);
  }

  return (
    <div className="lobby-page">
      <div className="lobby-header">
        <h1>⚔️ Adventure Lobby</h1>
        <div className={`lobby-connection ${connected ? 'lobby-connected' : 'lobby-disconnected'}`}>
          {connected ? '🟢 Connected' : '🔴 Connecting...'}
        </div>
      </div>

      <div className="lobby-grid">
        {/* Room Code Section */}
        <div className="lobby-card lobby-room-code-card">
          <h2>Room Code</h2>
          <div className="lobby-room-code">{roomCode || '...'}</div>
          <p className="lobby-hint">Players: open your phone browser and go to</p>
          <div className="lobby-url">{joinUrl}</div>
          <p className="lobby-hint">Or enter the code at <strong>/join</strong></p>

          {/* Simple QR placeholder — rendered as a text-based URL */}
          <div className="lobby-qr">
            <div className="lobby-qr-placeholder">
              📱 QR
            </div>
            <span className="lobby-qr-label">Scan to join</span>
          </div>
        </div>

        {/* Connected Players */}
        <div className="lobby-card lobby-players-card">
          <h2>Players ({connectionCount})</h2>
          <div className="lobby-player-list">
            {players.length === 0 && (
              <div className="lobby-waiting">Waiting for players to join...</div>
            )}
            {players.map((p) => (
              <div key={p.id} className={`lobby-player ${p.isReady ? 'lobby-player-ready' : ''}`}>
                <span className="lobby-player-icon">🧙</span>
                <span className="lobby-player-name">{p.name}</span>
                <span className="lobby-player-status">
                  {p.isReady ? '✅ Ready' : '⏳ Choosing...'}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Available Characters */}
        <div className="lobby-card lobby-characters-card">
          <h2>Party Characters</h2>
          <div className="lobby-character-list">
            {characters.map((c) => (
              <div key={c.id} className="lobby-character">
                {c.portrait_url && (
                  <img src={c.portrait_url} alt={c.name} className="lobby-character-portrait" />
                )}
                <div className="lobby-character-info">
                  <strong>{c.name}</strong>
                  <span>Lvl {c.level} {c.race} {c.class_name}</span>
                </div>
              </div>
            ))}
            {characters.length === 0 && (
              <div className="lobby-waiting">No characters in this campaign yet</div>
            )}
          </div>
        </div>
      </div>

      <div className="lobby-actions">
        <button className="lobby-btn lobby-btn-dm" onClick={launchDMDisplay}>
          🖥️ Launch DM Display (TV)
        </button>
        <button className="lobby-btn lobby-btn-play" onClick={launchGame}>
          ▶️ Start Adventure
        </button>
      </div>
    </div>
  );
}
