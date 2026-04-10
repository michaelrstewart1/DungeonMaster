import { useState } from 'react'
import type { CharacterCreate, Race, CharacterClass } from '../types'

const RACES: Race[] = ['human', 'elf', 'dwarf', 'halfling', 'gnome', 'half-elf', 'half-orc', 'tiefling', 'dragonborn']
const CLASSES: CharacterClass[] = [
  'barbarian', 'bard', 'cleric', 'druid', 'fighter',
  'monk', 'paladin', 'ranger', 'rogue', 'sorcerer', 'warlock', 'wizard',
]

interface CharacterCreatorProps {
  onCreate: (character: CharacterCreate) => void
  onCancel: () => void
}

const DEFAULT_ABILITIES = { strength: 10, dexterity: 10, constitution: 10, intelligence: 10, wisdom: 10, charisma: 10 }

export function CharacterCreator({ onCreate, onCancel }: CharacterCreatorProps) {
  const [name, setName] = useState('')
  const [race, setRace] = useState<Race>('human')
  const [className, setClassName] = useState<CharacterClass>('fighter')
  const [abilities, setAbilities] = useState(DEFAULT_ABILITIES)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onCreate({
      name,
      race,
      class_name: className,
      level: 1,
      hp: 10 + Math.floor((abilities.constitution - 10) / 2),
      max_hp: 10 + Math.floor((abilities.constitution - 10) / 2),
      ac: 10 + Math.floor((abilities.dexterity - 10) / 2),
      ...abilities,
    })
  }

  const updateAbility = (key: keyof typeof abilities, value: number) => {
    setAbilities((prev) => ({ ...prev, [key]: value }))
  }

  return (
    <form onSubmit={handleSubmit} className="character-creator" aria-label="form" role="form">
      <h2>Create Character</h2>

      <div className="form-group">
        <label htmlFor="char-name">Name</label>
        <input
          id="char-name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
      </div>

      <div className="form-group">
        <label htmlFor="char-race">Race</label>
        <select id="char-race" value={race} onChange={(e) => setRace(e.target.value as Race)}>
          {RACES.map((r) => (
            <option key={r} value={r}>{r.charAt(0).toUpperCase() + r.slice(1).replace('-', ' ')}</option>
          ))}
        </select>
      </div>

      <div className="form-group">
        <label htmlFor="char-class">Class</label>
        <select id="char-class" value={className} onChange={(e) => setClassName(e.target.value as CharacterClass)}>
          {CLASSES.map((c) => (
            <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
          ))}
        </select>
      </div>

      <fieldset className="ability-scores">
        <legend>Ability Scores</legend>
        {(Object.keys(abilities) as (keyof typeof abilities)[]).map((ability) => (
          <div key={ability} className="form-group">
            <label htmlFor={`ability-${ability}`}>
              {ability.charAt(0).toUpperCase() + ability.slice(1)}
            </label>
            <input
              id={`ability-${ability}`}
              type="number"
              min={3}
              max={18}
              value={abilities[ability]}
              onChange={(e) => updateAbility(ability, parseInt(e.target.value) || 10)}
            />
          </div>
        ))}
      </fieldset>

      <div className="form-actions">
        <button type="submit" className="btn-primary">Create Character</button>
        <button type="button" onClick={onCancel} className="btn-secondary">Cancel</button>
      </div>
    </form>
  )
}
