import type { CombatState } from '../types';
import { parseDiceNotation } from './diceRoll';

/** One row in the turn order, shared by the phone strip and the TV. */
export interface InitiativeChip {
  id: string;
  name: string;
  /** Rules-engine total (d20 + Dex). Null only when the server sent no roll. */
  initiative: number | null;
  isCurrent: boolean;
  hp?: number;
  maxHp?: number;
}

export type EngineAction = 'attack' | 'dodge' | 'heal';

const ATTACK_RE = /\b(attack|attacks|attacking|shoot|shoots|shooting|fire|fires|firing|strike|strikes|striking|swing|swings|swinging|stab|stabs|stabbing|slash|slashes|slashing|bow|hit|hits|hitting|cast|casts|casting|spell|spells)\b/i;
const HP_REPORT_RE = /\b(?:takes|take|took|suffers|suffered)\s+\d+\s+(?:points of\s+)?damage\b|(?:now at|down to)\s+\d+\s+(?:of|\/)\s+\d+/i;
const HEAL_RE = /\b(potion|potions|heal|heals|healing|drink|drinks|drinking)\b/i;
const DODGE_RE = /\b(dodge|dodges|dodging|defend|defends|defending|defense|defensive|retreat|retreats|retreating|flee|flees|fleeing|disengage)\b/i;
const DICE_RE = /\brolls?\s+d\d+\b/i;

/**
 * Same classification the server uses for a typed combat line.
 * Attack wording wins over a dice report.
 */
export function inferEngineAction(text: string): EngineAction | null {
  if (HP_REPORT_RE.test(text)) return null;
  if (ATTACK_RE.test(text)) return 'attack';
  if (HEAL_RE.test(text)) return 'heal';
  if (DODGE_RE.test(text)) return 'dodge';
  return null;
}

/** A dice-tab report ("Kael rolls d20: 15"), not a request to build the order. */
export function isDiceRollReport(text: string): boolean {
  return DICE_RE.test(text);
}

export function initiativeChips(state: CombatState | null | undefined): InitiativeChip[] {
  if (!state?.initiative_order?.length) return [];
  return state.initiative_order.map((name, idx) => {
    const cb = state.combatants?.find((c) => c.name === name || c.id === name);
    const initiative = typeof cb?.initiative === 'number' ? cb.initiative : null;
    return {
      id: cb?.id || `${name}-${idx}`,
      name: cb?.name || name,
      initiative,
      isCurrent: idx === state.current_turn_index,
      hp: cb?.hp,
      maxHp: cb?.max_hp,
    };
  });
}

/** Host initiative panel rows. Numbers are the rolled totals, never n, n-1, …. */
export function toCombatantDisplays(state: CombatState | null | undefined) {
  return initiativeChips(state).map((c) => ({
    id: c.id,
    name: c.name,
    initiative: c.initiative ?? 0,
    hp: c.hp ?? 0,
    max_hp: c.maxHp ?? 0,
    is_current: c.isCurrent,
  }));
}

/** Live announcement when combat starts. Does not ask anyone to roll. */
export function initiativeAnnouncement(state: CombatState | null | undefined): string {
  const chips = initiativeChips(state);
  if (!chips.length) return 'Combat begins.';
  const parts = chips.map((c) => (c.initiative == null ? c.name : `${c.name} ${c.initiative}`));
  return `Combat begins. Initiative: ${parts.join(', ')}.`;
}

export function diceRollLine(name: string, notation: string, total: number, note = ''): string {
  const parsed = parseDiceNotation(notation);
  if (!parsed) {
    const die = /d(\d+)/i.exec(notation || '');
    const label = die ? `d${die[1]}` : (notation || 'dice');
    return `🎲 ${name} rolls ${label}: ${total}${note}`;
  }
  const label = parsed.count === 1 ? `d${parsed.sides}` : `${parsed.count}d${parsed.sides}`;
  if (!parsed.explicitModifier && parsed.modifier === 0) {
    return `🎲 ${name} rolls ${label}: ${total}${note}`;
  }
  const diceSum = total - parsed.modifier;
  const sign = parsed.modifier >= 0 ? '+' : '-';
  const magnitude = Math.abs(parsed.modifier);
  return `🎲 ${name} rolls ${label} (${diceSum}) ${sign} ${magnitude} = ${total}${note}`;
}

export interface HpUpdate {
  character_id?: string;
  name?: string;
  hp: number;
  max_hp?: number;
}

/** Merge a server HP push into the phone header or the TV party list. */
export function applyHpUpdates<T extends { id: string; name?: string; hp: number; max_hp?: number }>(
  characters: T[],
  updates: HpUpdate[] | null | undefined,
): T[] {
  if (!updates?.length) return characters;
  return characters.map((character) => {
    const update = updates.find((entry) => (
      (entry.character_id && entry.character_id === character.id)
      || (entry.name && character.name && entry.name.toLowerCase() === character.name.toLowerCase())
    ));
    if (!update) return character;
    return {
      ...character,
      hp: update.hp,
      max_hp: update.max_hp ?? character.max_hp,
    };
  });
}

export interface SeatPlayer {
  id: string;
  characterId?: string;
}

/**
 * Whether this phone may act as `characterId`.
 * Mirrors the server: once players have joined, the seat's player id must own
 * that character. With no player id (solo table) the server skips the check.
 * Before the roster arrives, do not claim the turn — the banner would disagree
 * with the rejection the server is about to send.
 */
export function seatMayActAs(opts: {
  playerId: string;
  characterId?: string;
  players: SeatPlayer[];
  rosterReady: boolean;
}): boolean {
  if (!opts.characterId) return false;
  if (!opts.playerId) return true;
  if (!opts.rosterReady) return false;
  const me = opts.players.find((p) => p.id === opts.playerId);
  return !!me && me.characterId === opts.characterId;
}
