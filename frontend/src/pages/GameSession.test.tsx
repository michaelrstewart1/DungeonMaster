import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { GameSession } from './GameSession'
import type { GameState } from '../types'

const mockGameState: GameState = {
  phase: 'exploration',
  current_scene: 'You stand at the entrance of a dark dungeon.',
  narrative_history: [],
  combat_state: null,
  active_effects: [],
}

const mockGetGameState = vi.fn()
const mockSubmitAction = vi.fn()

vi.mock('../api/client', () => ({
  getGameState: (...args: unknown[]) => mockGetGameState(...args),
  submitAction: (...args: unknown[]) => mockSubmitAction(...args),
}))

const mockConnect = vi.fn()
const mockDisconnect = vi.fn()
const mockSend = vi.fn()
const mockOnMessage = vi.fn().mockReturnValue(vi.fn())
const mockOnStatusChange = vi.fn().mockReturnValue(vi.fn())

vi.mock('../api/websocket', () => {
  return {
    GameWebSocket: class {
      connect = mockConnect
      disconnect = mockDisconnect
      send = mockSend
      onMessage = mockOnMessage
      onStatusChange = mockOnStatusChange
      isConnected = false
    },
  }
})

// Mock all child components
vi.mock('../components/GameChat', () => ({
  GameChat: ({ messages, onSubmitAction }: any) => (
    <div data-testid="game-chat">
      <span data-testid="message-count">{messages.length}</span>
      <button
        onClick={() => onSubmitAction('test action')}
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

vi.mock('../components/DMAvatar', () => ({
  DMAvatar: ({ expression, isSpeaking }: any) => (
    <div data-testid="dm-avatar" data-expression={expression} data-speaking={isSpeaking} />
  ),
}))

vi.mock('../components/AudioControls', () => ({
  AudioControls: ({ onMicToggle, onMuteToggle }: any) => (
    <div data-testid="audio-controls">
      <button onClick={onMicToggle} data-testid="mic-toggle">Mic</button>
      <button onClick={onMuteToggle} data-testid="mute-toggle">Mute</button>
    </div>
  ),
}))

vi.mock('../components/BattleMap', () => ({
  default: ({ onCellClick }: any) => (
    <div data-testid="battle-map">
      <button onClick={() => onCellClick(1, 2)} data-testid="cell-click">Cell</button>
    </div>
  ),
}))

vi.mock('../components/TokenLayer', () => ({
  default: ({ tokens, onSelect }: any) => (
    <div data-testid="token-layer">
      <span data-testid="token-count">{tokens.length}</span>
      {tokens[0] && (
        <button onClick={() => onSelect(tokens[0].entity_id)} data-testid="select-token">
          Select
        </button>
      )}
    </div>
  ),
}))

vi.mock('../components/FogOfWar', () => ({
  default: ({ onReveal }: any) => (
    <div data-testid="fog-of-war">
      <button onClick={() => onReveal(3, 4)} data-testid="fog-reveal">Reveal</button>
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

  beforeEach(() => {
    vi.clearAllMocks()
    mockGetGameState.mockResolvedValue(mockGameState)
    mockSubmitAction.mockResolvedValue({ turn_number: 1, narration: 'DM responds', phase: 'exploration' })
  })

  it('shows loading state initially', () => {
    mockGetGameState.mockReturnValue(new Promise(() => {})) // never resolves
    renderWithRoute()
    expect(screen.getByTestId('game-loading')).toBeTruthy()
    expect(screen.getByText(/loading game/i)).toBeTruthy()
  })

  it('shows error state when API fails', async () => {
    mockGetGameState.mockRejectedValue(new Error('Network error'))
    renderWithRoute()
    await waitFor(() => {
      expect(screen.getByTestId('game-error')).toBeTruthy()
    })
    expect(screen.getByText(/network error/i)).toBeTruthy()
  })

  it('renders the game session page after loading', async () => {
    renderWithRoute()
    await waitFor(() => {
      expect(screen.getByText(/game session/i)).toBeTruthy()
    })
  })

  it('renders the game chat component', async () => {
    renderWithRoute()
    await waitFor(() => {
      expect(screen.getByTestId('game-chat')).toBeTruthy()
    })
  })

  it('renders the dice roller component', async () => {
    renderWithRoute()
    await waitFor(() => {
      expect(screen.getByTestId('dice-roller')).toBeTruthy()
    })
  })

  it('renders the initiative tracker', async () => {
    renderWithRoute()
    await waitFor(() => {
      expect(screen.getByTestId('initiative-tracker')).toBeTruthy()
    })
  })

  it('renders DMAvatar and AudioControls', async () => {
    renderWithRoute()
    await waitFor(() => {
      expect(screen.getByTestId('dm-avatar')).toBeTruthy()
      expect(screen.getByTestId('audio-controls')).toBeTruthy()
    })
  })

  it('renders TokenLayer', async () => {
    renderWithRoute()
    await waitFor(() => {
      expect(screen.getByTestId('token-layer')).toBeTruthy()
    })
  })

  it('calls getGameState on mount with sessionId', async () => {
    renderWithRoute('my-session')
    await waitFor(() => {
      expect(mockGetGameState).toHaveBeenCalledWith('my-session')
    })
  })

  it('connects WebSocket on mount', async () => {
    renderWithRoute()
    await waitFor(() => {
      expect(mockConnect).toHaveBeenCalled()
    })
  })

  it('subscribes to WebSocket messages and status', async () => {
    renderWithRoute()
    await waitFor(() => {
      expect(mockOnMessage).toHaveBeenCalled()
      expect(mockOnStatusChange).toHaveBeenCalled()
    })
  })

  it('shows WS connection status', async () => {
    renderWithRoute()
    await waitFor(() => {
      expect(screen.getByText(/connecting/i)).toBeTruthy()
    })
  })

  it('shows game phase from state', async () => {
    renderWithRoute()
    await waitFor(() => {
      expect(screen.getByText('exploration')).toBeTruthy()
    })
  })

  it('submits action via API client', async () => {
    const user = userEvent.setup()
    renderWithRoute()

    await waitFor(() => {
      expect(screen.getByTestId('chat-submit')).toBeTruthy()
    })

    await act(async () => {
      await user.click(screen.getByTestId('chat-submit'))
    })

    await waitFor(() => {
      expect(mockSubmitAction).toHaveBeenCalledWith('sess1', { type: 'interact', message: 'test action' })
    })
  })

  it('sends dice roll through WebSocket', async () => {
    const user = userEvent.setup()
    renderWithRoute()

    await waitFor(() => {
      expect(screen.getByTestId('roll-btn')).toBeTruthy()
    })

    await act(async () => {
      await user.click(screen.getByTestId('roll-btn'))
    })

    expect(mockSend).toHaveBeenCalledWith({ type: 'dice_roll', notation: '1d20' })
  })
})
