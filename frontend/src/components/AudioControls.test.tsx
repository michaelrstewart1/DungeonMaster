import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { AudioControls } from './AudioControls'

describe('AudioControls', () => {
  const mockOnMicToggle = vi.fn()
  const mockOnMuteToggle = vi.fn()

  beforeEach(() => {
    mockOnMicToggle.mockClear()
    mockOnMuteToggle.mockClear()
  })

  it('renders mic toggle button', () => {
    render(
      <AudioControls
        isMicOn={false}
        isMuted={false}
        onMicToggle={mockOnMicToggle}
        onMuteToggle={mockOnMuteToggle}
      />
    )
    expect(screen.getByRole('button', { name: /mic/i })).toBeTruthy()
  })

  it('renders mute toggle button', () => {
    render(
      <AudioControls
        isMicOn={false}
        isMuted={false}
        onMicToggle={mockOnMicToggle}
        onMuteToggle={mockOnMuteToggle}
      />
    )
    expect(screen.getByRole('button', { name: /mute|speaker/i })).toBeTruthy()
  })

  it('calls onMicToggle when mic button clicked', () => {
    render(
      <AudioControls
        isMicOn={false}
        isMuted={false}
        onMicToggle={mockOnMicToggle}
        onMuteToggle={mockOnMuteToggle}
      />
    )
    fireEvent.click(screen.getByRole('button', { name: /mic/i }))
    expect(mockOnMicToggle).toHaveBeenCalled()
  })

  it('shows recording indicator when mic is on', () => {
    render(
      <AudioControls
        isMicOn={true}
        isMuted={false}
        onMicToggle={mockOnMicToggle}
        onMuteToggle={mockOnMuteToggle}
      />
    )
    expect(document.querySelector('.recording-indicator')).toBeTruthy()
  })

  it('does not show recording indicator when mic is off', () => {
    render(
      <AudioControls
        isMicOn={false}
        isMuted={false}
        onMicToggle={mockOnMicToggle}
        onMuteToggle={mockOnMuteToggle}
      />
    )
    expect(document.querySelector('.recording-indicator')).toBeNull()
  })

  it('shows muted state', () => {
    render(
      <AudioControls
        isMicOn={false}
        isMuted={true}
        onMicToggle={mockOnMicToggle}
        onMuteToggle={mockOnMuteToggle}
      />
    )
    expect(document.querySelector('.is-muted')).toBeTruthy()
  })
})
