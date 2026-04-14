import { useState, useEffect, useCallback, useRef } from 'react'
import type { DiceResult } from '../types'

const DICE_TYPES = ['d4', 'd6', 'd8', 'd10', 'd12', 'd20', 'd100'] as const
type DieType = typeof DICE_TYPES[number]

const DICE_CONFIG: Record<DieType, { color: string; symbol: string; label: string }> = {
  d4:   { color: '#c0392b', symbol: '▲', label: 'd4' },
  d6:   { color: '#ecf0f1', symbol: '⬡', label: 'd6' },
  d8:   { color: '#2980b9', symbol: '◆', label: 'd8' },
  d10:  { color: '#27ae60', symbol: '◈', label: 'd10' },
  d12:  { color: '#8e44ad', symbol: '⬠', label: 'd12' },
  d20:  { color: '#d4a846', symbol: '✦', label: 'd20' },
  d100: { color: '#16a085', symbol: '%%', label: 'd100' },
}

const KEY_MAP: Record<string, DieType> = {
  '1': 'd4', '2': 'd6', '3': 'd8', '4': 'd10', '5': 'd12', '6': 'd20', '7': 'd100'
}

/** Random rotation values for the tumble animation */
function randomRotation(): string {
  const rx = Math.floor(Math.random() * 720) + 720
  const ry = Math.floor(Math.random() * 720) + 720
  const rz = Math.floor(Math.random() * 360)
  return `rotateX(${rx}deg) rotateY(${ry}deg) rotateZ(${rz}deg)`
}

/** Final rotation to "land" on a face showing the result number */
function settleRotation(faceIndex: number): string {
  const faces: string[] = [
    'rotateX(0deg) rotateY(0deg)',       // front
    'rotateX(0deg) rotateY(180deg)',     // back
    'rotateX(0deg) rotateY(-90deg)',     // left
    'rotateX(0deg) rotateY(90deg)',      // right
    'rotateX(-90deg) rotateY(0deg)',     // top
    'rotateX(90deg) rotateY(0deg)',      // bottom
  ]
  return faces[faceIndex % 6]
}

interface DiceRollerProps {
  onRoll: (notation: string) => void
  lastResult?: DiceResult
}

export function DiceRoller({ onRoll, lastResult }: DiceRollerProps) {
  const [rolling, setRolling] = useState(false)
  const [activeDie, setActiveDie] = useState<DieType>('d20')
  const [modifier, setModifier] = useState(0)
  const [showResult, setShowResult] = useState(false)
  const [rollHistory, setRollHistory] = useState<DiceResult[]>([])
  const [tumbleStyle, setTumbleStyle] = useState<React.CSSProperties>({})
  const [settleStyle, setSettleStyle] = useState<React.CSSProperties>({})
  const [animPhase, setAnimPhase] = useState<'idle' | 'tumble' | 'settle'>('idle')
  const rollTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const settleTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const resultTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (lastResult) {
      setRollHistory(prev => [lastResult, ...prev].slice(0, 5))
      // If result arrives while not rolling (e.g., prop passed directly), show immediately
      if (!rolling) {
        setShowResult(true)
      }
    }
  }, [lastResult]) // eslint-disable-line react-hooks/exhaustive-deps

  // Cleanup timers
  useEffect(() => {
    return () => {
      if (rollTimerRef.current) clearTimeout(rollTimerRef.current)
      if (settleTimerRef.current) clearTimeout(settleTimerRef.current)
      if (resultTimerRef.current) clearTimeout(resultTimerRef.current)
    }
  }, [])

  const handleRoll = useCallback((die: DieType) => {
    if (rolling) return
    setRolling(true)
    setActiveDie(die)
    setShowResult(false)
    setAnimPhase('tumble')

    // Set tumble rotation
    setTumbleStyle({
      transform: randomRotation(),
      transition: 'transform 1.2s cubic-bezier(0.2, 0.8, 0.3, 1)',
    })

    // Fire the roll
    const mod = modifier !== 0 ? `${modifier > 0 ? '+' : ''}${modifier}` : ''
    if (die === 'd100') {
      onRoll(`1d100${mod}`)
    } else {
      onRoll(`1${die}${mod}`)
    }

    // Settle phase
    rollTimerRef.current = setTimeout(() => {
      setAnimPhase('settle')
      const face = Math.floor(Math.random() * 6)
      setSettleStyle({
        transform: settleRotation(face),
        transition: 'transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)',
      })
    }, 1200)

    // Show result
    settleTimerRef.current = setTimeout(() => {
      setAnimPhase('idle')
      setShowResult(true)
      setRolling(false)
    }, 1700)
  }, [onRoll, rolling, modifier])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return
      const die = KEY_MAP[e.key]
      if (die) handleRoll(die)
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [handleRoll])

  const isCrit = lastResult?.is_critical ?? false
  const isFumble = lastResult?.is_fumble ?? false
  const dieColor = DICE_CONFIG[activeDie].color

  const cubeInlineStyle = animPhase === 'tumble' ? tumbleStyle
    : animPhase === 'settle' ? settleStyle
    : {}

  // Build face labels for the 3D cube
  const resultNum = lastResult?.total ?? 0
  const faceLabels = [
    String(resultNum),
    String(Math.max(1, resultNum - 1)),
    String(Math.max(1, resultNum + 2)),
    String(Math.max(1, resultNum - 3)),
    String(Math.max(1, resultNum + 1)),
    String(Math.max(1, resultNum - 2)),
  ]

  return (
    <div className="dice-roller">
      <h3 className="dice-roller-title">⚔ Dice Roller</h3>

      {/* Dice Selection */}
      <div className="dice-buttons">
        {DICE_TYPES.map((die, idx) => (
          <button
            key={die}
            onClick={() => handleRoll(die)}
            className={`dice-btn ${activeDie === die && !rolling ? 'dice-btn-selected' : ''} ${rolling && activeDie === die ? 'dice-btn-pressed' : ''}`}
            aria-label={die}
            title={`Roll ${die} (press ${idx + 1})`}
            disabled={rolling}
          >
            <span className="dice-btn-symbol" style={{ color: DICE_CONFIG[die].color }}>
              {DICE_CONFIG[die].symbol}
            </span>
            <span className="dice-label">{DICE_CONFIG[die].label}</span>
          </button>
        ))}
      </div>

      {/* Modifier */}
      <div className="dice-modifier">
        <button
          className="dice-mod-btn"
          onClick={() => setModifier(m => Math.max(-10, m - 1))}
          disabled={rolling}
          aria-label="Decrease modifier"
        >−</button>
        <span className="dice-mod-value">
          {modifier >= 0 ? `+${modifier}` : modifier}
        </span>
        <button
          className="dice-mod-btn"
          onClick={() => setModifier(m => Math.min(10, m + 1))}
          disabled={rolling}
          aria-label="Increase modifier"
        >+</button>
      </div>

      {/* 3D Dice Stage */}
      <div className={`dice-stage ${rolling ? 'dice-stage-active' : ''}`}>
        {activeDie === 'd100' ? (
          <div className="dice-d100-pair">
            {[0, 1].map(i => (
              <div key={i} className="dice-3d-wrapper dice-3d-small">
                <div
                  className={`dice-3d ${animPhase === 'tumble' ? 'dice-tumbling' : ''}`}
                  style={{
                    ...cubeInlineStyle,
                    '--die-color': DICE_CONFIG.d100.color,
                  } as React.CSSProperties}
                >
                  {faceLabels.map((label, fi) => (
                    <div key={fi} className={`dice-face dice-face-${fi}`}>
                      {i === 0 ? label : String(Math.max(0, (Number(label) % 10)))}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="dice-3d-wrapper">
            <div
              className={`dice-3d ${animPhase === 'tumble' ? 'dice-tumbling' : ''}`}
              style={{
                ...cubeInlineStyle,
                '--die-color': dieColor,
              } as React.CSSProperties}
            >
              {faceLabels.map((label, fi) => (
                <div key={fi} className={`dice-face dice-face-${fi}`}>
                  {label}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Crit / Fumble overlays */}
        {showResult && isCrit && (
          <div className="dice-nat20-explosion">
            <span className="dice-nat20-text">NAT 20!</span>
            <div className="dice-nat20-burst" />
          </div>
        )}
        {showResult && isFumble && (
          <div className="dice-nat1-effect">
            <span className="dice-nat1-text">💀 CRITICAL FAIL!</span>
          </div>
        )}
      </div>

      {/* Result */}
      {showResult && lastResult && (
        <div className={`dice-result-epic ${isCrit ? 'dice-result-crit' : ''} ${isFumble ? 'dice-result-fumble' : ''}`}>
          <span className="dice-result-total">{lastResult.total}</span>
          <span className="dice-result-detail">
            {lastResult.notation} → [{lastResult.rolls.join(', ')}]
            {lastResult.modifier !== 0 && ` ${lastResult.modifier > 0 ? '+' : ''}${lastResult.modifier}`}
          </span>
          {isCrit && <span className="dice-badge critical">⚡ Critical Hit!</span>}
          {isFumble && <span className="dice-badge fumble">💀 Fumble!</span>}
        </div>
      )}

      {/* Roll History */}
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
