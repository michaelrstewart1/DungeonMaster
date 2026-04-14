import { useState } from 'react'

export interface Quest {
  id: string
  title: string
  description: string
  status: 'active' | 'completed' | 'failed'
  turnAdded: number
}

export interface AdventureEntry {
  id: string
  type: 'combat' | 'dialogue' | 'discovery' | 'quest' | 'loot' | 'rest'
  summary: string
  turnNumber: number
  timestamp: Date
}

export interface LootItem {
  id: string
  name: string
  rarity: 'common' | 'uncommon' | 'rare' | 'very-rare' | 'legendary'
  description: string
  turnFound: number
}

export interface AdventureLogProps {
  isOpen: boolean
  onClose: () => void
  quests: Quest[]
  entries: AdventureEntry[]
  loot: LootItem[]
}

const EVENT_ICONS: Record<AdventureEntry['type'], string> = {
  combat: '⚔️',
  dialogue: '💬',
  discovery: '🔍',
  quest: '🎯',
  loot: '💰',
  rest: '🏕️',
}

const RARITY_LABELS: Record<LootItem['rarity'], string> = {
  common: 'Common',
  uncommon: 'Uncommon',
  rare: 'Rare',
  'very-rare': 'Very Rare',
  legendary: 'Legendary',
}

type SectionKey = 'quests' | 'timeline' | 'loot'

export function AdventureLog({ isOpen, onClose, quests, entries, loot }: AdventureLogProps) {
  const [expandedSections, setExpandedSections] = useState<Record<SectionKey, boolean>>({
    quests: true,
    timeline: true,
    loot: true,
  })

  const toggleSection = (section: SectionKey) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }))
  }

  const activeQuests = quests.filter(q => q.status === 'active')
  const completedQuests = quests.filter(q => q.status === 'completed')
  const failedQuests = quests.filter(q => q.status === 'failed')
  const sortedEntries = [...entries].sort((a, b) => b.turnNumber - a.turnNumber)

  return (
    <>
      {isOpen && <div className="adventure-log-backdrop" onClick={onClose} />}
      <div className={`adventure-log-panel ${isOpen ? 'adventure-log-open' : ''}`} data-testid="adventure-log">
        {/* Header */}
        <div className="adventure-log-header">
          <h2>📜 Adventure Log</h2>
          <button className="adventure-log-close" onClick={onClose} title="Close adventure log">✕</button>
        </div>

        <div className="adventure-log-content">
          {/* Quest Log */}
          <div className="adventure-log-section">
            <button
              className={`adventure-log-section-toggle ${expandedSections.quests ? 'expanded' : ''}`}
              onClick={() => toggleSection('quests')}
            >
              <span className="section-chevron">▶</span>
              <span className="section-title">Quest Log</span>
              <span className="section-count">{activeQuests.length} active</span>
            </button>
            <div className={`adventure-log-section-body ${expandedSections.quests ? 'section-expanded' : ''}`}>
              {quests.length === 0 && (
                <p className="adventure-log-empty">No quests discovered yet. Explore the world to find adventure!</p>
              )}
              {activeQuests.map(q => (
                <div key={q.id} className="quest-item quest-active">
                  <div className="quest-status-icon">🎯</div>
                  <div className="quest-details">
                    <h4 className="quest-title">{q.title}</h4>
                    <p className="quest-description">{q.description}</p>
                    <span className="quest-turn">Turn {q.turnAdded}</span>
                  </div>
                </div>
              ))}
              {completedQuests.map(q => (
                <div key={q.id} className="quest-item quest-completed">
                  <div className="quest-status-icon">✅</div>
                  <div className="quest-details">
                    <h4 className="quest-title">{q.title}</h4>
                    <p className="quest-description">{q.description}</p>
                    <span className="quest-turn">Turn {q.turnAdded}</span>
                  </div>
                </div>
              ))}
              {failedQuests.map(q => (
                <div key={q.id} className="quest-item quest-failed">
                  <div className="quest-status-icon">❌</div>
                  <div className="quest-details">
                    <h4 className="quest-title">{q.title}</h4>
                    <p className="quest-description">{q.description}</p>
                    <span className="quest-turn">Turn {q.turnAdded}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Adventure Timeline */}
          <div className="adventure-log-section">
            <button
              className={`adventure-log-section-toggle ${expandedSections.timeline ? 'expanded' : ''}`}
              onClick={() => toggleSection('timeline')}
            >
              <span className="section-chevron">▶</span>
              <span className="section-title">Adventure Timeline</span>
              <span className="section-count">{entries.length} events</span>
            </button>
            <div className={`adventure-log-section-body ${expandedSections.timeline ? 'section-expanded' : ''}`}>
              {sortedEntries.length === 0 && (
                <p className="adventure-log-empty">Your story has yet to unfold...</p>
              )}
              {sortedEntries.map(entry => (
                <div key={entry.id} className={`timeline-entry timeline-${entry.type}`}>
                  <span className="timeline-icon">{EVENT_ICONS[entry.type]}</span>
                  <div className="timeline-details">
                    <p className="timeline-summary">{entry.summary}</p>
                    <span className="timeline-turn">Turn {entry.turnNumber}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Loot Log */}
          <div className="adventure-log-section">
            <button
              className={`adventure-log-section-toggle ${expandedSections.loot ? 'expanded' : ''}`}
              onClick={() => toggleSection('loot')}
            >
              <span className="section-chevron">▶</span>
              <span className="section-title">Loot Log</span>
              <span className="section-count">{loot.length} items</span>
            </button>
            <div className={`adventure-log-section-body ${expandedSections.loot ? 'section-expanded' : ''}`}>
              {loot.length === 0 && (
                <p className="adventure-log-empty">No treasure found yet. Keep searching!</p>
              )}
              {loot.map(item => (
                <div key={item.id} className={`loot-item loot-${item.rarity}`}>
                  <div className="loot-details">
                    <h4 className="loot-name">{item.name}</h4>
                    <span className={`loot-rarity rarity-${item.rarity}`}>{RARITY_LABELS[item.rarity]}</span>
                    <p className="loot-description">{item.description}</p>
                    <span className="loot-turn">Found on turn {item.turnFound}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
