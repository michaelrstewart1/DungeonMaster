import { useState, useEffect } from 'react'
import type { Character } from '../types'

interface SpellSlotTrackerProps {
  character: Character
  onClose?: () => void
}

// Spell slots per level for full casters (Wizard, Cleric, Druid, etc.)
const SPELL_SLOTS: Record<number, number> = {
  1: 2, 2: 2, 3: 2, 4: 3, 5: 3, 6: 3, 7: 4, 8: 4, 9: 4,
}

// Cantrips known per caster class/level - adjust as needed
const CANTRIPS_KNOWN = 3

export function SpellSlotTracker({ character, onClose }: SpellSlotTrackerProps) {
  const [spellSlots, setSpellSlots] = useState<Record<number, number>>({})
  const [spentSlots, setSpentSlots] = useState<Record<number, number>>({})
  const [cantripsSpent, setCantripsSpent] = useState(0)

  // Initialize spell slots based on character level
  useEffect(() => {
    const charLevel = character.level || 1
    const slots: Record<number, number> = {}

    // Determine caster level (same as char level for most casters)
    const casterLevel = Math.min(charLevel, 20)

    // Fill available slots based on level
    for (let level = 1; level <= 9; level++) {
      if (casterLevel >= level * 2 - 1) {
        // Character must be high enough level to have this spell slot
        slots[level] = SPELL_SLOTS[level]
      }
    }

    setSpellSlots(slots)
    setSpentSlots({})
    setCantripsSpent(0)
  }, [character.level])

  const toggleSpellSlot = (level: number) => {
    setSpentSlots(prev => {
      const current = prev[level] || 0
      const available = spellSlots[level] || 0
      const newSpent = current < available ? current + 1 : 0
      return { ...prev, [level]: newSpent }
    })
  }

  const toggleCantrip = () => {
    setCantripsSpent(prev => (prev < CANTRIPS_KNOWN ? prev + 1 : 0))
  }

  const resetAll = () => {
    setSpentSlots({})
    setCantripsSpent(0)
  }

  const totalSlotsAvailable = Object.values(spellSlots).reduce((a, b) => a + b, 0)
  const totalSlotsSpent = Object.values(spentSlots).reduce((a, b) => a + b, 0)

  // Only show tracker for spellcasting classes
  const isCaster = ['wizard', 'cleric', 'druid', 'sorcerer', 'bard', 'warlock'].includes(
    character.class_name?.toLowerCase() || ''
  )

  if (!isCaster || totalSlotsAvailable === 0) {
    return (
      <div className="spell-slot-tracker not-a-caster">
        <p className="spell-slot-placeholder">Not a spellcaster</p>
      </div>
    )
  }

  return (
    <div className="spell-slot-tracker">
      <div className="spell-slot-header">
        <h3 className="spell-slot-title">✨ Spell Slots</h3>
        <div className="spell-slot-level">Level {character.level || 1}</div>
      </div>

      <div className="spell-slot-content">
        {/* Cantrips Section */}
        <div className="spell-slot-section cantrips-section">
          <div className="spell-slot-section-label">Cantrips</div>
          <div className="spell-slot-row">
            {[...Array(CANTRIPS_KNOWN)].map((_, i) => (
              <button
                key={`cantrip-${i}`}
                onClick={toggleCantrip}
                className={`spell-slot-cantrip ${i < cantripsSpent ? 'spent' : 'available'}`}
                title={`Cantrip ${i + 1}`}
              >
                ✦
              </button>
            ))}
          </div>
          <div className="spell-slot-count">{cantripsSpent} / {CANTRIPS_KNOWN}</div>
        </div>

        {/* Spell Levels 1-9 */}
        <div className="spell-slot-levels">
          {[1, 2, 3, 4, 5, 6, 7, 8, 9].map(level => {
            const available = spellSlots[level] || 0
            const spent = spentSlots[level] || 0

            if (available === 0) return null

            return (
              <div key={`level-${level}`} className="spell-slot-level-row">
                <div className="spell-slot-level-label">Level {level}</div>
                <div className="spell-slot-row">
                  {[...Array(available)].map((_, i) => (
                    <button
                      key={`slot-${level}-${i}`}
                      onClick={() => toggleSpellSlot(level)}
                      className={`spell-slot-diamond ${i < spent ? 'spent' : 'available'}`}
                      title={`Level ${level} spell slot ${i + 1}`}
                    >
                      ◆
                    </button>
                  ))}
                </div>
                <div className="spell-slot-count">{spent} / {available}</div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Summary */}
      <div className="spell-slot-summary">
        <div className="spell-slot-summary-item">
          <span>Total Slots Used:</span>
          <span className="spell-slot-summary-value">{totalSlotsSpent} / {totalSlotsAvailable}</span>
        </div>
      </div>

      {/* Controls */}
      <div className="spell-slot-controls">
        <button onClick={resetAll} className="spell-slot-reset-btn" title="Reset all slots">
          ↻ Reset All
        </button>
      </div>

      {onClose && (
        <button onClick={onClose} className="spell-slot-close" title="Close tracker">
          ✕
        </button>
      )}
    </div>
  )
}
