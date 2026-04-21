/** Player View — mobile-optimized view for individual players at the table.
 * Shows their character sheet, action input, turn indicator, and narrative feed.
 * Supports push-to-talk voice input via audio WebSocket.
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { uuid } from '../utils/uuid';
import { useGameSocket } from '../hooks/useGameSocket';
import { DiceRoller } from '../components/DiceRoller';
import BattleMap from '../components/BattleMap';
import type { Character, GameState, GameMap, DiceResult } from '../types';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

interface NarrativeEntry {
  id: string;
  text: string;
  sender?: string;
  type: 'narration' | 'chat' | 'action' | 'system';
  timestamp: string;
}

type GamePhase = 'exploration' | 'combat';

interface QuickAction {
  emoji: string;
  label: string;
}

const EXPLORATION_ACTIONS: QuickAction[] = [
  { emoji: '🔍', label: 'Look Around' },
  { emoji: '🚪', label: 'Open Door' },
  { emoji: '💬', label: 'Talk to NPC' },
  { emoji: '🎒', label: 'Check Inventory' },
  { emoji: '⚔️', label: 'Draw Weapon' },
  { emoji: '🏕️', label: 'Set Up Camp' },
];

const COMBAT_ACTIONS: QuickAction[] = [
  { emoji: '⚔️', label: 'Attack' },
  { emoji: '🛡️', label: 'Defend' },
  { emoji: '🔮', label: 'Cast Spell' },
  { emoji: '🏃', label: 'Dodge' },
  { emoji: '💊', label: 'Use Potion' },
  { emoji: '🏳️', label: 'Retreat' },
];

export function PlayerView() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const playerName = sessionStorage.getItem('playerName') || 'Adventurer';
  const characterId = sessionStorage.getItem('characterId') || undefined;
  const { connected, messages, sendChat, sendAction, joinAsPlayer } = useGameSocket(sessionId);

  const [character, setCharacter] = useState<Character | null>(null);
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [narrative, setNarrative] = useState<NarrativeEntry[]>([]);
  const [actionText, setActionText] = useState('');
  const [isMyTurn, setIsMyTurn] = useState(false);
  const [tab, setTab] = useState<'play' | 'sheet' | 'map' | 'dice'>('play');
  const [gameMap, setGameMap] = useState<GameMap | null>(null);
  const [phase, setPhase] = useState<GamePhase>('exploration');
  const [lastDiceResult, setLastDiceResult] = useState<DiceResult | null>(null);
  const [waitingForDM, setWaitingForDM] = useState(false);
  const feedRef = useRef<HTMLDivElement>(null);

  // Push-to-talk state
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [micPermission, setMicPermission] = useState<'prompt' | 'granted' | 'denied'>('prompt');
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioWsRef = useRef<WebSocket | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // Identify ourselves to the game session on connect
  useEffect(() => {
    if (connected && playerName) {
      joinAsPlayer(playerName, characterId);
    }
  }, [connected, playerName, characterId, joinAsPlayer]);

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

    if (characterId) {
      fetch(`${API_BASE}/characters/${characterId}`)
        .then((r) => r.json())
        .then(setCharacter)
        .catch(() => {});
    }
  }, [sessionId, characterId]);

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
      setWaitingForDM(false);
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
      if (gs.phase === 'combat') setPhase('combat');
      else setPhase('exploration');
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
      if (p.phase === 'combat') setPhase('combat');
      else if (p.phase) setPhase('exploration');
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

  // Auto-scroll feed — only when user is already near the bottom
  useEffect(() => {
    const feed = feedRef.current;
    if (!feed) return;
    const isNearBottom = feed.scrollHeight - feed.scrollTop - feed.clientHeight < 100;
    if (isNearBottom) {
      feed.scrollTo({ top: feed.scrollHeight, behavior: 'smooth' });
    }
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
        const ws = audioWsRef.current;
        if (ws && ws.readyState === WebSocket.OPEN && blob.size > 0) {
          setIsTranscribing(true);
          const buffer = await blob.arrayBuffer();
          ws.send(buffer);
        }
        stream.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
      };

      recorder.start(250);
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

  // Stop recording if page is hidden (phone notification, call, app switch)
  useEffect(() => {
    const handleVisibility = () => {
      if (document.hidden) {
        const recorder = mediaRecorderRef.current;
        if (recorder && recorder.state !== 'inactive') {
          recorder.stop();
          setIsRecording(false);
        }
      }
    };
    document.addEventListener('visibilitychange', handleVisibility);
    return () => document.removeEventListener('visibilitychange', handleVisibility);
  }, []);

  function handleSendAction(text?: string) {
    const msg = (text || actionText).trim();
    if (!msg) return;
    sendAction(character?.id || 'unknown', msg);
    setNarrative((prev) => [
      ...prev,
      { id: uuid(), text: msg, type: 'action', sender: playerName, timestamp: new Date().toISOString() },
    ]);
    setActionText('');
    setWaitingForDM(true);
  }

  function handleSendChat() {
    const text = actionText.trim();
    if (!text) return;
    sendChat(text, playerName);
    setActionText('');
  }

  function handleDiceRoll(notation: string) {
    const match = notation.match(/(\d+)d(\d+)/);
    if (match) {
      const count = parseInt(match[1]);
      const sides = parseInt(match[2]);
      const rolls = Array.from({ length: count }, () => Math.floor(Math.random() * sides) + 1);
      const total = rolls.reduce((a, b) => a + b, 0);
      const result: DiceResult = {
        notation,
        rolls,
        modifier: 0,
        total,
        is_critical: sides === 20 && rolls[0] === 20,
        is_fumble: sides === 20 && rolls[0] === 1,
      };
      setLastDiceResult(result);

      // Auto-submit to DM
      const charName = character?.name || playerName;
      const critNote = result.is_critical ? ' (Natural 20!)' : result.is_fumble ? ' (Natural 1!)' : '';
      const rollMsg = `🎲 ${charName} rolls d${sides}: ${total}${critNote}`;
      handleSendAction(rollMsg);
    }
  }

  const quickActions = phase === 'combat' ? COMBAT_ACTIONS : EXPLORATION_ACTIONS;
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
        <span className="pv-name">{character?.name || playerName}</span>
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
        <button className={`pv-tab ${tab === 'dice' ? 'pv-tab-active' : ''}`} onClick={() => setTab('dice')}>
          🎲 Dice
        </button>
        <button className={`pv-tab ${tab === 'sheet' ? 'pv-tab-active' : ''}`} onClick={() => setTab('sheet')}>
          📜 Sheet
        </button>
        <button className={`pv-tab ${tab === 'map' ? 'pv-tab-active' : ''}`} onClick={() => setTab('map')}>
          🗺️ Map
        </button>
      </div>

      {/* Play tab — narrative feed + quick actions + input */}
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
            {waitingForDM && (
              <div className="pv-narrative-entry pv-entry-system">
                <span className="pv-entry-text">🎲 DM is composing...</span>
              </div>
            )}
          </div>

          {/* Quick Actions */}
          <div className="pv-quick-actions">
            {quickActions.map((action) => (
              <button
                key={action.label}
                className="pv-quick-action-btn"
                onClick={() => handleSendAction(`${action.emoji} ${action.label}`)}
                disabled={waitingForDM}
              >
                <span>{action.emoji}</span>
                <span>{action.label}</span>
              </button>
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
              disabled={waitingForDM}
              autoComplete="off"
              autoCorrect="off"
              spellCheck={false}
              inputMode="text"
            />
            <button className="pv-action-btn" onClick={() => handleSendAction()} disabled={!actionText.trim() || waitingForDM}>
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
              onPointerCancel={() => { if (isRecording) stopRecording(); }}
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

      {/* Dice tab */}
      {tab === 'dice' && (
        <div className="pv-dice-tab">
          <DiceRoller onRoll={handleDiceRoll} lastResult={lastDiceResult ?? undefined} />
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
