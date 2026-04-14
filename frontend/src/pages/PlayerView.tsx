/** Player View — mobile-optimized view for individual players at the table.
 * Shows their character sheet, action input, turn indicator, and narrative feed.
 */
import { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { useGameSocket } from '../hooks/useGameSocket';
import BattleMap from '../components/BattleMap';
import type { Character, GameState, GameMap } from '../types';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

interface NarrativeEntry {
  id: string;
  text: string;
  sender?: string;
  type: 'narration' | 'chat' | 'action' | 'system';
  timestamp: string;
}

export function PlayerView() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const playerName = sessionStorage.getItem('playerName') || 'Adventurer';
  const { connected, messages, sendChat, sendAction } = useGameSocket(sessionId);

  const [character, setCharacter] = useState<Character | null>(null);
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [narrative, setNarrative] = useState<NarrativeEntry[]>([]);
  const [actionText, setActionText] = useState('');
  const [isMyTurn, setIsMyTurn] = useState(false);
  const [tab, setTab] = useState<'play' | 'sheet' | 'map'>('play');
  const [gameMap, setGameMap] = useState<GameMap | null>(null);
  const feedRef = useRef<HTMLDivElement>(null);

  // Load game state and character
  useEffect(() => {
    if (!sessionId) return;
    fetch(`${API_BASE}/game/sessions/${sessionId}/state`)
      .then((r) => r.json())
      .then((data) => setGameState(data))
      .catch(() => {});

    const charId = sessionStorage.getItem('characterId');
    if (charId) {
      fetch(`${API_BASE}/characters/${charId}`)
        .then((r) => r.json())
        .then(setCharacter)
        .catch(() => {});
    }
  }, [sessionId]);

  // Process incoming WebSocket messages
  useEffect(() => {
    if (messages.length === 0) return;
    const last = messages[messages.length - 1];

    if (last.type === 'turn_result') {
      const p = last.payload as { narration?: string; character_id?: string };
      setNarrative((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          text: p.narration || '',
          type: 'narration',
          timestamp: new Date().toISOString(),
        },
      ]);
    }

    if (last.type === 'chat') {
      const p = last.payload as { message?: string; sender?: string };
      setNarrative((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          text: p.message || '',
          sender: p.sender,
          type: 'chat',
          timestamp: new Date().toISOString(),
        },
      ]);
    }

    if (last.type === 'game_state' as string) {
      setGameState(last.payload as GameState);
    }

    if (last.type === 'vision_update' as string) {
      const v = last.payload as { tokens?: Array<{ entity_id: string; x: number; y: number }>; grid_width?: number; grid_height?: number };
      if (v.grid_width && v.grid_height) {
        setGameMap((prev) => ({
          id: prev?.id || 'vision-map',
          width: v.grid_width!,
          height: v.grid_height!,
          terrain: prev?.terrain || Array.from({ length: v.grid_height! }, () => Array(v.grid_width!).fill('empty')),
          tokens: (v.tokens || []).map((t) => ({ entity_id: t.entity_id, x: t.x, y: t.y })),
          fog_of_war: prev?.fog_of_war || Array.from({ length: v.grid_height! }, () => Array(v.grid_width!).fill(false)),
        }));
      }
    }
  }, [messages]);

  // Auto-scroll feed
  useEffect(() => {
    feedRef.current?.scrollTo({ top: feedRef.current.scrollHeight, behavior: 'smooth' });
  }, [narrative]);

  function handleSendAction() {
    const text = actionText.trim();
    if (!text) return;
    sendAction(character?.id || 'unknown', text);
    setNarrative((prev) => [
      ...prev,
      { id: crypto.randomUUID(), text, type: 'action', sender: playerName, timestamp: new Date().toISOString() },
    ]);
    setActionText('');
  }

  function handleSendChat() {
    const text = actionText.trim();
    if (!text) return;
    sendChat(text, playerName);
    setActionText('');
  }

  const hpPct = character ? Math.round((character.hp / (character.max_hp || character.hp)) * 100) : 100;

  return (
    <div className="player-view">
      {/* Top bar */}
      <div className="pv-topbar">
        <span className="pv-name">{playerName}</span>
        <span className={`pv-connection ${connected ? 'pv-online' : 'pv-offline'}`}>
          {connected ? '🟢' : '🔴'}
        </span>
        {isMyTurn && <span className="pv-turn-badge">⚔️ YOUR TURN</span>}
      </div>

      {/* Character quick stats */}
      {character && (
        <div className="pv-stats-bar">
          <div className="pv-stat pv-hp">
            <span className="pv-stat-label">HP</span>
            <div className="pv-hp-bar">
              <div className="pv-hp-fill" style={{ width: `${hpPct}%`, background: hpPct > 50 ? 'var(--hp-green, #4caf50)' : hpPct > 25 ? '#ff9800' : '#f44336' }} />
            </div>
            <span className="pv-stat-val">{character.hp}/{character.max_hp || character.hp}</span>
          </div>
          <div className="pv-stat">
            <span className="pv-stat-label">AC</span>
            <span className="pv-stat-val">{character.ac}</span>
          </div>
          <div className="pv-stat">
            <span className="pv-stat-label">Lvl</span>
            <span className="pv-stat-val">{character.level}</span>
          </div>
        </div>
      )}

      {/* Tab navigation */}
      <div className="pv-tabs">
        <button className={`pv-tab ${tab === 'play' ? 'pv-tab-active' : ''}`} onClick={() => setTab('play')}>
          ⚔️ Play
        </button>
        <button className={`pv-tab ${tab === 'sheet' ? 'pv-tab-active' : ''}`} onClick={() => setTab('sheet')}>
          📜 Sheet
        </button>
        <button className={`pv-tab ${tab === 'map' ? 'pv-tab-active' : ''}`} onClick={() => setTab('map')}>
          🗺️ Map
        </button>
      </div>

      {/* Play tab — narrative feed + action input */}
      {tab === 'play' && (
        <div className="pv-play-tab">
          <div className="pv-narrative-feed" ref={feedRef}>
            {narrative.length === 0 && (
              <div className="pv-narrative-empty">The adventure awaits...</div>
            )}
            {narrative.map((entry) => (
              <div key={entry.id} className={`pv-narrative-entry pv-entry-${entry.type}`}>
                {entry.sender && <span className="pv-entry-sender">{entry.sender}: </span>}
                <span className="pv-entry-text">{entry.text}</span>
              </div>
            ))}
          </div>

          <div className="pv-action-bar">
            <input
              type="text"
              className="pv-action-input"
              value={actionText}
              onChange={(e) => setActionText(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSendAction()}
              placeholder="What do you do?"
            />
            <button className="pv-action-btn" onClick={handleSendAction} disabled={!actionText.trim()}>
              ⚔️
            </button>
            <button className="pv-chat-btn" onClick={handleSendChat} disabled={!actionText.trim()}>
              💬
            </button>
          </div>
        </div>
      )}

      {/* Sheet tab — compact character sheet */}
      {tab === 'sheet' && character && (
        <div className="pv-sheet-tab">
          <div className="pv-sheet-header">
            {character.portrait_url && (
              <img src={character.portrait_url} alt={character.name} className="pv-portrait" />
            )}
            <div>
              <h2>{character.name}</h2>
              <p>{character.race} {character.class_name} • Level {character.level}</p>
              {character.subclass && <p className="pv-subclass">{character.subclass}</p>}
            </div>
          </div>

          <div className="pv-abilities-grid">
            {(['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma'] as const).map((ab) => {
              const val = character[ab];
              const mod = Math.floor((val - 10) / 2);
              return (
                <div key={ab} className="pv-ability">
                  <span className="pv-ability-name">{ab.slice(0, 3).toUpperCase()}</span>
                  <span className="pv-ability-val">{val}</span>
                  <span className="pv-ability-mod">{mod >= 0 ? `+${mod}` : mod}</span>
                </div>
              );
            })}
          </div>

          {character.skills && character.skills.length > 0 && (
            <div className="pv-sheet-section">
              <h3>Skills</h3>
              <div className="pv-skill-tags">
                {character.skills.map((s) => <span key={s} className="pv-skill-tag">{s}</span>)}
              </div>
            </div>
          )}

          {character.equipment && character.equipment.length > 0 && (
            <div className="pv-sheet-section">
              <h3>Equipment</h3>
              <ul className="pv-equipment-list">
                {character.equipment.map((e, i) => <li key={i}>{e}</li>)}
              </ul>
            </div>
          )}

          {character.spells_known && character.spells_known.length > 0 && (
            <div className="pv-sheet-section">
              <h3>Spells</h3>
              <div className="pv-skill-tags">
                {character.spells_known.map((s) => <span key={s} className="pv-skill-tag pv-spell-tag">{s}</span>)}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Map tab — battle map from vision or game state */}
      {tab === 'map' && (
        <div className="pv-map-tab">
          {gameMap ? (
            <BattleMap map={gameMap} />
          ) : (
            <div className="pv-map-placeholder">
              🗺️ Battle map will appear when the DM scans the board
            </div>
          )}
        </div>
      )}
    </div>
  );
}
