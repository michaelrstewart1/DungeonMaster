import { useState, useMemo, useCallback, useRef, useEffect } from 'react'
import type { CharacterCreate, Race, CharacterClass } from '../types'
import { CharacterPortrait } from './CharacterPortrait'
import { CLASS_COLORS } from '../data/premadeCharacters'
import {
  SUBRACES, SUBCLASSES, BACKGROUNDS, SKILLS, CLASS_SKILL_CHOICES,
  ALIGNMENTS, LANGUAGES, RACIAL_LANGUAGES, HIT_DICE,
  POINT_BUY_COSTS, STANDARD_ARRAY, POINT_BUY_BUDGET,
  SPELLCASTING_CLASSES, STARTING_EQUIPMENT,
} from '../data/dnd5e'

const RACES: { value: Race; label: string; desc: string }[] = [
  { value: 'human', label: 'Human', desc: 'Versatile and ambitious, humans are the most adaptable of all races.' },
  { value: 'elf', label: 'Elf', desc: 'Graceful and long-lived, with keen senses and a deep connection to magic.' },
  { value: 'dwarf', label: 'Dwarf', desc: 'Bold and hardy, dwarves are skilled warriors and master artisans.' },
  { value: 'halfling', label: 'Halfling', desc: 'Small and nimble, halflings are resourceful survivors with remarkable luck.' },
  { value: 'gnome', label: 'Gnome', desc: 'Curious and inventive, gnomes delight in discovery and creation.' },
  { value: 'half-elf', label: 'Half-Elf', desc: 'Walking in two worlds, half-elves combine human drive with elven grace.' },
  { value: 'half-orc', label: 'Half-Orc', desc: 'Fierce and powerful, half-orcs channel their endurance into might.' },
  { value: 'tiefling', label: 'Tiefling', desc: 'Bearing an infernal bloodline, tieflings wield dark charisma and fire.' },
  { value: 'dragonborn', label: 'Dragonborn', desc: 'Proud dragon-blooded warriors who breathe elemental devastation.' },
]

const CLASSES: { value: CharacterClass; label: string; icon: string; desc: string }[] = [
  { value: 'barbarian', label: 'Barbarian', icon: '🪓', desc: 'A fierce warrior of primal rage and unmatched physical power.' },
  { value: 'bard', label: 'Bard', icon: '🎵', desc: 'An inspiring magician whose power echoes the music of creation.' },
  { value: 'cleric', label: 'Cleric', icon: '✝️', desc: 'A priestly champion who wields divine magic in service of a higher power.' },
  { value: 'druid', label: 'Druid', icon: '🌿', desc: 'A priest of the Old Faith, wielding the powers of nature.' },
  { value: 'fighter', label: 'Fighter', icon: '🛡️', desc: 'A master of martial combat, skilled with weapons and armor.' },
  { value: 'monk', label: 'Monk', icon: '👊', desc: 'A master of martial arts, harnessing the power of body and soul.' },
  { value: 'paladin', label: 'Paladin', icon: '⚜️', desc: 'A holy warrior bound to a sacred oath of justice and righteousness.' },
  { value: 'ranger', label: 'Ranger', icon: '🏹', desc: 'A warrior who combats threats on the edges of civilization.' },
  { value: 'rogue', label: 'Rogue', icon: '🗡️', desc: 'A scoundrel who uses stealth and cunning to overcome obstacles.' },
  { value: 'sorcerer', label: 'Sorcerer', icon: '⚡', desc: 'A spellcaster who draws on inherent magic from a gift or bloodline.' },
  { value: 'warlock', label: 'Warlock', icon: '👁️', desc: 'A wielder of magic derived from a bargain with an extraplanar entity.' },
  { value: 'wizard', label: 'Wizard', icon: '🔮', desc: 'A scholarly magic-user who commands arcane spells through study.' },
]

const ABILITY_INFO: { key: string; label: string; short: string; desc: string; tooltip: string }[] = [
  { key: 'strength', label: 'Strength', short: 'STR', desc: 'Physical power', tooltip: 'Measures bodily power. Affects melee attack/damage rolls, Athletics checks, carrying capacity, and how far you can jump or push.' },
  { key: 'dexterity', label: 'Dexterity', short: 'DEX', desc: 'Agility & reflexes', tooltip: 'Measures agility and reflexes. Affects AC (armor class), initiative, ranged attack rolls, Acrobatics, Sleight of Hand, and Stealth checks.' },
  { key: 'constitution', label: 'Constitution', short: 'CON', desc: 'Endurance & health', tooltip: 'Measures endurance and stamina. Determines your hit points (HP) at each level and affects concentration saves to maintain spells.' },
  { key: 'intelligence', label: 'Intelligence', short: 'INT', desc: 'Reasoning & memory', tooltip: 'Measures reasoning, memory, and analytical skill. Key ability for Wizards. Affects Arcana, History, Investigation, Nature, and Religion checks.' },
  { key: 'wisdom', label: 'Wisdom', short: 'WIS', desc: 'Perception & insight', tooltip: 'Measures awareness, intuition, and willpower. Key ability for Clerics, Druids, Rangers. Affects Perception, Insight, Medicine, Survival, and Animal Handling.' },
  { key: 'charisma', label: 'Charisma', short: 'CHA', desc: 'Force of personality', tooltip: 'Measures force of personality and social influence. Key ability for Bards, Paladins, Sorcerers, Warlocks. Affects Deception, Intimidation, Performance, and Persuasion.' },
]

type AbilityScores = { strength: number; dexterity: number; constitution: number; intelligence: number; wisdom: number; charisma: number }
type AbilityMethod = 'point-buy' | 'standard-array' | 'roll'

interface CharacterCreatorProps {
  onCreate: (character: CharacterCreate) => void
  onCancel: () => void
}

const DEFAULT_ABILITIES: AbilityScores = { strength: 8, dexterity: 8, constitution: 8, intelligence: 8, wisdom: 8, charisma: 8 }

export function CharacterCreator({ onCreate, onCancel }: CharacterCreatorProps) {
  const [step, setStep] = useState(0)
  const creatorRef = useRef<HTMLFormElement>(null)

  // Scroll to top of creator on step change
  useEffect(() => {
    // Use instant scroll + scrollIntoView to ensure content is visible
    creatorRef.current?.scrollIntoView?.({ behavior: 'auto', block: 'start' })
    window.scrollTo({ top: 0, behavior: 'auto' })
  }, [step])

  // Step 0: Race + Subrace
  const [race, setRace] = useState<Race>('human')
  const [subrace, setSubrace] = useState<string>('')

  // Step 1: Class + Subclass
  const [className, setClassName] = useState<CharacterClass>('fighter')
  const [subclass, setSubclass] = useState<string>('')

  // Step 2: Background
  const [background, setBackground] = useState<string>('acolyte')

  // Step 3: Ability Scores
  const [abilityMethod, setAbilityMethod] = useState<AbilityMethod>('point-buy')
  const [abilities, setAbilities] = useState<AbilityScores>({ ...DEFAULT_ABILITIES })
  const [standardArrayAssignments, setStandardArrayAssignments] = useState<Record<string, number>>({})

  // Step 4: Skills
  const [selectedSkills, setSelectedSkills] = useState<string[]>([])

  // Step 5: Equipment
  const [equipmentChoices, setEquipmentChoices] = useState<Record<number, number>>({})

  // Step 6: Spells (casters only)
  const [selectedCantrips, _setSelectedCantrips] = useState<string[]>([])
  const [selectedSpells, _setSelectedSpells] = useState<string[]>([])

  // Step 7: Details
  const [name, setName] = useState('')
  const [alignment, setAlignment] = useState<string>('true-neutral')
  const [personalityTraits, setPersonalityTraits] = useState('')
  const [ideals, setIdeals] = useState('')
  const [bonds, setBonds] = useState('')
  const [flaws, setFlaws] = useState('')
  const [backstory, setBackstory] = useState('')
  const [selectedLanguages, setSelectedLanguages] = useState<string[]>([])

  // Derived data
  const availableSubraces = useMemo(() =>
    SUBRACES.filter(s => s.parentRace === race), [race])

  const availableSubclasses = useMemo(() =>
    SUBCLASSES.filter(s => s.parentClass === className), [className])

  const selectedBackground = useMemo(() =>
    BACKGROUNDS.find(b => b.value === background), [background])

  const classSkillInfo = useMemo(() =>
    CLASS_SKILL_CHOICES[className] || { count: 2, options: [] }, [className])

  const isSpellcaster = useMemo(() =>
    className in SPELLCASTING_CLASSES, [className])

  const selectedSubrace = useMemo(() =>
    SUBRACES.find(s => s.value === subrace), [subrace])

  // Get racial ability bonuses
  const racialBonuses = useMemo(() => {
    const bonuses: Record<string, number> = {}
    if (selectedSubrace) {
      Object.entries(selectedSubrace.abilityBonuses).forEach(([k, v]) => {
        bonuses[k] = (bonuses[k] || 0) + v
      })
    }
    return bonuses
  }, [selectedSubrace])

  // Point buy cost calculation
  const pointBuySpent = useMemo(() => {
    if (abilityMethod !== 'point-buy') return 0
    return Object.values(abilities).reduce((sum, score) => {
      return sum + (POINT_BUY_COSTS[score] ?? 0)
    }, 0)
  }, [abilities, abilityMethod])

  const abilityMod = (score: number) => {
    const mod = Math.floor((score - 10) / 2)
    return mod >= 0 ? `+${mod}` : `${mod}`
  }

  const modClass = (score: number) => {
    const mod = Math.floor((score - 10) / 2)
    if (mod > 0) return 'mod-positive'
    if (mod < 0) return 'mod-negative'
    return 'mod-zero'
  }

  // Calculate final ability scores (base + racial)
  const finalAbilities = useMemo(() => {
    const result = { ...abilities }
    for (const [key, bonus] of Object.entries(racialBonuses)) {
      if (key in result) {
        result[key as keyof AbilityScores] += bonus
      }
    }
    return result
  }, [abilities, racialBonuses])

  // Calculate HP based on class hit die + CON mod
  const calculatedHP = useMemo(() => {
    const hitDie = HIT_DICE[className] || 8
    const conMod = Math.floor((finalAbilities.constitution - 10) / 2)
    return hitDie + conMod
  }, [className, finalAbilities])

  // Calculate AC (base 10 + DEX mod)
  const calculatedAC = useMemo(() => {
    return 10 + Math.floor((finalAbilities.dexterity - 10) / 2)
  }, [finalAbilities])

  const updateAbility = useCallback((key: keyof AbilityScores, delta: number) => {
    setAbilities(prev => {
      const newVal = Math.min(15, Math.max(8, prev[key] + delta))
      return { ...prev, [key]: newVal }
    })
  }, [])

  // Roll 4d6 drop lowest
  const rollAbilities = useCallback(() => {
    const roll4d6 = () => {
      const rolls = Array.from({ length: 4 }, () => Math.floor(Math.random() * 6) + 1)
      rolls.sort((a, b) => b - a)
      return rolls[0] + rolls[1] + rolls[2]
    }
    setAbilities({
      strength: roll4d6(),
      dexterity: roll4d6(),
      constitution: roll4d6(),
      intelligence: roll4d6(),
      wisdom: roll4d6(),
      charisma: roll4d6(),
    })
  }, [])

  // Apply standard array
  const applyStandardArray = useCallback((assignments: Record<string, number>) => {
    const newAbilities = { ...DEFAULT_ABILITIES }
    for (const [key, value] of Object.entries(assignments)) {
      if (key in newAbilities) {
        newAbilities[key as keyof AbilityScores] = value
      }
    }
    setAbilities(newAbilities)
    setStandardArrayAssignments(assignments)
  }, [])

  // Determine if we should show the spells step
  const spellcasterInfo = isSpellcaster ? SPELLCASTING_CLASSES[className] : null

  // Dynamic step list (spells step only for casters)
  const steps = useMemo(() => {
    const base = ['Race', 'Class', 'Background', 'Abilities', 'Skills', 'Equipment']
    if (isSpellcaster && spellcasterInfo && spellcasterInfo.cantripsKnown > 0) {
      base.push('Spells')
    }
    base.push('Details', 'Review')
    return base
  }, [isSpellcaster, spellcasterInfo])

  // Step validation — green checkmark on completed steps
  const isStepValid = useCallback((stepIndex: number): boolean => {
    const stepName = steps[stepIndex]
    switch (stepName) {
      case 'Race': return !!race
      case 'Class': return !!className
      case 'Background': return !!background
      case 'Abilities': return abilityMethod === 'point-buy' ? pointBuySpent <= POINT_BUY_BUDGET : true
      case 'Skills': return selectedSkills.length === classSkillInfo.count
      case 'Equipment': return true
      case 'Spells': return true
      case 'Details': return name.trim().length > 0
      case 'Review': return name.trim().length > 0
      default: return false
    }
  }, [steps, race, className, background, abilityMethod, pointBuySpent, selectedSkills.length, classSkillInfo.count, name])

  // Handle submit
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    // Gather equipment from choices
    const selectedEquipment: string[] = []
    const classEquip = STARTING_EQUIPMENT[className] || []
    classEquip.forEach((choice, idx) => {
      const choiceIdx = equipmentChoices[idx] ?? 0
      if (choice.options[choiceIdx]) {
        selectedEquipment.push(...choice.options[choiceIdx])
      }
    })

    // Gather background equipment
    if (selectedBackground) {
      selectedEquipment.push(...selectedBackground.equipment)
    }

    // Gather languages
    const raceLanguages = RACIAL_LANGUAGES[race] || ['Common']
    const allLanguages = [...new Set([...raceLanguages, ...selectedLanguages])]

    const hitDie = HIT_DICE[className] || 8

    onCreate({
      name,
      race,
      class_name: className,
      level: 1,
      hp: calculatedHP,
      max_hp: calculatedHP,
      ac: calculatedAC,
      speed: race === 'dwarf' || race === 'halfling' || race === 'gnome' ? 25 : 30,
      hit_dice: `1d${hitDie}`,
      ...finalAbilities,
      subrace: subrace || undefined,
      subclass: subclass || undefined,
      background,
      alignment,
      skills: selectedSkills,
      saving_throws: [],
      languages: allLanguages,
      features: [],
      spells_known: selectedSpells,
      cantrips_known: selectedCantrips,
      equipment: selectedEquipment,
      personality_traits: personalityTraits || undefined,
      ideals: ideals || undefined,
      bonds: bonds || undefined,
      flaws: flaws || undefined,
      backstory: backstory || undefined,
    })
  }

  // Determine actual step index for spells
  // const getStepIndex = (stepName: string) => steps.indexOf(stepName)

  return (
    <form ref={creatorRef} onSubmit={handleSubmit} className="character-creator" aria-label="form" role="form">
      <div className="creator-header">
        <h2>⚔️ Forge Your Hero</h2>
        <div className="creator-header-divider">
          <span className="divider-rune">☬</span>
        </div>
      </div>

      {/* Step indicator */}
      <div className="creator-steps" data-testid="creator-steps">
        <div className="creator-progress-bar">
          <div className="creator-progress-fill" style={{ width: `${(step / (steps.length - 1)) * 100}%` }} />
        </div>
        {steps.map((s, i) => (
          <button
            key={s}
            type="button"
            className={`creator-step ${i === step ? 'active' : ''} ${i < step ? 'complete' : ''} ${isStepValid(i) && i !== step ? 'valid' : ''}`}
            onClick={() => setStep(i)}
          >
            <span className="step-number">{i < step ? '✓' : i + 1}</span>
            <span className="step-label">{s}</span>
          </button>
        ))}
      </div>

      {/* Floating mini-preview (visible from step 2+) */}
      {step >= 2 && (
        <div className="creator-mini-preview">
          <CharacterPortrait race={race} className={className} size="sm" />
          <div className="mini-preview-info">
            <span className="mini-preview-race">{RACES.find(r => r.value === race)?.label}</span>
            <span className="mini-preview-class">{CLASSES.find(c => c.value === className)?.label}</span>
          </div>
        </div>
      )}

      {/* ================================================================ */}
      {/* Step 0: Race + Subrace */}
      {/* ================================================================ */}
      {steps[step] === 'Race' && (
        <div className="creator-section" data-testid="step-race">
          <h3>Choose Your Race</h3>
          <div className="race-grid stagger-children" role="radiogroup" aria-label="Race selection">
            {RACES.map(r => (
              <button
                key={r.value}
                type="button"
                className={`race-card animate-in ${race === r.value ? 'selected' : ''}`}
                onClick={() => { setRace(r.value); setSubrace('') }}
                aria-pressed={race === r.value}
                data-testid={`race-${r.value}`}
              >
                <img className="race-art" src={`/art/races/${r.value}.jpg`} alt={r.label} />
                <span className="race-name">{r.label}</span>
                <span className="card-tooltip">{r.desc}</span>
              </button>
            ))}
          </div>

          {/* Subrace selection */}
          {availableSubraces.length > 0 && (
            <div className="subrace-section">
              <h4>Choose Your Subrace</h4>
              <div className="subrace-grid" role="radiogroup" aria-label="Subrace selection">
                {availableSubraces.map(sr => (
                  <button
                    key={sr.value}
                    type="button"
                    className={`subrace-card ${subrace === sr.value ? 'selected' : ''}`}
                    onClick={() => setSubrace(sr.value)}
                    aria-pressed={subrace === sr.value}
                    data-testid={`subrace-${sr.value}`}
                  >
                    <span className="subrace-name">{sr.label}</span>
                    <span className="subrace-bonuses">
                      {Object.entries(sr.abilityBonuses).map(([ab, val]) =>
                        `${ab.slice(0, 3).toUpperCase()} ${val > 0 ? '+' : ''}${val}`
                      ).join(', ')}
                    </span>
                    <span className="subrace-traits">{sr.traits.join(', ')}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Hidden select for test compatibility */}
          <select
            id="char-race"
            aria-label="Race"
            value={race}
            onChange={e => setRace(e.target.value as Race)}
            style={{ position: 'absolute', opacity: 0, pointerEvents: 'none' }}
          >
            {RACES.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
          </select>

          <div className="form-actions">
            <button type="button" className="btn-primary" onClick={() => setStep(1)}>
              Next: Choose Class →
            </button>
            <button type="button" onClick={onCancel} className="btn-secondary">Cancel</button>
          </div>
        </div>
      )}

      {/* ================================================================ */}
      {/* Step 1: Class + Subclass */}
      {/* ================================================================ */}
      {steps[step] === 'Class' && (
        <div className="creator-section" data-testid="step-class">
          <h3>Choose Your Class</h3>
          <div className="class-grid stagger-children" role="radiogroup" aria-label="Class selection">
            {CLASSES.map(c => {
              const colors = CLASS_COLORS[c.value]
              return (
                <button
                  key={c.value}
                  type="button"
                  className={`class-card animate-in ${className === c.value ? 'selected' : ''}`}
                  onClick={() => { setClassName(c.value); setSubclass('') }}
                  aria-pressed={className === c.value}
                  data-testid={`class-${c.value}`}
                  style={{
                    '--class-color': colors.primary,
                    '--class-glow': colors.accent,
                  } as React.CSSProperties}
                >
                  <img className="class-art" src={`/art/classes/${c.value}.jpg`} alt={c.label} />
                  <span className="class-name">{c.label}</span>
                  <span className="class-hit-die">d{HIT_DICE[c.value]}</span>
                  <span className="card-tooltip">{c.desc}</span>
                </button>
              )
            })}
          </div>

          {/* Subclass selection */}
          {availableSubclasses.length > 0 && (
            <div className="subclass-section">
              <h4>Choose Your Subclass</h4>
              <div className="subclass-grid" role="radiogroup" aria-label="Subclass selection">
                {availableSubclasses.map(sc => (
                  <button
                    key={sc.value}
                    type="button"
                    className={`subclass-card ${subclass === sc.value ? 'selected' : ''}`}
                    onClick={() => setSubclass(sc.value)}
                    aria-pressed={subclass === sc.value}
                    data-testid={`subclass-${sc.value}`}
                  >
                    <span className="subclass-name">{sc.label}</span>
                    {sc.features.length > 0 && (
                      <span className="subclass-feature">{sc.features[0].name}</span>
                    )}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Hidden select for test compatibility */}
          <select
            id="char-class"
            aria-label="Class"
            value={className}
            onChange={e => setClassName(e.target.value as CharacterClass)}
            style={{ position: 'absolute', opacity: 0, pointerEvents: 'none' }}
          >
            {CLASSES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
          </select>

          <div className="form-actions">
            <button type="button" className="btn-secondary" onClick={() => setStep(0)}>← Back</button>
            <button type="button" className="btn-primary" onClick={() => setStep(2)}>Next: Background →</button>
          </div>
        </div>
      )}

      {/* ================================================================ */}
      {/* Step 2: Background */}
      {/* ================================================================ */}
      {steps[step] === 'Background' && (
        <div className="creator-section" data-testid="step-background">
          <h3>Choose Your Background</h3>
          <div className="background-grid" role="radiogroup" aria-label="Background selection">
            {BACKGROUNDS.map(bg => (
              <button
                key={bg.value}
                type="button"
                className={`background-card ${background === bg.value ? 'selected' : ''}`}
                onClick={() => setBackground(bg.value)}
                aria-pressed={background === bg.value}
                data-testid={`bg-${bg.value}`}
              >
                <img className="bg-art" src={`/art/backgrounds/${bg.value}.jpg`} alt={bg.label} />
                <span className="bg-name">{bg.label}</span>
                <span className="bg-skills">Skills: {bg.skillProficiencies.join(', ')}</span>
                {bg.toolProficiencies.length > 0 && (
                  <span className="bg-tools">Tools: {bg.toolProficiencies.join(', ')}</span>
                )}
                {bg.languages > 0 && (
                  <span className="bg-languages">+{bg.languages} language{bg.languages > 1 ? 's' : ''}</span>
                )}
              </button>
            ))}
          </div>

          {/* Background feature preview */}
          {selectedBackground && (
            <div className="background-preview">
              <h4>{selectedBackground.feature.name}</h4>
              <p>{selectedBackground.feature.description}</p>
            </div>
          )}

          <div className="form-actions">
            <button type="button" className="btn-secondary" onClick={() => setStep(1)}>← Back</button>
            <button type="button" className="btn-primary" onClick={() => setStep(3)}>Next: Abilities →</button>
          </div>
        </div>
      )}

      {/* ================================================================ */}
      {/* Step 3: Ability Scores */}
      {/* ================================================================ */}
      {steps[step] === 'Abilities' && (
        <div className="creator-section" data-testid="step-abilities">
          <h3>Set Ability Scores</h3>

          {/* Method selector */}
          <div className="ability-method-selector" role="radiogroup" aria-label="Ability score method">
            {(['point-buy', 'standard-array', 'roll'] as AbilityMethod[]).map(method => (
              <button
                key={method}
                type="button"
                className={`method-btn ${abilityMethod === method ? 'active' : ''}`}
                onClick={() => {
                  setAbilityMethod(method)
                  if (method === 'point-buy') setAbilities({ ...DEFAULT_ABILITIES })
                  if (method === 'roll') rollAbilities()
                }}
                data-testid={`method-${method}`}
              >
                {method === 'point-buy' ? '🎯 Point Buy' : method === 'standard-array' ? '📊 Standard Array' : '🎲 Roll 4d6'}
              </button>
            ))}
          </div>

          {/* Point Buy */}
          {abilityMethod === 'point-buy' && (
            <>
              <div className="points-budget">
                <div className="budget-label">
                  Points spent: <strong className={pointBuySpent > POINT_BUY_BUDGET ? 'over-budget' : ''}>{pointBuySpent}</strong> / {POINT_BUY_BUDGET}
                </div>
                <div className="budget-bar">
                  <div
                    className={`budget-fill ${pointBuySpent > POINT_BUY_BUDGET ? 'over-budget' : pointBuySpent === POINT_BUY_BUDGET ? 'at-budget' : ''}`}
                    style={{ width: `${Math.min(100, (pointBuySpent / POINT_BUY_BUDGET) * 100)}%` }}
                  />
                </div>
              </div>
              <div className="ability-grid">
                {ABILITY_INFO.map(({ key, label, short, desc, tooltip }) => {
                  const val = abilities[key as keyof AbilityScores]
                  const bonus = racialBonuses[key] || 0
                  const finalVal = val + bonus
                  return (
                    <div key={key} className="ability-card" data-tooltip={tooltip}>
                      <label htmlFor={`ability-${key}`} className="ability-card-label">
                        <span className="ability-short">{short}</span>
                        <span className="ability-name">{label}</span>
                        <span className="ability-desc">{desc}</span>
                      </label>
                      <div className="tooltip-text">{tooltip}</div>
                      <div className="ability-controls">
                        <button
                          type="button"
                          className="ability-btn"
                          onClick={() => updateAbility(key as keyof AbilityScores, -1)}
                          disabled={val <= 8}
                          aria-label={`Decrease ${label}`}
                        >−</button>
                        <input
                          id={`ability-${key}`}
                          type="number"
                          min={8}
                          max={15}
                          value={val}
                          onChange={e => {
                            const n = parseInt(e.target.value) || 8
                            setAbilities(prev => ({ ...prev, [key]: Math.min(15, Math.max(8, n)) }))
                          }}
                          className="ability-input"
                        />
                        <button
                          type="button"
                          className="ability-btn"
                          onClick={() => updateAbility(key as keyof AbilityScores, 1)}
                          disabled={val >= 15}
                          aria-label={`Increase ${label}`}
                        >+</button>
                      </div>
                      {bonus !== 0 && <span className="ability-racial-bonus">+{bonus} racial</span>}
                      <span className="ability-final">Final: {finalVal}</span>
                      <span className={`ability-modifier ${modClass(finalVal)}`}>{abilityMod(finalVal)}</span>
                      <span className="ability-cost">Cost: {POINT_BUY_COSTS[val] ?? 0} pts</span>
                    </div>
                  )
                })}
              </div>
            </>
          )}

          {/* Standard Array */}
          {abilityMethod === 'standard-array' && (
            <div className="standard-array-section">
              <p className="array-hint">Assign each value to an ability: {STANDARD_ARRAY.join(', ')}</p>
              <div className="ability-grid">
                {ABILITY_INFO.map(({ key, label, short, tooltip }) => {
                  const assigned = standardArrayAssignments[key]
                  const usedValues = Object.values(standardArrayAssignments)
                  const bonus = racialBonuses[key] || 0
                  const finalVal = (assigned || 8) + bonus
                  return (
                    <div key={key} className="ability-card" data-tooltip={tooltip}>
                      <label htmlFor={`ability-${key}`} className="ability-card-label">
                        <span className="ability-short">{short}</span>
                        <span className="ability-name">{label}</span>
                      </label>
                      <div className="tooltip-text">{tooltip}</div>
                      <select
                        id={`ability-${key}`}
                        value={assigned || ''}
                        onChange={e => {
                          const val = parseInt(e.target.value)
                          const newAssignments = { ...standardArrayAssignments, [key]: val }
                          applyStandardArray(newAssignments)
                        }}
                        className="ability-select"
                      >
                        <option value="">—</option>
                        {STANDARD_ARRAY.map(v => (
                          <option
                            key={v}
                            value={v}
                            disabled={usedValues.includes(v) && standardArrayAssignments[key] !== v}
                          >{v}</option>
                        ))}
                      </select>
                      {bonus !== 0 && <span className="ability-racial-bonus">+{bonus} racial</span>}
                      <span className="ability-final">Final: {finalVal}</span>
                      <span className={`ability-modifier ${modClass(finalVal)}`}>{abilityMod(finalVal)}</span>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {abilityMethod === 'roll' && (
            <div className="roll-section">
              <button type="button" className="btn-roll" onClick={rollAbilities} data-testid="reroll-btn">
                🎲 Re-Roll All
              </button>
              <div className="ability-grid">
                {ABILITY_INFO.map(({ key, label, short, tooltip }) => {
                  const val = abilities[key as keyof AbilityScores]
                  const bonus = racialBonuses[key] || 0
                  const finalVal = val + bonus
                  return (
                    <div key={key} className="ability-card" data-tooltip={tooltip}>
                      <label className="ability-card-label">
                        <span className="ability-short">{short}</span>
                        <span className="ability-name">{label}</span>
                      </label>
                      <div className="tooltip-text">{tooltip}</div>
                      <div className="ability-rolled-value">{val}</div>
                      {bonus !== 0 && <span className="ability-racial-bonus">+{bonus} racial</span>}
                      <span className="ability-final">Final: {finalVal}</span>
                      <span className={`ability-modifier ${modClass(finalVal)}`}>{abilityMod(finalVal)}</span>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          <div className="form-actions">
            <button type="button" className="btn-secondary" onClick={() => setStep(2)}>← Back</button>
            <button type="button" className="btn-primary" onClick={() => setStep(4)}>Next: Skills →</button>
          </div>
        </div>
      )}

      {/* ================================================================ */}
      {/* Step 4: Skills */}
      {/* ================================================================ */}
      {steps[step] === 'Skills' && (
        <div className="creator-section" data-testid="step-skills">
          <h3>Choose Your Skills</h3>
          <p className="skill-hint">
            Choose <strong>{classSkillInfo.count}</strong> skills from your class list.
            {selectedBackground && (
              <> Your background ({selectedBackground.label}) grants: <strong>{selectedBackground.skillProficiencies.join(', ')}</strong></>
            )}
          </p>

          <div className={`skill-selection-count ${selectedSkills.length === classSkillInfo.count ? 'skills-full' : selectedSkills.length > classSkillInfo.count ? 'skills-over' : ''}`}>
            Selected: {selectedSkills.length} / {classSkillInfo.count}
            {selectedSkills.length === classSkillInfo.count && <span className="skills-check"> ✓</span>}
          </div>

          <div className="skill-groups">
            {(['STR', 'DEX', 'INT', 'WIS', 'CHA'] as const).map(ability => {
              const groupSkills = SKILLS.filter(s => s.abilityShort === ability)
              if (groupSkills.length === 0) return null
              const abilityLabel = { STR: 'Strength', DEX: 'Dexterity', INT: 'Intelligence', WIS: 'Wisdom', CHA: 'Charisma' }[ability]
              return (
                <div key={ability} className="skill-group">
                  <div className="skill-group-header">
                    <span className="skill-group-ability">{ability}</span>
                    <span className="skill-group-label">{abilityLabel}</span>
                  </div>
                  <div className="skill-group-grid">
                    {groupSkills.map(skill => {
                      const isClassOption = classSkillInfo.options.includes(skill.value)
                      const isBackgroundSkill = selectedBackground?.skillProficiencies.includes(skill.label) ?? false
                      const isSelected = selectedSkills.includes(skill.value) || isBackgroundSkill
                      const canSelect = isClassOption && !isBackgroundSkill && selectedSkills.length < classSkillInfo.count

                      return (
                        <button
                          key={skill.value}
                          type="button"
                          className={`skill-card ${isSelected ? 'selected' : ''} ${isBackgroundSkill ? 'background-skill' : ''} ${!isClassOption && !isBackgroundSkill ? 'unavailable' : ''}`}
                          onClick={() => {
                            if (isBackgroundSkill) return
                            if (!isClassOption) return
                            if (selectedSkills.includes(skill.value)) {
                              setSelectedSkills(prev => prev.filter(s => s !== skill.value))
                            } else if (canSelect) {
                              setSelectedSkills(prev => [...prev, skill.value])
                            }
                          }}
                          disabled={isBackgroundSkill || (!isClassOption && !isBackgroundSkill)}
                          data-testid={`skill-${skill.value}`}
                        >
                          <span className="skill-check">{isSelected ? '◆' : '◇'}</span>
                          <span className="skill-name">{skill.label}</span>
                          {isBackgroundSkill && <span className="skill-source">Background</span>}
                        </button>
                      )
                    })}
                  </div>
                </div>
              )
            })}
          </div>

          <div className="form-actions">
            <button type="button" className="btn-secondary" onClick={() => setStep(3)}>← Back</button>
            <button type="button" className="btn-primary" onClick={() => setStep(5)}>Next: Equipment →</button>
          </div>
        </div>
      )}

      {/* ================================================================ */}
      {/* Step 5: Equipment */}
      {/* ================================================================ */}
      {steps[step] === 'Equipment' && (
        <div className="creator-section" data-testid="step-equipment">
          <h3>Choose Starting Equipment</h3>

          {(STARTING_EQUIPMENT[className] || []).map((choice, idx) => (
            <div key={idx} className="equipment-choice">
              <h4><span className="choice-number">Choice {idx + 1}</span> {choice.label}</h4>
              <div className="equipment-options" role="radiogroup" aria-label={choice.label}>
                {choice.options.map((option, optIdx) => (
                  <button
                    key={optIdx}
                    type="button"
                    className={`equipment-option ${(equipmentChoices[idx] ?? 0) === optIdx ? 'selected' : ''}`}
                    onClick={() => setEquipmentChoices(prev => ({ ...prev, [idx]: optIdx }))}
                    aria-pressed={(equipmentChoices[idx] ?? 0) === optIdx}
                  >
                    {option.join(', ')}
                  </button>
                ))}
              </div>
            </div>
          ))}

          {selectedBackground && selectedBackground.equipment.length > 0 && (
            <div className="background-equipment">
              <h4>From Background ({selectedBackground.label})</h4>
              <p>{selectedBackground.equipment.join(', ')}</p>
            </div>
          )}

          <div className="form-actions">
            <button type="button" className="btn-secondary" onClick={() => setStep(4)}>← Back</button>
            <button type="button" className="btn-primary" onClick={() => setStep(step + 1)}>
              Next: {isSpellcaster && spellcasterInfo && spellcasterInfo.cantripsKnown > 0 ? 'Spells' : 'Details'} →
            </button>
          </div>
        </div>
      )}

      {/* ================================================================ */}
      {/* Step 6: Spells (casters only) */}
      {/* ================================================================ */}
      {steps[step] === 'Spells' && spellcasterInfo && (
        <div className="creator-section" data-testid="step-spells">
          <h3>Choose Your Spells</h3>

          {spellcasterInfo.cantripsKnown > 0 && (
            <div className="spell-section">
              <h4>Cantrips (Choose {spellcasterInfo.cantripsKnown})</h4>
              <p className="spell-count">Selected: {selectedCantrips.length} / {spellcasterInfo.cantripsKnown}</p>
              <p className="spell-hint">Cantrip selection will be available after character creation via the spell management interface.</p>
            </div>
          )}

          {spellcasterInfo.spellsKnownOrPrepared > 0 && (
            <div className="spell-section">
              <h4>1st Level Spells (Choose {spellcasterInfo.spellsKnownOrPrepared})</h4>
              <p className="spell-count">Selected: {selectedSpells.length} / {spellcasterInfo.spellsKnownOrPrepared}</p>
              <p className="spell-hint">Spell selection will be available after character creation via the spell management interface.</p>
            </div>
          )}

          <div className="form-actions">
            <button type="button" className="btn-secondary" onClick={() => setStep(step - 1)}>← Back</button>
            <button type="button" className="btn-primary" onClick={() => setStep(step + 1)}>Next: Details →</button>
          </div>
        </div>
      )}

      {/* ================================================================ */}
      {/* Step 7: Details (Name, Alignment, Backstory, Personality) */}
      {/* ================================================================ */}
      {steps[step] === 'Details' && (
        <div className="creator-section" data-testid="step-details">
          <h3>Character Details</h3>

          <div className="details-grid">
            <div className="form-group">
              <label htmlFor="char-name">Name</label>
              <input
                id="char-name"
                type="text"
                value={name}
                onChange={e => setName(e.target.value)}
                placeholder="Enter your hero's name..."
                required
                autoFocus
                className="name-input"
              />
            </div>

            <div className="form-group">
              <label htmlFor="char-alignment">Alignment</label>
              <select
                id="char-alignment"
                value={alignment}
                onChange={e => setAlignment(e.target.value)}
                className="alignment-select"
              >
                {ALIGNMENTS.map(a => (
                  <option key={a.value} value={a.value}>{a.label}</option>
                ))}
              </select>
            </div>

            {/* Extra language selection (from background) */}
            {selectedBackground && selectedBackground.languages > 0 && (
              <div className="form-group">
                <label>Extra Languages ({selectedBackground.languages})</label>
                <div className="language-grid">
                  {LANGUAGES
                    .filter(l => !(RACIAL_LANGUAGES[race] || []).includes(l.value))
                    .map(lang => (
                      <button
                        key={lang.value}
                        type="button"
                        className={`language-btn ${selectedLanguages.includes(lang.value) ? 'selected' : ''}`}
                        onClick={() => {
                          if (selectedLanguages.includes(lang.value)) {
                            setSelectedLanguages(prev => prev.filter(l => l !== lang.value))
                          } else if (selectedLanguages.length < selectedBackground.languages) {
                            setSelectedLanguages(prev => [...prev, lang.value])
                          }
                        }}
                        disabled={!selectedLanguages.includes(lang.value) && selectedLanguages.length >= selectedBackground.languages}
                      >
                        {lang.label}
                      </button>
                    ))}
                </div>
              </div>
            )}

            {/* Personality from background */}
            {selectedBackground && (
              <>
                <div className="form-group">
                  <label htmlFor="char-personality">Personality Traits</label>
                  <textarea
                    id="char-personality"
                    value={personalityTraits}
                    onChange={e => setPersonalityTraits(e.target.value)}
                    placeholder="Describe your personality..."
                    rows={2}
                  />
                  {selectedBackground.personalityTraits.length > 0 && (
                    <div className="trait-suggestions">
                      <span className="suggestions-label">Suggestions:</span>
                      {selectedBackground.personalityTraits.slice(0, 4).map((trait, i) => (
                        <button
                          key={i}
                          type="button"
                          className="trait-suggestion"
                          onClick={() => setPersonalityTraits(trait)}
                        >{trait}</button>
                      ))}
                    </div>
                  )}
                </div>

                <div className="form-group">
                  <label htmlFor="char-ideals">Ideals</label>
                  <textarea
                    id="char-ideals"
                    value={ideals}
                    onChange={e => setIdeals(e.target.value)}
                    placeholder="What drives you?"
                    rows={2}
                  />
                  {selectedBackground.ideals.length > 0 && (
                    <div className="trait-suggestions">
                      <span className="suggestions-label">Suggestions:</span>
                      {selectedBackground.ideals.slice(0, 3).map((ideal, i) => (
                        <button
                          key={i}
                          type="button"
                          className="trait-suggestion"
                          onClick={() => setIdeals(ideal)}
                        >{ideal}</button>
                      ))}
                    </div>
                  )}
                </div>

                <div className="form-group">
                  <label htmlFor="char-bonds">Bonds</label>
                  <textarea
                    id="char-bonds"
                    value={bonds}
                    onChange={e => setBonds(e.target.value)}
                    placeholder="What connects you to the world?"
                    rows={2}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="char-flaws">Flaws</label>
                  <textarea
                    id="char-flaws"
                    value={flaws}
                    onChange={e => setFlaws(e.target.value)}
                    placeholder="What are your weaknesses?"
                    rows={2}
                  />
                </div>
              </>
            )}

            <div className="form-group form-group-full">
              <label htmlFor="char-backstory">Backstory</label>
              <textarea
                id="char-backstory"
                value={backstory}
                onChange={e => setBackstory(e.target.value)}
                placeholder="Tell your hero's story..."
                rows={4}
              />
            </div>
          </div>

          <div className="form-actions">
            <button type="button" className="btn-secondary" onClick={() => setStep(step - 1)}>← Back</button>
            <button type="button" className="btn-primary" onClick={() => setStep(step + 1)} disabled={!name.trim()}>
              Next: Review →
            </button>
          </div>
        </div>
      )}

      {/* ================================================================ */}
      {/* Step 8: Review */}
      {/* ================================================================ */}
      {steps[step] === 'Review' && (
        <div className="creator-section" data-testid="step-review">
          <h3>Review Your Hero</h3>
          <div className="review-layout">
            <div className="review-portrait">
              <CharacterPortrait race={race} className={className} size="lg" selected />
            </div>
            <div className="review-info">
              <h4 className="review-name">{name || '???'}</h4>
              <p className="review-summary">
                Level 1{' '}
                {selectedSubrace ? availableSubraces.find(s => s.value === subrace)?.label : RACES.find(r => r.value === race)?.label}{' '}
                {CLASSES.find(c => c.value === className)?.label}
                {subclass && ` (${availableSubclasses.find(s => s.value === subclass)?.label})`}
              </p>
              {background && (
                <p className="review-background">Background: {BACKGROUNDS.find(b => b.value === background)?.label}</p>
              )}
              {alignment && (
                <p className="review-alignment">Alignment: {ALIGNMENTS.find(a => a.value === alignment)?.label}</p>
              )}

              <div className="review-section">
                <h5 className="review-section-header"><span className="review-section-icon">⚔️</span> Ability Scores</h5>
                <div className="review-abilities">
                  {ABILITY_INFO.map(({ key, short }) => {
                    const base = abilities[key as keyof AbilityScores]
                    const bonus = racialBonuses[key] || 0
                    const final_ = base + bonus
                    return (
                      <span key={key} className="review-stat">
                        <span className="stat-label">{short}</span>
                        <span className="stat-value">{final_}</span>
                        <span className={`stat-mod ${modClass(final_)}`}>{abilityMod(final_)}</span>
                      </span>
                    )
                  })}
                </div>
              </div>

              <div className="review-section">
                <h5 className="review-section-header"><span className="review-section-icon">❤️</span> Combat Stats</h5>
                <div className="review-derived">
                  <span className="derived-stat"><span className="derived-label">HP</span><span className="derived-value">{calculatedHP}</span></span>
                  <span className="derived-stat"><span className="derived-label">AC</span><span className="derived-value">{calculatedAC}</span></span>
                  <span className="derived-stat"><span className="derived-label">Speed</span><span className="derived-value">{race === 'dwarf' || race === 'halfling' || race === 'gnome' ? 25 : 30} ft</span></span>
                  <span className="derived-stat"><span className="derived-label">Hit Die</span><span className="derived-value">d{HIT_DICE[className]}</span></span>
                </div>
              </div>

              {selectedSkills.length > 0 && (
                <div className="review-section">
                  <h5 className="review-section-header"><span className="review-section-icon">🎯</span> Skills</h5>
                  <div className="review-skills">
                    {selectedSkills.map(s => {
                      const sk = SKILLS.find(sk => sk.value === s)
                      return <span key={s} className="review-skill-tag">{sk?.label || s}</span>
                    })}
                    {selectedBackground && selectedBackground.skillProficiencies.map(sp => (
                      <span key={sp} className="review-skill-tag background-tag">{sp}</span>
                    ))}
                  </div>
                </div>
              )}

              {(() => {
                const selectedEquipment: string[] = []
                const classEquip = STARTING_EQUIPMENT[className] || []
                classEquip.forEach((choice, idx) => {
                  const choiceIdx = equipmentChoices[idx] ?? 0
                  if (choice.options[choiceIdx]) {
                    selectedEquipment.push(...choice.options[choiceIdx])
                  }
                })
                if (selectedBackground) selectedEquipment.push(...selectedBackground.equipment)
                return selectedEquipment.length > 0 ? (
                  <div className="review-section">
                    <h5 className="review-section-header"><span className="review-section-icon">🎒</span> Equipment</h5>
                    <div className="review-equipment-list">
                      {selectedEquipment.map((item, i) => (
                        <span key={i} className="review-equip-tag">{item}</span>
                      ))}
                    </div>
                  </div>
                ) : null
              })()}

              {backstory && (
                <div className="review-section">
                  <h5 className="review-section-header"><span className="review-section-icon">📖</span> Backstory</h5>
                  <div className="review-backstory">
                    {backstory.length > 200 ? backstory.slice(0, 200) + '...' : backstory}
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="review-note">
            <p>🎨 A portrait will be auto-generated after creation!</p>
          </div>

          <div className="form-actions">
            <button type="button" className="btn-secondary" onClick={() => setStep(step - 1)}>← Back</button>
            <button type="submit" className="btn-primary btn-create" disabled={!name.trim()}>
              ⚔️ Create Character
            </button>
          </div>
        </div>
      )}
    </form>
  )
}
