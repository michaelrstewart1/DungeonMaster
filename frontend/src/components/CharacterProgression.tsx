import { useCallback, useEffect, useState } from 'react'
import type { ProgressionData, Milestone } from '../types'
import { getCharacterProgression } from '../api/client'

interface CharacterProgressionProps {
  characterId: string
  level: number
  xp: number
  /** Optional pre-fetched data; if omitted the component fetches its own. */
  progression?: ProgressionData
}

export function CharacterProgression({
  characterId,
  level,
  xp,
  progression: externalData,
}: CharacterProgressionProps) {
  const [data, setData] = useState<ProgressionData | null>(externalData ?? null)
  const [levelUpVisible, setLevelUpVisible] = useState(false)
  const [prevLevel, setPrevLevel] = useState(level)

  // Detect level-up to trigger animation
  useEffect(() => {
    if (level > prevLevel) {
      setLevelUpVisible(true)
      const timer = setTimeout(() => setLevelUpVisible(false), 2400)
      return () => clearTimeout(timer)
    }
    setPrevLevel(level)
  }, [level, prevLevel])

  const fetchProgression = useCallback(async () => {
    try {
      const result = await getCharacterProgression(characterId)
      setData(result)
    } catch {
      // Silently degrade — progression display is optional
    }
  }, [characterId])

  // Fetch on mount or when xp/level changes (unless data was passed in)
  useEffect(() => {
    if (externalData) {
      setData(externalData)
    } else {
      void fetchProgression()
    }
  }, [externalData, fetchProgression, xp, level])

  if (!data) return null

  const isMaxLevel = level >= 20

  return (
    <div className={`xp-progression${levelUpVisible ? ' xp-level-up-active' : ''}`}>
      {/* Level-up overlay */}
      {levelUpVisible && (
        <div className="xp-level-up-overlay">
          <span className="xp-level-up-text">LEVEL UP!</span>
          <span className="xp-level-up-number">{level}</span>
          <div className="xp-particles">
            {Array.from({ length: 12 }).map((_, i) => (
              <span key={i} className="xp-particle" style={{ '--i': i } as React.CSSProperties} />
            ))}
          </div>
        </div>
      )}

      {/* XP bar */}
      <div className="xp-bar-container">
        <div className="xp-bar-labels">
          <span className="xp-bar-level">Level {level}</span>
          <span className="xp-bar-xp">
            {isMaxLevel
              ? `${data.xp.toLocaleString()} XP — Max Level`
              : `${data.xp.toLocaleString()} / ${(data.xp + data.xp_to_next).toLocaleString()} XP`}
          </span>
        </div>
        <div className="xp-bar-track">
          <div
            className="xp-bar-fill"
            style={{ width: `${data.xp_progress_pct}%` }}
          />
          <div className="xp-bar-shimmer" />
        </div>
      </div>

      {/* Milestone tracker */}
      <div className="xp-milestones">
        {data.milestones.map((m: Milestone) => (
          <div
            key={m.level}
            className={`xp-milestone${m.reached ? ' reached' : ''}`}
            title={`Lvl ${m.level}: ${m.label}`}
          >
            <span className="xp-milestone-dot" />
            <span className="xp-milestone-label">
              {m.level}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
