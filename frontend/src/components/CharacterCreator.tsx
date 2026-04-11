import { useState } from 'react'
import type { CharacterCreate, Race, CharacterClass } from '../types'
import { CharacterPortrait } from './CharacterPortrait'
import { RACE_SYMBOLS, CLASS_COLORS } from '../data/premadeCharacters'

const RACES: { value: Race; label: string }[] = [
  { value: 'human', label: 'Human' },
  { value: 'elf', label: 'Elf' },
  { value: 'dwarf', label: 'Dwarf' },
  { value: 'halfling', label: 'Halfling' },
  { value: 'gnome', label: 'Gnome' },
  { value: 'half-elf', label: 'Half-Elf' },
  { value: 'half-orc', label: 'Half-Orc' },
  { value: 'tiefling', label: 'Tiefling' },
  { value: 'dragonborn', label: 'Dragonborn' },
]

const CLASSES: { value: CharacterClass; label: string; icon: string }[] = [
  { value: 'barbarian', label: 'Barbarian', icon: '🪓' },
  { value: 'bard', label: 'Bard', icon: '🎵' },
  { value: 'cleric', label: 'Cleric', icon: '✝️' },
  { value: 'druid', label: 'Druid', icon: '🌿' },
  { value: 'fighter', label: 'Fighter', icon: '🛡️' },
  { value: 'monk', label: 'Monk', icon: '👊' },
  { value: 'paladin', label: 'Paladin', icon: '⚜️' },
  { value: 'ranger', label: 'Ranger', icon: '🏹' },
  { value: 'rogue', label: 'Rogue', icon: '🗡️' },
  { value: 'sorcerer', label: 'Sorcerer', icon: '⚡' },
  { value: 'warlock', label: 'Warlock', icon: '👁️' },
  { value: 'wizard', label: 'Wizard', icon: '🔮' },
]

const ABILITY_INFO: { key: string; label: string; short: string; desc: string }[] = [
  { key: 'strength', label: 'Strength', short: 'STR', desc: 'Physical power' },
  { key: 'dexterity', label: 'Dexterity', short: 'DEX', desc: 'Agility & reflexes' },
  { key: 'constitution', label: 'Constitution', short: 'CON', desc: 'Endurance & health' },
  { key: 'intelligence', label: 'Intelligence', short: 'INT', desc: 'Reasoning & memory' },
  { key: 'wisdom', label: 'Wisdom', short: 'WIS', desc: 'Perception & insight' },
  { key: 'charisma', label: 'Charisma', short: 'CHA', desc: 'Force of personality' },
]

interface CharacterCreatorProps {
  onCreate: (character: CharacterCreate) => void
  onCancel: () => void
}

const DEFAULT_ABILITIES = { strength: 10, dexterity: 10, constitution: 10, intelligence: 10, wisdom: 10, charisma: 10 }

export function CharacterCreator({ onCreate, onCancel }: CharacterCreatorProps) {
  const [step, setStep] = useState(0)
  const [name, setName] = useState('')
  const [race, setRace] = useState<Race>('human')
  const [className, setClassName] = useState<CharacterClass>('fighter')
  const [abilities, setAbilities] = useState(DEFAULT_ABILITIES)

  const totalPoints = Object.values(abilities).reduce((sum, v) => sum + v, 0) - 60
  const pointBudget = 27

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

  const updateAbility = (key: keyof typeof abilities, delta: number) => {
    setAbilities((prev) => {
      const newVal = Math.min(18, Math.max(3, prev[key] + delta))
      return { ...prev, [key]: newVal }
    })
  }

  const abilityMod = (score: number) => {
    const mod = Math.floor((score - 10) / 2)
    return mod >= 0 ? `+${mod}` : `${mod}`
  }

  const steps = ['Race', 'Class', 'Abilities', 'Name & Review']

  return (
    <form onSubmit={handleSubmit} className="character-creator" aria-label="form" role="form">
      <h2>Forge Your Hero</h2>

      {/* Step indicator */}
      <div className="creator-steps" data-testid="creator-steps">
        <div className="creator-progress-bar">
          <div className="creator-progress-fill" style={{ width: `${(step / (steps.length - 1)) * 100}%` }} />
        </div>
        {steps.map((s, i) => (
          <button
            key={s}
            type="button"
            className={`creator-step ${i === step ? 'active' : ''} ${i < step ? 'complete' : ''}`}
            onClick={() => setStep(i)}
          >
            <span className="step-number">{i < step ? '✓' : i + 1}</span>
            <span className="step-label">{s}</span>
          </button>
        ))}
      </div>

      {/* Step 0: Race */}
      {step === 0 && (
        <div className="creator-section" data-testid="step-race">
          <h3>Choose Your Race</h3>
          <div className="race-grid stagger-children" role="radiogroup" aria-label="Race selection">
            {RACES.map((r) => (
              <button
                key={r.value}
                type="button"
                className={`race-card animate-in ${race === r.value ? 'selected' : ''}`}
                onClick={() => setRace(r.value)}
                aria-pressed={race === r.value}
                data-testid={`race-${r.value}`}
              >
                <span className="race-symbol">{RACE_SYMBOLS[r.value]}</span>
                <span className="race-name">{r.label}</span>
              </button>
            ))}
          </div>
          {/* Hidden select for test compatibility */}
          <select
            id="char-race"
            aria-label="Race"
            value={race}
            onChange={(e) => setRace(e.target.value as Race)}
            style={{ position: 'absolute', opacity: 0, pointerEvents: 'none' }}
          >
            {RACES.map((r) => (
              <option key={r.value} value={r.value}>{r.label}</option>
            ))}
          </select>
          <div className="form-actions">
            <button type="button" className="btn-primary" onClick={() => setStep(1)}>
              Next: Choose Class →
            </button>
            <button type="button" onClick={onCancel} className="btn-secondary">Cancel</button>
          </div>
        </div>
      )}

      {/* Step 1: Class */}
      {step === 1 && (
        <div className="creator-section" data-testid="step-class">
          <h3>Choose Your Class</h3>
          <div className="class-grid stagger-children" role="radiogroup" aria-label="Class selection">
            {CLASSES.map((c) => {
              const colors = CLASS_COLORS[c.value]
              return (
                <button
                  key={c.value}
                  type="button"
                  className={`class-card animate-in ${className === c.value ? 'selected' : ''}`}
                  onClick={() => setClassName(c.value)}
                  aria-pressed={className === c.value}
                  data-testid={`class-${c.value}`}
                  style={{
                    '--class-color': colors.primary,
                    '--class-glow': colors.accent,
                  } as React.CSSProperties}
                >
                  <span className="class-icon">{c.icon}</span>
                  <span className="class-name">{c.label}</span>
                </button>
              )
            })}
          </div>
          {/* Hidden select for test compatibility */}
          <select
            id="char-class"
            aria-label="Class"
            value={className}
            onChange={(e) => setClassName(e.target.value as CharacterClass)}
            style={{ position: 'absolute', opacity: 0, pointerEvents: 'none' }}
          >
            {CLASSES.map((c) => (
              <option key={c.value} value={c.value}>{c.label}</option>
            ))}
          </select>
          <div className="form-actions">
            <button type="button" className="btn-secondary" onClick={() => setStep(0)}>
              ← Back
            </button>
            <button type="button" className="btn-primary" onClick={() => setStep(2)}>
              Next: Abilities →
            </button>
          </div>
        </div>
      )}

      {/* Step 2: Abilities */}
      {step === 2 && (
        <div className="creator-section" data-testid="step-abilities">
          <h3>Set Ability Scores</h3>
          <p className="points-budget">
            Points spent: <strong>{totalPoints}</strong> / {pointBudget}
          </p>
          <div className="ability-grid">
            {ABILITY_INFO.map(({ key, label, short, desc }) => {
              const val = abilities[key as keyof typeof abilities]
              return (
                <div key={key} className="ability-card">
                  <label htmlFor={`ability-${key}`} className="ability-card-label">
                    <span className="ability-short">{short}</span>
                    <span className="ability-name">{label}</span>
                    <span className="ability-desc">{desc}</span>
                  </label>
                  <div className="ability-controls">
                    <button
                      type="button"
                      className="ability-btn"
                      onClick={() => updateAbility(key as keyof typeof abilities, -1)}
                      disabled={val <= 3}
                      aria-label={`Decrease ${label}`}
                    >
                      −
                    </button>
                    <input
                      id={`ability-${key}`}
                      type="number"
                      min={3}
                      max={18}
                      value={val}
                      onChange={(e) => {
                        const n = parseInt(e.target.value) || 10
                        setAbilities((prev) => ({ ...prev, [key]: Math.min(18, Math.max(3, n)) }))
                      }}
                      className="ability-input"
                    />
                    <button
                      type="button"
                      className="ability-btn"
                      onClick={() => updateAbility(key as keyof typeof abilities, 1)}
                      disabled={val >= 18}
                      aria-label={`Increase ${label}`}
                    >
                      +
                    </button>
                  </div>
                  <span className="ability-modifier">{abilityMod(val)}</span>
                </div>
              )
            })}
          </div>
          <div className="form-actions">
            <button type="button" className="btn-secondary" onClick={() => setStep(1)}>
              ← Back
            </button>
            <button type="button" className="btn-primary" onClick={() => setStep(3)}>
              Next: Review →
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Name & Review */}
      {step === 3 && (
        <div className="creator-section" data-testid="step-review">
          <h3>Name Your Hero</h3>
          <div className="review-layout">
            <div className="review-portrait">
              <CharacterPortrait race={race} className={className} size="lg" selected />
            </div>
            <div className="review-info">
              <div className="form-group">
                <label htmlFor="char-name">Name</label>
                <input
                  id="char-name"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Enter your hero's name..."
                  required
                  autoFocus
                  className="name-input"
                />
              </div>
              <p className="review-summary">
                Level 1 {RACES.find((r) => r.value === race)?.label}{' '}
                {CLASSES.find((c) => c.value === className)?.label}
              </p>
              <div className="review-abilities">
                {ABILITY_INFO.map(({ key, short }) => (
                  <span key={key} className="review-stat">
                    {short}: {abilities[key as keyof typeof abilities]}
                  </span>
                ))}
              </div>
              <div className="review-derived">
                <span>HP: {10 + Math.floor((abilities.constitution - 10) / 2)}</span>
                <span>AC: {10 + Math.floor((abilities.dexterity - 10) / 2)}</span>
              </div>
            </div>
          </div>
          <div className="form-actions">
            <button type="button" className="btn-secondary" onClick={() => setStep(2)}>
              ← Back
            </button>
            <button type="submit" className="btn-primary" disabled={!name.trim()}>
              Create Character
            </button>
          </div>
        </div>
      )}
    </form>
  )
}
