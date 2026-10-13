import type { DiceResult } from '../types';

export interface ParsedDice {
  count: number;
  sides: number;
  modifier: number;
  /** True when the notation itself wrote a +N or -N, including +0. */
  explicitModifier: boolean;
}

/** Parse `1d20+5` / `2d6-1`. Returns null for anything that isn't dice notation. */
export function parseDiceNotation(notation: string): ParsedDice | null {
  const match = /^\s*(\d+)d(\d+)\s*([+-]\s*\d+)?\s*$/i.exec(notation || '');
  if (!match) return null;
  const modifier = match[3] ? parseInt(match[3].replace(/\s/g, ''), 10) : 0;
  return {
    count: parseInt(match[1], 10),
    sides: parseInt(match[2], 10),
    modifier: Number.isFinite(modifier) ? modifier : 0,
    explicitModifier: Boolean(match[3]),
  };
}

/**
 * Roll the notation, including its modifier in the total.
 * `1d20+5` with a face of 14 totals 19, not 14.
 * `adv:1d20+6` rolls two fresh d20s and keeps the higher. It does not take
 * a previous roll as an input.
 */
export function rollDiceNotation(
  notation: string,
  rng: () => number = Math.random,
): DiceResult | null {
  const advantage = notation.startsWith('adv:');
  const body = advantage ? notation.slice(4) : notation;
  const parsed = parseDiceNotation(body);
  if (!parsed || parsed.count < 1 || parsed.sides < 1) return null;
  if (advantage) {
    if (parsed.count !== 1 || parsed.sides !== 20) return null;
    const first = Math.floor(rng() * 20) + 1;
    const second = Math.floor(rng() * 20) + 1;
    const kept = Math.max(first, second);
    return {
      notation,
      rolls: [first, second],
      modifier: parsed.modifier,
      total: kept + parsed.modifier,
      is_critical: kept === 20,
      is_fumble: kept === 1,
    };
  }
  const rolls = Array.from({ length: parsed.count }, () => Math.floor(rng() * parsed.sides) + 1);
  const total = rolls.reduce((sum, face) => sum + face, 0) + parsed.modifier;
  const natural = rolls[0];
  return {
    notation,
    rolls,
    modifier: parsed.modifier,
    total,
    is_critical: parsed.sides === 20 && parsed.count === 1 && natural === 20,
    is_fumble: parsed.sides === 20 && parsed.count === 1 && natural === 1,
  };
}
