import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, within } from '@testing-library/react'
import { CharacterCreator } from './CharacterCreator'

describe('CharacterCreator', () => {
  const mockOnCreate = vi.fn()
  const mockOnCancel = vi.fn()

  beforeEach(() => {
    mockOnCreate.mockClear()
    mockOnCancel.mockClear()
  })

  it('renders form fields for character creation', () => {
    render(<CharacterCreator onCreate={mockOnCreate} onCancel={mockOnCancel} />)
    expect(screen.getByTestId('step-race')).toBeTruthy()
    expect(screen.getByTestId('race-human')).toBeTruthy()
  })

  it('renders race options as visual cards', () => {
    render(<CharacterCreator onCreate={mockOnCreate} onCancel={mockOnCancel} />)
    expect(screen.getByTestId('race-human')).toBeTruthy()
    expect(screen.getByTestId('race-elf')).toBeTruthy()
    expect(screen.getByTestId('race-dwarf')).toBeTruthy()
  })

  it('renders class options on step 2', () => {
    render(<CharacterCreator onCreate={mockOnCreate} onCancel={mockOnCancel} />)
    // Navigate to class step
    fireEvent.click(screen.getByText(/Next: Choose Class/))
    expect(screen.getByTestId('step-class')).toBeTruthy()
    expect(screen.getByTestId('class-fighter')).toBeTruthy()
    expect(screen.getByTestId('class-wizard')).toBeTruthy()
    expect(screen.getByTestId('class-rogue')).toBeTruthy()
  })

  it('renders ability score inputs on step 3', () => {
    render(<CharacterCreator onCreate={mockOnCreate} onCancel={mockOnCancel} />)
    fireEvent.click(screen.getByText(/Next: Choose Class/))
    fireEvent.click(screen.getByText(/Next: Abilities/))
    expect(screen.getByTestId('step-abilities')).toBeTruthy()
    const abilities = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
    abilities.forEach((a) => {
      expect(document.getElementById(`ability-${a}`)).toBeTruthy()
    })
  })

  it('calls onCreate with character data on submit', () => {
    render(<CharacterCreator onCreate={mockOnCreate} onCancel={mockOnCancel} />)
    // Select elf race
    fireEvent.click(screen.getByTestId('race-elf'))
    fireEvent.click(screen.getByText(/Next: Choose Class/))
    // Select wizard class
    fireEvent.click(screen.getByTestId('class-wizard'))
    fireEvent.click(screen.getByText(/Next: Abilities/))
    // Skip to review
    fireEvent.click(screen.getByText(/Next: Review/))
    // Enter name and submit
    fireEvent.change(screen.getByLabelText(/name/i), { target: { value: 'Gandalf' } })
    fireEvent.submit(screen.getByRole('form'))
    expect(mockOnCreate).toHaveBeenCalledWith(
      expect.objectContaining({
        name: 'Gandalf',
        race: 'elf',
        class_name: 'wizard',
      })
    )
  })

  it('calls onCancel when cancel button clicked', () => {
    render(<CharacterCreator onCreate={mockOnCreate} onCancel={mockOnCancel} />)
    fireEvent.click(screen.getByRole('button', { name: /cancel/i }))
    expect(mockOnCancel).toHaveBeenCalled()
  })

  it('validates that name is required on review step', () => {
    render(<CharacterCreator onCreate={mockOnCreate} onCancel={mockOnCancel} />)
    fireEvent.click(screen.getByText(/Next: Choose Class/))
    fireEvent.click(screen.getByText(/Next: Abilities/))
    fireEvent.click(screen.getByText(/Next: Review/))
    const nameInput = screen.getByLabelText(/name/i) as HTMLInputElement
    expect(nameInput.required).toBe(true)
  })

  it('navigates back through steps', () => {
    render(<CharacterCreator onCreate={mockOnCreate} onCancel={mockOnCancel} />)
    fireEvent.click(screen.getByText(/Next: Choose Class/))
    expect(screen.getByTestId('step-class')).toBeTruthy()
    fireEvent.click(screen.getByText(/← Back/))
    expect(screen.getByTestId('step-race')).toBeTruthy()
  })

  it('shows step indicator', () => {
    render(<CharacterCreator onCreate={mockOnCreate} onCancel={mockOnCancel} />)
    expect(screen.getByTestId('creator-steps')).toBeTruthy()
  })

  it('ability +/- buttons change values', () => {
    render(<CharacterCreator onCreate={mockOnCreate} onCancel={mockOnCancel} />)
    fireEvent.click(screen.getByText(/Next: Choose Class/))
    fireEvent.click(screen.getByText(/Next: Abilities/))
    const strInput = document.getElementById('ability-strength') as HTMLInputElement
    expect(strInput.value).toBe('10')
    fireEvent.click(screen.getByLabelText('Increase Strength'))
    expect((document.getElementById('ability-strength') as HTMLInputElement).value).toBe('11')
  })
})
