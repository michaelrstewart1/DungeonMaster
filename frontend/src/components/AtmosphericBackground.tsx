import { useMemo } from 'react'

export type Atmosphere = 'dark' | 'warm' | 'peaceful' | 'combat' | 'mystical' | 'neutral'
export type Lighting = 'bright' | 'dim' | 'dark' | 'magical' | 'fire'

interface AtmosphericBackgroundProps {
  atmosphere: Atmosphere
  lighting?: Lighting
}

interface ParticleConfig {
  count: number
  className: string
  content?: string
}

function seededRandom(seed: number): number {
  const x = Math.sin(seed * 9301 + 49297) * 49271
  return x - Math.floor(x)
}

function generateParticles(config: ParticleConfig, atmosphere: string): React.ReactElement[] {
  const particles: React.ReactElement[] = []
  for (let i = 0; i < config.count; i++) {
    const left = seededRandom(i * 7 + 1) * 100
    const delay = seededRandom(i * 13 + 3) * 8
    const duration = 6 + seededRandom(i * 17 + 5) * 10
    const size = 2 + seededRandom(i * 23 + 7) * 4

    const style: React.CSSProperties = {
      left: `${left}%`,
      animationDelay: `${delay}s`,
      animationDuration: `${duration}s`,
      width: `${size}px`,
      height: `${size}px`,
    }

    particles.push(
      <div
        key={`${atmosphere}-${config.className}-${i}`}
        className={`atmo-particle ${config.className}`}
        style={style}
      >
        {config.content || ''}
      </div>
    )
  }
  return particles
}

const RUNE_SYMBOLS = ['ᚠ', 'ᚢ', 'ᚦ', 'ᚨ', 'ᚱ', 'ᚲ']

function RuneParticles(): React.ReactElement {
  const runes: React.ReactElement[] = []
  for (let i = 0; i < 12; i++) {
    const left = seededRandom(i * 11 + 2) * 100
    const delay = seededRandom(i * 19 + 4) * 10
    const duration = 10 + seededRandom(i * 29 + 6) * 12
    const symbol = RUNE_SYMBOLS[i % RUNE_SYMBOLS.length]

    runes.push(
      <div
        key={`rune-${i}`}
        className="atmo-particle atmo-rune"
        style={{
          left: `${left}%`,
          animationDelay: `${delay}s`,
          animationDuration: `${duration}s`,
        }}
      >
        {symbol}
      </div>
    )
  }
  return <>{runes}</>
}

function getParticleConfigs(atmosphere: Atmosphere): ParticleConfig[] {
  switch (atmosphere) {
    case 'dark':
      return [
        { count: 15, className: 'atmo-drip' },
        { count: 8, className: 'atmo-dust' },
      ]
    case 'warm':
      return [
        { count: 20, className: 'atmo-ember' },
        { count: 6, className: 'atmo-spark' },
      ]
    case 'peaceful':
      return [
        { count: 12, className: 'atmo-leaf' },
        { count: 10, className: 'atmo-dapple' },
      ]
    case 'combat':
      return [
        { count: 18, className: 'atmo-combat-spark' },
        { count: 8, className: 'atmo-ash' },
      ]
    case 'mystical':
      return [
        { count: 18, className: 'atmo-sparkle' },
      ]
    case 'neutral':
    default:
      return [
        { count: 8, className: 'atmo-dust' },
      ]
  }
}

function getLightingOpacity(lighting?: Lighting): number {
  switch (lighting) {
    case 'bright': return 0.15
    case 'dim': return 0.6
    case 'dark': return 0.8
    case 'magical': return 0.3
    case 'fire': return 0.4
    default: return 0.5
  }
}

export function AtmosphericBackground({ atmosphere, lighting }: AtmosphericBackgroundProps) {
  const particles = useMemo(() => {
    const configs = getParticleConfigs(atmosphere)
    return configs.flatMap(c => generateParticles(c, atmosphere))
  }, [atmosphere])

  const darknessOpacity = getLightingOpacity(lighting)

  return (
    <div className={`atmo-bg atmo-${atmosphere}`} aria-hidden="true">
      <div className="atmo-gradient" />
      <div className="atmo-overlay" />
      <div className="atmo-darkness" style={{ opacity: darknessOpacity }} />
      <div className="atmo-particles">
        {particles}
        {atmosphere === 'mystical' && <RuneParticles />}
      </div>
      {atmosphere === 'combat' && <div className="atmo-vignette" />}
      {atmosphere === 'mystical' && <div className="atmo-glow" />}
      {atmosphere === 'warm' && <div className="atmo-firelight" />}
      {atmosphere === 'dark' && <div className="atmo-fog" />}
      {atmosphere === 'peaceful' && <div className="atmo-mist" />}
    </div>
  )
}
