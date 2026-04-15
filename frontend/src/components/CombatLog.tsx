import { useEffect, useRef, useState } from 'react'

export interface CombatLogEntry {
  id: string
  type: 'attack' | 'damage' | 'save' | 'spell' | 'condition' | 'defeat' | 'round'
  text: string
  details?: string
  result?: 'hit' | 'miss' | 'crit' | 'success' | 'fail'
  timestamp: number
}

export interface CombatLogProps {
  entries: CombatLogEntry[]
  isInCombat: boolean
}

const TYPE_ICONS: Record<CombatLogEntry['type'], string> = {
  attack: '⚔️',
  damage: '💥',
  save: '🛡️',
  spell: '🔮',
  condition: '⚡',
  defeat: '💀',
  round: '',
}

function resultClass(result?: CombatLogEntry['result']): string {
  if (!result) return ''
  switch (result) {
    case 'hit':
    case 'success':
      return 'combat-log-hit'
    case 'miss':
    case 'fail':
      return 'combat-log-miss'
    case 'crit':
      return 'combat-log-crit'
    default:
      return ''
  }
}

export function CombatLog({ entries, isInCombat }: CombatLogProps) {
  const [collapsed, setCollapsed] = useState(!isInCombat)
  const scrollRef = useRef<HTMLDivElement>(null)
  const prevCountRef = useRef(entries.length)

  // Auto-expand when combat starts
  useEffect(() => {
    if (isInCombat) setCollapsed(false)
  }, [isInCombat])

  // Auto-scroll to bottom when new entries arrive
  useEffect(() => {
    if (entries.length > prevCountRef.current && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
    prevCountRef.current = entries.length
  }, [entries.length])

  return (
    <div className="combat-log">
      <button
        className="combat-log-header"
        onClick={() => setCollapsed((v) => !v)}
        aria-expanded={!collapsed}
      >
        <span className="combat-log-title">⚔️ Combat Log</span>
        <span className="combat-log-count">
          {entries.length > 0 ? `(${entries.length} ${entries.length === 1 ? 'entry' : 'entries'})` : ''}
        </span>
        <span className={`sidebar-chevron ${collapsed ? 'collapsed' : ''}`}>▾</span>
      </button>

      {!collapsed && (
        <div className="combat-log-body" ref={scrollRef}>
          {!isInCombat && entries.length === 0 ? (
            <div className="combat-log-empty">No combat active</div>
          ) : entries.length === 0 ? (
            <div className="combat-log-empty">Awaiting first action…</div>
          ) : (
            entries.map((entry) => (
              <CombatLogRow key={entry.id} entry={entry} />
            ))
          )}
        </div>
      )}
    </div>
  )
}

function CombatLogRow({ entry }: { entry: CombatLogEntry }) {
  if (entry.type === 'round') {
    return (
      <div className="combat-log-round combat-log-entry-anim">
        <span className="combat-log-round-text">{entry.text}</span>
      </div>
    )
  }

  const icon = TYPE_ICONS[entry.type]
  const typeClass = `combat-log-type-${entry.type}`
  const resClass = resultClass(entry.result)

  return (
    <div className={`combat-log-entry combat-log-entry-anim ${typeClass} ${resClass}`}>
      <span className="combat-log-icon">{icon}</span>
      <div className="combat-log-content">
        <span className="combat-log-text">{entry.text}</span>
        {entry.details && <span className="combat-log-details">{entry.details}</span>}
      </div>
    </div>
  )
}
