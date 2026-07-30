/** Observer View — read-only spectator view of a live game session.
 *
 * Connects to the game WebSocket with role=observer, which the server
 * treats as invisible: no roster entry, no connection_count impact, no
 * join/leave broadcasts, and every game-mutating message is rejected.
 * The observer sees the live story feed, party roster, and combat state.
 */
import { useState, useEffect, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { uuid } from '../utils/uuid';
import { useGameSocket } from '../hooks/useGameSocket';
import type { WSMessage } from '../api/websocket';
import type { CombatState, GameState } from '../types';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

interface FeedEntry {
  id: string;
  text: string;
  sender?: string;
  type: 'narration' | 'chat' | 'action' | 'system';
}

/** Rebuild the story feed from the server's authoritative narrative_history. */
function feedFromHistory(history: unknown, limit = 40): FeedEntry[] {
  if (!Array.isArray(history)) return [];
  return history.slice(-limit).map((line, i) => {
    const s = String(line);
    const isDM = s.startsWith('DM: ');
    return {
      id: `hist-${i}-${s.length}`,
      text: isDM ? s.slice(4) : s.replace(/^Player: /, ''),
      type: isDM ? ('narration' as const) : ('action' as const),
    };
  });
}

export function ObserverView() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const { connected, players, messages } = useGameSocket(sessionId, { observer: true });

  const [feed, setFeed] = useState<FeedEntry[]>([]);
  const [phase, setPhase] = useState<'exploration' | 'combat'>('exploration');
  const [combatState, setCombatState] = useState<CombatState | null>(null);
  const [sceneName, setSceneName] = useState('');
  const feedRef = useRef<HTMLDivElement>(null);

  // Load authoritative state on mount (read-only GET — no side effects).
  useEffect(() => {
    if (!sessionId) return;
    fetch(`${API_BASE}/game/sessions/${sessionId}/state`)
      .then((r) => r.json())
      .then((data: GameState & { narrative_history?: unknown; combat_state?: CombatState; current_phase?: string; current_scene?: string }) => {
        const ph = data.current_phase || (data as { phase?: string }).phase;
        if (ph === 'combat') setPhase('combat');
        if (data.combat_state?.initiative_order?.length) setCombatState(data.combat_state);
        if (data.current_scene) setSceneName(data.current_scene);
        const hist = feedFromHistory(data.narrative_history);
        if (hist.length) setFeed((prev) => (prev.length ? prev : hist));
      })
      .catch(() => {});
  }, [sessionId]);

  // Process EVERY unseen WS message in order (cursor over seq — see
  // PlayerView for the burst-drop rationale).
  const lastSeqRef = useRef(0);
  useEffect(() => {
    const unseen = messages.filter((m) => (m.seq ?? 0) > lastSeqRef.current);
    if (unseen.length === 0) return;
    lastSeqRef.current = unseen[unseen.length - 1].seq ?? lastSeqRef.current;
    unseen.forEach((m) => handleWsMessage(m));

    function handleWsMessage(msg: WSMessage) {
      if ((msg.type as string) === 'reconnected') {
        // Resync authoritative state after a drop — observers never re-join,
        // they just re-fetch what they missed.
        if (sessionId) {
          fetch(`${API_BASE}/game/sessions/${sessionId}/state`)
            .then((r) => r.json())
            .then((data) => {
              const ph = data.current_phase || data.phase;
              if (ph === 'combat') setPhase('combat');
              else if (ph) { setPhase('exploration'); setCombatState(null); }
              if (data.combat_state?.initiative_order?.length) setCombatState(data.combat_state);
              const hist = feedFromHistory(data.narrative_history);
              if (hist.length) {
                setFeed([
                  ...hist,
                  { id: uuid(), text: '— reconnected, story synced —', type: 'system' },
                ]);
              }
            })
            .catch(() => {});
        }
        return;
      }

      if (msg.type === 'turn_result') {
        const p = msg.payload as { narration?: string; character_name?: string; action?: string };
        if (p.character_name && p.action) {
          setFeed((prev) => [...prev, { id: uuid(), text: p.action!, sender: p.character_name, type: 'action' }]);
        }
        if (p.narration) {
          setFeed((prev) => [...prev, { id: uuid(), text: p.narration!, type: 'narration' }]);
        }
      }

      if ((msg.type as string) === 'chat') {
        const p = msg.payload as { message?: string; sender?: string };
        setFeed((prev) => [...prev, { id: uuid(), text: p.message || '', sender: p.sender, type: 'chat' }]);
      }

      if (msg.type === 'combat_started') {
        const p = msg.payload as { combat_state?: CombatState };
        setPhase('combat');
        if (p.combat_state) setCombatState(p.combat_state);
        setFeed((prev) => [...prev, { id: uuid(), text: '⚔️ Combat begins — roll for initiative!', type: 'system' }]);
      }

      if (msg.type === 'combat_update') {
        const p = msg.payload as { events?: string[]; combat_state?: CombatState | null; combat_over?: boolean };
        setPhase('combat');
        if (p.events?.length) {
          setFeed((prev) => [
            ...prev,
            ...p.events!.map((ev) => ({ id: uuid(), text: ev, type: 'narration' as const })),
          ]);
        }
        if (p.combat_over) {
          setPhase('exploration');
          setCombatState(null);
          setFeed((prev) => [...prev, { id: uuid(), text: '🏆 Combat has ended.', type: 'system' }]);
        } else if (p.combat_state) {
          setCombatState(p.combat_state);
        }
      }
    }
  }, [messages, sessionId]);

  // Keep the feed pinned to the newest entry.
  useEffect(() => {
    feedRef.current?.scrollTo({ top: feedRef.current.scrollHeight, behavior: 'smooth' });
  }, [feed]);

  return (
    <div className="player-view observer-view">
      {/* Top bar */}
      <div className="pv-topbar">
        <span className="pv-name">👁 Observer</span>
        <span className="ov-badge">READ ONLY</span>
        <span className={`pv-connection ${connected ? 'pv-online' : 'pv-offline'}`}>
          {connected ? '🟢' : '🔴'}
        </span>
      </div>

      {/* Party roster */}
      {players.length > 0 && (
        <div className="ov-roster">
          {players.map((p) => (
            <span key={p.id} className="ov-roster-chip">{p.name}</span>
          ))}
        </div>
      )}

      <div className="pv-play-tab">
        <div className="pv-narrative-feed" ref={feedRef}>
          {feed.length === 0 && (
            <div className="pv-narrative-empty">
              {sceneName || 'Watching the table — the story will appear here…'}
            </div>
          )}
          {feed.map((entry) => (
            <div key={entry.id} className={`pv-narrative-entry pv-entry-${entry.type}`}>
              {entry.sender && <span className="pv-entry-sender">{entry.sender}: </span>}
              <span className="pv-entry-text">{entry.text}</span>
            </div>
          ))}
        </div>

        {/* Combat initiative strip */}
        {phase === 'combat' && combatState && (
          <div className="pv-initiative-strip">
            <span className="pv-round-chip">R{combatState.round_number}</span>
            {combatState.initiative_order.map((n, i) => (
              <span
                key={`${n}-${i}`}
                className={`pv-init-chip ${i === combatState.current_turn_index ? 'pv-init-chip-active' : ''}`}
              >
                {n}
              </span>
            ))}
          </div>
        )}

        <div className="ov-footer">
          You are watching as a spectator — the game cannot see you.
          <Link to="/join" className="ov-join-link">Want to play? Join the game</Link>
        </div>
      </div>
    </div>
  );
}
