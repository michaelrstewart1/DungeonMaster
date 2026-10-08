import { useState, useEffect } from 'react'
import { getEnvironment } from '../api/client'
import './WeatherOverlay.css'

interface WeatherOverlayProps {
  sessionId: string
  /** scene = over the top scene art panel; chat = behind the dialog log */
  variant: 'scene' | 'chat'
}

/** Ambient rain/snow/storm/wind background layer, reusing the same
 * DOM-element falling-effect technique as EnvironmentPanel but scaled
 * up to cover a much larger container. */
export function WeatherOverlay({ sessionId, variant }: WeatherOverlayProps) {
  const [weather, setWeather] = useState<string | null>(null)

  useEffect(() => {
    if (!sessionId) return
    let cancelled = false

    const fetchWeather = async () => {
      try {
        const env = await getEnvironment(sessionId)
        if (!cancelled) setWeather(env.weather)
      } catch {
        // Purely decorative — ignore fetch failures.
      }
    }

    fetchWeather()
    const interval = setInterval(fetchWeather, 30000)
    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [sessionId])

  if (!weather || !['rain', 'snow', 'storm', 'wind'].includes(weather)) {
    return null
  }

  return (
    <div className={`weather-overlay weather-overlay-${variant}`} aria-hidden="true">
      {weather === 'rain' && (
        <div className="wx-rain">
          {Array.from({ length: 20 }, (_, i) => <i key={i} />)}
        </div>
      )}
      {weather === 'snow' && (
        <div className="wx-snow">
          {['❄', '•', '❅', '•', '❆', '•', '❄', '•', '❅', '•', '❆', '•'].map((glyph, i) => (
            <i key={i}>{glyph}</i>
          ))}
        </div>
      )}
      {weather === 'storm' && (
        <div className="wx-storm">
          {Array.from({ length: 24 }, (_, i) => <i key={i} />)}
        </div>
      )}
      {weather === 'wind' && (
        <div className="wx-wind">
          {Array.from({ length: 7 }, (_, i) => <i key={i} />)}
          <span>🍃</span>
          <span>🍂</span>
        </div>
      )}
    </div>
  )
}
