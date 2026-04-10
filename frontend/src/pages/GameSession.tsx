import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { getGameState, submitAction } from '../api/client'
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

export function GameSession() {
  const { sessionId } = useParams<{ sessionId: string }>()

  const [gameState, setGameState] = useState<GameState | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [combatants, setCombatants] = useState<CombatantDisplay[]>([])
  const [lastDiceResult, setLastDiceResult] = useState<DiceResult | null>(null)
  const [mapData, setMapData] = useState<GameMap | null>(null)
  const [avatarState, setAvatarState] = useState({ expression: 'neutral', isSpeaking: false, amplitude: 0 })
  const [audioState, setAudioState] = useState({ micOn: false, muted: false })
  const [selectedToken, setSelectedToken] = useState<string | null>(null)
  const [fogRevealed, setFogRevealed] = useState<Set<string>>(new Set())
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [wsConnected, setWsConnected] = useState(false)

  const wsRef = useRef<GameWebSocket | null>(null)

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
      setMessages([{ role: 'dm', text: state.current_scene || `Welcome to the adventure!` }])
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
          setMessages((prev) => [...prev, { role: 'dm', text }])
          setAvatarState((prev) => ({ ...prev, expression: 'speaking', isSpeaking: true }))
          setTimeout(() => setAvatarState((prev) => ({ ...prev, isSpeaking: false, expression: 'neutral' })), 2000)
          if (result.dice_results?.length) {
            setLastDiceResult(result.dice_results[0])
          }
          break
        }
        case 'player_joined': {
          const data = msg.payload as { player_id: string }
          setMessages((prev) => [...prev, { role: 'dm', text: `${data.player_id} joined the session` }])
          break
        }
        case 'player_left': {
          const data = msg.payload as { player_id: string }
          setMessages((prev) => [...prev, { role: 'dm', text: `${data.player_id} left the session` }])
          break
        }
        case 'error': {
          const data = msg.payload as { message: string }
          setMessages((prev) => [...prev, { role: 'dm', text: `Error: ${data.message}` }])
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
    setMessages((prev) => [...prev, { role: 'player', text: action }])
    try {
      const result = await submitAction(sessionId, { type: 'interact', message: action })
      setMessages((prev) => [...prev, { role: 'dm', text: result.narration || 'The DM ponders...' }])
    } catch {
      setMessages((prev) => [...prev, { role: 'dm', text: 'Failed to send action. Try again.' }])
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
      <div className="game-loading" data-testid="game-loading">
        <p>Loading game...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="game-error" data-testid="game-error">
        <p>{error}</p>
        <button onClick={loadGameState}>Retry</button>
      </div>
    )
  }

  return (
    <div className="game-session">
      {/* Header */}
      <header className="game-header">
        <h1>Game Session</h1>
        <div className="session-info">
          {gameState && <span className="phase-badge">{gameState.phase}</span>}
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
          <div className="map-area">
            {mapData ? (
              <>
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
              </>
            ) : (
              <div className="map-placeholder">No map loaded</div>
            )}
            <TokenLayer
              tokens={tokenInfos}
              selectedTokenId={selectedToken ?? undefined}
              onSelect={setSelectedToken}
            />
          </div>
          <div className="chat-area">
            <GameChat messages={messages} onSubmitAction={handleSubmitAction} />
          </div>
        </div>

        {/* Right panel */}
        <aside className="game-sidebar-right">
          <InitiativeTracker combatants={combatants} />
          <DiceRoller onRoll={handleDiceRoll} lastResult={lastDiceResult ?? undefined} />
        </aside>
      </div>
    </div>
  )
}
