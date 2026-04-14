import { useMemo } from 'react'

export type SceneType = 'tavern' | 'dungeon' | 'forest' | 'cave' | 'castle' | 'battlefield'

interface MiniMapProps {
  sceneType: SceneType
  className?: string
}

/**
 * CSS-art mini-map showing party location.
 * Small 150x150px panel with abstract layout based on scene type.
 * Pulsing gold dot shows current position.
 */
export function MiniMap({ sceneType, className = '' }: MiniMapProps) {
  // Generate a stable unique class suffix for CSS specificity
  const mapLayoutClass = useMemo(() => {
    const layouts: Record<SceneType, string> = {
      tavern: 'mini-map-tavern',
      dungeon: 'mini-map-dungeon',
      forest: 'mini-map-forest',
      cave: 'mini-map-cave',
      castle: 'mini-map-castle',
      battlefield: 'mini-map-battlefield',
    }
    return layouts[sceneType]
  }, [sceneType])

  return (
    <div className={`mini-map ${mapLayoutClass} ${className}`}>
      {/* Grid background */}
      <div className="mini-map-grid" />

      {/* Scene-specific layout elements are drawn via CSS */}
      <div className="mini-map-layout" />

      {/* Current position indicator - pulsing gold dot */}
      <div className="mini-map-position" />

      {/* Optional scene label */}
      <div className="mini-map-label">
        {sceneType.charAt(0).toUpperCase() + sceneType.slice(1)}
      </div>
    </div>
  )
}
