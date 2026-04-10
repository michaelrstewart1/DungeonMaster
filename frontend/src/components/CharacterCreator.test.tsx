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
    expect(screen.getByLabelText(/name/i)).toBeTruthy()
    expect(screen.getByLabelText(/race/i)).toBeTruthy()
    expect(screen.getByLabelText(/class/i)).toBeTruthy()
  })

  it('renders race options', () => {
    render(<CharacterCreator onCreate={mockOnCreate} onCancel={mockOnCancel} />)
    const raceSelect = screen.getByLabelText(/race/i)
    expect(within(raceSelect).getByText('Human')).toBeTruthy()
    expect(within(raceSelect).getByText('Elf')).toBeTruthy()
    expect(within(raceSelect).getByText('Dwarf')).toBeTruthy()
  })

  it('renders class options', () => {
    render(<CharacterCreator onCreate={mockOnCreate} onCancel={mockOnCancel} />)
    const classSelect = screen.getByLabelText(/class/i)
    expect(within(classSelect).getByText(/fighter/i)).toBeTruthy()
    expect(within(classSelect).getByText(/wizard/i)).toBeTruthy()
    expect(within(classSelect).getByText(/rogue/i)).toBeTruthy()
  })

  it('renders ability score inputs', () => {
    render(<CharacterCreator onCreate={mockOnCreate} onCancel={mockOnCancel} />)
    expect(screen.getByLabelText(/strength/i)).toBeTruthy()
    expect(screen.getByLabelText(/dexterity/i)).toBeTruthy()
    expect(screen.getByLabelText(/constitution/i)).toBeTruthy()
    expect(screen.getByLabelText(/intelligence/i)).toBeTruthy()
    expect(screen.getByLabelText(/wisdom/i)).toBeTruthy()
    expect(screen.getByLabelText(/charisma/i)).toBeTruthy()
  })

  it('calls onCreate with character data on submit', () => {
    render(<CharacterCreator onCreate={mockOnCreate} onCancel={mockOnCancel} />)
    fireEvent.change(screen.getByLabelText(/name/i), { target: { value: 'Gandalf' } })
    fireEvent.change(screen.getByLabelText(/race/i), { target: { value: 'human' } })
    fireEvent.change(screen.getByLabelText(/class/i), { target: { value: 'wizard' } })
    fireEvent.submit(screen.getByRole('form'))
    expect(mockOnCreate).toHaveBeenCalledWith(
      expect.objectContaining({
        name: 'Gandalf',
        race: 'human',
        class_name: 'wizard',
      })
    )
  })

  it('calls onCancel when cancel button clicked', () => {
    render(<CharacterCreator onCreate={mockOnCreate} onCancel={mockOnCancel} />)
    fireEvent.click(screen.getByRole('button', { name: /cancel/i }))
    expect(mockOnCancel).toHaveBeenCalled()
  })

  it('validates that name is required', () => {
    render(<CharacterCreator onCreate={mockOnCreate} onCancel={mockOnCancel} />)
    const nameInput = screen.getByLabelText(/name/i) as HTMLInputElement
    expect(nameInput.required).toBe(true)
  })
})
