import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { CampaignList } from './CampaignList'
import type { Campaign } from '../types'

describe('CampaignList', () => {
  const mockOnSelect = vi.fn()
  const mockOnCreate = vi.fn()

  const campaigns: Campaign[] = [
    {
      id: 'c1',
      name: 'Lost Mine of Phandelver',
      description: 'A classic starter adventure',
      character_ids: ['ch1', 'ch2'],
      world_state: {},
      dm_settings: {},
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-02T00:00:00Z',
    },
    {
      id: 'c2',
      name: 'Curse of Strahd',
      description: 'Gothic horror in Barovia',
      character_ids: [],
      world_state: {},
      dm_settings: {},
      created_at: '2025-01-03T00:00:00Z',
      updated_at: '2025-01-03T00:00:00Z',
    },
  ]

  beforeEach(() => {
    mockOnSelect.mockClear()
    mockOnCreate.mockClear()
  })

  it('renders campaign names', () => {
    render(<CampaignList campaigns={campaigns} onSelect={mockOnSelect} onCreate={mockOnCreate} />)
    expect(screen.getByText('Lost Mine of Phandelver')).toBeTruthy()
    expect(screen.getByText('Curse of Strahd')).toBeTruthy()
  })

  it('renders campaign descriptions', () => {
    render(<CampaignList campaigns={campaigns} onSelect={mockOnSelect} onCreate={mockOnCreate} />)
    expect(screen.getByText('A classic starter adventure')).toBeTruthy()
    expect(screen.getByText('Gothic horror in Barovia')).toBeTruthy()
  })

  it('calls onSelect when a campaign is clicked', () => {
    render(<CampaignList campaigns={campaigns} onSelect={mockOnSelect} onCreate={mockOnCreate} />)
    fireEvent.click(screen.getByText('Lost Mine of Phandelver'))
    expect(mockOnSelect).toHaveBeenCalledWith('c1')
  })

  it('shows player count', () => {
    render(<CampaignList campaigns={campaigns} onSelect={mockOnSelect} onCreate={mockOnCreate} />)
    expect(screen.getByText(/2 players/i)).toBeTruthy()
    expect(screen.getByText(/0 players/i)).toBeTruthy()
  })

  it('renders a create button', () => {
    render(<CampaignList campaigns={campaigns} onSelect={mockOnSelect} onCreate={mockOnCreate} />)
    const btn = screen.getByRole('button', { name: /new campaign|create/i })
    fireEvent.click(btn)
    expect(mockOnCreate).toHaveBeenCalled()
  })

  it('shows empty state when no campaigns', () => {
    render(<CampaignList campaigns={[]} onSelect={mockOnSelect} onCreate={mockOnCreate} />)
    expect(screen.getByText(/no campaigns/i)).toBeTruthy()
  })
})
