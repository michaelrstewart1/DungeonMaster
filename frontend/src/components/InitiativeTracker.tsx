import { useState, useEffect } from 'react'

export interface CombatantDisplay {
  id: string
  name: string
  initiative: number
  hp: number
  max_hp: number
  is_current: boolean
}

interface InitiativeTrackerProps {
  combatants: CombatantDisplay[]
}

export function InitiativeTracker({ combatants }: InitiativeTrackerProps) {
  const hasCombat = combatants.length > 0
  const [collapsed, setCollapsed] = useState(!hasCombat)

  // Auto-expand when combat starts, auto-collapse when it ends
  useEffect(() => {
    setCollapsed(!hasCombat)
  }, [hasCombat])

  return (
    <div className={`initiative-tracker ${!hasCombat ? 'empty' : ''}`}>
      <div
        className="initiative-header"
        onClick={() => setCollapsed(c => !c)}
        role="button"
        tabIndex={0}
      >
        <span className="initiative-header-title">⚔️ {hasCombat ? 'Initiative Order' : 'Initiative'}</span>
        <span className={`sidebar-chevron ${collapsed ? 'collapsed' : ''}`}>▾</span>
      </div>
      {!collapsed && (
        !hasCombat ? (
          <p className="initiative-empty-text">No combat active</p>
        ) : (
          <div className="initiative-list">
            {combatants.map((c) => {
              const hpPercent = Math.round((c.hp / c.max_hp) * 100)
              const hpColor = hpPercent > 50 ? 'hp-healthy' : hpPercent > 25 ? 'hp-wounded' : 'hp-critical'
              return (
                <div
                  key={c.id}
                  className={`initiative-row ${c.is_current ? 'current-turn' : ''}`}
                >
                  <span className="init-value">{c.initiative}</span>
                  <span className="init-name">{c.name}</span>
                  <span className="init-hp">
                    <span className="hp-text">{c.hp}/{c.max_hp}</span>
                    <div className={`hp-bar ${hpColor}`} style={{ width: `${hpPercent}%` }} />
                  </span>
                </div>
              )
            })}
          </div>
        )
      )}
    </div>
  )
}
