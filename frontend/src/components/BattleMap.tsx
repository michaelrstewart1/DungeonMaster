import React from 'react'
import type { GameMap } from '../types'
import './BattleMap.css'

interface BattleMapProps {
  map: GameMap
  onCellClick?: (x: number, y: number) => void
  onTokenMove?: (entityId: string, x: number, y: number) => void
  selectedTokenId?: string
}

const BattleMap: React.FC<BattleMapProps> = ({
  map,
  onCellClick,
  selectedTokenId,
}) => {
  // Create a map of token positions for quick lookup
  const tokenMap = new Map(map.tokens.map((token) => [`${token.x}-${token.y}`, token]))

  // Generate column labels (A, B, C, ...)
  const columnLabels = Array.from({ length: map.width }, (_, i) =>
    String.fromCharCode(65 + i)
  )

  return (
    <div className="battle-map">
      <table className="battle-map-grid">
        <thead>
          <tr>
            <th className="corner-header"></th>
            {columnLabels.map((label) => (
              <th key={label} className="column-header">
                {label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: map.height }, (_, rowIndex) => (
            <tr key={rowIndex}>
              <th className="row-header">{rowIndex + 1}</th>
              {Array.from({ length: map.width }, (_, colIndex) => {
                const terrain = map.terrain[rowIndex]?.[colIndex] || 'empty'
                const hasFog = map.fog_of_war[rowIndex]?.[colIndex]
                const token = tokenMap.get(`${colIndex}-${rowIndex}`)
                const isSelected = token?.entity_id === selectedTokenId

                return (
                  <td
                    key={`${colIndex}-${rowIndex}`}
                    data-testid={`cell-${colIndex}-${rowIndex}`}
                    className={`cell cell-${terrain} ${hasFog ? 'cell-fog' : ''}`}
                    onClick={() => onCellClick?.(colIndex, rowIndex)}
                  >
                    {token && (
                      <div
                        className={`token ${isSelected ? 'token-selected' : ''}`}
                      >
                        {token.entity_id}
                      </div>
                    )}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default BattleMap
