import { describe, expect, it } from 'vitest';
import { parseDiceNotation, rollDiceNotation } from './diceRoll';

describe('rollDiceNotation', () => {
  it('adds the modifier into the total', () => {
    const result = rollDiceNotation('1d20+5', () => 0.65);
    expect(result).not.toBeNull();
    expect(result?.rolls).toEqual([14]);
    expect(result?.modifier).toBe(5);
    expect(result?.total).toBe(19);
    expect(result?.is_critical).toBe(false);
  });

  it('keeps a natural 20 critical and still adds the modifier', () => {
    const result = rollDiceNotation('1d20+6', () => 0.99);
    expect(result?.rolls).toEqual([20]);
    expect(result?.total).toBe(26);
    expect(result?.is_critical).toBe(true);
  });

  it('parses a bare d20 as modifier 0', () => {
    expect(parseDiceNotation('1d20')).toEqual({
      count: 1,
      sides: 20,
      modifier: 0,
      explicitModifier: false,
    });
  });
});
