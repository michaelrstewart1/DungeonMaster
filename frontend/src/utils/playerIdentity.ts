/**
 * Durable player identity, stored in localStorage so it survives phone
 * refreshes, tab closes, and device sleep — sessionStorage is kept in sync
 * for backward compatibility with older reads.
 */

export interface PlayerIdentity {
  playerId: string;
  playerName: string;
  sessionId: string;
  characterId?: string;
  roomCode?: string;
}

const KEY_PREFIX = 'dm_identity_';

export function saveIdentity(identity: PlayerIdentity): void {
  try {
    localStorage.setItem(KEY_PREFIX + identity.sessionId, JSON.stringify(identity));
    localStorage.setItem(KEY_PREFIX + 'last', identity.sessionId);
  } catch { /* storage may be unavailable (private mode) */ }
  sessionStorage.setItem('playerName', identity.playerName);
  sessionStorage.setItem('playerId', identity.playerId);
  sessionStorage.setItem('sessionId', identity.sessionId);
  if (identity.characterId) sessionStorage.setItem('characterId', identity.characterId);
}

export function loadIdentity(sessionId: string): PlayerIdentity | null {
  try {
    const raw = localStorage.getItem(KEY_PREFIX + sessionId);
    if (raw) return JSON.parse(raw) as PlayerIdentity;
  } catch { /* fall through */ }
  // Fallback to legacy sessionStorage values
  const playerId = sessionStorage.getItem('playerId');
  const playerName = sessionStorage.getItem('playerName');
  if (playerId && playerName && sessionStorage.getItem('sessionId') === sessionId) {
    return {
      playerId,
      playerName,
      sessionId,
      characterId: sessionStorage.getItem('characterId') || undefined,
    };
  }
  return null;
}

export function loadLastIdentity(): PlayerIdentity | null {
  try {
    const last = localStorage.getItem(KEY_PREFIX + 'last');
    if (last) return loadIdentity(last);
  } catch { /* ignore */ }
  return null;
}

export function updateIdentity(sessionId: string, patch: Partial<PlayerIdentity>): void {
  const current = loadIdentity(sessionId);
  if (current) saveIdentity({ ...current, ...patch });
}
