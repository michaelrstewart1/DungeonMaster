import { useState } from 'react'
import type { WorldLocation } from '../types'
import './WorldMapPanel.css'

const SCENE_ICONS: Record<string, string> = {
  village: '🏘️',
  town: '🏘️',
  city: '🏰',
  tavern: '🍺',
  forest: '🌲',
  mountain: '⛰️',
  cave: '🕳️',
  dungeon: '💀',
  ruins: '🏛️',
  temple: '🏛️',
  swamp: '🐸',
  coast: '🌊',
  road: '🛤️',
}

interface WorldMapPanelProps {
  isOpen: boolean
  onClose: () => void
  locations: WorldLocation[]
  currentLocationId: string | null | undefined
  inCombat: boolean
  onTravel: (destinationId: string) => Promise<void>
}

export function WorldMapPanel({ isOpen, onClose, locations, currentLocationId, inCombat, onTravel }: WorldMapPanelProps) {
  const [traveling, setTraveling] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  if (!isOpen) return null

  const current = locations.find(l => l.id === currentLocationId)
  const connectedIds = new Set(current?.connections ?? [])

  const handleTravel = async (destId: string) => {
    setTraveling(destId)
    setError(null)
    try {
      await onTravel(destId)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Travel failed')
    } finally {
      setTraveling(null)
    }
  }

  const visible = locations.filter(l => l.discovered || l.visited)
  const hiddenCount = locations.length - visible.length

  return (
    <div className="world-map-overlay" onClick={onClose}>
      <div className="world-map-panel" onClick={e => e.stopPropagation()}>
        <div className="world-map-header">
          <h2>🗺️ World Map</h2>
          <button className="world-map-close" onClick={onClose} title="Close">✕</button>
        </div>

        {inCombat && <div className="world-map-notice">⚔️ The party cannot travel during combat.</div>}
        {error && <div className="world-map-error">{error}</div>}

        <div className="world-map-locations">
          {visible.map(loc => {
            const isCurrent = loc.id === currentLocationId
            const reachable = connectedIds.has(loc.id) && !isCurrent
            return (
              <div
                key={loc.id}
                className={`world-map-location${isCurrent ? ' current' : ''}${reachable ? ' reachable' : ''}`}
              >
                <div className="world-map-location-icon">
                  {SCENE_ICONS[loc.scene_type ?? ''] ?? '📍'}
                </div>
                <div className="world-map-location-body">
                  <div className="world-map-location-name">
                    {loc.name}
                    {isCurrent && <span className="world-map-badge current-badge">You are here</span>}
                    {!isCurrent && loc.visited && <span className="world-map-badge visited-badge">Visited</span>}
                  </div>
                  <div className="world-map-location-desc">
                    {loc.visited || reachable ? loc.description : 'You have heard rumors of this place…'}
                  </div>
                </div>
                {reachable && (
                  <button
                    className="world-map-travel-btn"
                    disabled={inCombat || traveling !== null}
                    onClick={() => handleTravel(loc.id)}
                  >
                    {traveling === loc.id ? '🐎 …' : '🐎 Travel'}
                  </button>
                )}
              </div>
            )
          })}
          {hiddenCount > 0 && (
            <div className="world-map-hidden-hint">
              🌫️ {hiddenCount} undiscovered location{hiddenCount > 1 ? 's' : ''} await{hiddenCount === 1 ? 's' : ''} beyond the known paths…
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
