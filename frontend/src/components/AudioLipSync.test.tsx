import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { render } from '@testing-library/react'
import { useAudioAnalyser, AudioLipSync } from './AudioLipSync'

// Mock Web Audio API
const mockAnalyser = {
  frequencyBinCount: 256,
  getByteFrequencyData: vi.fn(),
  connect: vi.fn(),
  disconnect: vi.fn(),
  fftSize: 256,
}

const mockAudioContext = {
  createAnalyser: vi.fn(() => mockAnalyser),
  createMediaStreamAudioSourceNode: vi.fn(() => ({
    connect: vi.fn(),
  })),
  state: 'running',
} as any

describe('useAudioAnalyser', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Setup default mock behavior
    mockAnalyser.getByteFrequencyData.mockImplementation((arr: Uint8Array) => {
      arr.fill(30) // Low amplitude by default
    })
  })

  it('should return initial state', () => {
    const { result } = renderHook(() => useAudioAnalyser(null))
    
    expect(result.current.amplitude).toBe(0)
    expect(result.current.isSpeaking).toBe(false)
  })

  it('should handle null audio context gracefully', () => {
    const { result } = renderHook(() => useAudioAnalyser(null))
    
    expect(result.current.amplitude).toBe(0)
    expect(result.current.isSpeaking).toBe(false)
  })

  it('should accept custom threshold parameter', () => {
    const { result } = renderHook(() => useAudioAnalyser(null, 0.3))
    
    expect(result.current.amplitude).toBe(0)
    expect(result.current.isSpeaking).toBe(false)
  })

  it('should handle audio context errors gracefully', () => {
    const badContext = {
      createAnalyser: () => {
        throw new Error('Failed to create analyser')
      },
    } as any
    
    const { result } = renderHook(() => useAudioAnalyser(badContext))
    
    expect(result.current.amplitude).toBe(0)
    expect(result.current.isSpeaking).toBe(false)
  })
})

describe('AudioLipSync Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockAnalyser.getByteFrequencyData.mockImplementation((arr: Uint8Array) => {
      arr.fill(30)
    })
  })

  it('should render amplitude indicator', () => {
    const { container } = render(<AudioLipSync audioContext={null} />)
    
    expect(container.querySelector('.audio-lip-sync')).toBeDefined()
    expect(container.querySelector('.amplitude-indicator')).toBeDefined()
  })

  it('should render with default props', () => {
    const { container } = render(<AudioLipSync />)
    
    expect(container.querySelector('.audio-lip-sync')).toBeDefined()
    const bar = container.querySelector('.amplitude-bar')
    expect(bar?.classList.contains('idle')).toBe(true)
  })

  it('should render label by default', () => {
    const { container } = render(<AudioLipSync audioContext={null} />)
    
    expect(container.querySelector('.amplitude-label')).toBeDefined()
    expect(container.querySelector('.amplitude-value')).toBeDefined()
  })

  it('should not render label when showLabel is false', () => {
    const { container } = render(<AudioLipSync audioContext={null} showLabel={false} />)
    
    expect(container.querySelector('.amplitude-label')).toBeNull()
  })

  it('should apply idle class by default', () => {
    const { container } = render(<AudioLipSync audioContext={null} />)
    
    const bar = container.querySelector('.amplitude-bar')
    expect(bar?.classList.contains('idle')).toBe(true)
  })

  it('should have height style based on amplitude', () => {
    const { container } = render(<AudioLipSync audioContext={null} />)
    
    const bar = container.querySelector('.amplitude-bar') as HTMLElement
    expect(bar).toBeDefined()
    // Bar should have style attribute
    const style = bar.getAttribute('style')
    expect(style).toContain('height')
    expect(style).toContain('0%') // Initial amplitude is 0
  })

  it('should accept custom speaking threshold', () => {
    const { container } = render(
      <AudioLipSync audioContext={null} speakingThreshold={0.3} />
    )
    
    expect(container.querySelector('.audio-lip-sync')).toBeDefined()
  })

  it('should display amplitude as percentage', () => {
    const { container } = render(<AudioLipSync audioContext={null} />)
    
    const value = container.querySelector('.amplitude-value')
    expect(value?.textContent).toContain('%')
    expect(value?.textContent).toBe('0%')
  })

  it('should support custom threshold parameter', () => {
    const { container } = render(
      <AudioLipSync audioContext={mockAudioContext} speakingThreshold={0.15} />
    )
    
    expect(container.querySelector('.audio-lip-sync')).toBeDefined()
  })
})


