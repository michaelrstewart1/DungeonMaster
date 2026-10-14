import { beforeEach, describe, expect, it } from 'vitest';
import {
  clearClaimedThisSession,
  getDeviceId,
  hasClaimedThisSession,
  loadIdentity,
  loadIdentityForRoom,
  markClaimedThisSession,
  saveIdentity,
} from './playerIdentity';

describe('player identity scoping', () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
  });

  it('loads the identity stored for a room code, not the last session', () => {
    saveIdentity({
      playerId: 'p-old',
      playerName: 'Bram',
      sessionId: 'sess-blackwood',
      characterId: 'char-thorne',
      roomCode: 'OLD1',
    });
    saveIdentity({
      playerId: 'p-live',
      playerName: 'Bram',
      sessionId: 'sess-lighthouse',
      characterId: 'char-thorne',
      roomCode: 'LIVE',
    });

    expect(loadIdentityForRoom('live')?.sessionId).toBe('sess-lighthouse');
    expect(loadIdentityForRoom('OLD1')?.playerId).toBe('p-old');
    expect(loadIdentityForRoom('missing')).toBeNull();
  });

  it('does not reuse sessionStorage from a different session', () => {
    sessionStorage.setItem('playerId', 'p-other');
    sessionStorage.setItem('playerName', 'Aria');
    sessionStorage.setItem('sessionId', 'sess-other');
    sessionStorage.setItem('characterId', 'char-lyra');

    expect(loadIdentity('sess-lighthouse')).toBeNull();
  });

  it('clears a leftover character id when the saved identity has none', () => {
    sessionStorage.setItem('characterId', 'char-from-blackwood');
    saveIdentity({
      playerId: 'p-live',
      playerName: 'Bram',
      sessionId: 'sess-lighthouse',
      roomCode: 'LIVE',
    });
    expect(sessionStorage.getItem('characterId')).toBeNull();
    expect(loadIdentity('sess-lighthouse')?.characterId).toBeUndefined();
  });

  it('keeps one device id and treats a claim as this visit only', () => {
    const first = getDeviceId();
    expect(getDeviceId()).toBe(first);
    expect(hasClaimedThisSession('sess-live')).toBe(false);
    markClaimedThisSession('sess-live');
    expect(hasClaimedThisSession('sess-live')).toBe(true);
    clearClaimedThisSession();
    expect(hasClaimedThisSession('sess-live')).toBe(false);
  });
});
