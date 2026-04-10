import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import userEvent from '@testing-library/user-event'
import TokenLayer from './TokenLayer'
import type { TokenInfo } from './TokenLayer'

describe('TokenLayer', () => {
  const createMockToken = (
    entityId: string = 'token-1',
    overrides: Partial<TokenInfo> = {}
  ): TokenInfo => ({
    entity_id: entityId,
    name: `Token ${entityId}`,
    x: 1,
    y: 1,
    hp: 10,
    max_hp: 10,
    is_player: false,
    ...overrides,
  })

  it('renders all tokens in the list', () => {
    const tokens: TokenInfo[] = [
      createMockToken('token-1'),
      createMockToken('token-2'),
      createMockToken('token-3'),
    ]

    render(<TokenLayer tokens={tokens} />)

    expect(screen.getByText('Token token-1')).toBeInTheDocument()
    expect(screen.getByText('Token token-2')).toBeInTheDocument()
    expect(screen.getByText('Token token-3')).toBeInTheDocument()
  })

  it('shows token name, position, and HP', () => {
    const tokens: TokenInfo[] = [
      createMockToken('wizard', {
        name: 'Gandalf the Grey',
        x: 5,
        y: 3,
        hp: 12,
        max_hp: 15,
      }),
    ]

    render(<TokenLayer tokens={tokens} />)

    // Check that token appears in document
    const tokenElement = screen.getByTestId('token-wizard')
    expect(tokenElement).toBeInTheDocument()

    // Check name
    expect(tokenElement.textContent).toContain('Gandalf the Grey')

    // Check position
    expect(tokenElement.textContent).toContain('5')
    expect(tokenElement.textContent).toContain('3')

    // Check HP
    expect(tokenElement.textContent).toContain('12')
    expect(tokenElement.textContent).toContain('15')
  })

  it('calls onSelect when a token is clicked', async () => {
    const tokens: TokenInfo[] = [createMockToken('wizard')]
    const onSelect = vi.fn()
    const user = userEvent.setup()

    render(<TokenLayer tokens={tokens} onSelect={onSelect} />)

    const tokenButton = screen.getByTestId('token-wizard')
    await user.click(tokenButton)

    expect(onSelect).toHaveBeenCalledWith('wizard')
  })

  it('applies active class to selected token', () => {
    const tokens: TokenInfo[] = [
      createMockToken('token-1'),
      createMockToken('token-2'),
    ]

    const { container } = render(
      <TokenLayer tokens={tokens} selectedTokenId="token-1" />
    )

    const token1 = container.querySelector('[data-testid="token-token-1"]')
    const token2 = container.querySelector('[data-testid="token-token-2"]')

    expect(token1).toHaveClass('token-item-active')
    expect(token2).not.toHaveClass('token-item-active')
  })

  it('styles player tokens differently from monsters', () => {
    const tokens: TokenInfo[] = [
      createMockToken('player-warrior', { is_player: true }),
      createMockToken('goblin-1', { is_player: false }),
    ]

    const { container } = render(<TokenLayer tokens={tokens} />)

    const playerToken = container.querySelector(
      '[data-testid="token-player-warrior"]'
    )
    const monsterToken = container.querySelector(
      '[data-testid="token-goblin-1"]'
    )

    expect(playerToken).toHaveClass('token-player')
    expect(monsterToken).toHaveClass('token-monster')
  })

  it('shows defeated status for zero HP tokens', () => {
    const tokens: TokenInfo[] = [
      createMockToken('wizard', {
        hp: 0,
        max_hp: 10,
      }),
    ]

    render(<TokenLayer tokens={tokens} />)

    const tokenElement = screen.getByTestId('token-wizard')
    expect(tokenElement.textContent).toContain('Defeated')
  })

  it('renders empty list without errors', () => {
    const { container } = render(<TokenLayer tokens={[]} />)
    expect(container.querySelector('.token-layer')).toBeInTheDocument()
  })
})
