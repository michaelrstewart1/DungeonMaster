/** DM Display — full-screen TV view with AI DM avatar, battle map, narrative, and initiative tracker.
 * Designed for a TV at the head of the dining table.
 */
import { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { uuid } from '../utils/uuid';
import { useGameSocket } from '../hooks/useGameSocket';
import type { WSMessage } from '../api/websocket';
import { useWakeLock } from '../hooks/useWakeLock';
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
  const { connected, messages, connectionCount } = useGameSocket(sessionId);
  // The TV must never sleep mid-session.
  useWakeLock();

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
  const [streamingNarration, setStreamingNarration] = useState('');
  const [gameMap, setGameMap] = useState<GameMap | null>(null);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [liveCamera, setLiveCamera] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const cameraStreamRef = useRef<MediaStream | null>(null);
  const autoScanTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const narrativeRef = useRef<HTMLDivElement>(null);

  // Client-side lip sync: while the avatar is speaking, oscillate the mouth
  // amplitude locally (the server only reports the speaking window).
  const [mouthAmp, setMouthAmp] = useState(0);
  useEffect(() => {
    if (!avatar.is_speaking) {
      setMouthAmp(0);
      return;
    }
    const t = setInterval(() => setMouthAmp(0.25 + Math.random() * 0.75), 120);
    return () => clearInterval(t);
  }, [avatar.is_speaking]);

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

  // Process WebSocket messages — EVERY unseen one, in order (bursts like
  // combat_started + combat_update arrive within one render batch).
  const lastSeqRef = useRef(0);
  useEffect(() => {
    const unseen = messages.filter((m) => (m.seq ?? 0) > lastSeqRef.current);
    if (unseen.length === 0) return;
    lastSeqRef.current = unseen[unseen.length - 1].seq ?? lastSeqRef.current;
    unseen.forEach((m) => handleWsMessage(m));

    function handleWsMessage(last: WSMessage) {

    if (last.type === 'reconnected' as string) {
      // Resync after a drop — the TV must never sit stale on the wall while
      // the game moved on (turns taken, combat started/ended, new narration).
      if (sessionId) {
        fetch(`${API_BASE}/game/sessions/${sessionId}/state`)
          .then((r) => r.json())
          .then((data) => {
            setGameState(data);
            const history = Array.isArray(data.narrative_history) ? data.narrative_history : [];
            const lastDM = [...history].reverse().find((l: unknown) => String(l).startsWith('DM: '));
            if (lastDM) setCurrentNarration(String(lastDM).slice(4));
          })
          .catch(() => {});
      }
    }

    if (last.type === 'turn_result') {
      const p = last.payload as { narration?: string };
      const text = p.narration || '';
      setStreamingNarration('');
      setCurrentNarration(text);
      setNarrative((prev) => [
        ...prev.slice(-50),
        { id: uuid(), text, type: 'narration', timestamp: new Date().toISOString() },
      ]);
      // TTS: speak the narration aloud
      if (text) speakNarration(text);
    }

    if (last.type === 'game_state' as string) {
      setGameState(last.payload as GameState);
    }

    if (last.type === 'narration_chunk' as string) {
      // Live LLM token stream — the TV shows narration as it is written
      const p = last.payload as { chunk?: string };
      if (p.chunk) setStreamingNarration((prev) => prev + p.chunk);
    }

    if (last.type === 'scene_change' as string) {
      const p = last.payload as { location?: { name?: string; description?: string }; narration?: string; detected_scene?: string; current_location?: string }
      const text = p.narration || (p.location?.name ? `The party arrives at ${p.location.name}.` : '');
      if (text) {
        setStreamingNarration('');
        setCurrentNarration(text);
        setNarrative((prev) => [
          ...prev.slice(-50),
          { id: uuid(), text: `🧭 ${text}`, type: 'narration', timestamp: new Date().toISOString() },
        ]);
        speakNarration(text);
      }
      setGameState((prev) => prev ? {
        ...prev,
        current_location: p.current_location ?? prev.current_location,
        current_scene: p.location?.description ?? prev.current_scene,
        detected_scene: p.detected_scene ?? prev.detected_scene,
      } : prev);
    }

    if (last.type === 'combat_started' as string) {
      const p = last.payload as { combat_state?: GameState['combat_state'] };
      setGameState((prev) => prev ? { ...prev, phase: 'combat', combat_state: p.combat_state ?? prev.combat_state } : prev);
      const text = '⚔️ Roll for initiative!';
      setNarrative((prevN) => [
        ...prevN.slice(-50),
        { id: uuid(), text, type: 'narration', timestamp: new Date().toISOString() },
      ]);
    }

    if (last.type === 'combat_update' as string) {
      const p = last.payload as {
        events?: string[];
        narration?: string;
        combat_state?: GameState['combat_state'];
        phase?: string;
        combat_over?: boolean;
      };
      setGameState((prev) => prev ? {
        ...prev,
        phase: (p.phase as GameState['phase']) ?? prev.phase,
        combat_state: p.combat_state ?? (p.combat_over ? null : prev.combat_state),
      } : prev);
      const text = p.narration || (p.events || []).join(' ');
      if (text) {
        setCurrentNarration(text);
        setNarrative((prevN) => [
          ...prevN.slice(-50),
          { id: uuid(), text, type: 'narration', timestamp: new Date().toISOString() },
        ]);
        speakNarration(text);
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
    }
  }, [messages]);

  // Camera upload handler
  async function handleBoardUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !sessionId) return;
    await uploadBoardBlob(file);
    if (fileInputRef.current) fileInputRef.current.value = '';
  }

  async function uploadBoardBlob(blob: Blob) {
    if (!sessionId) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', blob, 'board.jpg');
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
    }
  }

  // Live board camera: getUserMedia preview + periodic auto-scan uploads
  async function startLiveCamera() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } },
      });
      cameraStreamRef.current = stream;
      setLiveCamera(true);
      // Attach after render
      setTimeout(() => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.play().catch(() => {});
        }
      }, 50);
      autoScanTimerRef.current = setInterval(captureFrame, 30000);
    } catch {
      // Camera permission denied or unavailable
    }
  }

  function stopLiveCamera() {
    if (autoScanTimerRef.current) clearInterval(autoScanTimerRef.current);
    autoScanTimerRef.current = null;
    cameraStreamRef.current?.getTracks().forEach((t) => t.stop());
    cameraStreamRef.current = null;
    setLiveCamera(false);
  }

  function captureFrame() {
    const video = videoRef.current;
    if (!video || video.videoWidth === 0) return;
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d')?.drawImage(video, 0, 0);
    canvas.toBlob((blob) => { if (blob) uploadBoardBlob(blob); }, 'image/jpeg', 0.85);
  }

  useEffect(() => () => stopLiveCamera(), []); // eslint-disable-line react-hooks/exhaustive-deps

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

  // DM face expressions (must cover every backend Expression value)
  const faceExpressions: Record<string, string> = {
    neutral: '🧙',
    happy: '😊',
    angry: '😠',
    sad: '😢',
    surprised: '😲',
    thinking: '🤔',
    menacing: '😈',
    excited: '🤩',
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
            transform: `translate(${(typeof avatar.gaze === 'object' ? avatar.gaze.x : 0) * 5}px, ${(typeof avatar.gaze === 'object' ? avatar.gaze.y : 0) * 5}px)`,
          }}>
            {faceEmoji}
          </span>
          {avatar.is_speaking && (
            <div className="dm-speaking-indicator">
              <span className="dm-speak-bar" style={{ height: `${20 + mouthAmp * 30}px` }} />
              <span className="dm-speak-bar" style={{ height: `${10 + mouthAmp * 50}px` }} />
              <span className="dm-speak-bar" style={{ height: `${15 + mouthAmp * 40}px` }} />
              <span className="dm-speak-bar" style={{ height: `${10 + mouthAmp * 50}px` }} />
              <span className="dm-speak-bar" style={{ height: `${20 + mouthAmp * 30}px` }} />
            </div>
          )}
        </div>
        <div className="dm-title">Dungeon Master</div>
      </div>

      {/* Current Narration — large display text (streams live while the DM writes) */}
      <div className="dm-narration-section">
        <div className="dm-narration-text">
          {streamingNarration ? (
            <>
              {streamingNarration}
              <span className="stream-cursor" />
            </>
          ) : (
            currentNarration || 'The adventure begins...'
          )}
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
            <button
              className="dm-camera-btn"
              onClick={() => (liveCamera ? stopLiveCamera() : startLiveCamera())}
              title={liveCamera ? 'Stop live board camera' : 'Start live board camera (auto-scans every 30s)'}
            >
              {liveCamera ? '🔴 Stop Camera' : '🎥 Live Camera'}
            </button>
            {liveCamera && (
              <button className="dm-camera-btn" onClick={captureFrame} disabled={uploading} title="Scan the board now">
                ⚡ Scan Now
              </button>
            )}
          </div>
          {liveCamera && (
            <div className="dm-live-camera">
              <video ref={videoRef} muted playsInline className="dm-camera-preview" />
            </div>
          )}
        </div>

        {/* Initiative / Turn Order (combat) or Player list (non-combat) */}
        <div className="dm-sidebar">
          {isCombat && combatState ? (
            <div className="dm-initiative">
              <h3>⚔️ Initiative</h3>
              <div className="dm-init-list">
                {combatState.initiative_order.map((name, i) => {
                  const cb = combatState.combatants?.find((c) => c.name === name);
                  const cbPct = cb ? Math.max(0, Math.round((cb.hp / (cb.max_hp || 1)) * 100)) : null;
                  const down = cb ? cb.hp <= 0 : false;
                  return (
                    <div
                      key={`${name}-${i}`}
                      className={`dm-init-entry ${i === combatState.current_turn_index ? 'dm-init-active' : ''} ${down ? 'dm-init-down' : ''}`}
                    >
                      <span className="dm-init-order">{i + 1}</span>
                      <span className="dm-init-name">
                        {name}
                        {cb && cbPct !== null && (
                          <span className="dm-init-hp-bar">
                            <span
                              className="dm-init-hp-fill"
                              style={{
                                width: `${cbPct}%`,
                                background: cbPct > 50 ? '#4caf50' : cbPct > 25 ? '#ff9800' : '#f44336',
                              }}
                            />
                          </span>
                        )}
                      </span>
                      {cb && <span className="dm-init-hp-num">{down ? '💀' : `${cb.hp}/${cb.max_hp}`}</span>}
                      {i === combatState.current_turn_index && <span className="dm-init-arrow">◄</span>}
                    </div>
                  );
                })}
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
