/** Join Game page — enter a room code or scan QR to join a multiplayer session. */
import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { PRE_MADE_CHARACTERS } from '../data/premadeCharacters';
import { joinHeroOffers, premadeCreateBody, type HeroOffer, type PartyHero } from '../game/joinOffers';
import {
  saveIdentity,
  loadLastIdentity,
  loadIdentityForRoom,
  updateIdentity,
  getDeviceId,
  markClaimedThisSession,
  clearClaimedThisSession,
} from '../utils/playerIdentity';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

type SimpleCharacter = PartyHero;

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
  const [campaignId, setCampaignId] = useState('');
  const [party, setParty] = useState<SimpleCharacter[]>([]);
  const [takenBy, setTakenBy] = useState<Record<string, string>>({});
  const [claiming, setClaiming] = useState(false);
  const [pickError, setPickError] = useState('');
  const [previousCharacterId, setPreviousCharacterId] = useState('');

  /** Map character_id -> claiming player's name (excluding ourselves). */
  async function fetchTaken(sid: string, myPlayerId: string): Promise<Record<string, string>> {
    try {
      const res = await fetch(`${API_BASE}/game/sessions/${sid}/players`);
      if (!res.ok) return {};
      const data = await res.json();
      const map: Record<string, string> = {};
      for (const p of data.players || []) {
        // A seat left over from last night does not hold the hero.
        if (p.present === false) continue;
        if (p.character_id && p.id !== myPlayerId) map[p.character_id] = p.name || 'another player';
      }
      return map;
    } catch {
      return {};
    }
  }

  async function refreshTaken(sid: string, myPlayerId: string) {
    setTakenBy(await fetchTaken(sid, myPlayerId));
  }

  // Opening this form means the hero has not been claimed on this visit.
  // A stale "/play" route must not paint last night's screen over the join.
  useEffect(() => {
    clearClaimedThisSession();
  }, []);

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
      // Reuse a prior identity only when it was saved for this room code.
      // The last identity may belong to an earlier session at another table.
      const previous = loadIdentityForRoom(finalCode);
      const res = await fetch(`${API_BASE}/game/join`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          room_code: finalCode,
          player_name: finalName,
          player_id: previous?.roomCode === finalCode ? previous.playerId : undefined,
          device_id: getDeviceId(),
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
      setCampaignId(data.campaign_id || '');
      // Offer last night's hero, but do not skip the claim step. A rejoin
      // used to land straight on that character and hide the picker.
      setPreviousCharacterId(data.previous_character_id || data.character_id || '');

      // Party rows plus every unclaimed pre-made hero. The character list
      // alone is only who is already in the campaign, which hid the roster
      // from a player joining an occupied table.
      if (data.campaign_id) {
        try {
          const [charRes, taken] = await Promise.all([
            fetch(`${API_BASE}/characters?campaign_id=${data.campaign_id}`),
            fetchTaken(data.session_id, data.player_id),
          ]);
          const chars = charRes.ok ? await charRes.json() : [];
          setParty(Array.isArray(chars) ? chars : []);
          setTakenBy(taken);
          setPhase('pick-character');
          return;
        } catch { /* fall through to direct navigate */ }
      }

      // No characters to pick — go straight to player view
      markClaimedThisSession(data.session_id);
      navigate(`/play/${data.session_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to join');
    } finally {
      setJoining(false);
    }
  }

  async function resolveOfferId(offer: HeroOffer): Promise<string> {
    if (offer.characterId) return offer.characterId;
    const premade = PRE_MADE_CHARACTERS.find((hero) => hero.id === offer.premadeId);
    if (!premade || !campaignId) throw new Error('That hero is not available');

    // Someone may have added this name while the picker was open.
    const charRes = await fetch(`${API_BASE}/characters?campaign_id=${campaignId}`);
    if (charRes.ok) {
      const chars = await charRes.json() as SimpleCharacter[];
      if (Array.isArray(chars)) {
        setParty(chars);
        const existing = chars.find((hero) => hero.name.trim().toLowerCase() === premade.name.trim().toLowerCase());
        if (existing) return existing.id;
      }
    }

    const created = await fetch(`${API_BASE}/characters`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(premadeCreateBody(premade, campaignId)),
    });
    if (!created.ok) {
      const data = await created.json().catch(() => ({ detail: 'Could not add that hero' }));
      throw new Error(typeof data.detail === 'string' ? data.detail : 'Could not add that hero');
    }
    const row = await created.json() as { id: string };
    return row.id;
  }

  async function selectOffer(offer: HeroOffer) {
    if (claiming) return;
    setClaiming(true);
    setPickError('');
    try {
      const charId = await resolveOfferId(offer);
      const taken = await fetchTaken(sessionId, playerId);
      setTakenBy(taken);
      if (taken[charId]) {
        setPickError(`Taken by ${taken[charId]}`);
        return;
      }
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
      markClaimedThisSession(sessionId);
      navigate(`/play/${sessionId}`);
    } catch (err) {
      setPickError(err instanceof Error ? err.message : 'Failed to claim character — check your connection');
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
            {joinHeroOffers(party, PRE_MADE_CHARACTERS, takenBy).map((offer) => {
              const previous = !!previousCharacterId && (
                offer.characterId === previousCharacterId || offer.key === previousCharacterId
              );
              return (
              <button
                key={offer.key}
                className={`character-picker-card${previous ? ' character-picker-card-previous' : ''}`}
                onClick={() => selectOffer(offer)}
                disabled={claiming}
                data-testid={`join-hero-${offer.key}`}
              >
                <div className="character-picker-portrait">
                  {offer.portrait_url ? (
                    <img src={offer.portrait_url} alt={offer.name} />
                  ) : (
                    <span className="character-picker-initial">{offer.name[0]}</span>
                  )}
                </div>
                <div className="character-picker-info">
                  <strong>{offer.name}</strong>
                  <span>Lvl {offer.level} {offer.race} {offer.class_name}</span>
                  {previous && <span className="character-picker-last">Last night</span>}
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

