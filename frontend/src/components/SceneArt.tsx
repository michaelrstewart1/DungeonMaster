import { useMemo, useState, useCallback } from 'react'

export type SceneType = 'tavern' | 'dungeon' | 'forest' | 'cave' | 'castle' | 'battlefield'
  | 'temple' | 'market' | 'ship' | 'mountain' | 'swamp' | 'desert' | 'village' | 'camp' | 'road'

interface SceneArtProps {
  sceneType?: SceneType | string
  /** AI-generated background image URL — fades in over the procedural CSS art */
  backgroundImageUrl?: string
  /** When true, renders only the generated image (no CSS art), used for full-screen bg */
  imageOnly?: boolean
}

/**
 * Detects the scene type from DM narration text
 * Analyzes keywords to determine the appropriate atmospheric backdrop
 */
export function detectScene(text: string): SceneType | string {
  const lowerText = text.toLowerCase()

  // Tavern keywords
  if (
    lowerText.match(/tavern|inn|bar|ale|mead|fireplace|cozy|warm|hearth|flagon|patrons|barkeep|wench|table|drinks?|gather/i)
  ) {
    return 'tavern'
  }

  // Dungeon keywords
  if (
    lowerText.match(/dungeon|cell|prison|chain|torch|stone wall|dripping|damp|underground|chamber|trap|gate|guard|captive/i)
  ) {
    return 'dungeon'
  }

  // Forest keywords
  if (
    lowerText.match(/forest|woods?|tree|clearing|moonlight|night air|undergrowth|path|ancient|glade|fireflies?|owl|whisper|branch/i)
  ) {
    return 'forest'
  }

  // Cave keywords
  if (
    lowerText.match(/cave|cavern|stalactite|crystal|underground|rock|formation|glow|darkness|tunnel|entrance|abyss|echo/i)
  ) {
    return 'cave'
  }

  // Castle keywords
  if (
    lowerText.match(/castle|hall|throne|grand|pillar|banner|stained glass|corridor|royal|palace|tapestry|archway|splendor/i)
  ) {
    return 'castle'
  }

  // Battlefield keywords
  if (
    lowerText.match(/battlefield|battle|fight|combat|sword|blood|ground|smoke|mist|dust|fallen|smoke|crater|destruction|war/i)
  ) {
    return 'battlefield'
  }

  // Default to tavern if no match
  return 'tavern'
}

function TavernScene() {
  return (
    <div className="scene-art scene-tavern">
      {/* Wooden beams */}
      <div className="tavern-beam tavern-beam-1" />
      <div className="tavern-beam tavern-beam-2" />
      <div className="tavern-beam tavern-beam-3" />

      {/* Arched window with moonlight */}
      <div className="tavern-window">
        <div className="tavern-window-arch" />
        <div className="tavern-window-pane" />
        <div className="tavern-window-light" />
      </div>

      {/* Candles */}
      <div className="tavern-candle tavern-candle-1">
        <div className="tavern-flame tavern-flame-1" />
      </div>
      <div className="tavern-candle tavern-candle-2">
        <div className="tavern-flame tavern-flame-2" />
      </div>
      <div className="tavern-candle tavern-candle-3">
        <div className="tavern-flame tavern-flame-3" />
      </div>

      {/* Fireplace glow */}
      <div className="tavern-fireplace-glow" />

      {/* Ambient particles (embers) */}
      <div className="scene-particles">
        {[...Array(8)].map((_, i) => (
          <div key={`tavern-ember-${i}`} className="scene-ember" style={{ '--delay': `${i * 0.2}s` } as React.CSSProperties} />
        ))}
      </div>
    </div>
  )
}

function DungeonScene() {
  return (
    <div className="scene-art scene-dungeon">
      {/* Stone walls */}
      <div className="dungeon-wall dungeon-wall-left" />
      <div className="dungeon-wall dungeon-wall-right" />
      <div className="dungeon-wall dungeon-wall-back" />

      {/* Torch on wall */}
      <div className="dungeon-torch">
        <div className="dungeon-torch-holder" />
        <div className="dungeon-torch-flame dungeon-torch-flame-1" />
        <div className="dungeon-torch-glow" />
      </div>

      {/* Torch #2 */}
      <div className="dungeon-torch dungeon-torch-2">
        <div className="dungeon-torch-holder" />
        <div className="dungeon-torch-flame dungeon-torch-flame-2" />
        <div className="dungeon-torch-glow" />
      </div>

      {/* Dripping water effect */}
      <div className="dungeon-drips">
        {[...Array(5)].map((_, i) => (
          <div key={`drip-${i}`} className="dungeon-drip" style={{ '--drip-delay': `${i * 0.6}s` } as React.CSSProperties} />
        ))}
      </div>

      {/* Chains */}
      <div className="dungeon-chain dungeon-chain-1" />
      <div className="dungeon-chain dungeon-chain-2" />

      {/* Fog/Mist */}
      <div className="dungeon-mist" />
    </div>
  )
}

function ForestScene() {
  return (
    <div className="scene-art scene-forest">
      {/* Trees - silhouettes */}
      <div className="forest-tree forest-tree-1" />
      <div className="forest-tree forest-tree-2" />
      <div className="forest-tree forest-tree-3" />
      <div className="forest-tree forest-tree-4" />

      {/* Distant trees (smaller, lighter) */}
      <div className="forest-tree-far forest-tree-far-1" />
      <div className="forest-tree-far forest-tree-far-2" />

      {/* Moon */}
      <div className="forest-moon" />

      {/* Moonlight rays */}
      <div className="forest-light-ray forest-light-ray-1" />
      <div className="forest-light-ray forest-light-ray-2" />

      {/* Floating fireflies */}
      <div className="scene-particles">
        {[...Array(12)].map((_, i) => (
          <div key={`firefly-${i}`} className="scene-firefly" style={{ '--firefly-delay': `${i * 0.3}s` } as React.CSSProperties} />
        ))}
      </div>

      {/* Ground/Undergrowth */}
      <div className="forest-ground" />
    </div>
  )
}

function CaveScene() {
  return (
    <div className="scene-art scene-cave">
      {/* Cave entrance walls */}
      <div className="cave-wall-left" />
      <div className="cave-wall-right" />

      {/* Stalactites */}
      <div className="cave-stalactite cave-stalactite-1" />
      <div className="cave-stalactite cave-stalactite-2" />
      <div className="cave-stalactite cave-stalactite-3" />
      <div className="cave-stalactite cave-stalactite-4" />

      {/* Stalagmites (ground) */}
      <div className="cave-stalagmite cave-stalagmite-1" />
      <div className="cave-stalagmite cave-stalagmite-2" />
      <div className="cave-stalagmite cave-stalagmite-3" />

      {/* Glowing crystals */}
      <div className="cave-crystal cave-crystal-1" />
      <div className="cave-crystal cave-crystal-2" />
      <div className="cave-crystal cave-crystal-3" />
      <div className="cave-crystal cave-crystal-4" />

      {/* Cave depth/darkness */}
      <div className="cave-darkness" />

      {/* Ambient glow */}
      <div className="cave-glow cave-glow-1" />
      <div className="cave-glow cave-glow-2" />

      {/* Fog */}
      <div className="cave-fog" />
    </div>
  )
}

function CastleScene() {
  return (
    <div className="scene-art scene-castle">
      {/* Pillars */}
      <div className="castle-pillar castle-pillar-1" />
      <div className="castle-pillar castle-pillar-2" />
      <div className="castle-pillar castle-pillar-3" />
      <div className="castle-pillar castle-pillar-4" />

      {/* Arches connecting pillars */}
      <div className="castle-arch castle-arch-1" />
      <div className="castle-arch castle-arch-2" />

      {/* Stained glass windows */}
      <div className="castle-window castle-window-1" />
      <div className="castle-window castle-window-2" />
      <div className="castle-window castle-window-3" />

      {/* Banners */}
      <div className="castle-banner castle-banner-1" />
      <div className="castle-banner castle-banner-2" />

      {/* Floor details */}
      <div className="castle-floor" />

      {/* Torches */}
      <div className="castle-torch castle-torch-1">
        <div className="castle-torch-flame" />
      </div>
      <div className="castle-torch castle-torch-2">
        <div className="castle-torch-flame" />
      </div>

      {/* Ambient light rays */}
      <div className="castle-light-ray castle-light-ray-1" />
      <div className="castle-light-ray castle-light-ray-2" />
    </div>
  )
}

function BattlefieldScene() {
  return (
    <div className="scene-art scene-battlefield">
      {/* Broken ground/craters */}
      <div className="battlefield-crater battlefield-crater-1" />
      <div className="battlefield-crater battlefield-crater-2" />
      <div className="battlefield-crater battlefield-crater-3" />

      {/* Crossed swords */}
      <div className="battlefield-sword battlefield-sword-1" />
      <div className="battlefield-sword battlefield-sword-2" />

      {/* Fallen objects */}
      <div className="battlefield-debris battlefield-debris-1" />
      <div className="battlefield-debris battlefield-debris-2" />

      {/* Smoke/mist particles */}
      <div className="scene-particles">
        {[...Array(15)].map((_, i) => (
          <div key={`smoke-${i}`} className="scene-smoke" style={{ '--smoke-delay': `${i * 0.15}s` } as React.CSSProperties} />
        ))}
      </div>

      {/* Blood/Impact marks */}
      <div className="battlefield-mark battlefield-mark-1" />
      <div className="battlefield-mark battlefield-mark-2" />
      <div className="battlefield-mark battlefield-mark-3" />

      {/* Eerie glow */}
      <div className="battlefield-glow" />
    </div>
  )
}

export function SceneArt({ sceneType = 'tavern', backgroundImageUrl, imageOnly }: SceneArtProps) {
  const [imageLoaded, setImageLoaded] = useState(false)
  const [currentImageUrl, setCurrentImageUrl] = useState<string | null>(null)
  const [prevImageUrl, setPrevImageUrl] = useState<string | null>(null)

  // Cross-fade: when new URL arrives, move current to prev, start loading new
  if (backgroundImageUrl && backgroundImageUrl !== currentImageUrl && backgroundImageUrl !== prevImageUrl) {
    if (currentImageUrl) {
      setPrevImageUrl(currentImageUrl)
    }
    setCurrentImageUrl(backgroundImageUrl)
    setImageLoaded(false)
  }

  const handleImageLoad = useCallback(() => {
    setImageLoaded(true)
    // After fade completes, clear the old image
    setTimeout(() => setPrevImageUrl(null), 2500)
  }, [])

  const scene = useMemo(() => {
    const type = sceneType as SceneType
    switch (type) {
      case 'tavern':
        return <TavernScene />
      case 'dungeon':
        return <DungeonScene />
      case 'forest':
        return <ForestScene />
      case 'cave':
        return <CaveScene />
      case 'castle':
        return <CastleScene />
      case 'battlefield':
        return <BattlefieldScene />
      default:
        // For types without CSS art (temple, market, etc.), use tavern as fallback
        return <TavernScene />
    }
  }, [sceneType])

  // Image-only mode: just render the generated image with fade (used for full-screen background)
  if (imageOnly) {
    return (
      <div className="scene-art-container scene-art-image-only" aria-hidden="true">
        {/* Previous image (fading out) */}
        {prevImageUrl && (
          <img
            src={prevImageUrl}
            alt=""
            className="scene-art-bg-image scene-art-bg-prev"
          />
        )}
        {/* Current image (fading in) */}
        {currentImageUrl && (
          <img
            src={currentImageUrl}
            alt=""
            className={`scene-art-bg-image ${imageLoaded ? 'scene-art-bg-visible' : 'scene-art-bg-loading'}`}
            onLoad={handleImageLoad}
          />
        )}
        {/* Dark overlay for text readability */}
        <div className="scene-art-image-overlay" />
      </div>
    )
  }

  return (
    <div className="scene-art-container" aria-hidden="true">
      {/* AI-generated background image layer (behind CSS art) */}
      {prevImageUrl && (
        <img
          src={prevImageUrl}
          alt=""
          className="scene-art-bg-image scene-art-bg-prev"
        />
      )}
      {currentImageUrl && (
        <img
          src={currentImageUrl}
          alt=""
          className={`scene-art-bg-image ${imageLoaded ? 'scene-art-bg-visible' : 'scene-art-bg-loading'}`}
          onLoad={handleImageLoad}
        />
      )}
      {/* CSS procedural art as overlay */}
      <div className={`scene-art-css-layer ${currentImageUrl && imageLoaded ? 'scene-art-css-dimmed' : ''}`}>
        {scene}
      </div>
    </div>
  )
}
