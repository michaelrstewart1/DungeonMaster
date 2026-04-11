import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { CharacterPortrait } from './CharacterPortrait'

describe('CharacterPortrait', () => {
  it('renders with default size', () => {
    render(<CharacterPortrait race="elf" className="wizard" />)
    expect(screen.getByTestId('character-portrait')).toBeTruthy()
  })

  it('renders with custom portrait symbol', () => {
    render(<CharacterPortrait race="human" className="fighter" portrait="🛡️" />)
    const el = screen.getByTestId('character-portrait')
    expect(el.textContent).toContain('🛡️')
  })

  it('applies selected class', () => {
    render(<CharacterPortrait race="dwarf" className="barbarian" selected />)
    const el = screen.getByTestId('character-portrait')
    expect(el.className).toContain('selected')
  })

  it('renders different sizes', () => {
    const { rerender } = render(<CharacterPortrait race="human" className="fighter" size="sm" />)
    let el = screen.getByTestId('character-portrait')
    expect(el.style.width).toBe('64px')

    rerender(<CharacterPortrait race="human" className="fighter" size="lg" />)
    el = screen.getByTestId('character-portrait')
    expect(el.style.width).toBe('128px')
  })
})
