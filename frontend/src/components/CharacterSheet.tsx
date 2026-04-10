import type { Character } from '../types'

interface CharacterSheetProps {
  character: Character
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

export function CharacterSheet({ character }: CharacterSheetProps) {
  return (
    <div className="character-sheet">
      <div className="char-header">
        <h2>{character.name}</h2>
        <p className="char-subtitle">
          Level {character.level} {character.race} {character.class_name}
        </p>
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
          return (
            <div key={key} className="ability-block">
              <span className="ability-label">{label}</span>
              <span className="ability-score">{score}</span>
              <span className="ability-mod">{abilityModifier(score)}</span>
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

      <div className="char-inventory">
        <h3>Inventory</h3>
        <ul>
          {character.inventory.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </div>
    </div>
  )
}
