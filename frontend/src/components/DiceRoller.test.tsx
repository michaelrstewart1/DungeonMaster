import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { DiceRoller } from './DiceRoller'

describe('DiceRoller', () => {
  const mockOnRoll = vi.fn()

  beforeEach(() => {
    mockOnRoll.mockClear()
  })

  it('renders dice buttons for standard D&D dice', () => {
    render(<DiceRoller onRoll={mockOnRoll} />)
    expect(screen.getByRole('button', { name: 'd4' })).toBeTruthy()
    expect(screen.getByRole('button', { name: 'd6' })).toBeTruthy()
    expect(screen.getByRole('button', { name: 'd8' })).toBeTruthy()
    expect(screen.getByRole('button', { name: 'd10' })).toBeTruthy()
    expect(screen.getByRole('button', { name: 'd12' })).toBeTruthy()
    expect(screen.getByRole('button', { name: 'd20' })).toBeTruthy()
    expect(screen.getByRole('button', { name: 'd100' })).toBeTruthy()
  })

  it('calls onRoll with dice notation when clicked', () => {
    render(<DiceRoller onRoll={mockOnRoll} />)
    fireEvent.click(screen.getByRole('button', { name: 'd20' }))
    expect(mockOnRoll).toHaveBeenCalledWith('1d20')
  })

  it('displays last roll result when provided', () => {
    render(
      <DiceRoller
        onRoll={mockOnRoll}
        lastResult={{ notation: '1d20', rolls: [17], modifier: 0, total: 17, is_critical: false, is_fumble: false }}
      />
    )
    expect(screen.getByText('17', { selector: '.dice-result-total' })).toBeTruthy()
  })

  it('highlights critical hits', () => {
    render(
      <DiceRoller
        onRoll={mockOnRoll}
        lastResult={{ notation: '1d20', rolls: [20], modifier: 0, total: 20, is_critical: true, is_fumble: false }}
      />
    )
    expect(screen.getByText(/critical/i)).toBeTruthy()
  })

  it('highlights fumbles', () => {
    render(
      <DiceRoller
        onRoll={mockOnRoll}
        lastResult={{ notation: '1d20', rolls: [1], modifier: 0, total: 1, is_critical: false, is_fumble: true }}
      />
    )
    expect(screen.getByText(/fumble/i)).toBeTruthy()
  })
})
