import { describe, expect, it } from 'vitest';
import { PRE_MADE_CHARACTERS } from '../data/premadeCharacters';
import { joinHeroOffers, premadeCreateBody, type PartyHero } from './joinOffers';

const thorne: PartyHero = {
  id: 'char-thorne',
  name: 'Thorne Ironfist',
  race: 'dwarf',
  class_name: 'fighter',
  level: 3,
  portrait_url: '/portraits/thorne.jpg',
};

describe('joinHeroOffers', () => {
  it('offers unclaimed pre-made heroes that are not already in the party', () => {
    const offers = joinHeroOffers([thorne], PRE_MADE_CHARACTERS, { 'char-thorne': 'Aria' });
    const names = offers.map((offer) => offer.name);
    expect(names).not.toContain('Thorne Ironfist');
    expect(names).toContain('Lyra Moonwhisper');
    expect(names).toContain('Kael Shadowstep');
    expect(offers.find((offer) => offer.name === 'Lyra Moonwhisper')?.premadeId).toBe('premade-lyra');
  });

  it('keeps an unclaimed party hero and does not duplicate that pre-made name', () => {
    const offers = joinHeroOffers([thorne], PRE_MADE_CHARACTERS, {});
    const thorneCards = offers.filter((offer) => offer.name === 'Thorne Ironfist');
    expect(thorneCards).toHaveLength(1);
    expect(thorneCards[0].characterId).toBe('char-thorne');
    expect(thorneCards[0].premadeId).toBeUndefined();
  });

  it('still offers a custom hero who is not in the pre-made catalog', () => {
    const custom: PartyHero = {
      id: 'char-custom',
      name: 'Bramble',
      race: 'gnome',
      class_name: 'bard',
      level: 2,
    };
    const offers = joinHeroOffers([thorne, custom], PRE_MADE_CHARACTERS, { 'char-thorne': 'Aria' });
    expect(offers.find((offer) => offer.characterId === 'char-custom')?.name).toBe('Bramble');
  });
});

describe('premadeCreateBody', () => {
  it('drops the catalog id and sends portrait_url plus the campaign', () => {
    const lyra = PRE_MADE_CHARACTERS.find((hero) => hero.id === 'premade-lyra');
    expect(lyra).toBeTruthy();
    const body = premadeCreateBody(lyra!, 'camp-1');
    expect(body).not.toHaveProperty('id');
    expect(body).not.toHaveProperty('portrait');
    expect(body).not.toHaveProperty('backstory');
    expect(body).not.toHaveProperty('equipment');
    expect(body.portrait_url).toBe('/portraits/lyra.jpg');
    expect(body.campaign_id).toBe('camp-1');
    expect(body.name).toBe('Lyra Moonwhisper');
  });
});
