import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { CharacterCreator } from './CharacterCreator'

// Helper to navigate through the wizard steps
function navigateTo(stepName: string) {
  const navMap: Record<string, string[]> = {
    'Class': ['Next: Choose Class'],
    'Background': ['Next: Choose Class', 'Next: Background'],
    'Abilities': ['Next: Choose Class', 'Next: Background', 'Next: Abilities'],
    'Skills': ['Next: Choose Class', 'Next: Background', 'Next: Abilities', 'Next: Skills'],
    'Equipment': ['Next: Choose Class', 'Next: Background', 'Next: Abilities', 'Next: Skills', 'Next: Equipment'],
    'Details': ['Next: Choose Class', 'Next: Background', 'Next: Abilities', 'Next: Skills', 'Next: Equipment', 'Next: Details'],
    'Review': ['Next: Choose Class', 'Next: Background', 'Next: Abilities', 'Next: Skills', 'Next: Equipment', 'Next: Details', 'Next: Review'],
  }
  const clicks = navMap[stepName] || []
  for (const text of clicks) {
    fireEvent.click(screen.getByText(new RegExp(text)))
  }
}

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
    navigateTo('Class')
    expect(screen.getByTestId('step-class')).toBeTruthy()
    expect(screen.getByTestId('class-fighter')).toBeTruthy()
    expect(screen.getByTestId('class-wizard')).toBeTruthy()
    expect(screen.getByTestId('class-rogue')).toBeTruthy()
  })

  it('renders background options on step 3', () => {
    render(<CharacterCreator onCreate={mockOnCreate} onCancel={mockOnCancel} />)
    navigateTo('Background')
    expect(screen.getByTestId('step-background')).toBeTruthy()
    expect(screen.getByTestId('bg-acolyte')).toBeTruthy()
    expect(screen.getByTestId('bg-sage')).toBeTruthy()
  })

  it('renders ability score inputs on step 4', () => {
    render(<CharacterCreator onCreate={mockOnCreate} onCancel={mockOnCancel} />)
    navigateTo('Abilities')
    expect(screen.getByTestId('step-abilities')).toBeTruthy()
    const abilities = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
    abilities.forEach((a) => {
      expect(document.getElementById(`ability-${a}`)).toBeTruthy()
    })
  })

  it('renders skill selection on step 5', () => {
    render(<CharacterCreator onCreate={mockOnCreate} onCancel={mockOnCancel} />)
    navigateTo('Skills')
    expect(screen.getByTestId('step-skills')).toBeTruthy()
  })

  it('renders equipment choices on step 6', () => {
    render(<CharacterCreator onCreate={mockOnCreate} onCancel={mockOnCancel} />)
    navigateTo('Equipment')
    expect(screen.getByTestId('step-equipment')).toBeTruthy()
  })

  it('calls onCreate with character data on submit', () => {
    render(<CharacterCreator onCreate={mockOnCreate} onCancel={mockOnCancel} />)
    // Select elf race
    fireEvent.click(screen.getByTestId('race-elf'))
    navigateTo('Class')
    // Select wizard class
    fireEvent.click(screen.getByTestId('class-wizard'))
    // Navigate through remaining steps to Details
    fireEvent.click(screen.getByText(/Next: Background/))
    fireEvent.click(screen.getByText(/Next: Abilities/))
    fireEvent.click(screen.getByText(/Next: Skills/))
    fireEvent.click(screen.getByText(/Next: Equipment/))
    // Wizard is a caster, so go through Spells step first
    fireEvent.click(screen.getByText(/Next: Spells/))
    fireEvent.click(screen.getByText(/Next: Details/))
    // Enter name on details step
    fireEvent.change(screen.getByLabelText(/name/i), { target: { value: 'Gandalf' } })
    fireEvent.click(screen.getByText(/Next: Review/))
    // Submit on review
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

  it('validates that name is required on details step', () => {
    render(<CharacterCreator onCreate={mockOnCreate} onCancel={mockOnCancel} />)
    navigateTo('Details')
    const nameInput = screen.getByLabelText(/name/i) as HTMLInputElement
    expect(nameInput.required).toBe(true)
  })

  it('navigates back through steps', () => {
    render(<CharacterCreator onCreate={mockOnCreate} onCancel={mockOnCancel} />)
    navigateTo('Class')
    expect(screen.getByTestId('step-class')).toBeTruthy()
    fireEvent.click(screen.getByText(/← Back/))
    expect(screen.getByTestId('step-race')).toBeTruthy()
  })

  it('shows step indicator', () => {
    render(<CharacterCreator onCreate={mockOnCreate} onCancel={mockOnCancel} />)
    expect(screen.getByTestId('creator-steps')).toBeTruthy()
  })

  it('ability +/- buttons change values with point buy', () => {
    render(<CharacterCreator onCreate={mockOnCreate} onCancel={mockOnCancel} />)
    navigateTo('Abilities')
    // Default point buy starts at 8
    const strInput = document.getElementById('ability-strength') as HTMLInputElement
    expect(strInput.value).toBe('8')
    fireEvent.click(screen.getByLabelText('Increase Strength'))
    expect((document.getElementById('ability-strength') as HTMLInputElement).value).toBe('9')
  })

  it('supports multiple ability score methods', () => {
    render(<CharacterCreator onCreate={mockOnCreate} onCancel={mockOnCancel} />)
    navigateTo('Abilities')
    expect(screen.getByTestId('method-point-buy')).toBeTruthy()
    expect(screen.getByTestId('method-standard-array')).toBeTruthy()
    expect(screen.getByTestId('method-roll')).toBeTruthy()
  })

  it('shows subrace options for races that have them', () => {
    render(<CharacterCreator onCreate={mockOnCreate} onCancel={mockOnCancel} />)
    fireEvent.click(screen.getByTestId('race-dwarf'))
    expect(screen.getByTestId('subrace-hill-dwarf')).toBeTruthy()
    expect(screen.getByTestId('subrace-mountain-dwarf')).toBeTruthy()
  })

  it('shows subclass options for classes', () => {
    render(<CharacterCreator onCreate={mockOnCreate} onCancel={mockOnCancel} />)
    navigateTo('Class')
    fireEvent.click(screen.getByTestId('class-fighter'))
    expect(screen.getByTestId('subclass-champion')).toBeTruthy()
  })

  it('shows alignment selection on details step', () => {
    render(<CharacterCreator onCreate={mockOnCreate} onCancel={mockOnCancel} />)
    navigateTo('Details')
    expect(screen.getByLabelText(/alignment/i)).toBeTruthy()
  })

  it('shows background feature preview', () => {
    render(<CharacterCreator onCreate={mockOnCreate} onCancel={mockOnCancel} />)
    navigateTo('Background')
    expect(screen.getByText(/Shelter of the Faithful/)).toBeTruthy()
  })
})
