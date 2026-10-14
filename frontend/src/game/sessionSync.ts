import type { CombatState } from '../types';

/** Fields a resync payload needs in order to be applied or ignored. */
export interface SessionSnapshot {
  id?: string;
  state_version?: number;
  current_phase?: string;
  phase?: string;
  combat_state?: { initiative_order?: unknown[] } | null;
}

export interface AcceptedSession {
  accepted: true;
  version: number;
  phase: 'combat' | 'exploration';
  combat: CombatState | null;
}

export interface RejectedSession {
  accepted: false;
  version: number;
}

/**
 * Decide whether a fetched or pushed session snapshot may replace what this
 * client is showing.
 *
 * A payload for a different session is ignored. When both sides have a
 * positive revision, an older one is ignored — that is the phone that
 * redraws an earlier combat while the rest of the table has moved on.
 * Combat UI is shown only when the authoritative phase is combat, and only
 * with an initiative list. Any other phase clears combat.
 */
export function acceptSessionSnapshot(
  data: SessionSnapshot | null | undefined,
  expectedSessionId: string,
  seenVersion: number,
): AcceptedSession | RejectedSession {
  const seen = seenVersion > 0 ? seenVersion : 0;
  if (!data || (data.id && data.id !== expectedSessionId)) {
    return { accepted: false, version: seen };
  }
  const raw = data.state_version;
  const incoming = typeof raw === 'number' && raw > 0 ? raw : 0;
  if (incoming > 0 && seen > 0 && incoming < seen) {
    return { accepted: false, version: seen };
  }
  const phaseName = data.current_phase || data.phase;
  const inCombat = phaseName === 'combat';
  const order = data.combat_state?.initiative_order;
  const combat = inCombat && Array.isArray(order) && order.length > 0
    ? (data.combat_state as CombatState)
    : null;
  return {
    accepted: true,
    version: Math.max(incoming, seen),
    phase: inCombat ? 'combat' : 'exploration',
    combat,
  };
}

/** GET /state must not be served from the HTTP cache. */
export function fetchSessionState(apiBase: string, sessionId: string): Promise<Response> {
  return fetch(`${apiBase}/game/sessions/${sessionId}/state`, { cache: 'no-store' });
}
