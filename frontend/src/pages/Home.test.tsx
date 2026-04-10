import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { Home } from './Home'
import { getCampaigns, createCampaign } from '../api/client'
import type { Campaign } from '../types'

vi.mock('../api/client', () => ({
  getCampaigns: vi.fn(),
  createCampaign: vi.fn(),
}))

vi.mock('../components/CampaignList', () => ({
  CampaignList: ({ campaigns, onSelect, onCreate }: any) => (
    <div data-testid="campaign-list">
      <span data-testid="campaign-count">{campaigns.length}</span>
      <button onClick={onCreate} data-testid="create-btn">Create</button>
      {campaigns.map((c: any) => (
        <div key={c.id} onClick={() => onSelect(c.id)} data-testid={`campaign-${c.id}`}>
          {c.name}
        </div>
      ))}
    </div>
  ),
}))

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

const mockCampaigns: Campaign[] = [
  {
    id: 'c1',
    name: 'Lost Mine',
    description: 'A classic adventure',
    character_ids: ['ch1'],
    world_state: {},
    dm_settings: {},
    created_at: '2024-01-01',
    updated_at: '2024-01-01',
  },
]

describe('Home', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(getCampaigns).mockResolvedValue([])
  })

  it('shows loading state initially', () => {
    vi.mocked(getCampaigns).mockReturnValue(new Promise(() => {}))
    render(
      <MemoryRouter>
        <Home />
      </MemoryRouter>
    )
    expect(screen.getByText('Loading...')).toBeTruthy()
  })

  it('renders the app title after loading', async () => {
    render(
      <MemoryRouter>
        <Home />
      </MemoryRouter>
    )
    await waitFor(() => {
      expect(screen.getByText(/dungeon master/i)).toBeTruthy()
    })
  })

  it('renders campaign list with fetched data', async () => {
    vi.mocked(getCampaigns).mockResolvedValue(mockCampaigns)
    render(
      <MemoryRouter>
        <Home />
      </MemoryRouter>
    )
    await waitFor(() => {
      expect(screen.getByTestId('campaign-count').textContent).toBe('1')
    })
  })

  it('shows error message on fetch failure', async () => {
    vi.mocked(getCampaigns).mockRejectedValue(new Error('Network error'))
    render(
      <MemoryRouter>
        <Home />
      </MemoryRouter>
    )
    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeTruthy()
    })
  })

  it('navigates to campaign detail on select', async () => {
    vi.mocked(getCampaigns).mockResolvedValue(mockCampaigns)
    render(
      <MemoryRouter>
        <Home />
      </MemoryRouter>
    )
    await waitFor(() => {
      expect(screen.getByTestId('campaign-c1')).toBeTruthy()
    })
    fireEvent.click(screen.getByTestId('campaign-c1'))
    expect(mockNavigate).toHaveBeenCalledWith('/campaign/c1')
  })

  it('shows create form when create button is clicked', async () => {
    render(
      <MemoryRouter>
        <Home />
      </MemoryRouter>
    )
    await waitFor(() => {
      expect(screen.getByTestId('create-btn')).toBeTruthy()
    })
    fireEvent.click(screen.getByTestId('create-btn'))
    expect(screen.getByLabelText('Name')).toBeTruthy()
    expect(screen.getByLabelText('Description')).toBeTruthy()
  })

  it('creates campaign and refreshes list', async () => {
    vi.mocked(getCampaigns).mockResolvedValueOnce([]).mockResolvedValueOnce(mockCampaigns)
    vi.mocked(createCampaign).mockResolvedValue(mockCampaigns[0])

    render(
      <MemoryRouter>
        <Home />
      </MemoryRouter>
    )
    await waitFor(() => {
      expect(screen.getByTestId('create-btn')).toBeTruthy()
    })

    fireEvent.click(screen.getByTestId('create-btn'))
    fireEvent.change(screen.getByLabelText('Name'), { target: { value: 'Lost Mine' } })
    fireEvent.change(screen.getByLabelText('Description'), { target: { value: 'A classic adventure' } })
    fireEvent.submit(screen.getByRole('form'))

    await waitFor(() => {
      expect(createCampaign).toHaveBeenCalledWith({
        name: 'Lost Mine',
        description: 'A classic adventure',
      })
    })
    await waitFor(() => {
      expect(screen.getByTestId('campaign-count').textContent).toBe('1')
    })
  })
})
