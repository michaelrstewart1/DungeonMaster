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
const DEVICE_KEY = 'dm_device_id';
const CLAIM_PREFIX = 'dm_claimed_';

let memoryDeviceId = '';

/** Stable id for this phone, so a rejoin can reclaim a seat after the name changes. */
export function getDeviceId(): string {
  try {
    const existing = localStorage.getItem(DEVICE_KEY);
    if (existing) return existing;
    const created = typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
      ? crypto.randomUUID()
      : `dev-${Date.now().toString(16)}-${Math.random().toString(16).slice(2)}`;
    localStorage.setItem(DEVICE_KEY, created);
    return created;
  } catch {
    if (!memoryDeviceId) {
      memoryDeviceId = `mem-${Date.now().toString(16)}-${Math.random().toString(16).slice(2)}`;
    }
    return memoryDeviceId;
  }
}

/** This browser tab has finished the claim step for the session. */
export function markClaimedThisSession(sessionId: string): void {
  try { sessionStorage.setItem(CLAIM_PREFIX + sessionId, '1'); } catch { /* ignore */ }
}

export function hasClaimedThisSession(sessionId: string | undefined | null): boolean {
  if (!sessionId) return false;
  try { return sessionStorage.getItem(CLAIM_PREFIX + sessionId) === '1'; } catch { return false; }
}

/** Opening the join form starts a visit that has not claimed a hero yet. */
export function clearClaimedThisSession(): void {
  try {
    const keys: string[] = [];
    for (let i = 0; i < sessionStorage.length; i++) {
      const key = sessionStorage.key(i);
      if (key && key.startsWith(CLAIM_PREFIX)) keys.push(key);
    }
    for (const key of keys) sessionStorage.removeItem(key);
  } catch { /* ignore */ }
}

export function saveIdentity(identity: PlayerIdentity): void {
  try {
    localStorage.setItem(KEY_PREFIX + identity.sessionId, JSON.stringify(identity));
    localStorage.setItem(KEY_PREFIX + 'last', identity.sessionId);
  } catch { /* storage may be unavailable (private mode) */ }
  sessionStorage.setItem('playerName', identity.playerName);
  sessionStorage.setItem('playerId', identity.playerId);
  sessionStorage.setItem('sessionId', identity.sessionId);
  if (identity.characterId) sessionStorage.setItem('characterId', identity.characterId);
  else sessionStorage.removeItem('characterId');
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

/** Identity saved for this table's room code, ignoring whichever session was last. */
export function loadIdentityForRoom(roomCode: string): PlayerIdentity | null {
  const code = roomCode.trim().toUpperCase();
  if (!code) return null;
  try {
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (!key || !key.startsWith(KEY_PREFIX) || key === KEY_PREFIX + 'last') continue;
      const raw = localStorage.getItem(key);
      if (!raw) continue;
      const identity = JSON.parse(raw) as PlayerIdentity;
      if ((identity.roomCode || '').toUpperCase() === code && identity.sessionId) {
        return identity;
      }
    }
  } catch { /* ignore */ }
  return null;
}

export function updateIdentity(sessionId: string, patch: Partial<PlayerIdentity>): void {
  const current = loadIdentity(sessionId);
  if (current) saveIdentity({ ...current, ...patch });
}
