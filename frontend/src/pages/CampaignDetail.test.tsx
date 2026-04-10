import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { CampaignDetail } from './CampaignDetail'
import { getCampaign, getCharacters, createCharacter, createGameSession } from '../api/client'
import type { Campaign, Character, GameSession } from '../types'

vi.mock('../api/client', () => ({
  getCampaign: vi.fn(),
  getCharacters: vi.fn(),
  createCharacter: vi.fn(),
  createGameSession: vi.fn(),
}))

vi.mock('../components/CharacterSheet', () => ({
  CharacterSheet: ({ character }: any) => (
    <div data-testid={`character-sheet-${character.id}`}>{character.name}</div>
  ),
}))

vi.mock('../components/CharacterCreator', () => ({
  CharacterCreator: ({ onCreate, onCancel }: any) => (
    <div data-testid="character-creator">
      <button
        data-testid="submit-character"
        onClick={() =>
          onCreate({
            name: 'Gandalf',
            race: 'human',
            class_name: 'wizard',
            level: 1,
            hp: 10,
            max_hp: 10,
            ac: 10,
            strength: 10,
            dexterity: 10,
            constitution: 10,
            intelligence: 18,
            wisdom: 14,
            charisma: 12,
          })
        }
      >
        Create
      </button>
      <button data-testid="cancel-character" onClick={onCancel}>
        Cancel
      </button>
    </div>
  ),
}))

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

const mockCampaign: Campaign = {
  id: 'camp1',
  name: 'Dragon Quest',
  description: 'Slay the dragon',
  character_ids: ['ch1'],
  world_state: {},
  dm_settings: {},
  created_at: '2024-01-01',
  updated_at: '2024-01-01',
}

const mockCharacters: Character[] = [
  {
    id: 'ch1',
    name: 'Aragorn',
    race: 'human',
    class_name: 'ranger',
    level: 5,
    hp: 45,
    max_hp: 45,
    ac: 16,
    strength: 16,
    dexterity: 14,
    constitution: 14,
    intelligence: 10,
    wisdom: 14,
    charisma: 12,
    conditions: [],
    inventory: ['Longsword'],
    proficiency_bonus: 3,
  },
]

const renderWithRoute = (campaignId = 'camp1') =>
  render(
    <MemoryRouter initialEntries={[`/campaign/${campaignId}`]}>
      <Routes>
        <Route path="/campaign/:campaignId" element={<CampaignDetail />} />
      </Routes>
    </MemoryRouter>
  )

describe('CampaignDetail', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(getCampaign).mockResolvedValue(mockCampaign)
    vi.mocked(getCharacters).mockResolvedValue(mockCharacters)
  })

  it('shows loading state initially', () => {
    vi.mocked(getCampaign).mockReturnValue(new Promise(() => {}))
    vi.mocked(getCharacters).mockReturnValue(new Promise(() => {}))
    renderWithRoute()
    expect(screen.getByText('Loading...')).toBeTruthy()
  })

  it('renders campaign name after loading', async () => {
    renderWithRoute()
    await waitFor(() => {
      expect(screen.getByText('Dragon Quest')).toBeTruthy()
    })
  })

  it('shows character list', async () => {
    renderWithRoute()
    await waitFor(() => {
      expect(screen.getByTestId('character-sheet-ch1')).toBeTruthy()
      expect(screen.getByText('Aragorn')).toBeTruthy()
    })
  })

  it('shows error on load failure', async () => {
    vi.mocked(getCampaign).mockRejectedValue(new Error('Not found'))
    vi.mocked(getCharacters).mockRejectedValue(new Error('Not found'))
    renderWithRoute()
    await waitFor(() => {
      expect(screen.getByText('Not found')).toBeTruthy()
    })
  })

  it('shows character creator when add button is clicked', async () => {
    renderWithRoute()
    await waitFor(() => {
      expect(screen.getByText('Add Character')).toBeTruthy()
    })
    fireEvent.click(screen.getByText('Add Character'))
    expect(screen.getByTestId('character-creator')).toBeTruthy()
  })

  it('character creation calls API and refreshes', async () => {
    vi.mocked(createCharacter).mockResolvedValue({
      ...mockCharacters[0],
      id: 'ch2',
      name: 'Gandalf',
    })
    renderWithRoute()
    await waitFor(() => {
      expect(screen.getByText('Add Character')).toBeTruthy()
    })

    fireEvent.click(screen.getByText('Add Character'))
    fireEvent.click(screen.getByTestId('submit-character'))

    await waitFor(() => {
      expect(createCharacter).toHaveBeenCalled()
    })
  })

  it('start game button creates session and navigates', async () => {
    const mockSession: GameSession = {
      id: 'sess1',
      campaign_id: 'camp1',
      phase: 'lobby',
      turn_count: 0,
      players: [],
    }
    vi.mocked(createGameSession).mockResolvedValue(mockSession)

    renderWithRoute()
    await waitFor(() => {
      expect(screen.getByText('Start Game')).toBeTruthy()
    })

    fireEvent.click(screen.getByText('Start Game'))

    await waitFor(() => {
      expect(createGameSession).toHaveBeenCalledWith('camp1')
      expect(mockNavigate).toHaveBeenCalledWith('/game/sess1')
    })
  })
})
