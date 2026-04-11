import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getGameState, submitAction, getCampaign } from '../api/client'
import { GameWebSocket } from '../api/websocket'
import { GameChat, type ChatMessage } from '../components/GameChat'
import { DiceRoller } from '../components/DiceRoller'
import { InitiativeTracker, type CombatantDisplay } from '../components/InitiativeTracker'
import { DMAvatar } from '../components/DMAvatar'
import { AudioControls } from '../components/AudioControls'
import BattleMap from '../components/BattleMap'
import TokenLayer from '../components/TokenLayer'
import type { TokenInfo } from '../components/TokenLayer'
import FogOfWar from '../components/FogOfWar'
import type { GameState, GameMap, DiceResult } from '../types'
import './GameSession.css'

function formatTime(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  return h > 0
    ? `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
    : `${m}:${String(s).padStart(2, '0')}`
}

export function GameSession() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()

  const [gameState, setGameState] = useState<GameState | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [combatants, setCombatants] = useState<CombatantDisplay[]>([])
  const [lastDiceResult, setLastDiceResult] = useState<DiceResult | null>(null)
  const [mapData, _setMapData] = useState<GameMap | null>(null)
  const [avatarState, setAvatarState] = useState({ expression: 'neutral', isSpeaking: false, amplitude: 0 })
  const [audioState, setAudioState] = useState({ micOn: false, muted: false })
  const [selectedToken, setSelectedToken] = useState<string | null>(null)
  const [fogRevealed, setFogRevealed] = useState<Set<string>>(new Set())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [wsConnected, setWsConnected] = useState(false)
  const [campaignName, setCampaignName] = useState<string>('Game Session')
  const [waitingForDM, setWaitingForDM] = useState(false)
  const [sessionTime, setSessionTime] = useState(0)
  const [showKeyboardHelp, setShowKeyboardHelp] = useState(false)

  const wsRef = useRef<GameWebSocket | null>(null)

  // Session timer
  useEffect(() => {
    const timer = setInterval(() => setSessionTime(t => t + 1), 1000)
    return () => clearInterval(timer)
  }, [])

  // ? key toggles keyboard help
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return
      if (e.key === '?') setShowKeyboardHelp(v => !v)
      if (e.key === 'Escape') setShowKeyboardHelp(false)
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  // Derive token info from map tokens for the TokenLayer component
  const tokenInfos: TokenInfo[] = (mapData?.tokens || []).map((t) => ({
    entity_id: t.entity_id,
    name: t.entity_id,
    x: t.x,
    y: t.y,
    hp: 10,
    max_hp: 10,
    is_player: true,
  }))

  // Derive fog grid from map data for the FogOfWar component
  const fogGrid: string[][] = mapData
    ? mapData.terrain.map((row) => row.map((cell) => cell))
    : []

  const loadGameState = useCallback(async () => {
    if (!sessionId) return
    setLoading(true)
    setError(null)
    try {
      const state = await getGameState(sessionId)
      setGameState(state)
      setMessages([{ role: 'dm', text: state.current_scene || `Welcome to the adventure!`, timestamp: Date.now() }])
      // Fetch campaign name for the header
      if (state.campaign_id) {
        try {
          const campaign = await getCampaign(state.campaign_id)
          setCampaignName(campaign.name)
        } catch { /* fallback to default */ }
      }
      if (state.combat_state) {
        setCombatants(
          state.combat_state.initiative_order.map((id, idx) => ({
            id,
            name: id,
            initiative: state.combat_state!.initiative_order.length - idx,
            hp: 10,
            max_hp: 10,
            is_current: idx === state.combat_state!.current_turn_index,
          }))
        )
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load game state')
    } finally {
      setLoading(false)
    }
  }, [sessionId])

  useEffect(() => {
    loadGameState()

    if (!sessionId) return

    const ws = new GameWebSocket(sessionId)
    wsRef.current = ws

    const unsubMessage = ws.onMessage((msg) => {
      switch (msg.type) {
        case 'game_state':
          setGameState(msg.payload as GameState)
          break
        case 'turn_result': {
          const result = msg.payload as { narration?: string; narrative?: string; dice_results?: DiceResult[] }
          const text = result.narration || result.narrative || 'The DM ponders...'
          setMessages((prev) => [...prev, { role: 'dm', text, timestamp: Date.now() }])
          setAvatarState((prev) => ({ ...prev, expression: 'speaking', isSpeaking: true }))
          setTimeout(() => setAvatarState((prev) => ({ ...prev, isSpeaking: false, expression: 'neutral' })), 2000)
          if (result.dice_results?.length) {
            setLastDiceResult(result.dice_results[0])
          }
          break
        }
        case 'player_joined': {
          const data = msg.payload as { player_id: string }
          const shortId = data.player_id.split('-')[0]
          setMessages((prev) => [...prev, { role: 'dm', text: `A new adventurer (${shortId}) has joined the party!`, timestamp: Date.now() }])
          break
        }
        case 'player_left': {
          const data = msg.payload as { player_id: string }
          const shortId = data.player_id.split('-')[0]
          setMessages((prev) => [...prev, { role: 'dm', text: `Adventurer ${shortId} has departed.`, timestamp: Date.now() }])
          break
        }
        case 'error': {
          const data = msg.payload as { message: string }
          setMessages((prev) => [...prev, { role: 'dm', text: `Error: ${data.message}`, timestamp: Date.now() }])
          break
        }
      }
    })

    const unsubStatus = ws.onStatusChange(setWsConnected)
    ws.connect()

    return () => {
      unsubMessage()
      unsubStatus()
      ws.disconnect()
      wsRef.current = null
    }
  }, [sessionId, loadGameState])

  const handleSubmitAction = useCallback(async (action: string) => {
    if (!sessionId) return
    setMessages((prev) => [...prev, { role: 'player', text: action, timestamp: Date.now() }])
    setWaitingForDM(true)
    try {
      const result = await submitAction(sessionId, { type: 'interact', message: action })
      setMessages((prev) => [...prev, { role: 'dm', text: result.narration || 'The DM ponders...', timestamp: Date.now() }])
    } catch {
      setMessages((prev) => [...prev, { role: 'dm', text: 'Failed to send action. Try again.', timestamp: Date.now() }])
    } finally {
      setWaitingForDM(false)
    }
  }, [sessionId])

  const handleDiceRoll = useCallback((notation: string) => {
    if (wsRef.current) {
      wsRef.current.send({ type: 'dice_roll', notation })
    }
    // Local fallback for immediate feedback
    const match = notation.match(/(\d+)d(\d+)/)
    if (match) {
      const count = parseInt(match[1])
      const sides = parseInt(match[2])
      const rolls = Array.from({ length: count }, () => Math.floor(Math.random() * sides) + 1)
      const total = rolls.reduce((a, b) => a + b, 0)
      setLastDiceResult({
        notation,
        rolls,
        modifier: 0,
        total,
        is_critical: sides === 20 && rolls[0] === 20,
        is_fumble: sides === 20 && rolls[0] === 1,
      })
    }
  }, [])

  const handleCellClick = useCallback((x: number, y: number) => {
    if (selectedToken && wsRef.current) {
      wsRef.current.send({ type: 'token_move', entity_id: selectedToken, x, y })
    }
  }, [selectedToken])

  const handleMicToggle = useCallback(() => {
    setAudioState((prev) => ({ ...prev, micOn: !prev.micOn }))
  }, [])

  const handleMuteToggle = useCallback(() => {
    setAudioState((prev) => ({ ...prev, muted: !prev.muted }))
  }, [])

  const handleFogReveal = useCallback((x: number, y: number) => {
    const key = `${x},${y}`
    setFogRevealed((prev) => {
      const next = new Set(prev)
      next.add(key)
      return next
    })
    if (wsRef.current) {
      wsRef.current.send({ type: 'fog_update', x, y, revealed: true })
    }
  }, [])

  if (loading) {
    return (
      <div className="game-session">
        <div className="game-loading" data-testid="game-loading">
          <div className="loading-orb">
            <div className="orb-inner" />
          </div>
          <p className="loading-text">Preparing your adventure...</p>
          <p className="loading-subtext">The Dungeon Master is setting the stage</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="game-session">
        <div className="game-error" data-testid="game-error">
          <span className="error-icon">⚠️</span>
          <h2>Something went wrong</h2>
          <p className="error-detail">{error}</p>
          <button className="btn-retry" onClick={loadGameState}>Try Again</button>
        </div>
      </div>
    )
  }

  return (
    <div className="game-session">
      {/* Header */}
      <header className="game-header">
        <div className="game-header-left">
          <button className="btn-back" onClick={() => navigate('/')} title="Back to campaigns">
            ← 
          </button>
          <h1>{campaignName}</h1>
        </div>
        <div className="session-info">
          {gameState && <span className="phase-badge">{gameState.phase}</span>}
          <span className="session-timer" title="Session duration">⏱ {formatTime(sessionTime)}</span>
          <button className="btn-keyboard-help" onClick={() => setShowKeyboardHelp(v => !v)} title="Keyboard shortcuts (?)">
            ⌨
          </button>
          <div className="ws-status">
            <span className={`ws-dot ${wsConnected ? 'connected' : 'disconnected'}`} />
            <span>{wsConnected ? 'Connected' : 'Connecting...'}</span>
          </div>
        </div>
      </header>

      {/* Game body */}
      <div className="game-body">
        {/* Left sidebar */}
        <aside className="game-sidebar-left">
          <DMAvatar
            expression={avatarState.expression}
            isSpeaking={avatarState.isSpeaking}
            mouthAmplitude={avatarState.amplitude}
          />
          <AudioControls
            isMicOn={audioState.micOn}
            isMuted={audioState.muted}
            onMicToggle={handleMicToggle}
            onMuteToggle={handleMuteToggle}
          />
        </aside>

        {/* Main content */}
        <div className="game-main-content">
          {mapData && (
            <div className="map-area">
              <BattleMap
                map={mapData}
                selectedTokenId={selectedToken ?? undefined}
                onCellClick={handleCellClick}
              />
              <FogOfWar
                grid={fogGrid}
                revealed={fogRevealed}
                isDM={true}
                onReveal={handleFogReveal}
              />
              <TokenLayer
                tokens={tokenInfos}
                selectedTokenId={selectedToken ?? undefined}
                onSelect={setSelectedToken}
              />
            </div>
          )}
          <div className={`chat-area ${!mapData ? 'chat-area-full' : ''}`}>
            <GameChat messages={messages} onSubmitAction={handleSubmitAction} isWaitingForDM={waitingForDM} />
          </div>
        </div>

        {/* Right panel */}
        <aside className="game-sidebar-right">
          <InitiativeTracker combatants={combatants} />
          <DiceRoller onRoll={handleDiceRoll} lastResult={lastDiceResult ?? undefined} />
        </aside>
      </div>

      {/* Keyboard shortcuts overlay */}
      {showKeyboardHelp && (
        <div className="keyboard-help-overlay" onClick={() => setShowKeyboardHelp(false)}>
          <div className="keyboard-help-panel" onClick={e => e.stopPropagation()}>
            <h3>⌨ Keyboard Shortcuts</h3>
            <div className="shortcut-list">
              <div className="shortcut-item"><kbd>1</kbd>–<kbd>6</kbd> <span>Roll dice (d4–d20)</span></div>
              <div className="shortcut-item"><kbd>Enter</kbd> <span>Send message</span></div>
              <div className="shortcut-item"><kbd>Shift+Enter</kbd> <span>New line in chat</span></div>
              <div className="shortcut-item"><kbd>?</kbd> <span>Toggle this help</span></div>
              <div className="shortcut-item"><kbd>Esc</kbd> <span>Close overlay</span></div>
            </div>
            <button className="btn-close-help" onClick={() => setShowKeyboardHelp(false)}>Close</button>
          </div>
        </div>
      )}
    </div>
  )
}
