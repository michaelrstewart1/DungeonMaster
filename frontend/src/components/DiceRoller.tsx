import type { DiceResult } from '../types'

const DICE_TYPES = ['d4', 'd6', 'd8', 'd10', 'd12', 'd20'] as const

interface DiceRollerProps {
  onRoll: (notation: string) => void
  lastResult?: DiceResult
}

export function DiceRoller({ onRoll, lastResult }: DiceRollerProps) {
  return (
    <div className="dice-roller">
      <div className="dice-buttons">
        {DICE_TYPES.map((die) => (
          <button
            key={die}
            onClick={() => onRoll(`1${die}`)}
            className="dice-btn"
            aria-label={die}
          >
            {die}
          </button>
        ))}
      </div>

      {lastResult && (
        <div className={`dice-result ${lastResult.is_critical ? 'critical' : ''} ${lastResult.is_fumble ? 'fumble' : ''}`}>
          <span className="dice-total">{lastResult.total}</span>
          <span className="dice-detail">
            {lastResult.notation} → [{lastResult.rolls.join(', ')}]
            {lastResult.modifier !== 0 && ` ${lastResult.modifier > 0 ? '+' : ''}${lastResult.modifier}`}
          </span>
          {lastResult.is_critical && <span className="dice-badge critical">Critical Hit!</span>}
          {lastResult.is_fumble && <span className="dice-badge fumble">Fumble!</span>}
        </div>
      )}
    </div>
  )
}
