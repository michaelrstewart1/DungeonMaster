import { describe, it, expect, vi } from 'vitest';
import { render } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import FogOfWar from './FogOfWar';

describe('FogOfWar', () => {
  const mockGrid = [
    ['empty', 'empty', 'empty'],
    ['empty', 'empty', 'empty'],
    ['empty', 'empty', 'empty'],
  ];

  describe('rendering', () => {
    it('renders as overlay on grid', () => {
      const revealed = new Set<string>();
      const { container } = render(
        <FogOfWar
          grid={mockGrid}
          revealed={revealed}
          isDM={false}
          onReveal={() => {}}
        />
      );

      const overlay = container.querySelector('[data-testid="fog-overlay"]');
      expect(overlay).toBeInTheDocument();
    });

    it('creates cells for each grid position', () => {
      const revealed = new Set<string>();
      const { container } = render(
        <FogOfWar
          grid={mockGrid}
          revealed={revealed}
          isDM={false}
          onReveal={() => {}}
        />
      );

      const cells = container.querySelectorAll('[data-testid^="fog-cell"]');
      expect(cells).toHaveLength(9); // 3x3 grid
    });
  });

  describe('fog state', () => {
    it('shows hidden cells as opaque/dark', () => {
      const revealed = new Set<string>();
      const { container } = render(
        <FogOfWar
          grid={mockGrid}
          revealed={revealed}
          isDM={false}
          onReveal={() => {}}
        />
      );

      const cells = container.querySelectorAll('[data-testid^="fog-cell"]');
      cells.forEach((cell) => {
        expect(cell).toHaveClass('fogged');
      });
    });

    it('shows revealed cells as transparent', () => {
      const revealed = new Set(['0,0', '1,1', '2,2']);
      const { container } = render(
        <FogOfWar
          grid={mockGrid}
          revealed={revealed}
          isDM={false}
          onReveal={() => {}}
        />
      );

      const cell00 = container.querySelector('[data-testid="fog-cell-0-0"]');
      const cell11 = container.querySelector('[data-testid="fog-cell-1-1"]');
      const cell22 = container.querySelector('[data-testid="fog-cell-2-2"]');
      const cell01 = container.querySelector('[data-testid="fog-cell-0-1"]');

      expect(cell00).toHaveClass('revealed');
      expect(cell11).toHaveClass('revealed');
      expect(cell22).toHaveClass('revealed');
      expect(cell01).toHaveClass('fogged');
    });
  });

  describe('DM interactions', () => {
    it('allows DM to click cells to toggle reveal state', async () => {
      const user = userEvent.setup();
      const onReveal = vi.fn();
      const revealed = new Set<string>();

      const { container } = render(
        <FogOfWar
          grid={mockGrid}
          revealed={revealed}
          isDM={true}
          onReveal={onReveal}
        />
      );

      const cell = container.querySelector('[data-testid="fog-cell-0-0"]');
      await user.click(cell!);

      expect(onReveal).toHaveBeenCalledWith(0, 0);
    });

    it('calls onReveal with x,y coordinates when DM clicks', async () => {
      const user = userEvent.setup();
      const onReveal = vi.fn();
      const revealed = new Set<string>();

      const { container } = render(
        <FogOfWar
          grid={mockGrid}
          revealed={revealed}
          isDM={true}
          onReveal={onReveal}
        />
      );

      const cell21 = container.querySelector('[data-testid="fog-cell-2-1"]');
      await user.click(cell21!);

      expect(onReveal).toHaveBeenCalledWith(2, 1);
    });

    it('makes cells clickable when isDM is true', async () => {
      const revealed = new Set<string>();
      const { container } = render(
        <FogOfWar
          grid={mockGrid}
          revealed={revealed}
          isDM={true}
          onReveal={() => {}}
        />
      );

      const cells = container.querySelectorAll('[data-testid^="fog-cell"]');
      cells.forEach((cell) => {
        expect(cell).not.toHaveClass('disabled');
      });
    });

    it('makes cells not clickable when isDM is false', () => {
      const revealed = new Set<string>();
      const { container } = render(
        <FogOfWar
          grid={mockGrid}
          revealed={revealed}
          isDM={false}
          onReveal={() => {}}
        />
      );

      const cells = container.querySelectorAll('[data-testid^="fog-cell"]');
      cells.forEach((cell) => {
        expect(cell).toHaveClass('disabled');
      });
    });
  });

  describe('player view', () => {
    it('does not show a click handler for players', async () => {
      const onReveal = vi.fn();
      const revealed = new Set(['0,0']);

      const { container } = render(
        <FogOfWar
          grid={mockGrid}
          revealed={revealed}
          isDM={false}
          onReveal={onReveal}
        />
      );

      const overlay = container.querySelector('[data-testid="fog-overlay"]');
      // Players should have pointer-events: none
      expect(overlay).toHaveStyle('pointer-events: none');
    });

    it('only shows revealed cells to players', () => {
      const revealed = new Set(['0,0', '2,2']);
      const { container } = render(
        <FogOfWar
          grid={mockGrid}
          revealed={revealed}
          isDM={false}
          onReveal={() => {}}
        />
      );

      const cell00 = container.querySelector('[data-testid="fog-cell-0-0"]');
      const cell22 = container.querySelector('[data-testid="fog-cell-2-2"]');
      const cell11 = container.querySelector('[data-testid="fog-cell-1-1"]');

      expect(cell00).toHaveClass('revealed');
      expect(cell22).toHaveClass('revealed');
      expect(cell11).toHaveClass('fogged');
    });
  });

  describe('grid updates', () => {
    it('updates when grid prop changes', () => {
      const revealed = new Set<string>();
      const { container, rerender } = render(
        <FogOfWar
          grid={mockGrid}
          revealed={revealed}
          isDM={false}
          onReveal={() => {}}
        />
      );

      let cells = container.querySelectorAll('[data-testid^="fog-cell"]');
      expect(cells).toHaveLength(9);

      const largerGrid = [
        ['empty', 'empty', 'empty', 'empty'],
        ['empty', 'empty', 'empty', 'empty'],
        ['empty', 'empty', 'empty', 'empty'],
        ['empty', 'empty', 'empty', 'empty'],
      ];

      rerender(
        <FogOfWar
          grid={largerGrid}
          revealed={revealed}
          isDM={false}
          onReveal={() => {}}
        />
      );

      cells = container.querySelectorAll('[data-testid^="fog-cell"]');
      expect(cells).toHaveLength(16); // 4x4 grid
    });

    it('updates when revealed set changes', () => {
      const { container, rerender } = render(
        <FogOfWar
          grid={mockGrid}
          revealed={new Set<string>()}
          isDM={false}
          onReveal={() => {}}
        />
      );

      let cell00 = container.querySelector('[data-testid="fog-cell-0-0"]');
      expect(cell00).toHaveClass('fogged');

      rerender(
        <FogOfWar
          grid={mockGrid}
          revealed={new Set(['0,0'])}
          isDM={false}
          onReveal={() => {}}
        />
      );

      cell00 = container.querySelector('[data-testid="fog-cell-0-0"]');
      expect(cell00).toHaveClass('revealed');
    });
  });
});
