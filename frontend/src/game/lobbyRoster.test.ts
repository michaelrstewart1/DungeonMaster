import { describe, expect, it } from 'vitest';
import { lobbyRoster } from './lobbyRoster';

describe('lobbyRoster', () => {
  it('drops stale seats and duplicate names', () => {
    const rows = lobbyRoster([
      { id: 'p1', name: 'Aria' },
      { id: 'p2', name: 'Cyra', present: false },
      { id: 'p3', name: 'Cyra' },
      { id: 'p4', name: ' cyra ' },
      { id: 'p5', name: 'Dain' },
    ]);
    expect(rows.map((row) => row.id)).toEqual(['p1', 'p3', 'p5']);
  });
});
