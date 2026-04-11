import { useState } from 'react'
import type { Character } from '../types'

const CLASS_ICONS: Record<string, string> = {
  fighter: '⚔️',
  wizard: '🔮',
  rogue: '🗡️',
  cleric: '✝️',
  ranger: '🏹',
  paladin: '🛡️',
  barbarian: '🪓',
  bard: '🎵',
  druid: '🌿',
  monk: '👊',
  sorcerer: '✨',
  warlock: '🔥',
}

const CLASS_COLORS: Record<string, string> = {
  fighter: '#8b4513',
  wizard: '#4a0080',
  rogue: '#2d2d2d',
  cleric: '#daa520',
  ranger: '#228b22',
  paladin: '#c0c0c0',
  barbarian: '#8b0000',
  bard: '#6a0dad',
  druid: '#006400',
  monk: '#d2691e',
  sorcerer: '#ff4500',
  warlock: '#800080',
}

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
  return (
    <div className="character-sheet">
      <div className="char-header">
        <div
          className="char-portrait"
          style={{ background: `linear-gradient(135deg, ${CLASS_COLORS[character.class_name] || '#444'}, ${CLASS_COLORS[character.class_name] || '#444'}88)` }}
        >
          <span className="char-portrait-icon">{CLASS_ICONS[character.class_name] || '⚔️'}</span>
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
