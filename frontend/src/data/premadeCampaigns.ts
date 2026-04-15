import type { CampaignCreate } from '../types'

export interface PremadeCampaign extends CampaignCreate {
  id: string
  icon: string
  theme: string
  levelRange: string
  playerCount: string
  thumbnail: string
}

export const PREMADE_CAMPAIGNS: PremadeCampaign[] = [
  {
    id: 'wrath-of-the-stormspire',
    icon: '⛈️',
    thumbnail: '/campaigns/wrath-of-the-stormspire.jpg',
    theme: 'Elemental / High Fantasy',
    levelRange: 'Levels 3–10',
    playerCount: '4–6 players',
    name: 'Wrath of the Stormspire',
    description:
      'A mythical citadel perched above the eternal cloud sea has gone silent. The Skylords — an order of dragonborn knights who patrolled the heavens on griffons — have vanished. Unnatural violet storms now choke the mountain passes, and crystalline shards rain down at night, burning everything they touch. The Alliance of Lowland Lords has hired your party to ascend the Stormspire, breach the Bastion, and discover what silenced the Skylords before the storms consume the realm below.',
    world_state: {
      context:
        'The Stormspire is a mountain so tall its peak pierces the cloud sea. The Skylord Bastion at its summit once kept peace between surface kingdoms and elemental powers. Elemental hazards, sky-pirate outposts, and ancient wind temples guard the ascent. The storms grow worse each day.',
      setting: 'Stormspire Mountains & the Skylord Bastion',
      tone: 'dark_fantasy',
    },
    dm_settings: {
      difficulty: 'challenging',
      combat_frequency: 'balanced',
      roleplay_emphasis: 'high',
    },
  },
  {
    id: 'the-drowned-throne',
    icon: '🌊',
    thumbnail: '/campaigns/the-drowned-throne.jpg',
    theme: 'Oceanic / Horror',
    levelRange: 'Levels 1–8',
    playerCount: '3–5 players',
    name: 'The Drowned Throne',
    description:
      'The coastal city of Saltmere is sinking. Not slowly — whole districts vanish overnight into churning sinkholes that fill with black seawater. Survivors speak of pale figures glimpsed in the depths, and fishermen pull up nets tangled with gold coins minted by a kingdom that drowned a thousand years ago. An ancient merfolk empire is rising from the ocean floor, and its undead king believes Saltmere was built on stolen land. Your party must navigate flooded ruins, negotiate with deep-sea factions, and decide: save the city, or let the sea reclaim what was always hers.',
    world_state: {
      context:
        'Saltmere is a prosperous port city built on the ruins of the sunken merfolk empire of Thalassyr. The Drowned King Nethys has awakened and commands legions of undead sailors and corrupted sea creatures. The city has weeks before it sinks entirely. Underwater dungeons, haunted shipwrecks, and a kraken cultist faction complicate matters.',
      setting: 'Saltmere & the Sunken Empire of Thalassyr',
      tone: 'dark_fantasy',
    },
    dm_settings: {
      difficulty: 'moderate',
      combat_frequency: 'balanced',
      roleplay_emphasis: 'high',
    },
  },
  {
    id: 'ember-of-the-last-god',
    icon: '🔥',
    thumbnail: '/campaigns/ember-of-the-last-god.jpg',
    theme: 'Apocalyptic / Divine',
    levelRange: 'Levels 5–12',
    playerCount: '4–6 players',
    name: 'Ember of the Last God',
    description:
      'The gods are dead. All but one. Somewhere in the Ashfields — a continent-spanning wasteland left by the Godswar — the last divine spark flickers inside a child who doesn\'t know what they carry. Every faction on the continent wants that ember: the Iron Theocracy wants to resurrect their war god, the Arcane Collective wants to dissect divinity itself, and the Hollow Court of liches wants to snuff it out forever. Your party has been entrusted with the child\'s protection. The journey across the Ashfields will test every alliance, every moral boundary, and every blade you carry.',
    world_state: {
      context:
        'The Godswar destroyed the pantheon and scorched the continent into the Ashfields. Divine magic is dying — clerics lose their powers, holy sites crumble. A child named Sola carries the last ember of divine power. Three major factions hunt her. The Ashfields are filled with god-corpse dungeons, wild magic storms, and settlements fighting over dwindling resources.',
      setting: 'The Ashfields — post-divine apocalypse wasteland',
      tone: 'gritty',
    },
    dm_settings: {
      difficulty: 'hard',
      combat_frequency: 'high',
      roleplay_emphasis: 'high',
    },
  },
  {
    id: 'carnival-of-stolen-faces',
    icon: '🎭',
    thumbnail: '/campaigns/carnival-of-stolen-faces.jpg',
    theme: 'Mystery / Feywild',
    levelRange: 'Levels 2–7',
    playerCount: '3–6 players',
    name: 'Carnival of Stolen Faces',
    description:
      'A traveling carnival has arrived in the town of Willowmere, and everyone is delighted — except the people who\'ve started waking up with someone else\'s face. The Carnival of Wonders is run by an archfey called the Mirthless Prince, who collects identities like others collect coins. His performers are all stolen people, trapped in roles they can never leave. When one of your party members looks in a mirror and sees a stranger staring back, the clock starts ticking. You have three nights of carnival to find the Prince, break his collection, and reclaim what was taken — all while navigating fey bargains where every deal has a hidden cost.',
    world_state: {
      context:
        'The Carnival of Wonders appears in a new town each full moon, hosted by the Mirthless Prince — an archfey banished from the Seelie Court for his obsession with mortal identity. The carnival exists in a pocket dimension overlapping the Feywild. Each tent holds a different challenge. Fey rules apply: names have power, gifts create debts, and nothing is what it seems.',
      setting: 'Willowmere & the Carnival of Wonders (Feywild pocket)',
      tone: 'storybook',
    },
    dm_settings: {
      difficulty: 'moderate',
      combat_frequency: 'low',
      roleplay_emphasis: 'very_high',
    },
  },
  {
    id: 'iron-oath-of-karak-dum',
    icon: '⛏️',
    thumbnail: '/campaigns/iron-oath-of-karak-dum.jpg',
    theme: 'Dungeon Crawl / Dwarven',
    levelRange: 'Levels 3–9',
    playerCount: '4–6 players',
    name: 'Iron Oath of Karak-Dum',
    description:
      'Karak-Dum was the greatest dwarven citadel ever carved — a city of a hundred thousand souls built into the heart of a volcano. Two centuries ago, the dwarves sealed it shut from the inside. No one knows why. Now the mountain trembles, and the sealed gates have cracked open six inches. Steam and screams pour from the gap. The last descendant of Karak-Dum\'s royal line has gathered your party to enter the citadel, discover what forced the sealing, and fulfill the Iron Oath — a blood pact sworn by her ancestors that can only be completed in the throne room, thirty levels below the surface.',
    world_state: {
      context:
        'Karak-Dum is a massive vertical dungeon built into Mount Ashengaard. Thirty levels descend from the surface gates to the Molten Throne at the volcano\'s heart. Each level was a district: forges, temples, markets, noble halls, and deep mines. Something corrupted the lower levels — the dwarves sealed them to contain it. Now the corruption is breaking through. Expect traps, undead dwarves, lava hazards, and ancient constructs still following two-hundred-year-old orders.',
      setting: 'Mount Ashengaard & the sealed citadel of Karak-Dum',
      tone: 'dark_fantasy',
    },
    dm_settings: {
      difficulty: 'challenging',
      combat_frequency: 'high',
      roleplay_emphasis: 'moderate',
    },
  },
]
