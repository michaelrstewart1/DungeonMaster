import { useState } from 'react'
import type { Character } from '../types'
import { CharacterPortrait } from './CharacterPortrait'
import { generatePortrait } from '../api/client'

const ABILITY_FULL_NAMES: Record<string, string> = {
  strength: 'Strength — Physical power, melee attacks',
  dexterity: 'Dexterity — Agility, reflexes, ranged attacks',
  constitution: 'Constitution — Health, stamina, endurance',
  intelligence: 'Intelligence — Memory, reasoning, arcane magic',
  wisdom: 'Wisdom — Perception, insight, divine magic',
  charisma: 'Charisma — Force of personality, social skills',
}

interface CharacterSheetProps {
  character: Character
  onRemove?: (id: string) => void
}

function abilityModifier(score: number): string {
  const mod = Math.floor((score - 10) / 2)
  return mod >= 0 ? `+${mod}` : `${mod}`
}

const ABILITY_NAMES = [
  { key: 'strength', label: 'STR' },
  { key: 'dexterity', label: 'DEX' },
  { key: 'constitution', label: 'CON' },
  { key: 'intelligence', label: 'INT' },
  { key: 'wisdom', label: 'WIS' },
  { key: 'charisma', label: 'CHA' },
] as const

export function CharacterSheet({ character, onRemove }: CharacterSheetProps) {
  const [inventoryOpen, setInventoryOpen] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [portraitUrl, setPortraitUrl] = useState(character.portrait_url || null)

  const handleGeneratePortrait = async () => {
    setGenerating(true)
    try {
      const updated = await generatePortrait(character.id)
      setPortraitUrl(updated.portrait_url || null)
    } catch {
      // Silently fail — button stays visible for retry
    } finally {
      setGenerating(false)
    }
  }

  return (
    <div className="character-sheet">
      <div className="char-header">
        <div className="char-portrait-wrapper">
          <CharacterPortrait
            race={character.race}
            className={character.class_name}
            portrait={portraitUrl || undefined}
            size="md"
          />
          {!portraitUrl && (
            <button
              className="btn-generate-portrait"
              onClick={handleGeneratePortrait}
              disabled={generating}
              title="Generate AI portrait"
            >
              {generating ? '⏳' : '🎨'}
            </button>
          )}
        </div>
        <div>
          <h2>{character.name}</h2>
          <p className="char-subtitle">
            Level {character.level} {character.race} {character.class_name}
          </p>
        </div>
        {onRemove && (
          <button
            className="char-remove-btn"
            onClick={() => onRemove(character.id)}
            title="Remove from party"
            aria-label="Remove character"
          >
            ✕
          </button>
        )}
      </div>

      <div className="char-stats">
        <div className="stat-block">
          <span className="stat-label">HP</span>
          <span className="stat-value">{character.hp} / {character.max_hp}</span>
        </div>
        <div className="stat-block">
          <span className="stat-label">AC</span>
          <span className="stat-value">{character.ac}</span>
        </div>
        <div className="stat-block">
          <span className="stat-label">Prof. Bonus</span>
          <span className="stat-value">+{character.proficiency_bonus}</span>
        </div>
      </div>

      <div className="ability-scores">
        {ABILITY_NAMES.map(({ key, label }) => {
          const score = character[key]
          const mod = Math.floor((score - 10) / 2)
          const modClass = mod > 0 ? 'mod-positive' : mod < 0 ? 'mod-negative' : 'mod-neutral'
          return (
            <div key={key} className="ability-block" title={ABILITY_FULL_NAMES[key]}>
              <span className="ability-label">{label}</span>
              <span className="ability-score">{score}</span>
              <span className={`ability-mod ${modClass}`}>{abilityModifier(score)}</span>
            </div>
          )
        })}
      </div>

      {character.conditions.length > 0 && (
        <div className="char-conditions">
          <h3>Conditions</h3>
          <div className="condition-tags">
            {character.conditions.map((c) => (
              <span key={c} className="condition-tag">{c}</span>
            ))}
          </div>
        </div>
      )}

      <div className={`char-inventory ${inventoryOpen ? 'open' : ''}`}>
        <h3 onClick={() => setInventoryOpen(!inventoryOpen)} className="inventory-toggle">
          Inventory ({character.inventory.length})
          <span className="toggle-arrow">{inventoryOpen ? '▾' : '▸'}</span>
        </h3>
        {inventoryOpen && (
          <ul>
            {character.inventory.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
