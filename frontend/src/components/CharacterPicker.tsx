import { useState } from 'react'
import { PRE_MADE_CHARACTERS, CLASS_COLORS } from '../data/premadeCharacters'
import type { CharacterCreate } from '../types'
import { CharacterPortrait } from './CharacterPortrait'

interface CharacterPickerProps {
  onSelect: (character: CharacterCreate) => void
  onCancel: () => void
}

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1).replace(/-/g, ' ')
}

function abilityMod(score: number): string {
  const mod = Math.floor((score - 10) / 2)
  return mod >= 0 ? `+${mod}` : `${mod}`
}

export function CharacterPicker({ onSelect, onCancel }: CharacterPickerProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const selected = PRE_MADE_CHARACTERS.find((c) => c.id === selectedId) || null

  const handleConfirm = () => {
    if (!selected) return
    const { id: _id, portrait: _p, backstory: _b, equipment: _e, ...charData } = selected
    onSelect(charData)
  }

  return (
    <div className="character-picker" data-testid="character-picker">
      <h2>Choose Your Hero</h2>
      <p className="picker-subtitle">Select a pre-made character to join your adventure</p>

      <div className="picker-grid stagger-children">
        {PRE_MADE_CHARACTERS.map((char) => {
          const colors = CLASS_COLORS[char.class_name]
          return (
            <button
              key={char.id}
              className={`picker-card animate-in ${selectedId === char.id ? 'selected' : ''}`}
              onClick={() => setSelectedId(char.id)}
              data-testid={`picker-card-${char.id}`}
              style={{
                '--card-accent': colors.primary,
                '--card-glow': colors.accent,
              } as React.CSSProperties}
            >
              <CharacterPortrait
                race={char.race}
                className={char.class_name}
                portrait={char.portrait}
                size="md"
                selected={selectedId === char.id}
              />
              <div className="picker-card-info">
                <span className="picker-card-name">{char.name}</span>
                <span className="picker-card-class">
                  {capitalize(char.race)} {capitalize(char.class_name)}
                </span>
              </div>
            </button>
          )
        })}
      </div>

      {selected && (
        <div className="picker-detail" data-testid="picker-detail">
          <div className="picker-detail-header">
            <CharacterPortrait
              race={selected.race}
              className={selected.class_name}
              portrait={selected.portrait}
              size="lg"
              selected
            />
            <div className="picker-detail-title">
              <h3>{selected.name}</h3>
              <p className="picker-detail-subtitle">
                Level {selected.level} {capitalize(selected.race)} {capitalize(selected.class_name)}
              </p>
              <p className="picker-detail-backstory">{selected.backstory}</p>
            </div>
          </div>

          <div className="picker-detail-stats">
            <div className="picker-stat-group">
              <h4>Combat</h4>
              <div className="picker-stats-row">
                <div className="picker-stat">
                  <span className="picker-stat-label">HP</span>
                  <span className="picker-stat-value">{selected.hp}</span>
                </div>
                <div className="picker-stat">
                  <span className="picker-stat-label">AC</span>
                  <span className="picker-stat-value">{selected.ac}</span>
                </div>
              </div>
            </div>

            <div className="picker-stat-group">
              <h4>Abilities</h4>
              <div className="picker-stats-row">
                {(['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma'] as const).map(
                  (ability) => (
                    <div key={ability} className="picker-stat">
                      <span className="picker-stat-label">{ability.slice(0, 3).toUpperCase()}</span>
                      <span className="picker-stat-value">{selected[ability]}</span>
                      <span className="picker-stat-mod">{abilityMod(selected[ability])}</span>
                    </div>
                  )
                )}
              </div>
            </div>

            <div className="picker-stat-group">
              <h4>Equipment</h4>
              <div className="picker-equipment">
                {selected.equipment.map((item) => (
                  <span key={item} className="equipment-tag">{item}</span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="form-actions">
        <button
          className="btn-primary"
          onClick={handleConfirm}
          disabled={!selected}
          data-testid="picker-confirm"
        >
          {selected ? `Choose ${selected.name}` : 'Select a Character'}
        </button>
        <button className="btn-secondary" onClick={onCancel}>
          Cancel
        </button>
      </div>
    </div>
  )
}
