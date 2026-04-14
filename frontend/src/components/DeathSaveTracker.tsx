import { useState, useEffect } from 'react'

interface DeathSaveTrackerProps {
  characterName: string
  onClose?: () => void
}

export function DeathSaveTracker({ characterName, onClose }: DeathSaveTrackerProps) {
  const [successes, setSuccesses] = useState(0)
  const [failures, setFailures] = useState(0)
  const [lastAction, setLastAction] = useState<'success' | 'failure' | null>(null)
  const [animatingIndex, setAnimatingIndex] = useState<number | null>(null)

  // Track animating icon
  useEffect(() => {
    if (animatingIndex !== null) {
      const timer = setTimeout(() => setAnimatingIndex(null), 600)
      return () => clearTimeout(timer)
    }
  }, [animatingIndex])

  const handleSuccess = () => {
    if (successes < 3) {
      setSuccesses(prev => prev + 1)
      setLastAction('success')
      setAnimatingIndex(successes)
    }
  }

  const handleFailure = () => {
    if (failures < 3) {
      setFailures(prev => prev + 1)
      setLastAction('failure')
      setAnimatingIndex(failures)
    }
  }

  const handleReset = () => {
    setSuccesses(0)
    setFailures(0)
    setLastAction(null)
    setAnimatingIndex(null)
  }

  const isComplete = successes >= 3 || failures >= 3
  const outcome = successes >= 3 ? 'stabilized' : failures >= 3 ? 'deceased' : null

  return (
    <div className="death-save-tracker">
      <div className="death-save-header">
        <h3 className="death-save-title">⚰️ Death Saves</h3>
        <p className="death-save-character">{characterName}</p>
      </div>

      <div className="death-save-content">
        {/* Successes */}
        <div className="death-save-track success-track">
          <div className="death-save-label">Successes</div>
          <div className="death-save-icons">
            {[0, 1, 2].map(i => (
              <div
                key={`success-${i}`}
                className={`death-save-icon heart ${
                  i < successes ? 'filled' : 'empty'
                } ${animatingIndex === i && lastAction === 'success' ? 'animate-in' : ''}`}
              >
                ❤️
              </div>
            ))}
          </div>
        </div>

        {/* Failures */}
        <div className="death-save-track failure-track">
          <div className="death-save-label">Failures</div>
          <div className="death-save-icons">
            {[0, 1, 2].map(i => (
              <div
                key={`failure-${i}`}
                className={`death-save-icon skull ${
                  i < failures ? 'filled' : 'empty'
                } ${animatingIndex === i && lastAction === 'failure' ? 'animate-in' : ''}`}
              >
                ☠️
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Status Message */}
      {isComplete && outcome && (
        <div className={`death-save-outcome ${outcome}`}>
          <p className="death-save-outcome-text">
            {outcome === 'stabilized'
              ? '✨ Character Stabilized!'
              : '💀 Character Defeated...'}
          </p>
        </div>
      )}

      {/* Controls */}
      <div className="death-save-controls">
        <button
          onClick={handleSuccess}
          disabled={isComplete || successes >= 3}
          className="death-save-btn success-btn"
          title="Add success"
        >
          ✓ Success
        </button>
        <button
          onClick={handleFailure}
          disabled={isComplete || failures >= 3}
          className="death-save-btn failure-btn"
          title="Add failure"
        >
          ✗ Failure
        </button>
        <button
          onClick={handleReset}
          className="death-save-btn reset-btn"
          title="Reset tracker"
        >
          ↻ Reset
        </button>
      </div>

      {onClose && (
        <button onClick={onClose} className="death-save-close" title="Close tracker">
          ✕
        </button>
      )}
    </div>
  )
}
