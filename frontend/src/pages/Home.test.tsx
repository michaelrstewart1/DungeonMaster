import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { Home } from './Home'

// Mock the CampaignList component
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

describe('Home', () => {
  beforeEach(() => {
    mockNavigate.mockClear()
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([]),
    })
  })

  it('renders the app title', () => {
    render(
      <MemoryRouter>
        <Home />
      </MemoryRouter>
    )
    expect(screen.getByText(/dungeon master/i)).toBeTruthy()
  })

  it('renders campaign list', async () => {
    render(
      <MemoryRouter>
        <Home />
      </MemoryRouter>
    )
    expect(screen.getByTestId('campaign-list')).toBeTruthy()
  })
})
