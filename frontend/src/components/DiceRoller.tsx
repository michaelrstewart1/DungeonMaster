import { useState, useEffect, useCallback } from 'react'
import type { DiceResult } from '../types'

const DICE_TYPES = ['d4', 'd6', 'd8', 'd10', 'd12', 'd20'] as const

const DICE_EMOJI: Record<string, string> = {
  d4: '🔺', d6: '🎲', d8: '💎', d10: '🔷', d12: '⬡', d20: '🎯'
}

// Keys 1-6 map to dice types
const KEY_MAP: Record<string, string> = {
  '1': 'd4', '2': 'd6', '3': 'd8', '4': 'd10', '5': 'd12', '6': 'd20'
}

interface DiceRollerProps {
  onRoll: (notation: string) => void
  lastResult?: DiceResult
}

export function DiceRoller({ onRoll, lastResult }: DiceRollerProps) {
  const [rolling, setRolling] = useState(false)
  const [activeDie, setActiveDie] = useState<string | null>(null)
  const [rollHistory, setRollHistory] = useState<DiceResult[]>([])

  // Track history of rolls
  useEffect(() => {
    if (lastResult) {
      setRollHistory(prev => [lastResult, ...prev].slice(0, 5))
    }
  }, [lastResult])

  const handleRoll = useCallback((die: string) => {
    setRolling(true)
    setActiveDie(die)
    onRoll(`1${die}`)
    setTimeout(() => setRolling(false), 600)
  }, [onRoll])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger if user is typing in an input/textarea
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return
      const die = KEY_MAP[e.key]
      if (die) handleRoll(die)
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [handleRoll])

  return (
    <div className="dice-roller">
      <h3 className="dice-roller-title">Dice</h3>
      <div className="dice-buttons">
        {DICE_TYPES.map((die, idx) => (
          <button
            key={die}
            onClick={() => handleRoll(die)}
            className={`dice-btn ${rolling && activeDie === die ? 'dice-rolling' : ''}`}
            aria-label={die}
            title={`Roll ${die} (press ${idx + 1})`}
          >
            <span className="dice-emoji">{DICE_EMOJI[die]}</span>
            <span className="dice-label">{die}</span>
          </button>
        ))}
      </div>

      {lastResult && (
        <div className={`dice-result ${lastResult.is_critical ? 'critical' : ''} ${lastResult.is_fumble ? 'fumble' : ''} ${rolling ? 'result-animating' : ''}`}>
          <span className="dice-total">{lastResult.total}</span>
          <span className="dice-detail">
            {lastResult.notation} → [{lastResult.rolls.join(', ')}]
            {lastResult.modifier !== 0 && ` ${lastResult.modifier > 0 ? '+' : ''}${lastResult.modifier}`}
          </span>
          {lastResult.is_critical && <span className="dice-badge critical">⚡ Critical Hit!</span>}
          {lastResult.is_fumble && <span className="dice-badge fumble">💀 Fumble!</span>}
        </div>
      )}

      {rollHistory.length > 1 && (
        <div className="dice-history">
          <span className="dice-history-label">Recent</span>
          {rollHistory.slice(1).map((r, i) => (
            <span key={i} className={`dice-history-item ${r.is_critical ? 'critical' : ''} ${r.is_fumble ? 'fumble' : ''}`}>
              {r.notation}: {r.total}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
