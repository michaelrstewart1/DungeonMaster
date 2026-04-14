import { useEffect, useRef, useMemo } from 'react'

export type EffectType = 'shake' | 'nat20' | 'damage' | 'spell' | 'levelup' | 'boss' | null

interface ScreenEffectsProps {
  activeEffect: EffectType
  onEffectComplete?: () => void
  showAmbientParticles?: boolean
}

const EFFECT_DURATIONS: Record<string, number> = {
  shake: 500,
  nat20: 800,
  damage: 600,
  spell: 1500,
  levelup: 2000,
  boss: 3000,
}

interface AmbientParticle {
  id: number
  left: string
  animDelay: string
  animDuration: string
  size: string
  opacity: number
}

export function ScreenEffects({
  activeEffect,
  onEffectComplete,
  showAmbientParticles = true,
}: ScreenEffectsProps) {
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current)
      timerRef.current = null
    }

    if (activeEffect && onEffectComplete) {
      const duration = EFFECT_DURATIONS[activeEffect] ?? 1000
      timerRef.current = setTimeout(() => {
        onEffectComplete()
        timerRef.current = null
      }, duration)
    }

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [activeEffect, onEffectComplete])

  // Apply shake class to game-session container
  useEffect(() => {
    if (activeEffect === 'shake') {
      const el = document.querySelector('.game-session')
      if (el) {
        el.classList.add('screen-shake-active')
        const timeout = setTimeout(() => el.classList.remove('screen-shake-active'), 500)
        return () => {
          clearTimeout(timeout)
          el.classList.remove('screen-shake-active')
        }
      }
    }
  }, [activeEffect])

  // Stable ambient particle definitions
  const ambientParticles = useMemo<AmbientParticle[]>(() => {
    const particles: AmbientParticle[] = []
    for (let i = 0; i < 18; i++) {
      particles.push({
        id: i,
        left: `${(i * 5.5 + 1.5) % 100}%`,
        animDelay: `${(i * 1.3) % 8}s`,
        animDuration: `${6 + (i % 5) * 2}s`,
        size: `${1.5 + (i % 3)}px`,
        opacity: 0.15 + (i % 4) * 0.08,
      })
    }
    return particles
  }, [])

  // Sparkle particles for spell effect
  const sparkleParticles = useMemo(() => {
    const particles: { id: number; left: string; delay: string; duration: string }[] = []
    for (let i = 0; i < 24; i++) {
      particles.push({
        id: i,
        left: `${(i * 4.2 + 2) % 100}%`,
        delay: `${(i * 0.06)}s`,
        duration: `${0.8 + (i % 4) * 0.2}s`,
      })
    }
    return particles
  }, [])

  // Level up rising particles
  const levelUpParticles = useMemo(() => {
    const particles: { id: number; left: string; delay: string }[] = []
    for (let i = 0; i < 20; i++) {
      particles.push({
        id: i,
        left: `${(i * 5 + 2.5) % 100}%`,
        delay: `${(i * 0.08)}s`,
      })
    }
    return particles
  }, [])

  return (
    <>
      {/* Gold Flash — Natural 20 */}
      {activeEffect === 'nat20' && (
        <div className="sfx-overlay sfx-nat20" aria-hidden="true" />
      )}

      {/* Red Damage Pulse */}
      {activeEffect === 'damage' && (
        <div className="sfx-overlay sfx-damage" aria-hidden="true" />
      )}

      {/* Magical Sparkle */}
      {activeEffect === 'spell' && (
        <div className="sfx-overlay sfx-spell" aria-hidden="true">
          {sparkleParticles.map((p) => (
            <span
              key={p.id}
              className="sfx-sparkle-dot"
              style={{
                left: p.left,
                animationDelay: p.delay,
                animationDuration: p.duration,
              }}
            />
          ))}
        </div>
      )}

      {/* Level Up Celebration */}
      {activeEffect === 'levelup' && (
        <div className="sfx-overlay sfx-levelup" aria-hidden="true">
          <span className="sfx-levelup-text">LEVEL UP!</span>
          {levelUpParticles.map((p) => (
            <span
              key={p.id}
              className="sfx-levelup-particle"
              style={{ left: p.left, animationDelay: p.delay }}
            />
          ))}
        </div>
      )}

      {/* Boss Encounter */}
      {activeEffect === 'boss' && (
        <div className="sfx-overlay sfx-boss" aria-hidden="true">
          <div className="sfx-boss-crack sfx-boss-crack-left" />
          <div className="sfx-boss-crack sfx-boss-crack-right" />
          <span className="sfx-boss-text">A DARK PRESENCE APPROACHES...</span>
        </div>
      )}

      {/* Ambient Particles — always-on subtle gold dust */}
      {showAmbientParticles && (
        <div className="sfx-ambient" aria-hidden="true">
          {ambientParticles.map((p) => (
            <span
              key={p.id}
              className="sfx-ambient-mote"
              style={{
                left: p.left,
                animationDelay: p.animDelay,
                animationDuration: p.animDuration,
                width: p.size,
                height: p.size,
                opacity: p.opacity,
              }}
            />
          ))}
        </div>
      )}
    </>
  )
}
