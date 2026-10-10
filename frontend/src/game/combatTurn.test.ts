import { describe, expect, it } from 'vitest';
import type { CombatState } from '../types';
import {
  applyHpUpdates,
  diceRollLine,
  inferEngineAction,
  initiativeAnnouncement,
  initiativeChips,
  isDiceRollReport,
  seatMayActAs,
  toCombatantDisplays,
} from './combatTurn';

const state: CombatState = {
  round_number: 1,
  current_turn_index: 0,
  initiative_order: ['Kael Shadowstep', 'Lyra Moonwhisper', 'Hostile Creature'],
  combatants: [
    { id: 'kael', name: 'Kael Shadowstep', is_player: true, initiative: 18, hp: 24, max_hp: 24, ac: 15 },
    { id: 'lyra', name: 'Lyra Moonwhisper', is_player: true, initiative: 11, hp: 18, max_hp: 18, ac: 12 },
    { id: 'enemy-1', name: 'Hostile Creature', is_player: false, initiative: 7, hp: 30, max_hp: 30, ac: 13 },
  ],
};

describe('initiative display', () => {
  it('uses rolled totals in turn order, not placeholder ranks', () => {
    const chips = initiativeChips(state);
    expect(chips.map((c) => c.name)).toEqual(state.initiative_order);
    expect(chips.map((c) => c.initiative)).toEqual([18, 11, 7]);
    // The old host panel showed length, length-1, … (3, 2, 1) for this fight.
    expect(chips.map((c) => c.initiative)).not.toEqual([3, 2, 1]);
    expect(toCombatantDisplays(state).map((c) => c.initiative)).toEqual([18, 11, 7]);
  });

  it('keeps a rolled zero instead of inventing a rank', () => {
    const zeroed: CombatState = {
      ...state,
      combatants: state.combatants!.map((c, i) => (i === 1 ? { ...c, initiative: 0 } : c)),
    };
    expect(initiativeChips(zeroed).map((c) => c.initiative)).toEqual([18, 0, 7]);
  });

  it('announces the same order with totals and does not ask for a roll', () => {
    const text = initiativeAnnouncement(state);
    expect(text).toBe('Combat begins. Initiative: Kael Shadowstep 18, Lyra Moonwhisper 11, Hostile Creature 7.');
    expect(text.toLowerCase()).not.toContain('roll');
  });

  it('phone chips and host rows are the same order', () => {
    const chips = initiativeChips(state);
    const rows = toCombatantDisplays(state);
    expect(rows.map((r) => r.name)).toEqual(chips.map((c) => c.name));
    expect(rows.map((r) => r.initiative)).toEqual(chips.map((c) => c.initiative));
    expect(rows.map((r) => r.is_current)).toEqual(chips.map((c) => c.isCurrent));
  });
});

describe('combat text', () => {
  it('treats a typed attack and the Attack button label as the same action', () => {
    expect(inferEngineAction('Kael fires his shortbow at the tall robed leader.')).toBe('attack');
    expect(inferEngineAction('⚔️ Attack')).toBe('attack');
    expect(inferEngineAction('🛡️ Defend')).toBe('dodge');
    expect(inferEngineAction('💊 Use Potion')).toBe('heal');
  });

  it('recognizes a dice-tab initiative report', () => {
    expect(isDiceRollReport('🎲 Kael Shadowstep rolls d20: 15')).toBe(true);
    expect(diceRollLine('Kael Shadowstep', '1d20', 15)).toBe('🎲 Kael Shadowstep rolls d20: 15');
  });

  it('includes a set modifier in the log total', () => {
    expect(diceRollLine('Thorne Ironfist', '1d20+5', 19)).toBe('🎲 Thorne Ironfist rolls d20 (14) + 5 = 19');
    expect(diceRollLine('Kael Shadowstep', '1d20+6', 26, ' (Natural 20!)'))
      .toBe('🎲 Kael Shadowstep rolls d20 (20) + 6 = 26 (Natural 20!)');
    expect(isDiceRollReport('🎲 Thorne Ironfist rolls d20 (14) + 5 = 19')).toBe(true);
  });

  it('does not treat an HP report as an attack', () => {
    expect(inferEngineAction('Thorne takes 14 damage (11 slashing + 3 lightning) and is now at 20 of 34 HP.')).toBeNull();
  });
});

describe('seatMayActAs', () => {
  const players = [
    { id: 'dain', characterId: 'kael' },
    { id: 'cyra', characterId: 'lyra' },
  ];

  it('allows the seat that owns the character once the roster is in', () => {
    expect(seatMayActAs({
      playerId: 'dain',
      characterId: 'kael',
      players,
      rosterReady: true,
    })).toBe(true);
  });

  it('refuses a seat that does not own the character, even on that character\'s turn', () => {
    expect(seatMayActAs({
      playerId: 'cyra',
      characterId: 'kael',
      players,
      rosterReady: true,
    })).toBe(false);
  });

  it('does not claim the turn before the roster confirms ownership', () => {
    expect(seatMayActAs({
      playerId: 'dain',
      characterId: 'kael',
      players: [],
      rosterReady: false,
    })).toBe(false);
  });

  it('skips the check when there is no joined seat (solo table)', () => {
    expect(seatMayActAs({
      playerId: '',
      characterId: 'kael',
      players: [],
      rosterReady: false,
    })).toBe(true);
  });
});

describe('applyHpUpdates', () => {
  it('writes the server total onto the matching character', () => {
    const party = [{ id: 'thorne', name: 'Thorne Ironfist', hp: 34, max_hp: 34 }];
    const next = applyHpUpdates(party, [{ character_id: 'thorne', hp: 20, max_hp: 34 }]);
    expect(next[0].hp).toBe(20);
    expect(party[0].hp).toBe(34);
  });
});
