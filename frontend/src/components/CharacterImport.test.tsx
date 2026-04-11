import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { CharacterImport } from './CharacterImport'

describe('CharacterImport', () => {
  const mockOnImport = vi.fn()
  const mockOnCancel = vi.fn()

  beforeEach(() => {
    mockOnImport.mockClear()
    mockOnCancel.mockClear()
  })

  it('renders import component with tabs', () => {
    render(<CharacterImport onImport={mockOnImport} onCancel={mockOnCancel} />)
    expect(screen.getByTestId('character-import')).toBeTruthy()
    expect(screen.getByText(/Upload File/)).toBeTruthy()
    expect(screen.getByText(/Paste JSON/)).toBeTruthy()
  })

  it('shows file drop zone on file tab', () => {
    render(<CharacterImport onImport={mockOnImport} onCancel={mockOnCancel} />)
    expect(screen.getByTestId('drop-zone')).toBeTruthy()
    expect(screen.getByText(/Drop JSON file here/)).toBeTruthy()
  })

  it('shows textarea on paste tab', () => {
    render(<CharacterImport onImport={mockOnImport} onCancel={mockOnCancel} />)
    fireEvent.click(screen.getByText(/Paste JSON/))
    expect(screen.getByTestId('json-input')).toBeTruthy()
  })

  it('shows preview when valid generic JSON is pasted', () => {
    render(<CharacterImport onImport={mockOnImport} onCancel={mockOnCancel} />)
    fireEvent.click(screen.getByText(/Paste JSON/))
    const textarea = screen.getByTestId('json-input')
    fireEvent.change(textarea, {
      target: {
        value: JSON.stringify({
          name: 'Gandalf',
          race: 'human',
          class_name: 'wizard',
          level: 5,
          strength: 10,
          dexterity: 14,
          hp: 30,
          ac: 12,
        }),
      },
    })
    expect(screen.getByTestId('import-preview')).toBeTruthy()
    expect(screen.getByText('Gandalf')).toBeTruthy()
    expect(screen.getByText('Generic JSON')).toBeTruthy()
  })

  it('shows preview when valid r20 JSON is pasted', () => {
    render(<CharacterImport onImport={mockOnImport} onCancel={mockOnCancel} />)
    fireEvent.click(screen.getByText(/Paste JSON/))
    const textarea = screen.getByTestId('json-input')
    fireEvent.change(textarea, {
      target: {
        value: JSON.stringify({
          name: 'Legolas',
          attribs: [
            { name: 'strength', current: '12' },
            { name: 'dexterity', current: '18' },
            { name: 'constitution', current: '14' },
            { name: 'intelligence', current: '10' },
            { name: 'wisdom', current: '14' },
            { name: 'charisma', current: '12' },
            { name: 'base_level', current: 'Ranger 8' },
            { name: 'race', current: 'Elf' },
            { name: 'hp', current: '65' },
            { name: 'ac', current: '16' },
          ],
        }),
      },
    })
    expect(screen.getByTestId('import-preview')).toBeTruthy()
    expect(screen.getByText('Legolas')).toBeTruthy()
    expect(screen.getByText('Roll20 (r20Exporter)')).toBeTruthy()
  })

  it('shows error for invalid JSON', () => {
    render(<CharacterImport onImport={mockOnImport} onCancel={mockOnCancel} />)
    fireEvent.click(screen.getByText(/Paste JSON/))
    const textarea = screen.getByTestId('json-input')
    fireEvent.change(textarea, { target: { value: 'not json{{{' } })
    expect(screen.getByTestId('import-error')).toBeTruthy()
    expect(screen.getByText(/Invalid JSON/)).toBeTruthy()
  })

  it('import button is disabled without preview', () => {
    render(<CharacterImport onImport={mockOnImport} onCancel={mockOnCancel} />)
    const btn = screen.getByTestId('import-btn')
    expect(btn).toBeDisabled()
  })

  it('calls onCancel when cancel button clicked', () => {
    render(<CharacterImport onImport={mockOnImport} onCancel={mockOnCancel} />)
    fireEvent.click(screen.getByRole('button', { name: /cancel/i }))
    expect(mockOnCancel).toHaveBeenCalled()
  })

  it('calls API and onImport when import is clicked with valid data', async () => {
    const mockCharacter = {
      id: 'ch-1',
      name: 'Gandalf',
      race: 'human',
      class_name: 'wizard',
      level: 5,
    }
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockCharacter),
    })

    render(<CharacterImport onImport={mockOnImport} onCancel={mockOnCancel} />)
    fireEvent.click(screen.getByText(/Paste JSON/))
    const textarea = screen.getByTestId('json-input')
    fireEvent.change(textarea, {
      target: {
        value: JSON.stringify({
          name: 'Gandalf',
          race: 'human',
          class_name: 'wizard',
          level: 5,
        }),
      },
    })

    fireEvent.click(screen.getByTestId('import-btn'))

    await waitFor(() => {
      expect(mockOnImport).toHaveBeenCalledWith(mockCharacter)
    })
  })

  it('shows error when API import fails', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      text: () => Promise.resolve('Server error'),
    })

    render(<CharacterImport onImport={mockOnImport} onCancel={mockOnCancel} />)
    fireEvent.click(screen.getByText(/Paste JSON/))
    const textarea = screen.getByTestId('json-input')
    fireEvent.change(textarea, {
      target: {
        value: JSON.stringify({ name: 'Test', race: 'human', class_name: 'fighter', level: 1 }),
      },
    })

    fireEvent.click(screen.getByTestId('import-btn'))

    await waitFor(() => {
      expect(screen.getByTestId('import-error')).toBeTruthy()
    })
  })
})
