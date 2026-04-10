import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { InitiativeTracker } from './InitiativeTracker'

describe('InitiativeTracker', () => {
  const combatants = [
    { id: '1', name: 'Fighter', initiative: 18, hp: 45, max_hp: 50, is_current: true },
    { id: '2', name: 'Wizard', initiative: 15, hp: 22, max_hp: 22, is_current: false },
    { id: '3', name: 'Goblin', initiative: 12, hp: 5, max_hp: 7, is_current: false },
  ]

  it('renders all combatants', () => {
    render(<InitiativeTracker combatants={combatants} />)
    expect(screen.getByText('Fighter')).toBeTruthy()
    expect(screen.getByText('Wizard')).toBeTruthy()
    expect(screen.getByText('Goblin')).toBeTruthy()
  })

  it('shows initiative values', () => {
    render(<InitiativeTracker combatants={combatants} />)
    expect(screen.getByText('18')).toBeTruthy()
    expect(screen.getByText('15')).toBeTruthy()
    expect(screen.getByText('12')).toBeTruthy()
  })

  it('highlights the current combatant', () => {
    render(<InitiativeTracker combatants={combatants} />)
    const currentRow = screen.getByText('Fighter').closest('.initiative-row')
    expect(currentRow?.classList.contains('current-turn')).toBe(true)
  })

  it('shows HP as fraction', () => {
    render(<InitiativeTracker combatants={combatants} />)
    expect(screen.getByText('45/50')).toBeTruthy()
    expect(screen.getByText('22/22')).toBeTruthy()
    expect(screen.getByText('5/7')).toBeTruthy()
  })

  it('renders empty state when no combatants', () => {
    render(<InitiativeTracker combatants={[]} />)
    expect(screen.getByText(/no combat/i)).toBeTruthy()
  })
})
