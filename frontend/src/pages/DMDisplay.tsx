/** DM Display — full-screen TV view with AI DM avatar, battle map, narrative, and initiative tracker.
 * Designed for a TV at the head of the dining table.
 */
import { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { useGameSocket } from '../hooks/useGameSocket';
import BattleMap from '../components/BattleMap';
import type { GameState, GameMap, Character } from '../types';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

interface NarrativeEntry {
  id: string;
  text: string;
  type: 'narration' | 'action' | 'system';
  timestamp: string;
}

interface AvatarState {
  expression: string;
  is_speaking: boolean;
  mouth_amplitude: number;
  gaze: { x: number; y: number };
}

export function DMDisplay() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const { connected, messages, players, connectionCount } = useGameSocket(sessionId);

  const [gameState, setGameState] = useState<GameState | null>(null);
  const [characters, setCharacters] = useState<Character[]>([]);
  const [narrative, setNarrative] = useState<NarrativeEntry[]>([]);
  const [roomCode, setRoomCode] = useState('');
  const [avatar, setAvatar] = useState<AvatarState>({
    expression: 'neutral',
    is_speaking: false,
    mouth_amplitude: 0,
    gaze: { x: 0, y: 0 },
  });
  const [currentNarration, setCurrentNarration] = useState('');
  const [gameMap, setGameMap] = useState<GameMap | null>(null);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const narrativeRef = useRef<HTMLDivElement>(null);

  // Load initial data
  useEffect(() => {
    if (!sessionId) return;

    fetch(`${API_BASE}/game/sessions/${sessionId}/state`)
      .then((r) => r.json())
      .then((data) => {
        setGameState(data);
        if (data.current_scene) {
          setCurrentNarration(data.current_scene);
        }
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

  // Poll avatar state
  useEffect(() => {
    if (!sessionId) return;
    const interval = setInterval(() => {
      fetch(`${API_BASE}/avatar/${sessionId}`)
        .then((r) => r.json())
        .then(setAvatar)
        .catch(() => {});
    }, 500);
    return () => clearInterval(interval);
  }, [sessionId]);

  // Process WebSocket messages
  useEffect(() => {
    if (messages.length === 0) return;
    const last = messages[messages.length - 1];

    if (last.type === 'turn_result') {
      const p = last.payload as { narration?: string };
      const text = p.narration || '';
      setCurrentNarration(text);
      setNarrative((prev) => [
        ...prev.slice(-50),
        { id: crypto.randomUUID(), text, type: 'narration', timestamp: new Date().toISOString() },
      ]);
      // TTS: speak the narration aloud
      if (text) speakNarration(text);
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

  // Camera upload handler
  async function handleBoardUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !sessionId) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch(`${API_BASE}/vision/${sessionId}/upload`, {
        method: 'POST',
        body: formData,
      });
      if (res.ok) {
        const data = await res.json();
        if (data.grid_width && data.grid_height) {
          setGameMap({
            id: 'vision-map',
            width: data.grid_width,
            height: data.grid_height,
            terrain: Array.from({ length: data.grid_height }, () => Array(data.grid_width).fill('empty')),
            tokens: (data.tokens || []).map((t: { entity_id: string; x: number; y: number }) => ({ entity_id: t.entity_id, x: t.x, y: t.y })),
            fog_of_war: Array.from({ length: data.grid_height }, () => Array(data.grid_width).fill(false)),
          });
        }
      }
    } catch {
      // Vision upload failed silently
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  }

  // TTS audio playback
  async function speakNarration(text: string) {
    try {
      const res = await fetch(`${API_BASE}/game/sessions/${sessionId}/narrate-tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      });
      if (!res.ok) return;
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audio.onended = () => URL.revokeObjectURL(url);
      audio.play().catch(() => {}); // browser may block autoplay until user interaction
    } catch {
      // TTS unavailable, silent fallback
    }
  }

  // Auto-scroll
  useEffect(() => {
    narrativeRef.current?.scrollTo({ top: narrativeRef.current.scrollHeight, behavior: 'smooth' });
  }, [narrative]);

  const phase = gameState?.phase || 'lobby';
  const isCombat = phase === 'combat';
  const combatState = gameState?.combat_state;

  // DM face expressions
  const faceExpressions: Record<string, string> = {
    neutral: '🧙',
    happy: '😊',
    angry: '😠',
    surprised: '😲',
    thinking: '🤔',
    laughing: '😈',
    dramatic: '🔥',
  };

  const faceEmoji = faceExpressions[avatar.expression] || '🧙';

  return (
    <div className="dm-display" data-phase={phase}>
      {/* DM Avatar Section */}
      <div className="dm-avatar-section">
        <div className={`dm-face ${avatar.is_speaking ? 'dm-face-speaking' : ''}`}>
          <span className="dm-face-emoji" style={{
            transform: `translate(${avatar.gaze.x * 5}px, ${avatar.gaze.y * 5}px)`,
          }}>
            {faceEmoji}
          </span>
          {avatar.is_speaking && (
            <div className="dm-speaking-indicator">
              <span className="dm-speak-bar" style={{ height: `${20 + avatar.mouth_amplitude * 30}px` }} />
              <span className="dm-speak-bar" style={{ height: `${10 + avatar.mouth_amplitude * 50}px` }} />
              <span className="dm-speak-bar" style={{ height: `${15 + avatar.mouth_amplitude * 40}px` }} />
              <span className="dm-speak-bar" style={{ height: `${10 + avatar.mouth_amplitude * 50}px` }} />
              <span className="dm-speak-bar" style={{ height: `${20 + avatar.mouth_amplitude * 30}px` }} />
            </div>
          )}
        </div>
        <div className="dm-title">Dungeon Master</div>
      </div>

      {/* Current Narration — large display text */}
      <div className="dm-narration-section">
        <div className="dm-narration-text">
          {currentNarration || 'The adventure begins...'}
        </div>
      </div>

      {/* Middle section: Battle Map + Initiative */}
      <div className="dm-main-section">
        {/* Battle Map */}
        <div className="dm-map-area">
          {gameMap ? (
            <BattleMap map={gameMap} />
          ) : isCombat ? (
            <div className="dm-battle-map">
              <div className="dm-map-grid">
                {Array.from({ length: 100 }).map((_, i) => (
                  <div key={i} className="dm-map-cell" />
                ))}
              </div>
            </div>
          ) : (
            <div className="dm-scene-art">
              <span className="dm-scene-icon">
                {phase === 'exploration' ? '🏰' : phase === 'rest' ? '🏕️' : phase === 'shopping' ? '🏪' : '⚔️'}
              </span>
              <span className="dm-scene-label">{phase.charAt(0).toUpperCase() + phase.slice(1)}</span>
            </div>
          )}
          {/* Camera upload button */}
          <div className="dm-camera-controls">
            <input
              type="file"
              ref={fileInputRef}
              accept="image/*"
              capture="environment"
              onChange={handleBoardUpload}
              style={{ display: 'none' }}
            />
            <button
              className="dm-camera-btn"
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              title="Upload board photo"
            >
              {uploading ? '⏳ Analyzing...' : '📷 Scan Board'}
            </button>
          </div>
        </div>

        {/* Initiative / Turn Order (combat) or Player list (non-combat) */}
        <div className="dm-sidebar">
          {isCombat && combatState ? (
            <div className="dm-initiative">
              <h3>⚔️ Initiative</h3>
              <div className="dm-init-list">
                {combatState.initiative_order.map((name, i) => (
                  <div
                    key={name}
                    className={`dm-init-entry ${i === combatState.current_turn_index ? 'dm-init-active' : ''}`}
                  >
                    <span className="dm-init-order">{i + 1}</span>
                    <span className="dm-init-name">{name}</span>
                    {i === combatState.current_turn_index && <span className="dm-init-arrow">◄</span>}
                  </div>
                ))}
              </div>
              <div className="dm-round">Round {combatState.round_number}</div>
            </div>
          ) : (
            <div className="dm-player-roster">
              <h3>🎭 Party</h3>
              {characters.map((c) => {
                const hpPct = Math.round((c.hp / (c.max_hp || c.hp)) * 100);
                return (
                  <div key={c.id} className="dm-party-member">
                    {c.portrait_url && (
                      <img src={c.portrait_url} alt={c.name} className="dm-party-portrait" />
                    )}
                    <div className="dm-party-info">
                      <span className="dm-party-name">{c.name}</span>
                      <span className="dm-party-class">{c.race} {c.class_name}</span>
                      <div className="dm-party-hp-bar">
                        <div
                          className="dm-party-hp-fill"
                          style={{
                            width: `${hpPct}%`,
                            background: hpPct > 50 ? '#4caf50' : hpPct > 25 ? '#ff9800' : '#f44336',
                          }}
                        />
                      </div>
                    </div>
                  </div>
                );
              })}
              {/* Connected players count */}
              <div className="dm-connected-count">
                {connectionCount} player{connectionCount !== 1 ? 's' : ''} connected
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Bottom bar: Room code + connection status */}
      <div className="dm-bottom-bar">
        <div className="dm-room-code-display">
          <span className="dm-room-label">JOIN CODE:</span>
          <span className="dm-room-value">{roomCode || '...'}</span>
        </div>
        <div className="dm-status">
          <span className={connected ? 'dm-online' : 'dm-offline'}>
            {connected ? '🟢 Live' : '🔴 Reconnecting...'}
          </span>
        </div>
      </div>

      {/* Narrative history (scrolling at bottom) */}
      <div className="dm-narrative-history" ref={narrativeRef}>
        {narrative.map((entry) => (
          <div key={entry.id} className="dm-history-entry">
            {entry.text}
          </div>
        ))}
      </div>
    </div>
  );
}
