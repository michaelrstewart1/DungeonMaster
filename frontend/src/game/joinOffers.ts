import type { PreMadeCharacter } from '../data/premadeCharacters';
import type { CharacterCreate } from '../types';

/** A hero already on the campaign, claimed or not. */
export interface PartyHero {
  id: string;
  name: string;
  race: string;
  class_name: string;
  level: number;
  portrait_url?: string;
}

/** One card in the phone join picker. */
export interface HeroOffer {
  key: string;
  name: string;
  race: string;
  class_name: string;
  level: number;
  portrait_url?: string;
  /** Set when this card claims an existing party row. */
  characterId?: string;
  /** Set when claiming creates the pre-made hero first. */
  premadeId?: string;
}

function norm(name: string): string {
  return name.trim().toLowerCase();
}

/**
 * Cards a joining phone may pick.
 *
 * Unclaimed party members stay (including custom heroes). A pre-made hero
 * whose name is already in the party is not offered twice. Claimed character
 * ids are omitted — another player cannot take them.
 */
export function joinHeroOffers(
  party: PartyHero[],
  premades: PreMadeCharacter[],
  taken: Record<string, string>,
): HeroOffer[] {
  const partyNames = new Set(party.map((hero) => norm(hero.name)));
  const offers: HeroOffer[] = [];

  for (const hero of party) {
    if (taken[hero.id]) continue;
    offers.push({
      key: hero.id,
      characterId: hero.id,
      name: hero.name,
      race: hero.race,
      class_name: hero.class_name,
      level: hero.level,
      portrait_url: hero.portrait_url,
    });
  }

  for (const premade of premades) {
    if (partyNames.has(norm(premade.name))) continue;
    offers.push({
      key: premade.id,
      premadeId: premade.id,
      name: premade.name,
      race: premade.race,
      class_name: premade.class_name,
      level: premade.level,
      portrait_url: premade.portrait,
    });
  }

  return offers;
}

/** Body for POST /characters. Matches the host picker: no catalog id, portrait renamed. */
export function premadeCreateBody(premade: PreMadeCharacter, campaignId: string): CharacterCreate {
  const { id: _id, backstory: _backstory, equipment: _equipment, portrait, ...rest } = premade;
  return { ...rest, portrait_url: portrait, campaign_id: campaignId };
}
