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
      locations: [
        { id: 'basecamp-thornwall', name: 'Thornwall Basecamp', description: 'The Alliance staging camp at the foot of the Stormspire, tents snapping in the rising wind.', scene_type: 'village', connections: ['shattered-switchbacks', 'pirate-roost'] },
        { id: 'shattered-switchbacks', name: 'The Shattered Switchbacks', description: 'Crumbling mountain trail littered with crystalline storm-shards that hum before they burn.', scene_type: 'mountain', connections: ['basecamp-thornwall', 'wind-temple'] },
        { id: 'pirate-roost', name: 'Sky-Pirate Roost', description: 'A ramshackle outpost of grounded skyships, its crews trading rumor and stolen griffon tack.', scene_type: 'tavern', connections: ['basecamp-thornwall', 'wind-temple'] },
        { id: 'wind-temple', name: 'Temple of the Four Gales', description: 'An ancient wind temple whose bells ring backward when the violet storms pass overhead.', scene_type: 'temple', connections: ['shattered-switchbacks', 'pirate-roost', 'cloudsea-gate'] },
        { id: 'cloudsea-gate', name: 'Cloudsea Gate', description: 'The last threshold above the cloud sea, where the Skylords once mustered their griffon wings.', scene_type: 'ruins', connections: ['wind-temple', 'skylord-bastion'] },
        { id: 'skylord-bastion', name: 'The Skylord Bastion', description: 'The silent citadel at the summit, wrapped in a crown of unending violet lightning.', scene_type: 'dungeon', connections: ['cloudsea-gate'] },
      ],
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
      locations: [
        { id: 'saltmere-docks', name: 'Saltmere Docks', description: 'The last dry district of a sinking city, crowded with refugees and doom-saying fishermen.', scene_type: 'city', connections: ['drowned-quarter', 'wrecker-reef'] },
        { id: 'drowned-quarter', name: 'The Drowned Quarter', description: 'Flooded streets where rooftops serve as walkways and pale figures move beneath the water.', scene_type: 'ruins', connections: ['saltmere-docks', 'kraken-shrine'] },
        { id: 'wrecker-reef', name: 'Wrecker\u2019s Reef', description: 'A graveyard of haunted shipwrecks picked over by smugglers and worse things.', scene_type: 'coast', connections: ['saltmere-docks', 'kraken-shrine'] },
        { id: 'kraken-shrine', name: 'Shrine of the Deep Coil', description: 'A barnacled shrine where kraken cultists barter drowned gold for terrible favors.', scene_type: 'temple', connections: ['drowned-quarter', 'wrecker-reef', 'thalassyr-gates'] },
        { id: 'thalassyr-gates', name: 'Gates of Thalassyr', description: 'Coral-crusted gates of the sunken empire, rising inch by inch from the ocean floor.', scene_type: 'ruins', connections: ['kraken-shrine', 'drowned-throne'] },
        { id: 'drowned-throne', name: 'The Drowned Throne', description: 'The abyssal throne room of King Nethys, lit by ghost-light and the glitter of stolen crowns.', scene_type: 'dungeon', connections: ['thalassyr-gates'] },
      ],
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
      locations: [
        { id: 'cinder-market', name: 'Cinder Market', description: 'A fortified trade settlement built in the ribcage of a fallen god, neutral ground for now.', scene_type: 'town', connections: ['ash-wastes', 'pilgrim-road'] },
        { id: 'ash-wastes', name: 'The Ash Wastes', description: 'Endless grey dunes where wild magic storms rewrite the horizon every night.', scene_type: 'road', connections: ['cinder-market', 'godcorpse-vault'] },
        { id: 'pilgrim-road', name: 'The Pilgrim Road', description: 'A cracked highway of dead faiths, lined with toppled idols and desperate caravans.', scene_type: 'road', connections: ['cinder-market', 'theocracy-bastion'] },
        { id: 'theocracy-bastion', name: 'Iron Theocracy Bastion', description: 'A war-fortress of the god-resurrectionists, its furnaces burning relics for fuel.', scene_type: 'city', connections: ['pilgrim-road', 'godcorpse-vault'] },
        { id: 'godcorpse-vault', name: 'The God-Corpse Vault', description: 'A dungeon hollowed from a divine skull, where dead miracles still twitch in the dark.', scene_type: 'dungeon', connections: ['ash-wastes', 'theocracy-bastion', 'last-ember-sanctum'] },
        { id: 'last-ember-sanctum', name: 'Sanctum of the Last Ember', description: 'The hidden refuge where the final divine spark waits — and every faction converges.', scene_type: 'temple', connections: ['godcorpse-vault'] },
      ],
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
      locations: [
        { id: 'willowmere-square', name: 'Willowmere Town Square', description: 'A cheerful market town gone uneasy, where neighbors no longer recognize each other\u2019s faces.', scene_type: 'village', connections: ['carnival-gates', 'mirror-maze'] },
        { id: 'carnival-gates', name: 'The Carnival Gates', description: 'Striped tents and impossible lanterns marking the threshold between Willowmere and the Feywild.', scene_type: 'road', connections: ['willowmere-square', 'menagerie-tent', 'hall-of-masks'] },
        { id: 'mirror-maze', name: 'The Mirror Maze', description: 'A labyrinth of glass where reflections lag half a heartbeat behind — or act on their own.', scene_type: 'ruins', connections: ['willowmere-square', 'hall-of-masks'] },
        { id: 'menagerie-tent', name: 'The Impossible Menagerie', description: 'Cages of creatures that should not exist, each one whispering bargains through the bars.', scene_type: 'forest', connections: ['carnival-gates', 'princes-pavilion'] },
        { id: 'hall-of-masks', name: 'The Hall of Masks', description: 'A gallery of stolen faces hung like trophies, each mask warm to the touch.', scene_type: 'dungeon', connections: ['carnival-gates', 'mirror-maze', 'princes-pavilion'] },
        { id: 'princes-pavilion', name: 'The Mirthless Prince\u2019s Pavilion', description: 'The heart of the carnival, where the archfey holds court and every deal has a hidden cost.', scene_type: 'temple', connections: ['menagerie-tent', 'hall-of-masks'] },
      ],
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
      locations: [
        { id: 'ashengaard-gates', name: 'The Cracked Gates', description: 'The sealed surface gates of Karak-Dum, now open six inches and breathing steam and screams.', scene_type: 'mountain', connections: ['forge-district', 'market-warrens'] },
        { id: 'forge-district', name: 'The Forge District', description: 'Cold anvils and dead furnaces, patrolled by constructs still following two-century-old orders.', scene_type: 'dungeon', connections: ['ashengaard-gates', 'temple-of-stone'] },
        { id: 'market-warrens', name: 'The Market Warrens', description: 'Collapsed trade halls where undead merchants still haggle over dust and bones.', scene_type: 'ruins', connections: ['ashengaard-gates', 'temple-of-stone'] },
        { id: 'temple-of-stone', name: 'Temple of the Stone Fathers', description: 'A desecrated dwarven temple whose runes flicker between blessing and warning.', scene_type: 'temple', connections: ['forge-district', 'market-warrens', 'deep-mines'] },
        { id: 'deep-mines', name: 'The Deep Mines', description: 'Lava-lit shafts descending toward the corruption the dwarves died to contain.', scene_type: 'cave', connections: ['temple-of-stone', 'molten-throne'] },
        { id: 'molten-throne', name: 'The Molten Throne', description: 'The throne room at the volcano\u2019s heart, where the Iron Oath must finally be fulfilled.', scene_type: 'dungeon', connections: ['deep-mines'] },
      ],
    },
    dm_settings: {
      difficulty: 'challenging',
      combat_frequency: 'high',
      roleplay_emphasis: 'moderate',
    },
  },
]
