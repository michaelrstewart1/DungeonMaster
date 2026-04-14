import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { CharacterSheet } from './CharacterSheet'
import type { Character } from '../types'

describe('CharacterSheet', () => {
  const character: Character = {
    id: 'ch1',
    name: 'Thorin Ironforge',
    race: 'dwarf',
    class_name: 'fighter',
    level: 5,
    hp: 42,
    max_hp: 50,
    ac: 18,
    strength: 16,
    dexterity: 12,
    constitution: 14,
    intelligence: 10,
    wisdom: 13,
    charisma: 8,
    conditions: ['poisoned'],
    inventory: ['Battleaxe', 'Chain Mail', 'Shield'],
    proficiency_bonus: 3,
  }

  it('renders character name and level', () => {
    render(<CharacterSheet character={character} />)
    expect(screen.getByText('Thorin Ironforge')).toBeTruthy()
    expect(screen.getByText(/level 5/i)).toBeTruthy()
  })

  it('renders race and class', () => {
    render(<CharacterSheet character={character} />)
    expect(screen.getByText(/dwarf/i)).toBeTruthy()
    expect(screen.getByText(/fighter/i)).toBeTruthy()
  })

  it('renders HP', () => {
    render(<CharacterSheet character={character} />)
    expect(screen.getByText(/42\s*\/\s*50/)).toBeTruthy()
  })

  it('renders AC', () => {
    render(<CharacterSheet character={character} />)
    expect(screen.getByText('18')).toBeTruthy()
  })

  it('renders ability scores with modifiers', () => {
    render(<CharacterSheet character={character} />)
    // STR 16 → +3
    expect(screen.getByText('16')).toBeTruthy()
    const strBlock = screen.getByText('STR').closest('.ability-block')!
    expect(strBlock.querySelector('.ability-mod')!.textContent).toBe('+3')
  })

  it('renders conditions', () => {
    render(<CharacterSheet character={character} />)
    expect(screen.getByText(/poisoned/i)).toBeTruthy()
  })

  it('renders inventory', () => {
    render(<CharacterSheet character={character} />)
    // Inventory starts collapsed — click to expand
    fireEvent.click(screen.getByText(/Inventory/))
    expect(screen.getByText('Battleaxe')).toBeTruthy()
    expect(screen.getByText('Chain Mail')).toBeTruthy()
    expect(screen.getByText('Shield')).toBeTruthy()
  })

  it('shows proficiency bonus', () => {
    render(<CharacterSheet character={character} />)
    const profBlock = screen.getByText(/Prof\. Bonus/).closest('.stat-block')!
    expect(profBlock.querySelector('.stat-value')!.textContent).toContain('3')
  })
})
