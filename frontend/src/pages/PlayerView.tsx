/** Player View — mobile-optimized view for individual players at the table.
 * Shows their character sheet, action input, turn indicator, and narrative feed.
 * Supports push-to-talk voice input via audio WebSocket.
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { uuid } from '../utils/uuid';
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

  // Push-to-talk state
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [micPermission, setMicPermission] = useState<'prompt' | 'granted' | 'denied'>('prompt');
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioWsRef = useRef<WebSocket | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // Connect to audio WebSocket for STT
  useEffect(() => {
    if (!sessionId) return;
    const wsBase = import.meta.env.VITE_WS_URL || `ws://${window.location.host}`;
    const ws = new WebSocket(`${wsBase}/ws/audio/${sessionId}`);
    ws.binaryType = 'arraybuffer';

    ws.onmessage = (event) => {
      if (typeof event.data === 'string') {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'transcription' && msg.text) {
            setActionText((prev) => {
              const combined = prev ? `${prev} ${msg.text}` : msg.text;
              return combined;
            });
            setIsTranscribing(false);
          }
        } catch { /* ignore parse errors */ }
      }
    };

    ws.onclose = () => { audioWsRef.current = null; };
    audioWsRef.current = ws;

    return () => {
      ws.close();
      audioWsRef.current = null;
    };
  }, [sessionId]);

  // Check mic permission on mount
  useEffect(() => {
    navigator.permissions?.query({ name: 'microphone' as PermissionName })
      .then((result) => setMicPermission(result.state as 'prompt' | 'granted' | 'denied'))
      .catch(() => {});
  }, []);

  // Determine turn status from game state
  useEffect(() => {
    if (!gameState || !character) return;
    const currentTurn = (gameState as GameState & { current_turn?: string }).current_turn;
    setIsMyTurn(currentTurn === character.id);
  }, [gameState, character]);

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
      const p = last.payload as { narration?: string; character_id?: string; current_turn?: string };
      setNarrative((prev) => [
        ...prev,
        {
          id: uuid(),
          text: p.narration || '',
          type: 'narration',
          timestamp: new Date().toISOString(),
        },
      ]);
      // Update turn status if included in result
      if (p.current_turn && character) {
        setIsMyTurn(p.current_turn === character.id);
      }
    }

    if ((last.type as string) === 'chat') {
      const p = last.payload as { message?: string; sender?: string };
      setNarrative((prev) => [
        ...prev,
        {
          id: uuid(),
          text: p.message || '',
          sender: p.sender,
          type: 'chat',
          timestamp: new Date().toISOString(),
        },
      ]);
    }

    if (last.type === 'game_state' as string) {
      const gs = last.payload as GameState;
      setGameState(gs);
      if (character) {
        const ct = (gs as GameState & { current_turn?: string }).current_turn;
        setIsMyTurn(ct === character.id);
      }
    }

    if ((last.type as string) === 'turn_update') {
      const p = last.payload as { current_turn?: string; phase?: string };
      if (p.current_turn && character) {
        setIsMyTurn(p.current_turn === character.id);
      }
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
  }, [messages, character]);

  // Auto-scroll feed
  useEffect(() => {
    feedRef.current?.scrollTo({ top: feedRef.current.scrollHeight, behavior: 'smooth' });
  }, [narrative]);

  // Push-to-talk handlers
  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      setMicPermission('granted');

      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' });
      mediaRecorderRef.current = recorder;
      audioChunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        // Send audio to backend for STT
        const ws = audioWsRef.current;
        if (ws && ws.readyState === WebSocket.OPEN && blob.size > 0) {
          setIsTranscribing(true);
          const buffer = await blob.arrayBuffer();
          ws.send(buffer);
        }
        // Stop all mic tracks
        stream.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
      };

      recorder.start(250); // collect chunks every 250ms
      setIsRecording(true);
    } catch (err) {
      console.error('Microphone access denied:', err);
      setMicPermission('denied');
    }
  }, []);

  const stopRecording = useCallback(() => {
    const recorder = mediaRecorderRef.current;
    if (recorder && recorder.state !== 'inactive') {
      recorder.stop();
    }
    setIsRecording(false);
  }, []);

  function handleSendAction() {
    const text = actionText.trim();
    if (!text) return;
    sendAction(character?.id || 'unknown', text);
    setNarrative((prev) => [
      ...prev,
      { id: uuid(), text, type: 'action', sender: playerName, timestamp: new Date().toISOString() },
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
    <div className={`player-view ${isMyTurn ? 'pv-my-turn' : ''}`}>
      {/* Turn overlay banner */}
      {isMyTurn && (
        <div className="pv-turn-overlay">
          <div className="pv-turn-overlay-text">⚔️ YOUR TURN ⚔️</div>
        </div>
      )}

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
              placeholder={isTranscribing ? 'Transcribing...' : isMyTurn ? "It's your turn! What do you do?" : 'What do you do?'}
            />
            <button className="pv-action-btn" onClick={handleSendAction} disabled={!actionText.trim()}>
              ⚔️
            </button>
            <button className="pv-chat-btn" onClick={handleSendChat} disabled={!actionText.trim()}>
              💬
            </button>
          </div>

          {/* Push-to-Talk button */}
          <div className="pv-ptt-container">
            <button
              className={`pv-ptt-btn ${isRecording ? 'pv-ptt-recording' : ''} ${isTranscribing ? 'pv-ptt-transcribing' : ''} ${micPermission === 'denied' ? 'pv-ptt-denied' : ''}`}
              onPointerDown={(e) => { e.preventDefault(); startRecording(); }}
              onPointerUp={(e) => { e.preventDefault(); stopRecording(); }}
              onPointerLeave={() => { if (isRecording) stopRecording(); }}
              onContextMenu={(e) => e.preventDefault()}
              disabled={micPermission === 'denied'}
              aria-label="Push to talk"
            >
              <div className="pv-ptt-icon">
                {isRecording ? (
                  <svg viewBox="0 0 24 24" fill="currentColor" width="28" height="28">
                    <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                    <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
                  </svg>
                ) : isTranscribing ? (
                  <div className="pv-ptt-dots">
                    <span /><span /><span />
                  </div>
                ) : (
                  <svg viewBox="0 0 24 24" fill="currentColor" width="28" height="28">
                    <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                    <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
                  </svg>
                )}
              </div>
              <span className="pv-ptt-label">
                {isRecording ? 'Listening...' : isTranscribing ? 'Transcribing...' : micPermission === 'denied' ? 'Mic Blocked' : 'Hold to Speak'}
              </span>
            </button>
            {isRecording && (
              <div className="pv-ptt-pulse-ring" />
            )}
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
