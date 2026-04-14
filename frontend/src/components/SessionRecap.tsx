import { useState, useEffect, useCallback, useMemo } from 'react'

export interface SessionRecapProps {
  campaignName: string
  recapText: string
  onContinue: () => void
}

/** Split recap text into individual dramatic sentences (max 6). */
function splitRecapSentences(text: string): string[] {
  const raw = text
    .split(/(?<=[.!?])\s+/)
    .map(s => s.trim())
    .filter(s => s.length > 10)
  return raw.slice(0, 6)
}

export function SessionRecap({ campaignName, recapText, onContinue }: SessionRecapProps) {
  const [phase, setPhase] = useState<'title' | 'events' | 'ready'>('title')
  const [visibleEvents, setVisibleEvents] = useState(0)
  const [skipped, setSkipped] = useState(false)

  const events = useMemo(() => splitRecapSentences(recapText), [recapText])

  // Animation sequencer
  useEffect(() => {
    if (skipped) return

    // 1s: show title → 2.5s: start showing events
    const titleTimer = setTimeout(() => setPhase('events'), 2500)

    return () => clearTimeout(titleTimer)
  }, [skipped])

  // Stagger event reveals
  useEffect(() => {
    if (phase !== 'events' || skipped) return
    if (visibleEvents >= events.length) {
      // All events shown → pause then show Continue button
      const readyTimer = setTimeout(() => setPhase('ready'), 1500)
      return () => clearTimeout(readyTimer)
    }
    const eventTimer = setTimeout(
      () => setVisibleEvents(v => v + 1),
      visibleEvents === 0 ? 200 : 1000,
    )
    return () => clearTimeout(eventTimer)
  }, [phase, visibleEvents, events.length, skipped])

  const handleSkip = useCallback(() => {
    setSkipped(true)
    setPhase('ready')
    setVisibleEvents(events.length)
  }, [events.length])

  return (
    <div className="recap-overlay" data-testid="session-recap">
      {/* Atmospheric glow */}
      <div className="recap-glow" />

      {/* Title */}
      <div className={`recap-title ${phase !== 'title' || skipped ? 'recap-visible' : ''}`}>
        Previously, on <em>{campaignName}</em>&hellip;
      </div>

      {/* Events list */}
      <div className="recap-events">
        {events.map((event, i) => (
          <p
            key={i}
            className={`recap-event ${i < visibleEvents ? 'recap-event-visible' : ''}`}
          >
            {event}
          </p>
        ))}
      </div>

      {/* Continue button */}
      {phase === 'ready' && (
        <button
          className="recap-continue"
          onClick={onContinue}
          data-testid="recap-continue"
        >
          Continue Your Adventure
        </button>
      )}

      {/* Skip button (always visible) */}
      {phase !== 'ready' && (
        <button
          className="recap-skip"
          onClick={handleSkip}
          data-testid="recap-skip"
        >
          Skip ⏭
        </button>
      )}
    </div>
  )
}
