import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { Footer } from './Footer'

describe('Footer', () => {
  it('renders copyright text', () => {
    render(<Footer />)
    expect(screen.getByText(/AI Dungeon Master. All rights reserved/)).toBeTruthy()
  })

  it('renders powered by AI', () => {
    render(<Footer />)
    expect(screen.getByText('Powered by AI')).toBeTruthy()
  })

  it('renders version info', () => {
    render(<Footer />)
    expect(screen.getByText('v0.1.0')).toBeTruthy()
  })

  it('renders decorative ornament', () => {
    render(<Footer />)
    expect(screen.getByText('⚜ ✦ ⚜')).toBeTruthy()
  })
})
