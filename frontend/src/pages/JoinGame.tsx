/** Join Game page — enter a room code or scan QR to join a multiplayer session. */
import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { saveIdentity, loadLastIdentity, updateIdentity } from '../utils/playerIdentity';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

interface SimpleCharacter {
  id: string;
  name: string;
  race: string;
  class_name: string;
  level: number;
  portrait_url?: string;
}

export function JoinGame() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [roomCode, setRoomCode] = useState(searchParams.get('code') || '');
  const [playerName, setPlayerName] = useState(() => loadLastIdentity()?.playerName || '');
  const [error, setError] = useState('');
  const [joining, setJoining] = useState(false);
  const [phase, setPhase] = useState<'join' | 'pick-character'>('join');
  const [sessionId, setSessionId] = useState('');
  const [playerId, setPlayerId] = useState('');
  const [characters, setCharacters] = useState<SimpleCharacter[]>([]);
  const [takenBy, setTakenBy] = useState<Record<string, string>>({});
  const [claiming, setClaiming] = useState(false);
  const [pickError, setPickError] = useState('');

  /** Map character_id -> claiming player's name (excluding ourselves). */
  async function refreshTaken(sid: string, myPlayerId: string) {
    try {
      const res = await fetch(`${API_BASE}/game/sessions/${sid}/players`);
      if (!res.ok) return;
      const data = await res.json();
      const map: Record<string, string> = {};
      for (const p of data.players || []) {
        if (p.character_id && p.id !== myPlayerId) map[p.character_id] = p.name || 'another player';
      }
      setTakenBy(map);
    } catch { /* non-fatal — picker still works */ }
  }

  // Auto-join if code + name are both in URL
  useEffect(() => {
    const code = searchParams.get('code');
    const name = searchParams.get('name');
    if (code && name) {
      handleJoin(code, name);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleWatch() {
    // Observer path: resolve the code WITHOUT joining the roster, then open
    // the read-only spectator view. Zero side effects on the game.
    const finalCode = roomCode.trim().toUpperCase();
    if (!finalCode) { setError('Enter a room code'); return; }
    setJoining(true);
    setError('');
    try {
      const res = await fetch(`${API_BASE}/game/resolve-code/${finalCode}`);
      if (!res.ok) {
        const data = await res.json().catch(() => ({ detail: 'Invalid room code' }));
        throw new Error(data.detail || 'Invalid room code');
      }
      const data = await res.json();
      navigate(`/watch/${data.session_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to find that table');
    } finally {
      setJoining(false);
    }
  }

  async function handleJoin(code?: string, name?: string) {
    const finalCode = (code || roomCode).trim().toUpperCase();
    const finalName = (name || playerName).trim();

    if (!finalCode) { setError('Enter a room code'); return; }
    if (!finalName) { setError('Enter your name'); return; }

    setJoining(true);
    setError('');

    try {
      // Reuse a prior identity when rejoining the same table (phone refresh,
      // backend restart) so the roster doesn't grow duplicates.
      const previous = loadLastIdentity();
      const res = await fetch(`${API_BASE}/game/join`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          room_code: finalCode,
          player_name: finalName,
          player_id: previous?.roomCode === finalCode ? previous.playerId : undefined,
        }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({ detail: 'Failed to join' }));
        throw new Error(data.detail || 'Failed to join');
      }

      const data = await res.json();
      saveIdentity({
        playerId: data.player_id,
        playerName: finalName,
        sessionId: data.session_id,
        characterId: data.character_id || undefined,
        roomCode: finalCode,
      });
      setSessionId(data.session_id);
      setPlayerId(data.player_id);

      // Rejoining with a character already selected — skip the picker
      if (data.rejoined && data.character_id) {
        navigate(`/play/${data.session_id}`);
        return;
      }

      // Fetch available characters for this campaign
      if (data.campaign_id) {
        try {
          const charRes = await fetch(`${API_BASE}/characters?campaign_id=${data.campaign_id}`);
          if (charRes.ok) {
            const chars = await charRes.json();
            if (Array.isArray(chars) && chars.length > 0) {
              setCharacters(chars);
              refreshTaken(data.session_id, data.player_id);
              setPhase('pick-character');
              return;
            }
          }
        } catch { /* fall through to direct navigate */ }
      }

      // No characters to pick — go straight to player view
      navigate(`/play/${data.session_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to join');
    } finally {
      setJoining(false);
    }
  }

  async function selectCharacter(charId: string) {
    if (claiming) return;
    setClaiming(true);
    setPickError('');
    try {
      // Claim server-side so two phones can't pick the same hero.
      const res = await fetch(`${API_BASE}/game/sessions/${sessionId}/select-character`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ player_id: playerId, character_id: charId }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({ detail: 'Character unavailable' }));
        setPickError(typeof data.detail === 'string' ? data.detail : 'Character unavailable');
        refreshTaken(sessionId, playerId);
        return;
      }
      updateIdentity(sessionId, { characterId: charId });
      navigate(`/play/${sessionId}`);
    } catch {
      setPickError('Failed to claim character — check your connection');
    } finally {
      setClaiming(false);
    }
  }

  // Character picker phase
  if (phase === 'pick-character') {
    return (
      <div className="join-game-page">
        <div className="join-game-card join-game-card-wide">
          <h1>Choose Your Character</h1>
          <p className="join-game-subtitle">Select the character you'll be playing</p>
          {pickError && <div className="join-error">{pickError}</div>}
          <div className="character-picker-grid">
            {characters.map((c) => {
              const taken = takenBy[c.id];
              return (
              <button
                key={c.id}
                className={`character-picker-card${taken ? ' character-picker-card-taken' : ''}`}
                onClick={() => selectCharacter(c.id)}
                disabled={!!taken || claiming}
              >
                <div className="character-picker-portrait">
                  {c.portrait_url ? (
                    <img src={c.portrait_url} alt={c.name} />
                  ) : (
                    <span className="character-picker-initial">{c.name[0]}</span>
                  )}
                </div>
                <div className="character-picker-info">
                  <strong>{c.name}</strong>
                  <span>Lvl {c.level} {c.race} {c.class_name}</span>
                  {taken && <span className="character-picker-taken-label">Taken by {taken}</span>}
                </div>
              </button>
              );
            })}
          </div>
        </div>
      </div>
    );
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
              autoComplete="nickname"
              spellCheck={false}
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
              autoCapitalize="characters"
              autoComplete="off"
              autoCorrect="off"
              spellCheck={false}
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

          <button
            className="join-watch-btn"
            onClick={() => handleWatch()}
            disabled={joining || !roomCode.trim()}
            title="Spectate without affecting the game"
          >
            👁 Just watching? Observe the table
          </button>
        </div>
      </div>
    </div>
  );
}

