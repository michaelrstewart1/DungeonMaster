import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import App from './App'

vi.mock('./api/client', () => ({
  getCampaigns: vi.fn().mockResolvedValue([]),
  createCampaign: vi.fn(),
  getCampaign: vi.fn().mockResolvedValue({ id: '1', name: 'Test', description: '', character_ids: [], world_state: {}, dm_settings: {}, created_at: '', updated_at: '' }),
  getCharacters: vi.fn().mockResolvedValue([]),
  createCharacter: vi.fn(),
  createGameSession: vi.fn(),
}))

beforeEach(() => {
  vi.clearAllMocks()
})

describe('App', () => {
  it('renders without crashing', () => {
    render(<App />)
    expect(document.body).toBeTruthy()
  })

  it('renders the app with router', () => {
    const { container } = render(<App />)
    expect(container.querySelector('.app')).toBeTruthy()
  })
})
