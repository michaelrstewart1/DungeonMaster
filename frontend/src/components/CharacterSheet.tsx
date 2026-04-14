import { useState } from 'react'
import type { Character } from '../types'
import { CharacterPortrait } from './CharacterPortrait'
import { CharacterProgression } from './CharacterProgression'
import { generatePortrait, exportCharacter } from '../api/client'

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
  const [skillsOpen, setSkillsOpen] = useState(false)
  const [spellsOpen, setSpellsOpen] = useState(false)
  const [detailsOpen, setDetailsOpen] = useState(false)
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

  const handleExportJSON = async () => {
    try {
      const data = await exportCharacter(character.id)
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${character.name.toLowerCase().replace(/\s+/g, '-')}.json`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      // Silently fail
    }
  }

  const hasSkills = character.skills && character.skills.length > 0
  const hasSpells = (character.spells_known && character.spells_known.length > 0) ||
                    (character.cantrips_known && character.cantrips_known.length > 0)
  const hasDetails = character.background || character.alignment || character.backstory

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
            Level {character.level}{' '}
            {character.subrace || character.race}{' '}
            {character.class_name}
            {character.subclass && ` (${character.subclass})`}
          </p>
          {character.background && (
            <p className="char-background-line">{character.background} • {character.alignment || 'Unaligned'}</p>
          )}
        </div>
        <div className="char-header-actions">
          <button
            className="btn-export-json"
            onClick={handleExportJSON}
            title="Export as JSON"
            aria-label="Export character"
          >
            📥
          </button>
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
        {character.speed && (
          <div className="stat-block">
            <span className="stat-label">Speed</span>
            <span className="stat-value">{character.speed} ft</span>
          </div>
        )}
        {character.hit_dice && (
          <div className="stat-block">
            <span className="stat-label">Hit Die</span>
            <span className="stat-value">{character.hit_dice}</span>
          </div>
        )}
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

      {/* XP Progression */}
      <CharacterProgression
        characterId={character.id}
        level={character.level}
        xp={character.experience_points ?? 0}
      />

      {/* Skills */}
      {hasSkills && (
        <div className={`char-skills ${skillsOpen ? 'open' : ''}`}>
          <h3 onClick={() => setSkillsOpen(!skillsOpen)} className="section-toggle">
            Skills ({character.skills!.length})
            <span className="toggle-arrow">{skillsOpen ? '▾' : '▸'}</span>
          </h3>
          {skillsOpen && (
            <div className="skill-tags">
              {character.skills!.map(s => (
                <span key={s} className="skill-tag">{s.replace(/-/g, ' ')}</span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Spells */}
      {hasSpells && (
        <div className={`char-spells ${spellsOpen ? 'open' : ''}`}>
          <h3 onClick={() => setSpellsOpen(!spellsOpen)} className="section-toggle">
            Spells
            <span className="toggle-arrow">{spellsOpen ? '▾' : '▸'}</span>
          </h3>
          {spellsOpen && (
            <>
              {character.cantrips_known && character.cantrips_known.length > 0 && (
                <div className="spell-group">
                  <h4>Cantrips</h4>
                  <div className="spell-tags">
                    {character.cantrips_known.map(s => (
                      <span key={s} className="spell-tag cantrip-tag">{s}</span>
                    ))}
                  </div>
                </div>
              )}
              {character.spells_known && character.spells_known.length > 0 && (
                <div className="spell-group">
                  <h4>Known Spells</h4>
                  <div className="spell-tags">
                    {character.spells_known.map(s => (
                      <span key={s} className="spell-tag">{s}</span>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* Languages */}
      {character.languages && character.languages.length > 0 && (
        <div className="char-languages">
          <span className="lang-label">Languages:</span>
          {character.languages.map(l => (
            <span key={l} className="lang-tag">{l}</span>
          ))}
        </div>
      )}

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

      {/* Equipment & Inventory */}
      <div className={`char-inventory ${inventoryOpen ? 'open' : ''}`}>
        <h3 onClick={() => setInventoryOpen(!inventoryOpen)} className="inventory-toggle">
          Equipment & Inventory ({(character.equipment?.length || 0) + character.inventory.length})
          <span className="toggle-arrow">{inventoryOpen ? '▾' : '▸'}</span>
        </h3>
        {inventoryOpen && (
          <ul>
            {character.equipment && character.equipment.map((item) => (
              <li key={`eq-${item}`} className="equipment-item">{item}</li>
            ))}
            {character.inventory.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        )}
      </div>

      {/* Character Details (backstory, traits, etc.) */}
      {hasDetails && (
        <div className={`char-details ${detailsOpen ? 'open' : ''}`}>
          <h3 onClick={() => setDetailsOpen(!detailsOpen)} className="section-toggle">
            Character Details
            <span className="toggle-arrow">{detailsOpen ? '▾' : '▸'}</span>
          </h3>
          {detailsOpen && (
            <div className="details-content">
              {character.personality_traits && (
                <div className="detail-block">
                  <h4>Personality Traits</h4>
                  <p>{character.personality_traits}</p>
                </div>
              )}
              {character.ideals && (
                <div className="detail-block">
                  <h4>Ideals</h4>
                  <p>{character.ideals}</p>
                </div>
              )}
              {character.bonds && (
                <div className="detail-block">
                  <h4>Bonds</h4>
                  <p>{character.bonds}</p>
                </div>
              )}
              {character.flaws && (
                <div className="detail-block">
                  <h4>Flaws</h4>
                  <p>{character.flaws}</p>
                </div>
              )}
              {character.backstory && (
                <div className="detail-block">
                  <h4>Backstory</h4>
                  <p>{character.backstory}</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
