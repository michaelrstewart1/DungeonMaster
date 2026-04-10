import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { GameSession } from './GameSession'

vi.mock('../components/GameChat', () => ({
  GameChat: ({ messages, onSubmitAction, disabled }: any) => (
    <div data-testid="game-chat">
      <span data-testid="message-count">{messages.length}</span>
      <button
        onClick={() => onSubmitAction('test action')}
        disabled={disabled}
        data-testid="chat-submit"
      >
        Submit
      </button>
    </div>
  ),
}))

vi.mock('../components/DiceRoller', () => ({
  DiceRoller: ({ onRoll }: any) => (
    <div data-testid="dice-roller">
      <button onClick={() => onRoll('1d20')} data-testid="roll-btn">Roll</button>
    </div>
  ),
}))

vi.mock('../components/InitiativeTracker', () => ({
  InitiativeTracker: ({ combatants }: any) => (
    <div data-testid="initiative-tracker">
      <span data-testid="combatant-count">{combatants.length}</span>
    </div>
  ),
}))

describe('GameSession', () => {
  const renderWithRoute = (sessionId = 'sess1') => {
    return render(
      <MemoryRouter initialEntries={[`/game/${sessionId}`]}>
        <Routes>
          <Route path="/game/:sessionId" element={<GameSession />} />
        </Routes>
      </MemoryRouter>
    )
  }

  it('renders the game session page', () => {
    renderWithRoute()
    expect(screen.getByText(/game session/i)).toBeTruthy()
  })

  it('renders the game chat component', () => {
    renderWithRoute()
    expect(screen.getByTestId('game-chat')).toBeTruthy()
  })

  it('renders the dice roller component', () => {
    renderWithRoute()
    expect(screen.getByTestId('dice-roller')).toBeTruthy()
  })

  it('renders the initiative tracker', () => {
    renderWithRoute()
    expect(screen.getByTestId('initiative-tracker')).toBeTruthy()
  })
})
