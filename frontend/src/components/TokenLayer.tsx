import React from 'react'
import './TokenLayer.css'

export interface TokenInfo {
  entity_id: string
  name: string
  x: number
  y: number
  hp: number
  max_hp: number
  is_player: boolean
}

interface TokenLayerProps {
  tokens: TokenInfo[]
  selectedTokenId?: string
  onSelect?: (entityId: string) => void
}

const TokenLayer: React.FC<TokenLayerProps> = ({
  tokens,
  selectedTokenId,
  onSelect,
}) => {
  return (
    <div className="token-layer">
      <div className="token-list">
        {tokens.map((token) => {
          const isDefeated = token.hp <= 0
          const isSelected = token.entity_id === selectedTokenId

          return (
            <button
              key={token.entity_id}
              data-testid={`token-${token.entity_id}`}
              className={`token-item ${
                token.is_player ? 'token-player' : 'token-monster'
              } ${isSelected ? 'token-item-active' : ''} ${
                isDefeated ? 'token-defeated' : ''
              }`}
              onClick={() => onSelect?.(token.entity_id)}
            >
              <div className="token-header">
                <span className="token-name">{token.name}</span>
                <span className="token-position">
                  ({token.x}, {token.y})
                </span>
              </div>
              <div className="token-stats">
                <div className="token-hp">
                  {isDefeated ? (
                    <span className="defeated-label">Defeated</span>
                  ) : (
                    <>
                      <span className="hp-value">{token.hp}</span>/
                      <span className="hp-max">{token.max_hp}</span> HP
                    </>
                  )}
                </div>
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}

export default TokenLayer
