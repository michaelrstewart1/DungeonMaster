import { useState, useEffect, useCallback } from 'react'
import type { Campaign } from '../types'
import { updateCampaign } from '../api/client'

// ─── Setting types ───────────────────────────────────────────────

export type DMPersonality =
  | 'classic_wizard'
  | 'dark_lord'
  | 'theatrical_bard'
  | 'trickster'
  | 'scholarly_sage'
  | 'battle_commander'

export type DifficultyLevel = 'story' | 'balanced' | 'hard' | 'nightmare'

export type WorldTheme =
  | 'classic_fantasy'
  | 'gothic_horror'
  | 'seafaring'
  | 'desert_wastelands'
  | 'planar_cosmic'
  | 'urban_intrigue'

export interface SessionOptions {
  auto_roll_dice: boolean
  show_dice_results: boolean
  mature_content_filter: boolean
  atmospheric_effects: boolean
}

export interface CampaignSettingsData {
  dm_personality: DMPersonality
  difficulty: DifficultyLevel
  world_theme: WorldTheme
  session_options: SessionOptions
}

// ─── Option descriptors ──────────────────────────────────────────

interface PersonalityOption {
  id: DMPersonality
  emoji: string
  name: string
  desc: string
}

const PERSONALITIES: PersonalityOption[] = [
  { id: 'classic_wizard', emoji: '🧙', name: 'Classic Wizard', desc: 'Mysterious, dramatic, Gandalf-like' },
  { id: 'dark_lord', emoji: '💀', name: 'Dark Lord', desc: 'Menacing, foreboding, everything sounds dangerous' },
  { id: 'theatrical_bard', emoji: '🎭', name: 'Theatrical Bard', desc: 'Flowery, dramatic, loves metaphors' },
  { id: 'trickster', emoji: '😈', name: 'Trickster', desc: 'Sarcastic, witty, loves plot twists' },
  { id: 'scholarly_sage', emoji: '📚', name: 'Scholarly Sage', desc: 'Detailed, lore-heavy, encyclopedic' },
  { id: 'battle_commander', emoji: '⚔️', name: 'Battle Commander', desc: 'Military precision, tactical, combat-focused' },
]

interface DifficultyOption {
  id: DifficultyLevel
  emoji: string
  color: string
  name: string
  desc: string
}

const DIFFICULTIES: DifficultyOption[] = [
  { id: 'story', emoji: '🟢', color: '#4caf50', name: 'Story Mode', desc: 'Forgiving encounters, narrative focus' },
  { id: 'balanced', emoji: '🟡', color: '#d4a846', name: 'Balanced', desc: 'Fair challenges, good story' },
  { id: 'hard', emoji: '🟠', color: '#ff9800', name: 'Hard', desc: 'Deadly encounters, tough choices' },
  { id: 'nightmare', emoji: '🔴', color: '#f44336', name: 'Nightmare', desc: 'You WILL lose characters' },
]

interface ThemeOption {
  id: WorldTheme
  emoji: string
  name: string
}

const THEMES: ThemeOption[] = [
  { id: 'classic_fantasy', emoji: '🏰', name: 'Classic Fantasy' },
  { id: 'gothic_horror', emoji: '🧛', name: 'Gothic Horror' },
  { id: 'seafaring', emoji: '🌊', name: 'Seafaring Adventure' },
  { id: 'desert_wastelands', emoji: '🏜️', name: 'Desert Wastelands' },
  { id: 'planar_cosmic', emoji: '🌌', name: 'Planar / Cosmic' },
  { id: 'urban_intrigue', emoji: '🏙️', name: 'Urban Intrigue' },
]

// ─── Defaults ────────────────────────────────────────────────────

const DEFAULT_SETTINGS: CampaignSettingsData = {
  dm_personality: 'classic_wizard',
  difficulty: 'balanced',
  world_theme: 'classic_fantasy',
  session_options: {
    auto_roll_dice: false,
    show_dice_results: true,
    mature_content_filter: true,
    atmospheric_effects: true,
  },
}

function loadSettings(campaign: Campaign): CampaignSettingsData {
  const ws = campaign.world_state as Record<string, unknown>
  const stored = ws?.campaign_settings as Partial<CampaignSettingsData> | undefined
  if (!stored) return { ...DEFAULT_SETTINGS }
  return {
    dm_personality: stored.dm_personality ?? DEFAULT_SETTINGS.dm_personality,
    difficulty: stored.difficulty ?? DEFAULT_SETTINGS.difficulty,
    world_theme: stored.world_theme ?? DEFAULT_SETTINGS.world_theme,
    session_options: {
      ...DEFAULT_SETTINGS.session_options,
      ...(stored.session_options ?? {}),
    },
  }
}

// ─── Component ───────────────────────────────────────────────────

interface CampaignSettingsProps {
  campaign: Campaign
  onClose: () => void
  onSaved: (campaign: Campaign) => void
}

export function CampaignSettings({ campaign, onClose, onSaved }: CampaignSettingsProps) {
  const [settings, setSettings] = useState<CampaignSettingsData>(() => loadSettings(campaign))
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    personality: true,
    difficulty: true,
    theme: true,
    session: true,
  })

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose])

  const toggleSection = useCallback((key: string) => {
    setExpandedSections(prev => ({ ...prev, [key]: !prev[key] }))
  }, [])

  const handleSave = async () => {
    setSaving(true)
    setError(null)
    try {
      const updated = await updateCampaign(campaign.id, {
        world_state: {
          ...campaign.world_state,
          campaign_settings: settings,
        },
      })
      onSaved(updated)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save settings')
    } finally {
      setSaving(false)
    }
  }

  const setSessionOption = (key: keyof SessionOptions, value: boolean) => {
    setSettings(prev => ({
      ...prev,
      session_options: { ...prev.session_options, [key]: value },
    }))
  }

  const difficultyIndex = DIFFICULTIES.findIndex(d => d.id === settings.difficulty)

  return (
    <div className="modal-overlay" onClick={onClose} data-testid="campaign-settings-overlay">
      <div
        className="modal settings-modal"
        onClick={e => e.stopPropagation()}
        role="dialog"
        aria-label="Campaign Settings"
      >
        <div className="modal-header">
          <h2>⚙️ Campaign Settings</h2>
          <button className="modal-close" onClick={onClose} aria-label="Close settings">✕</button>
        </div>

        <div className="settings-body">
          {error && <p className="error-message settings-error">{error}</p>}

          {/* DM Personality */}
          <div className="settings-section">
            <button
              className="settings-section-header"
              onClick={() => toggleSection('personality')}
              aria-expanded={expandedSections.personality}
            >
              <span className="settings-section-title">🧙 DM Personality</span>
              <span className={`settings-chevron ${expandedSections.personality ? 'open' : ''}`}>›</span>
            </button>
            {expandedSections.personality && (
              <div className="settings-section-content">
                <div className="personality-grid">
                  {PERSONALITIES.map(p => (
                    <button
                      key={p.id}
                      className={`personality-card ${settings.dm_personality === p.id ? 'selected' : ''}`}
                      onClick={() => setSettings(s => ({ ...s, dm_personality: p.id }))}
                      data-testid={`personality-${p.id}`}
                    >
                      <span className="personality-emoji">{p.emoji}</span>
                      <span className="personality-name">{p.name}</span>
                      <span className="personality-desc">{p.desc}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Difficulty */}
          <div className="settings-section">
            <button
              className="settings-section-header"
              onClick={() => toggleSection('difficulty')}
              aria-expanded={expandedSections.difficulty}
            >
              <span className="settings-section-title">⚔️ Difficulty Level</span>
              <span className={`settings-chevron ${expandedSections.difficulty ? 'open' : ''}`}>›</span>
            </button>
            {expandedSections.difficulty && (
              <div className="settings-section-content">
                <div className="difficulty-track">
                  <div className="difficulty-track-bar">
                    <div
                      className="difficulty-track-fill"
                      style={{
                        width: `${(difficultyIndex / (DIFFICULTIES.length - 1)) * 100}%`,
                        background: DIFFICULTIES[difficultyIndex].color,
                      }}
                    />
                    {DIFFICULTIES.map((d, i) => (
                      <button
                        key={d.id}
                        className={`difficulty-stop ${settings.difficulty === d.id ? 'active' : ''}`}
                        style={{
                          left: `${(i / (DIFFICULTIES.length - 1)) * 100}%`,
                          borderColor: settings.difficulty === d.id ? d.color : undefined,
                          background: settings.difficulty === d.id ? d.color : undefined,
                        }}
                        onClick={() => setSettings(s => ({ ...s, difficulty: d.id }))}
                        title={d.name}
                        data-testid={`difficulty-${d.id}`}
                      />
                    ))}
                  </div>
                  <div className="difficulty-labels">
                    {DIFFICULTIES.map((d, i) => (
                      <button
                        key={d.id}
                        className={`difficulty-label ${settings.difficulty === d.id ? 'active' : ''}`}
                        style={{
                          left: `${(i / (DIFFICULTIES.length - 1)) * 100}%`,
                          color: settings.difficulty === d.id ? d.color : undefined,
                        }}
                        onClick={() => setSettings(s => ({ ...s, difficulty: d.id }))}
                      >
                        <span className="difficulty-label-emoji">{d.emoji}</span>
                        <span className="difficulty-label-name">{d.name}</span>
                      </button>
                    ))}
                  </div>
                </div>
                <p className="difficulty-desc">
                  {DIFFICULTIES[difficultyIndex].desc}
                </p>
              </div>
            )}
          </div>

          {/* World Theme */}
          <div className="settings-section">
            <button
              className="settings-section-header"
              onClick={() => toggleSection('theme')}
              aria-expanded={expandedSections.theme}
            >
              <span className="settings-section-title">🌍 World Theme</span>
              <span className={`settings-chevron ${expandedSections.theme ? 'open' : ''}`}>›</span>
            </button>
            {expandedSections.theme && (
              <div className="settings-section-content">
                <div className="theme-grid">
                  {THEMES.map(t => (
                    <button
                      key={t.id}
                      className={`theme-card ${settings.world_theme === t.id ? 'selected' : ''}`}
                      onClick={() => setSettings(s => ({ ...s, world_theme: t.id }))}
                      data-testid={`theme-${t.id}`}
                    >
                      <span className="theme-emoji">{t.emoji}</span>
                      <span className="theme-name">{t.name}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Session Options */}
          <div className="settings-section">
            <button
              className="settings-section-header"
              onClick={() => toggleSection('session')}
              aria-expanded={expandedSections.session}
            >
              <span className="settings-section-title">🎲 Session Options</span>
              <span className={`settings-chevron ${expandedSections.session ? 'open' : ''}`}>›</span>
            </button>
            {expandedSections.session && (
              <div className="settings-section-content">
                <div className="session-toggles">
                  <ToggleRow
                    label="Auto-roll dice"
                    sublabel="DM rolls for you vs you roll manually"
                    checked={settings.session_options.auto_roll_dice}
                    onChange={v => setSessionOption('auto_roll_dice', v)}
                    testId="toggle-auto-roll"
                  />
                  <ToggleRow
                    label="Show dice results"
                    sublabel="See the actual numbers behind each roll"
                    checked={settings.session_options.show_dice_results}
                    onChange={v => setSessionOption('show_dice_results', v)}
                    testId="toggle-show-dice"
                  />
                  <ToggleRow
                    label="Mature content filter"
                    sublabel="Filter graphic violence and mature themes"
                    checked={settings.session_options.mature_content_filter}
                    onChange={v => setSessionOption('mature_content_filter', v)}
                    testId="toggle-mature-filter"
                  />
                  <ToggleRow
                    label="Atmospheric effects"
                    sublabel="Screen effects like fog, fire glow, etc."
                    checked={settings.session_options.atmospheric_effects}
                    onChange={v => setSessionOption('atmospheric_effects', v)}
                    testId="toggle-atmospheric"
                  />
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="modal-footer settings-footer">
          <button className="btn-secondary" onClick={onClose}>Cancel</button>
          <button
            className="btn-primary"
            onClick={handleSave}
            disabled={saving}
            data-testid="settings-save"
          >
            {saving ? 'Saving…' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ─── Toggle sub-component ────────────────────────────────────────

interface ToggleRowProps {
  label: string
  sublabel: string
  checked: boolean
  onChange: (value: boolean) => void
  testId: string
}

function ToggleRow({ label, sublabel, checked, onChange, testId }: ToggleRowProps) {
  return (
    <label className="toggle-row" data-testid={testId}>
      <div className="toggle-text">
        <span className="toggle-label">{label}</span>
        <span className="toggle-sublabel">{sublabel}</span>
      </div>
      <div
        className={`toggle-switch ${checked ? 'on' : ''}`}
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') onChange(!checked) }}
        tabIndex={0}
      >
        <div className="toggle-knob" />
      </div>
    </label>
  )
}
