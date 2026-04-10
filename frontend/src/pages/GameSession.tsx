import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { GameChat, type ChatMessage } from '../components/GameChat'
import { DiceRoller } from '../components/DiceRoller'
import { InitiativeTracker, type CombatantDisplay } from '../components/InitiativeTracker'
import type { DiceResult } from '../types'

export function GameSession() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: 'dm', text: `Welcome to the adventure! Session: ${sessionId}` },
  ])
  const [combatants] = useState<CombatantDisplay[]>([])
  const [lastRoll, setLastRoll] = useState<DiceResult | undefined>()
  const [isProcessing, setIsProcessing] = useState(false)

  const handleAction = async (action: string) => {
    setMessages((prev) => [...prev, { role: 'player', text: action }])
    setIsProcessing(true)

    try {
      const res = await fetch(`/api/game/sessions/${sessionId}/action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: 'interact', message: action }),
      })
      if (res.ok) {
        const result = await res.json()
        setMessages((prev) => [...prev, { role: 'dm', text: result.narration || 'The DM ponders...' }])
      }
    } catch {
      setMessages((prev) => [...prev, { role: 'dm', text: 'Connection lost...' }])
    } finally {
      setIsProcessing(false)
    }
  }

  const handleRoll = (notation: string) => {
    // Simple local dice roll for UI feedback
    const match = notation.match(/(\d+)d(\d+)/)
    if (match) {
      const count = parseInt(match[1])
      const sides = parseInt(match[2])
      const rolls = Array.from({ length: count }, () => Math.floor(Math.random() * sides) + 1)
      const total = rolls.reduce((a, b) => a + b, 0)
      setLastRoll({
        notation,
        rolls,
        modifier: 0,
        total,
        is_critical: sides === 20 && rolls[0] === 20,
        is_fumble: sides === 20 && rolls[0] === 1,
      })
    }
  }

  return (
    <div className="page-game-session">
      <h1>Game Session</h1>

      <div className="game-layout">
        <aside className="game-sidebar">
          <InitiativeTracker combatants={combatants} />
          <DiceRoller onRoll={handleRoll} lastResult={lastRoll} />
        </aside>

        <main className="game-main">
          <GameChat messages={messages} onSubmitAction={handleAction} disabled={isProcessing} />
        </main>
      </div>
    </div>
  )
}
