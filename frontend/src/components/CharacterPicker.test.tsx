import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { CharacterPicker } from './CharacterPicker'

describe('CharacterPicker', () => {
  const mockOnSelect = vi.fn()
  const mockOnCancel = vi.fn()

  beforeEach(() => {
    mockOnSelect.mockClear()
    mockOnCancel.mockClear()
  })

  it('renders the picker with character cards', () => {
    render(<CharacterPicker onSelect={mockOnSelect} onCancel={mockOnCancel} />)
    expect(screen.getByTestId('character-picker')).toBeTruthy()
    expect(screen.getByText('Choose Your Hero')).toBeTruthy()
    expect(screen.getByTestId('picker-card-premade-thorne')).toBeTruthy()
    expect(screen.getByTestId('picker-card-premade-lyra')).toBeTruthy()
  })

  it('renders all 10 pre-made characters', () => {
    render(<CharacterPicker onSelect={mockOnSelect} onCancel={mockOnCancel} />)
    const cards = screen.getAllByTestId(/^picker-card-premade-/)
    expect(cards.length).toBe(10)
  })

  it('shows detail panel when a character is selected', () => {
    render(<CharacterPicker onSelect={mockOnSelect} onCancel={mockOnCancel} />)
    fireEvent.click(screen.getByTestId('picker-card-premade-thorne'))
    expect(screen.getByTestId('picker-detail')).toBeTruthy()
    expect(screen.getAllByText('Thorne Ironfist').length).toBeGreaterThanOrEqual(1)
  })

  it('shows backstory in detail panel', () => {
    render(<CharacterPicker onSelect={mockOnSelect} onCancel={mockOnCancel} />)
    fireEvent.click(screen.getByTestId('picker-card-premade-lyra'))
    expect(screen.getByText(/elven scholar/)).toBeTruthy()
  })

  it('shows equipment tags in detail panel', () => {
    render(<CharacterPicker onSelect={mockOnSelect} onCancel={mockOnCancel} />)
    fireEvent.click(screen.getByTestId('picker-card-premade-thorne'))
    expect(screen.getByText('Battleaxe')).toBeTruthy()
    expect(screen.getByText('Chain Mail')).toBeTruthy()
  })

  it('confirm button is disabled without selection', () => {
    render(<CharacterPicker onSelect={mockOnSelect} onCancel={mockOnCancel} />)
    expect(screen.getByTestId('picker-confirm')).toBeDisabled()
  })

  it('confirm button shows character name when selected', () => {
    render(<CharacterPicker onSelect={mockOnSelect} onCancel={mockOnCancel} />)
    fireEvent.click(screen.getByTestId('picker-card-premade-sera'))
    expect(screen.getByTestId('picker-confirm').textContent).toContain('Sera Dawnbringer')
  })

  it('calls onSelect with character data when confirmed', () => {
    render(<CharacterPicker onSelect={mockOnSelect} onCancel={mockOnCancel} />)
    fireEvent.click(screen.getByTestId('picker-card-premade-thorne'))
    fireEvent.click(screen.getByTestId('picker-confirm'))
    expect(mockOnSelect).toHaveBeenCalledWith(
      expect.objectContaining({
        name: 'Thorne Ironfist',
        race: 'dwarf',
        class_name: 'fighter',
        level: 3,
      })
    )
  })

  it('does not include portrait/backstory/equipment in onSelect data', () => {
    render(<CharacterPicker onSelect={mockOnSelect} onCancel={mockOnCancel} />)
    fireEvent.click(screen.getByTestId('picker-card-premade-thorne'))
    fireEvent.click(screen.getByTestId('picker-confirm'))
    const arg = mockOnSelect.mock.calls[0][0]
    expect(arg.portrait).toBeUndefined()
    expect(arg.backstory).toBeUndefined()
    expect(arg.equipment).toBeUndefined()
  })

  it('calls onCancel when cancel button clicked', () => {
    render(<CharacterPicker onSelect={mockOnSelect} onCancel={mockOnCancel} />)
    fireEvent.click(screen.getByRole('button', { name: /cancel/i }))
    expect(mockOnCancel).toHaveBeenCalled()
  })

  it('allows switching selection between characters', () => {
    render(<CharacterPicker onSelect={mockOnSelect} onCancel={mockOnCancel} />)
    fireEvent.click(screen.getByTestId('picker-card-premade-thorne'))
    expect(screen.getByTestId('picker-detail')).toBeTruthy()

    fireEvent.click(screen.getByTestId('picker-card-premade-kael'))
    expect(screen.getAllByText('Kael Shadowstep').length).toBeGreaterThanOrEqual(1)
  })
})
