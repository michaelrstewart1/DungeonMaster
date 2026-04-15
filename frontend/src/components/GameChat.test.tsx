import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { GameChat } from './GameChat'

describe('GameChat', () => {
  const mockOnSubmit = vi.fn()

  const sampleMessages = [
    { role: 'dm' as const, text: 'You enter a dimly lit tavern.' },
    { role: 'player' as const, text: 'I look around for suspicious characters.' },
    { role: 'dm' as const, text: 'You notice a hooded figure in the corner booth.' },
  ]

  it('renders chat messages', () => {
    render(<GameChat messages={sampleMessages} onSubmitAction={mockOnSubmit} />)
    expect(screen.getByText('You enter a dimly lit tavern.')).toBeTruthy()
    expect(screen.getByText('I look around for suspicious characters.')).toBeTruthy()
  })

  it('renders an input field for player actions', () => {
    render(<GameChat messages={[]} onSubmitAction={mockOnSubmit} />)
    expect(screen.getByPlaceholderText(/action|what do you do/i)).toBeTruthy()
  })

  it('calls onSubmitAction when submitting text', () => {
    render(<GameChat messages={[]} onSubmitAction={mockOnSubmit} />)
    const input = screen.getByPlaceholderText(/action|what do you do/i)
    fireEvent.change(input, { target: { value: 'I attack the goblin!' } })
    fireEvent.submit(input.closest('form')!)
    expect(mockOnSubmit).toHaveBeenCalledWith('I attack the goblin!')
  })

  it('clears input after submission', () => {
    render(<GameChat messages={[]} onSubmitAction={mockOnSubmit} />)
    const input = screen.getByPlaceholderText(/action|what do you do/i) as HTMLInputElement
    fireEvent.change(input, { target: { value: 'I search the room' } })
    fireEvent.submit(input.closest('form')!)
    expect(input.value).toBe('')
  })

  it('distinguishes DM and player messages visually', () => {
    render(<GameChat messages={sampleMessages} onSubmitAction={mockOnSubmit} />)
    const dmMessages = document.querySelectorAll('.message-dm')
    const playerMessages = document.querySelectorAll('.message-player')
    expect(dmMessages.length).toBe(2)
    expect(playerMessages.length).toBe(1)
  })

  it('disables input when disabled prop is true', () => {
    render(<GameChat messages={[]} onSubmitAction={mockOnSubmit} disabled />)
    const input = screen.getByPlaceholderText(/action|what do you do/i) as HTMLInputElement
    expect(input.disabled).toBe(true)
  })

  it('disables input when waiting for DM response', () => {
    render(<GameChat messages={[]} onSubmitAction={mockOnSubmit} isWaitingForDM />)
    const input = screen.getByPlaceholderText(/action|what do you do/i) as HTMLInputElement
    expect(input.disabled).toBe(true)
    const sendBtn = screen.getByText('Send') as HTMLButtonElement
    expect(sendBtn.disabled).toBe(true)
  })

  it('does not submit when waiting for DM response', () => {
    const submitFn = vi.fn()
    render(<GameChat messages={[]} onSubmitAction={submitFn} isWaitingForDM />)
    const input = screen.getByPlaceholderText(/action|what do you do/i) as HTMLInputElement
    fireEvent.change(input, { target: { value: 'I attack!' } })
    fireEvent.submit(input.closest('form')!)
    expect(submitFn).not.toHaveBeenCalled()
  })
})
