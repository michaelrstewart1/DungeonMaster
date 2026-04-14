import type { Character } from '../types'

const CLASS_ICONS: Record<string, string> = {
  barbarian: '⚔️',
  bard: '🎵',
  cleric: '✝️',
  druid: '🌿',
  fighter: '🗡️',
  monk: '👊',
  paladin: '🛡️',
  ranger: '🏹',
  rogue: '🗡️',
  sorcerer: '🔮',
  warlock: '👁️',
  wizard: '🧙',
}

const CONDITION_COLORS: Record<string, string> = {
  poisoned: '#6b8e23',
  stunned: '#daa520',
  blinded: '#555',
  frightened: '#8b008b',
  charmed: '#ff69b4',
  paralyzed: '#4682b4',
  prone: '#cd853f',
  restrained: '#a0522d',
  unconscious: '#333',
  exhaustion: '#8b0000',
}

function getHpColor(hp: number, maxHp: number): string {
  const ratio = maxHp > 0 ? hp / maxHp : 0
  if (ratio > 0.5) return '#4caf50'
  if (ratio > 0.25) return '#ff9800'
  return '#f44336'
}

function getConditionColor(condition: string): string {
  return CONDITION_COLORS[condition.toLowerCase()] || '#888'
}

interface PartyStatusProps {
  characters: Character[]
}

export function PartyStatus({ characters }: PartyStatusProps) {
  if (characters.length === 0) return null

  return (
    <div className="party-status">
      <h3 className="party-status-title">⚔ Party</h3>
      <div className="party-member-list">
        {characters.map((char) => {
          const hpPercent = (char.max_hp ?? 0) > 0 ? Math.max(0, Math.min(100, (char.hp / (char.max_hp ?? 1)) * 100)) : 0
          const hpColor = getHpColor(char.hp, char.max_hp ?? 0)
          const classIcon = CLASS_ICONS[char.class_name] || '⚔️'

          return (
            <div key={char.id} className="party-member-card">
              <div className="party-member-portrait">
                {char.portrait_url ? (
                  <img
                    src={char.portrait_url}
                    alt={char.name}
                    className="party-member-img"
                  />
                ) : (
                  <span className="party-member-placeholder">{char.name[0]?.toUpperCase()}</span>
                )}
              </div>
              <div className="party-member-info">
                <div className="party-member-name-row">
                  <span className="party-member-name">{char.name}</span>
                  <span className="party-member-class" title={char.class_name}>{classIcon}</span>
                </div>
                <div className="party-member-hp-bar" title={`${char.hp}/${char.max_hp} HP`}>
                  <div
                    className="party-member-hp-fill"
                    style={{ width: `${hpPercent}%`, backgroundColor: hpColor }}
                  />
                </div>
                {char.conditions.length > 0 && (
                  <div className="party-member-conditions">
                    {char.conditions.map((cond) => (
                      <span
                        key={cond}
                        className="condition-badge"
                        style={{ backgroundColor: getConditionColor(cond) }}
                      >
                        {cond}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
