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
  if (combatants.length === 0) {
    return <div className="initiative-tracker empty">No combat active</div>
  }

  return (
    <div className="initiative-tracker">
      <h3>Initiative Order</h3>
      <div className="initiative-list">
        {combatants.map((c) => {
          const hpPercent = Math.round((c.hp / c.max_hp) * 100)
          return (
            <div
              key={c.id}
              className={`initiative-row ${c.is_current ? 'current-turn' : ''}`}
            >
              <span className="init-value">{c.initiative}</span>
              <span className="init-name">{c.name}</span>
              <span className="init-hp">
                <span className="hp-text">{c.hp}/{c.max_hp}</span>
                <div className="hp-bar" style={{ width: `${hpPercent}%` }} />
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
