import { useState } from 'react'
import { generateEncounter } from '../api/client'

interface Enemy {
  name: string
  hp: number
  ac: number
  cr: number
  count: number
}

interface EncounterData {
  enemies: Enemy[]
  total_xp: number
  difficulty_rating: string
  description: string
}

interface EncounterPanelProps {
  sessionId: string
  partyLevel?: number
}

const ENVIRONMENTS = ['dungeon', 'forest', 'cave', 'mountain', 'swamp', 'urban']
const DIFFICULTIES = ['easy', 'medium', 'hard', 'deadly']

const DIFFICULTY_COLORS: Record<string, string> = {
  easy: '#90EE90',
  medium: '#FFD700',
  hard: '#FF8C00',
  deadly: '#DC143C',
}

const ENEMY_EMOJIS: Record<string, string> = {
  goblin: '👹',
  orc: '🧟',
  troll: '🔥',
  dragon: '🐉',
  giant: '⬛',
  skeleton: '💀',
  zombie: '🧟',
  wraith: '👻',
  demon: '😈',
  devil: '😈',
  elemental: '⚡',
  golem: '🗿',
  spider: '🕷️',
  serpent: '🐍',
  beast: '🐺',
  undead: '💀',
  cultist: '🖤',
  assassin: '🔪',
  knight: '⚔️',
  wizard: '🧙',
  priest: '⛪',
  guard: '🛡️',
  thug: '👊',
  bandit: '🏹',
}

function getEnemyEmoji(name: string): string {
  const lower = name.toLowerCase()
  for (const [key, emoji] of Object.entries(ENEMY_EMOJIS)) {
    if (lower.includes(key)) {
      return emoji
    }
  }
  return '⚔️'
}

export function EncounterPanel({ sessionId, partyLevel = 1 }: EncounterPanelProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [encounter, setEncounter] = useState<EncounterData | null>(null)
  const [selectedEnv, setSelectedEnv] = useState('dungeon')
  const [selectedDiff, setSelectedDiff] = useState('medium')

  const handleGenerate = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const data = await generateEncounter(sessionId, {
        environment: selectedEnv,
        difficulty: selectedDiff,
        party_level: partyLevel,
      })
      setEncounter(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate encounter')
    } finally {
      setIsLoading(false)
    }
  }

  const togglePanel = () => {
    setIsOpen(!isOpen)
  }

  const getDifficultyColor = (difficulty: string): string => {
    return DIFFICULTY_COLORS[difficulty] || '#D4A574'
  }

  return (
    <div className="encounter-panel-container">
      {/* Collapsed Button */}
      {!isOpen && (
        <button
          className="encounter-toggle-btn"
          onClick={togglePanel}
          title="Generate Random Encounter"
        >
          🎲 Encounter
        </button>
      )}

      {/* Expanded Panel */}
      {isOpen && (
        <div className="encounter-panel">
          {/* Close Button */}
          <button className="encounter-close-btn" onClick={togglePanel}>
            ✕
          </button>

          {/* Header */}
          <div className="encounter-header">
            <h2>Encounter Generator</h2>
          </div>

          {/* Controls */}
          <div className="encounter-controls">
            <div className="encounter-control-group">
              <label htmlFor="encounter-env">Environment:</label>
              <select
                id="encounter-env"
                value={selectedEnv}
                onChange={(e) => setSelectedEnv(e.target.value)}
                disabled={isLoading || !!encounter}
              >
                {ENVIRONMENTS.map((env) => (
                  <option key={env} value={env}>
                    {env.charAt(0).toUpperCase() + env.slice(1)}
                  </option>
                ))}
              </select>
            </div>

            <div className="encounter-control-group">
              <label htmlFor="encounter-diff">Difficulty:</label>
              <select
                id="encounter-diff"
                value={selectedDiff}
                onChange={(e) => setSelectedDiff(e.target.value)}
                disabled={isLoading || !!encounter}
              >
                {DIFFICULTIES.map((diff) => (
                  <option key={diff} value={diff}>
                    {diff.charAt(0).toUpperCase() + diff.slice(1)}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Generate Button */}
          <button
            className="encounter-generate-btn"
            onClick={handleGenerate}
            disabled={isLoading}
          >
            {isLoading ? 'Generating...' : '🎲 Generate Encounter'}
          </button>

          {/* Error Message */}
          {error && (
            <div className="encounter-error">
              <p>{error}</p>
            </div>
          )}

          {/* Encounter Display */}
          {encounter && (
            <div className="encounter-result">
              {/* Description */}
              <div className="encounter-description">
                <p>{encounter.description}</p>
              </div>

              {/* Enemies */}
              <div className="encounter-enemies">
                <h3>Enemies</h3>
                <div className="enemies-grid">
                  {encounter.enemies.map((enemy, idx) => (
                    <div key={idx} className="enemy-card">
                      <div className="enemy-icon">{getEnemyEmoji(enemy.name)}</div>
                      <div className="enemy-name">{enemy.name}</div>
                      <div className="enemy-count">×{enemy.count}</div>
                      <div className="enemy-stats">
                        <div className="stat">
                          <span className="stat-label">HP:</span>
                          <span className="stat-value">{enemy.hp}</span>
                        </div>
                        <div className="stat">
                          <span className="stat-label">AC:</span>
                          <span className="stat-value">{enemy.ac}</span>
                        </div>
                        <div className="stat">
                          <span className="stat-label">CR:</span>
                          <span className="stat-value">{enemy.cr}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* XP and Difficulty Info */}
              <div className="encounter-footer">
                <div className="encounter-xp">
                  <span className="xp-label">Total XP:</span>
                  <span className="xp-value">{encounter.total_xp}</span>
                </div>
                <div
                  className="encounter-difficulty-badge"
                  style={{ borderColor: getDifficultyColor(encounter.difficulty_rating) }}
                >
                  <span
                    className="difficulty-dot"
                    style={{ backgroundColor: getDifficultyColor(encounter.difficulty_rating) }}
                  ></span>
                  <span className="difficulty-text">{encounter.difficulty_rating.toUpperCase()}</span>
                </div>
              </div>

              {/* Reset Button */}
              <button
                className="encounter-reset-btn"
                onClick={() => {
                  setEncounter(null)
                  setSelectedEnv('dungeon')
                  setSelectedDiff('medium')
                }}
              >
                Generate New
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
