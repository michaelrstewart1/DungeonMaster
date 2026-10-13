import { describe, expect, it } from 'vitest';
import { suggestedRollModifier } from './rollModifier';

const thorne = {
  name: 'Thorne Ironfist',
  level: 3,
  class_name: 'fighter',
  strength: 16,
  dexterity: 12,
  constitution: 16,
  intelligence: 10,
  wisdom: 10,
  charisma: 8,
};

const lyra = {
  name: 'Lyra Moonwhisper',
  level: 3,
  class_name: 'wizard',
  strength: 8,
  dexterity: 14,
  constitution: 12,
  intelligence: 18,
  wisdom: 12,
  charisma: 10,
};

const kael = {
  name: 'Kael Shadowstep',
  level: 3,
  class_name: 'rogue',
  strength: 10,
  dexterity: 18,
  constitution: 12,
  intelligence: 12,
  wisdom: 14,
  charisma: 10,
};

describe('suggestedRollModifier', () => {
  it('uses Strength and proficiency for a fighter attack', () => {
    const text = 'Roll an attack roll for your warhammer, Thorne! This will be a d20 + your Strength modifier + your proficiency bonus.';
    expect(suggestedRollModifier(thorne, text)).toBe(5);
  });

  it('uses Intelligence and proficiency for a wizard Arcana check with no skills list', () => {
    const text = 'Lyra, make a DC 15 Intelligence (Arcana) check.';
    expect(suggestedRollModifier(lyra, text)).toBe(6);
  });

  it('does not add proficiency when the sheet lists other skills and omits Arcana', () => {
    const text = 'Lyra, make a DC 15 Intelligence (Arcana) check.';
    expect(suggestedRollModifier({ ...lyra, skills: ['history'] }, text)).toBe(4);
  });

  it('uses Dexterity and proficiency for a rogue Stealth check', () => {
    const text = 'Kael, make a DC 12 Dexterity (Stealth) check.';
    expect(suggestedRollModifier(kael, text)).toBe(6);
  });

  it('leaves a manual modifier alone when the text is not a roll request', () => {
    expect(suggestedRollModifier(thorne, 'The firelight flickers across the bar.')).toBeNull();
  });
});
