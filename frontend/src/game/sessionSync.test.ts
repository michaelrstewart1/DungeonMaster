import { describe, expect, it } from 'vitest';
import { acceptSessionSnapshot } from './sessionSync';

const lighthouse = {
  id: 'sess-live',
  state_version: 4,
  current_phase: 'exploration',
  current_scene: 'The lighthouse antechamber',
  combat_state: {
    initiative_order: ['ashara', 'lyra', 'undead-1'],
    round_number: 1,
    current_turn_index: 0,
  },
};

describe('acceptSessionSnapshot', () => {
  it('ignores a snapshot for a different session', () => {
    const decision = acceptSessionSnapshot(
      { ...lighthouse, id: 'sess-old' },
      'sess-live',
      4,
    );
    expect(decision.accepted).toBe(false);
  });

  it('ignores an older revision of the same session', () => {
    const decision = acceptSessionSnapshot(
      { ...lighthouse, state_version: 2, current_phase: 'combat' },
      'sess-live',
      4,
    );
    expect(decision.accepted).toBe(false);
    if (!decision.accepted) expect(decision.version).toBe(4);
  });

  it('clears combat when the authoritative phase is exploration', () => {
    const decision = acceptSessionSnapshot(lighthouse, 'sess-live', 3);
    expect(decision.accepted).toBe(true);
    if (decision.accepted) {
      expect(decision.phase).toBe('exploration');
      expect(decision.combat).toBeNull();
      expect(decision.version).toBe(4);
    }
  });

  it('keeps combat only when the phase is combat and initiative is present', () => {
    const decision = acceptSessionSnapshot(
      {
        ...lighthouse,
        state_version: 5,
        current_phase: 'combat',
        current_scene: 'Blackwood',
      },
      'sess-live',
      4,
    );
    expect(decision.accepted).toBe(true);
    if (decision.accepted) {
      expect(decision.phase).toBe('combat');
      expect(decision.combat?.initiative_order).toEqual(['ashara', 'lyra', 'undead-1']);
    }
  });

  it('does not treat a combat phase with an empty initiative list as a fight', () => {
    const decision = acceptSessionSnapshot(
      { id: 'sess-live', state_version: 2, current_phase: 'combat', combat_state: { initiative_order: [] } },
      'sess-live',
      0,
    );
    expect(decision.accepted).toBe(true);
    if (decision.accepted) expect(decision.combat).toBeNull();
  });
});
