import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { DMAvatar } from './DMAvatar'

describe('DMAvatar', () => {
  it('renders the avatar container', () => {
    render(<DMAvatar expression="neutral" isSpeaking={false} />)
    expect(document.querySelector('.dm-avatar')).toBeTruthy()
  })

  it('shows the DM face element', () => {
    render(<DMAvatar expression="neutral" isSpeaking={false} />)
    expect(document.querySelector('.avatar-face')).toBeTruthy()
  })

  it('applies expression class', () => {
    render(<DMAvatar expression="menacing" isSpeaking={false} />)
    expect(document.querySelector('.expression-menacing')).toBeTruthy()
  })

  it('applies speaking class when speaking', () => {
    render(<DMAvatar expression="neutral" isSpeaking={true} />)
    expect(document.querySelector('.is-speaking')).toBeTruthy()
  })

  it('does not apply speaking class when silent', () => {
    render(<DMAvatar expression="neutral" isSpeaking={false} />)
    expect(document.querySelector('.is-speaking')).toBeNull()
  })

  it('shows expression label', () => {
    render(<DMAvatar expression="excited" isSpeaking={false} />)
    expect(screen.getByText(/excited/i)).toBeTruthy()
  })

  it('animates mouth based on amplitude', () => {
    render(<DMAvatar expression="neutral" isSpeaking={true} mouthAmplitude={0.8} />)
    const mouth = document.querySelector('.avatar-mouth') as HTMLElement
    expect(mouth).toBeTruthy()
    // Mouth height should scale with amplitude
    expect(mouth.style.height).toBeTruthy()
  })

  it('shows idle animation when not speaking', () => {
    render(<DMAvatar expression="neutral" isSpeaking={false} />)
    expect(document.querySelector('.idle')).toBeTruthy()
  })
})
