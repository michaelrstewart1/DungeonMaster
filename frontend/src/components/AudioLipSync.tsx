/**
 * Audio-driven lip sync component
 * Uses Web Audio API to analyze audio amplitude and drive avatar mouth animation
 */
import { useState, useEffect, useRef, useCallback } from 'react'

interface UseAudioAnalyserReturn {
  amplitude: number
  isSpeaking: boolean
}

/**
 * Hook to analyze audio and track amplitude and speaking state
 * @param audioContext - Web Audio API context, or null to disable
 * @param speakingThreshold - Amplitude threshold to consider speaking (default 0.1)
 * @returns Object with current amplitude (0-1) and isSpeaking boolean
 */
export function useAudioAnalyser(
  audioContext: AudioContext | null,
  speakingThreshold: number = 0.1
): UseAudioAnalyserReturn {
  const [amplitude, setAmplitude] = useState(0)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const animationIdRef = useRef<number | null>(null)
  const dataArrayRef = useRef<Uint8Array<ArrayBuffer> | null>(null)

  // Initialize analyser on mount
  useEffect(() => {
    if (!audioContext) {
      setAmplitude(0)
      setIsSpeaking(false)
      return
    }

    try {
      const analyser = audioContext.createAnalyser()
      analyser.fftSize = 256
      analyserRef.current = analyser
      dataArrayRef.current = new Uint8Array(analyser.frequencyBinCount)
    } catch (error) {
      console.error('Failed to create analyser:', error)
      setAmplitude(0)
      setIsSpeaking(false)
    }

    return () => {
      if (animationIdRef.current) {
        cancelAnimationFrame(animationIdRef.current)
      }
    }
  }, [audioContext])

  // Update amplitude continuously
  const updateAmplitude = useCallback(() => {
    if (!analyserRef.current || !dataArrayRef.current) {
      setAmplitude(0)
      setIsSpeaking(false)
      return
    }

    try {
      analyserRef.current.getByteFrequencyData(dataArrayRef.current)

      // Calculate average amplitude from frequency data
      let sum = 0
      for (let i = 0; i < dataArrayRef.current.length; i++) {
        sum += dataArrayRef.current[i]
      }
      const average = sum / dataArrayRef.current.length

      // Normalize to 0-1 range (255 is max byte value)
      const normalizedAmplitude = average / 255

      setAmplitude(normalizedAmplitude)
      setIsSpeaking(normalizedAmplitude > speakingThreshold)
    } catch (error) {
      console.error('Failed to update amplitude:', error)
      setAmplitude(0)
      setIsSpeaking(false)
    }

    // Schedule next update
    animationIdRef.current = requestAnimationFrame(updateAmplitude)
  }, [speakingThreshold])

  // Start animation loop
  useEffect(() => {
    if (audioContext && analyserRef.current) {
      animationIdRef.current = requestAnimationFrame(updateAmplitude)
    }

    return () => {
      if (animationIdRef.current) {
        cancelAnimationFrame(animationIdRef.current)
      }
    }
  }, [audioContext, updateAmplitude])

  return { amplitude, isSpeaking }
}

interface AudioLipSyncProps {
  audioContext?: AudioContext | null
  speakingThreshold?: number
  showLabel?: boolean
}

/**
 * Visual component that shows audio amplitude with a lip sync indicator
 */
export function AudioLipSync({
  audioContext = null,
  speakingThreshold = 0.1,
  showLabel = true,
}: AudioLipSyncProps) {
  const { amplitude, isSpeaking } = useAudioAnalyser(audioContext, speakingThreshold)

  return (
    <div className="audio-lip-sync">
      <div className="amplitude-indicator">
        <div
          className={`amplitude-bar ${isSpeaking ? 'speaking' : 'idle'}`}
          style={{
            height: `${amplitude * 100}%`,
          }}
        />
      </div>
      {showLabel && (
        <div className="amplitude-label">
          <span className="amplitude-value">{(amplitude * 100).toFixed(0)}%</span>
        </div>
      )}
    </div>
  )
}
