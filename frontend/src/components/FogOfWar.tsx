import { type FC, useCallback } from 'react';

interface FogOfWarProps {
  grid: string[][];
  revealed: Set<string>;
  isDM: boolean;
  onReveal: (x: number, y: number) => void;
}

const FogOfWar: FC<FogOfWarProps> = ({ grid, revealed, isDM, onReveal }) => {
  const handleCellClick = useCallback(
    (x: number, y: number) => {
      if (isDM) {
        onReveal(x, y);
      }
    },
    [isDM, onReveal]
  );

  const height = grid.length;
  const width = height > 0 ? grid[0].length : 0;

  return (
    <div
      data-testid="fog-overlay"
      style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${width}, 1fr)`,
        gridTemplateRows: `repeat(${height}, 1fr)`,
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: isDM ? 'auto' : 'none',
      }}
    >
      {Array.from({ length: height }).map((_, y) =>
        Array.from({ length: width }).map((_, x) => {
          const key = `${x},${y}`;
          const isRevealed = revealed.has(key);

          return (
            <div
              key={key}
              data-testid={`fog-cell-${x}-${y}`}
              className={`fog-cell ${isRevealed ? 'revealed' : 'fogged'} ${
                !isDM ? 'disabled' : ''
              }`}
              onClick={() => handleCellClick(x, y)}
              style={{
                cursor: isDM ? 'pointer' : 'default',
                backgroundColor: isRevealed ? 'transparent' : 'rgba(0, 0, 0, 0.7)',
                width: '100%',
                height: '100%',
                transition: 'background-color 0.2s ease',
              }}
            />
          );
        })
      )}
    </div>
  );
};

export default FogOfWar;
