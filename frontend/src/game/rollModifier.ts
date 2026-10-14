/**
 * The modifier a check or attack should show on the dice tab.
 * Premade heroes often have no skills array; class defaults fill that gap
 * so a wizard's Arcana check is not rolled at +0.
 */

export type AbilityName =
  | 'strength'
  | 'dexterity'
  | 'constitution'
  | 'intelligence'
  | 'wisdom'
  | 'charisma';

export interface RollCharacter {
  level?: number;
  proficiency_bonus?: number;
  class_name?: string;
  strength?: number;
  dexterity?: number;
  constitution?: number;
  intelligence?: number;
  wisdom?: number;
  charisma?: number;
  skills?: string[];
  saving_throws?: string[];
}

const SKILL_ABILITY: Record<string, AbilityName> = {
  athletics: 'strength',
  acrobatics: 'dexterity',
  sleightofhand: 'dexterity',
  stealth: 'dexterity',
  arcana: 'intelligence',
  history: 'intelligence',
  investigation: 'intelligence',
  nature: 'intelligence',
  religion: 'intelligence',
  animalhandling: 'wisdom',
  insight: 'wisdom',
  medicine: 'wisdom',
  perception: 'wisdom',
  survival: 'wisdom',
  deception: 'charisma',
  intimidation: 'charisma',
  performance: 'charisma',
  persuasion: 'charisma',
};

const CLASS_ATTACK: Record<string, AbilityName> = {
  barbarian: 'strength',
  fighter: 'strength',
  paladin: 'strength',
  cleric: 'wisdom',
  druid: 'wisdom',
  monk: 'dexterity',
  ranger: 'dexterity',
  rogue: 'dexterity',
  bard: 'charisma',
  warlock: 'charisma',
  sorcerer: 'charisma',
  wizard: 'intelligence',
};

const CLASS_SAVES: Record<string, AbilityName[]> = {
  barbarian: ['strength', 'constitution'],
  bard: ['dexterity', 'charisma'],
  cleric: ['wisdom', 'charisma'],
  druid: ['intelligence', 'wisdom'],
  fighter: ['strength', 'constitution'],
  monk: ['strength', 'dexterity'],
  paladin: ['wisdom', 'charisma'],
  ranger: ['strength', 'dexterity'],
  rogue: ['dexterity', 'intelligence'],
  sorcerer: ['constitution', 'charisma'],
  warlock: ['wisdom', 'charisma'],
  wizard: ['intelligence', 'wisdom'],
};

/** Used only when the sheet didn't record skill proficiencies. */
const CLASS_DEFAULT_SKILLS: Record<string, string[]> = {
  barbarian: ['athletics', 'perception'],
  bard: ['persuasion', 'deception', 'performance'],
  cleric: ['insight', 'religion'],
  druid: ['nature', 'perception'],
  fighter: ['athletics', 'perception'],
  monk: ['acrobatics', 'stealth'],
  paladin: ['athletics', 'persuasion'],
  ranger: ['stealth', 'perception', 'survival'],
  rogue: ['stealth', 'acrobatics', 'sleightofhand', 'perception'],
  sorcerer: ['arcana', 'persuasion'],
  warlock: ['arcana', 'deception'],
  wizard: ['arcana', 'investigation'],
};

function norm(value: string): string {
  return value.toLowerCase().replace(/[^a-z]/g, '');
}

export function abilityModifier(score: number | undefined): number {
  const n = Number(score);
  if (!Number.isFinite(n)) return 0;
  return Math.floor((n - 10) / 2);
}

export function proficiencyBonus(character: RollCharacter): number {
  const level = Math.max(1, Number(character.level) || 1);
  const computed = Math.floor((level - 1) / 4) + 2;
  if (typeof character.proficiency_bonus === 'number' && character.proficiency_bonus > 0) {
    return character.proficiency_bonus;
  }
  return computed;
}

function classKey(character: RollCharacter): string {
  return (character.class_name || '').toLowerCase();
}

function abilityFromText(text: string): AbilityName | null {
  const match = /\b(strength|dexterity|constitution|intelligence|wisdom|charisma)\b/i.exec(text);
  return match ? (match[1].toLowerCase() as AbilityName) : null;
}

const SKILL_LABELS: Array<[string, string]> = [
  ['sleight of hand', 'sleightofhand'],
  ['animal handling', 'animalhandling'],
  ['acrobatics', 'acrobatics'],
  ['athletics', 'athletics'],
  ['arcana', 'arcana'],
  ['history', 'history'],
  ['investigation', 'investigation'],
  ['nature', 'nature'],
  ['religion', 'religion'],
  ['insight', 'insight'],
  ['medicine', 'medicine'],
  ['perception', 'perception'],
  ['survival', 'survival'],
  ['deception', 'deception'],
  ['intimidation', 'intimidation'],
  ['performance', 'performance'],
  ['persuasion', 'persuasion'],
  ['stealth', 'stealth'],
];

function skillFromText(text: string): string | null {
  const paren = /\(([A-Za-z][A-Za-z\s]+)\)/.exec(text);
  if (paren) {
    const key = norm(paren[1]);
    if (SKILL_ABILITY[key]) return key;
  }
  for (const [label, key] of SKILL_LABELS) {
    if (new RegExp(`\\b${label}\\b`, 'i').test(text)) return key;
  }
  return null;
}

function isSkillProficient(character: RollCharacter, skill: string): boolean {
  const listed = (character.skills || []).map(norm).filter(Boolean);
  if (listed.length > 0) return listed.includes(skill);
  const defaults = CLASS_DEFAULT_SKILLS[classKey(character)] || [];
  return defaults.includes(skill);
}

function isSaveProficient(character: RollCharacter, ability: AbilityName): boolean {
  const listed = (character.saving_throws || []).map(norm);
  if (listed.length > 0) return listed.includes(norm(ability)) || listed.includes(ability.slice(0, 3));
  return (CLASS_SAVES[classKey(character)] || []).includes(ability);
}

function clamp(modifier: number): number {
  return Math.max(-10, Math.min(10, modifier));
}

/**
 * Modifier for the check the DM just asked for.
 * Returns null when the text isn't a roll request, so a manual modifier stays.
 */
export function suggestedRollModifier(
  character: RollCharacter | null | undefined,
  requestText: string,
): number | null {
  if (!character || !requestText.trim()) return null;
  const text = requestText;
  const prof = proficiencyBonus(character);
  const skill = skillFromText(text);

  if (/\b(saving throw|save)\b/i.test(text)) {
    const ability = abilityFromText(text);
    if (!ability) return null;
    const mod = abilityModifier(character[ability]);
    return clamp(mod + (isSaveProficient(character, ability) ? prof : 0));
  }

  if (/\b(attack roll|to hit|melee attack|ranged attack|spell attack)\b/i.test(text)) {
    const ability = abilityFromText(text) || CLASS_ATTACK[classKey(character)] || 'strength';
    const mentionsProf = /\bproficiency\b/i.test(text);
    // Weapon and spell attacks add proficiency. A bare ability mention in an
    // attack request still does — "Strength modifier + your proficiency bonus".
    const addProf = mentionsProf || /\b(attack|to hit)\b/i.test(text);
    return clamp(abilityModifier(character[ability]) + (addProf ? prof : 0));
  }

  if (skill && (/\bcheck\b/i.test(text) || /\bdc\s*\d+/i.test(text) || /\broll\b/i.test(text))) {
    const ability = SKILL_ABILITY[skill];
    const mod = abilityModifier(character[ability]);
    return clamp(mod + (isSkillProficient(character, skill) ? prof : 0));
  }

  if (/\b(ability check|check)\b/i.test(text)) {
    const ability = abilityFromText(text);
    if (!ability) return null;
    const mod = abilityModifier(character[ability]);
    const addProf = /\bproficiency\b/i.test(text);
    return clamp(mod + (addProf ? prof : 0));
  }

  // "d20 + your Strength modifier + your proficiency bonus" with no other label.
  if (/\bd20\b/i.test(text) && /\bproficiency\b/i.test(text)) {
    const ability = abilityFromText(text);
    if (ability) return clamp(abilityModifier(character[ability]) + prof);
  }

  return null;
}
