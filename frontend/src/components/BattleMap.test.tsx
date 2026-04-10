import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import userEvent from '@testing-library/user-event'
import BattleMap from './BattleMap'
import type { GameMap } from '../types'

describe('BattleMap', () => {
  const createMockMap = (width: number = 5, height: number = 5): GameMap => ({
    id: 'test-map',
    width,
    height,
    terrain: Array(height)
      .fill(null)
      .map(() => Array(width).fill('empty')),
    tokens: [],
    fog_of_war: Array(height)
      .fill(null)
      .map(() => Array(width).fill(false)),
  })

  it('renders grid with correct dimensions (5x5 map has 5 rows of 5 cells)', () => {
    const map = createMockMap(5, 5)
    render(<BattleMap map={map} />)

    const rows = screen.getAllByRole('row')
    // +1 for header row with column labels
    expect(rows).toHaveLength(6)

    // Check each row has 6 cells (+1 for row label)
    rows.forEach((row, index) => {
      if (index === 0) {
        // Header row with column labels
        const headerCells = row.querySelectorAll('th')
        expect(headerCells).toHaveLength(6) // corner + 5 columns
      } else {
        // Data rows: 1 row header (th) + 5 data cells (td)
        const headerCells = row.querySelectorAll('th')
        const dataCells = row.querySelectorAll('td')
        expect(headerCells).toHaveLength(1)
        expect(dataCells).toHaveLength(5)
      }
    })
  })

  it('applies terrain-type CSS class to cells', () => {
    const map: GameMap = {
      id: 'test-map',
      width: 3,
      height: 3,
      terrain: [
        ['empty', 'wall', 'water'],
        ['difficult', 'pit', 'empty'],
        ['wall', 'empty', 'empty'],
      ],
      tokens: [],
      fog_of_war: Array(3)
        .fill(null)
        .map(() => Array(3).fill(false)),
    }

    const { container } = render(<BattleMap map={map} />)

    // Find cells by data-testid (x is column, y is row)
    expect(container.querySelector('[data-testid="cell-0-0"]')).toHaveClass(
      'cell-empty'
    )
    expect(container.querySelector('[data-testid="cell-1-0"]')).toHaveClass(
      'cell-wall'
    )
    expect(container.querySelector('[data-testid="cell-2-0"]')).toHaveClass(
      'cell-water'
    )
    expect(container.querySelector('[data-testid="cell-0-1"]')).toHaveClass(
      'cell-difficult'
    )
    expect(container.querySelector('[data-testid="cell-1-1"]')).toHaveClass(
      'cell-pit'
    )
  })

  it('renders tokens at correct positions', () => {
    const map: GameMap = {
      id: 'test-map',
      width: 5,
      height: 5,
      terrain: Array(5)
        .fill(null)
        .map(() => Array(5).fill('empty')),
      tokens: [
        { entity_id: 'goblin-1', x: 1, y: 1 },
        { entity_id: 'goblin-2', x: 3, y: 2 },
      ],
      fog_of_war: Array(5)
        .fill(null)
        .map(() => Array(5).fill(false)),
    }

    const { container } = render(<BattleMap map={map} />)

    // Check tokens are in correct cells
    const token1Cell = container.querySelector('[data-testid="cell-1-1"]')
    expect(token1Cell?.textContent).toContain('goblin-1')

    const token2Cell = container.querySelector('[data-testid="cell-3-2"]')
    expect(token2Cell?.textContent).toContain('goblin-2')
  })

  it('shows token entity id/name', () => {
    const map: GameMap = {
      id: 'test-map',
      width: 5,
      height: 5,
      terrain: Array(5)
        .fill(null)
        .map(() => Array(5).fill('empty')),
      tokens: [{ entity_id: 'player-wizard', x: 2, y: 2 }],
      fog_of_war: Array(5)
        .fill(null)
        .map(() => Array(5).fill(false)),
    }

    render(<BattleMap map={map} />)

    expect(screen.getByText('player-wizard')).toBeInTheDocument()
  })

  it('calls onCellClick when a cell is clicked', async () => {
    const map = createMockMap(5, 5)
    const onCellClick = vi.fn()
    const user = userEvent.setup()

    const { container } = render(
      <BattleMap map={map} onCellClick={onCellClick} />
    )

    const cell = container.querySelector('[data-testid="cell-2-3"]') as HTMLElement
    await user.click(cell)

    expect(onCellClick).toHaveBeenCalledWith(2, 3)
  })

  it('highlights selected token with class', () => {
    const map: GameMap = {
      id: 'test-map',
      width: 5,
      height: 5,
      terrain: Array(5)
        .fill(null)
        .map(() => Array(5).fill('empty')),
      tokens: [
        { entity_id: 'token-1', x: 1, y: 1 },
        { entity_id: 'token-2', x: 3, y: 3 },
      ],
      fog_of_war: Array(5)
        .fill(null)
        .map(() => Array(5).fill(false)),
    }

    const { container } = render(
      <BattleMap map={map} selectedTokenId="token-1" />
    )

    const token1 = screen.getByText('token-1')
    const token2 = screen.getByText('token-2')

    expect(token1).toHaveClass('token-selected')
    expect(token2).not.toHaveClass('token-selected')
  })

  it('applies fog class to fogged cells', () => {
    const map: GameMap = {
      id: 'test-map',
      width: 3,
      height: 3,
      terrain: Array(3)
        .fill(null)
        .map(() => Array(3).fill('empty')),
      tokens: [],
      fog_of_war: [
        [true, false, true],
        [false, true, false],
        [true, false, true],
      ],
    }

    const { container } = render(<BattleMap map={map} />)

    expect(container.querySelector('[data-testid="cell-0-0"]')).toHaveClass(
      'cell-fog'
    )
    expect(container.querySelector('[data-testid="cell-0-1"]')).not.toHaveClass(
      'cell-fog'
    )
    expect(container.querySelector('[data-testid="cell-1-1"]')).toHaveClass(
      'cell-fog'
    )
    expect(container.querySelector('[data-testid="cell-2-2"]')).toHaveClass(
      'cell-fog'
    )
  })

  it('renders empty map without errors', () => {
    const map = createMockMap(5, 5)
    const { container } = render(<BattleMap map={map} />)

    expect(container.querySelector('table')).toBeInTheDocument()
    const rows = screen.getAllByRole('row')
    expect(rows.length).toBeGreaterThan(0)
  })

  it('displays grid coordinates (A1, B2, etc.)', () => {
    const map = createMockMap(5, 5)
    const { container } = render(<BattleMap map={map} />)

    // Check column headers (A, B, C, D, E)
    const headerRow = container.querySelector('thead tr')
    const headerCells = headerRow?.querySelectorAll('th')
    expect(headerCells?.[1]?.textContent).toBe('A')
    expect(headerCells?.[2]?.textContent).toBe('B')
    expect(headerCells?.[3]?.textContent).toBe('C')

    // Check row headers (1, 2, 3, 4, 5)
    const rows = container.querySelectorAll('tbody tr')
    const firstRowHeader = rows[0]?.querySelector('th')
    expect(firstRowHeader?.textContent).toBe('1')

    const secondRowHeader = rows[1]?.querySelector('th')
    expect(secondRowHeader?.textContent).toBe('2')
  })
})
