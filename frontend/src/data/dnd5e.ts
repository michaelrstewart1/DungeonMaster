// ============================================================
// D&D 5e Character Creation Data
// Auto-generated — do not edit by hand
// ============================================================

export interface SubraceData {
  value: string;
  label: string;
  parentRace: string;
  abilityBonuses: Record<string, number>;
  traits: string[];
  traitDescriptions: Record<string, string>;
}

export interface SubclassData {
  value: string;
  label: string;
  parentClass: string;
  subclassLevel: number;
  features: { level: number; name: string; description: string }[];
}

export interface BackgroundData {
  value: string;
  label: string;
  skillProficiencies: string[];
  toolProficiencies: string[];
  languages: number;
  equipment: string[];
  feature: { name: string; description: string };
  personalityTraits: string[];
  ideals: string[];
  bonds: string[];
  flaws: string[];
}

export interface SkillData {
  value: string;
  label: string;
  ability: string;
  abilityShort: string;
  description: string;
}

export interface EquipmentChoice {
  label: string;
  options: string[][];
}

export interface SpellcastingInfo {
  ability: string;
  cantripsKnown: number;
  spellsKnownOrPrepared: number;
  spellSlots: number[];
}

// ============================================================
// SUBRACES
// ============================================================

export const SUBRACES: SubraceData[] = 
[
  {
    "value": "hill-dwarf",
    "label": "Hill Dwarf",
    "parentRace": "dwarf",
    "abilityBonuses": {
      "wisdom": 1
    },
    "traits": [
      "Dwarven Toughness"
    ],
    "traitDescriptions": {
      "Dwarven Toughness": "Your hit point maximum increases by 1, and it increases by 1 every time you gain a level."
    }
  },
  {
    "value": "mountain-dwarf",
    "label": "Mountain Dwarf",
    "parentRace": "dwarf",
    "abilityBonuses": {
      "strength": 2
    },
    "traits": [
      "Dwarven Armor Training"
    ],
    "traitDescriptions": {
      "Dwarven Armor Training": "You have proficiency with light and medium armor."
    }
  },
  {
    "value": "high-elf",
    "label": "High Elf",
    "parentRace": "elf",
    "abilityBonuses": {
      "intelligence": 1
    },
    "traits": [
      "Elf Weapon Training",
      "Cantrip",
      "Extra Language"
    ],
    "traitDescriptions": {
      "Elf Weapon Training": "You have proficiency with the longsword, shortsword, shortbow, and longbow.",
      "Cantrip": "You know one cantrip of your choice from the wizard spell list. Intelligence is your spellcasting ability for it.",
      "Extra Language": "You can speak, read, and write one extra language of your choice."
    }
  },
  {
    "value": "wood-elf",
    "label": "Wood Elf",
    "parentRace": "elf",
    "abilityBonuses": {
      "wisdom": 1
    },
    "traits": [
      "Elf Weapon Training",
      "Fleet of Foot",
      "Mask of the Wild"
    ],
    "traitDescriptions": {
      "Elf Weapon Training": "You have proficiency with the longsword, shortsword, shortbow, and longbow.",
      "Fleet of Foot": "Your base walking speed increases to 35 feet.",
      "Mask of the Wild": "You can attempt to hide even when you are only lightly obscured by natural phenomena."
    }
  },
  {
    "value": "dark-elf",
    "label": "Dark Elf (Drow)",
    "parentRace": "elf",
    "abilityBonuses": {
      "charisma": 1
    },
    "traits": [
      "Superior Darkvision",
      "Sunlight Sensitivity",
      "Drow Magic",
      "Drow Weapon Training"
    ],
    "traitDescriptions": {
      "Superior Darkvision": "Your darkvision has a radius of 120 feet.",
      "Sunlight Sensitivity": "You have disadvantage on attack rolls and Wisdom (Perception) checks that rely on sight when you or your target is in direct sunlight.",
      "Drow Magic": "You know the dancing lights cantrip. At 3rd level you can cast faerie fire once per long rest. At 5th level you can cast darkness once per long rest.",
      "Drow Weapon Training": "You have proficiency with rapiers, shortswords, and hand crossbows."
    }
  },
  {
    "value": "lightfoot-halfling",
    "label": "Lightfoot Halfling",
    "parentRace": "halfling",
    "abilityBonuses": {
      "charisma": 1
    },
    "traits": [
      "Naturally Stealthy"
    ],
    "traitDescriptions": {
      "Naturally Stealthy": "You can attempt to hide even when you are obscured only by a creature that is at least one size larger than you."
    }
  },
  {
    "value": "stout-halfling",
    "label": "Stout Halfling",
    "parentRace": "halfling",
    "abilityBonuses": {
      "constitution": 1
    },
    "traits": [
      "Stout Resilience"
    ],
    "traitDescriptions": {
      "Stout Resilience": "You have advantage on saving throws against poison, and you have resistance against poison damage."
    }
  },
  {
    "value": "standard-human",
    "label": "Standard Human",
    "parentRace": "human",
    "abilityBonuses": {},
    "traits": [
      "Versatile"
    ],
    "traitDescriptions": {
      "Versatile": "All ability scores increase by 1 (included in base race bonuses)."
    }
  },
  {
    "value": "variant-human",
    "label": "Variant Human",
    "parentRace": "human",
    "abilityBonuses": {},
    "traits": [
      "Two Ability Increases",
      "Skill Versatility",
      "Feat"
    ],
    "traitDescriptions": {
      "Two Ability Increases": "Two different ability scores of your choice each increase by 1 (replaces the standard +1 to all).",
      "Skill Versatility": "You gain proficiency in one skill of your choice.",
      "Feat": "You gain one feat of your choice."
    }
  },
  {
    "value": "black-dragon",
    "label": "Black Draconic Ancestry",
    "parentRace": "dragonborn",
    "abilityBonuses": {},
    "traits": [
      "Breath Weapon",
      "Damage Resistance"
    ],
    "traitDescriptions": {
      "Breath Weapon": "You can use your action to exhale acid damage in a 5x30 ft. line (DEX save). Damage is 2d6, scaling at higher levels.",
      "Damage Resistance": "You have resistance to acid damage."
    }
  },
  {
    "value": "blue-dragon",
    "label": "Blue Draconic Ancestry",
    "parentRace": "dragonborn",
    "abilityBonuses": {},
    "traits": [
      "Breath Weapon",
      "Damage Resistance"
    ],
    "traitDescriptions": {
      "Breath Weapon": "You can use your action to exhale lightning damage in a 5x30 ft. line (DEX save). Damage is 2d6, scaling at higher levels.",
      "Damage Resistance": "You have resistance to lightning damage."
    }
  },
  {
    "value": "brass-dragon",
    "label": "Brass Draconic Ancestry",
    "parentRace": "dragonborn",
    "abilityBonuses": {},
    "traits": [
      "Breath Weapon",
      "Damage Resistance"
    ],
    "traitDescriptions": {
      "Breath Weapon": "You can use your action to exhale fire damage in a 5x30 ft. line (DEX save). Damage is 2d6, scaling at higher levels.",
      "Damage Resistance": "You have resistance to fire damage."
    }
  },
  {
    "value": "bronze-dragon",
    "label": "Bronze Draconic Ancestry",
    "parentRace": "dragonborn",
    "abilityBonuses": {},
    "traits": [
      "Breath Weapon",
      "Damage Resistance"
    ],
    "traitDescriptions": {
      "Breath Weapon": "You can use your action to exhale lightning damage in a 5x30 ft. line (DEX save). Damage is 2d6, scaling at higher levels.",
      "Damage Resistance": "You have resistance to lightning damage."
    }
  },
  {
    "value": "copper-dragon",
    "label": "Copper Draconic Ancestry",
    "parentRace": "dragonborn",
    "abilityBonuses": {},
    "traits": [
      "Breath Weapon",
      "Damage Resistance"
    ],
    "traitDescriptions": {
      "Breath Weapon": "You can use your action to exhale acid damage in a 5x30 ft. line (DEX save). Damage is 2d6, scaling at higher levels.",
      "Damage Resistance": "You have resistance to acid damage."
    }
  },
  {
    "value": "gold-dragon",
    "label": "Gold Draconic Ancestry",
    "parentRace": "dragonborn",
    "abilityBonuses": {},
    "traits": [
      "Breath Weapon",
      "Damage Resistance"
    ],
    "traitDescriptions": {
      "Breath Weapon": "You can use your action to exhale fire damage in a 15 ft. cone (DEX save). Damage is 2d6, scaling at higher levels.",
      "Damage Resistance": "You have resistance to fire damage."
    }
  },
  {
    "value": "green-dragon",
    "label": "Green Draconic Ancestry",
    "parentRace": "dragonborn",
    "abilityBonuses": {},
    "traits": [
      "Breath Weapon",
      "Damage Resistance"
    ],
    "traitDescriptions": {
      "Breath Weapon": "You can use your action to exhale poison damage in a 15 ft. cone (CON save). Damage is 2d6, scaling at higher levels.",
      "Damage Resistance": "You have resistance to poison damage."
    }
  },
  {
    "value": "red-dragon",
    "label": "Red Draconic Ancestry",
    "parentRace": "dragonborn",
    "abilityBonuses": {},
    "traits": [
      "Breath Weapon",
      "Damage Resistance"
    ],
    "traitDescriptions": {
      "Breath Weapon": "You can use your action to exhale fire damage in a 15 ft. cone (DEX save). Damage is 2d6, scaling at higher levels.",
      "Damage Resistance": "You have resistance to fire damage."
    }
  },
  {
    "value": "silver-dragon",
    "label": "Silver Draconic Ancestry",
    "parentRace": "dragonborn",
    "abilityBonuses": {},
    "traits": [
      "Breath Weapon",
      "Damage Resistance"
    ],
    "traitDescriptions": {
      "Breath Weapon": "You can use your action to exhale cold damage in a 15 ft. cone (CON save). Damage is 2d6, scaling at higher levels.",
      "Damage Resistance": "You have resistance to cold damage."
    }
  },
  {
    "value": "white-dragon",
    "label": "White Draconic Ancestry",
    "parentRace": "dragonborn",
    "abilityBonuses": {},
    "traits": [
      "Breath Weapon",
      "Damage Resistance"
    ],
    "traitDescriptions": {
      "Breath Weapon": "You can use your action to exhale cold damage in a 15 ft. cone (CON save). Damage is 2d6, scaling at higher levels.",
      "Damage Resistance": "You have resistance to cold damage."
    }
  },
  {
    "value": "forest-gnome",
    "label": "Forest Gnome",
    "parentRace": "gnome",
    "abilityBonuses": {
      "dexterity": 1
    },
    "traits": [
      "Natural Illusionist",
      "Speak with Small Beasts"
    ],
    "traitDescriptions": {
      "Natural Illusionist": "You know the minor illusion cantrip. Intelligence is your spellcasting ability for it.",
      "Speak with Small Beasts": "Through sounds and gestures, you can communicate simple ideas with Small or smaller beasts."
    }
  },
  {
    "value": "rock-gnome",
    "label": "Rock Gnome",
    "parentRace": "gnome",
    "abilityBonuses": {
      "constitution": 1
    },
    "traits": [
      "Artificer's Lore",
      "Tinker"
    ],
    "traitDescriptions": {
      "Artificer's Lore": "Whenever you make an Intelligence (History) check related to magic items, alchemical objects, or technological devices, you add twice your proficiency bonus.",
      "Tinker": "You have proficiency with artisan's tools (tinker's tools). Using them, you can spend 1 hour and 10 gp to construct a Tiny clockwork device."
    }
  },
  {
    "value": "standard-half-elf",
    "label": "Standard Half-Elf",
    "parentRace": "half-elf",
    "abilityBonuses": {},
    "traits": [
      "Two Ability Increases",
      "Skill Versatility"
    ],
    "traitDescriptions": {
      "Two Ability Increases": "Two different ability scores of your choice each increase by 1 (in addition to +2 CHA from base race).",
      "Skill Versatility": "You gain proficiency in two skills of your choice."
    }
  },
  {
    "value": "standard-half-orc",
    "label": "Standard Half-Orc",
    "parentRace": "half-orc",
    "abilityBonuses": {},
    "traits": [
      "Menacing",
      "Relentless Endurance",
      "Savage Attacks"
    ],
    "traitDescriptions": {
      "Menacing": "You gain proficiency in the Intimidation skill.",
      "Relentless Endurance": "When you are reduced to 0 hit points but not killed outright, you can drop to 1 hit point instead. You must finish a long rest before using this again.",
      "Savage Attacks": "When you score a critical hit with a melee weapon attack, you can roll one of the damage dice one additional time and add it to the extra damage."
    }
  },
  {
    "value": "standard-tiefling",
    "label": "Standard Tiefling",
    "parentRace": "tiefling",
    "abilityBonuses": {},
    "traits": [
      "Infernal Legacy"
    ],
    "traitDescriptions": {
      "Infernal Legacy": "You know the thaumaturgy cantrip. At 3rd level you can cast hellish rebuke as a 2nd-level spell once per long rest. At 5th level you can cast darkness once per long rest."
    }
  }
];

// ============================================================
// SUBCLASSES
// ============================================================

export const SUBCLASSES: SubclassData[] = 
[
  {
    "value": "berserker",
    "label": "Path of the Berserker",
    "parentClass": "barbarian",
    "subclassLevel": 3,
    "features": [
      {
        "level": 3,
        "name": "Frenzy",
        "description": "While raging, you can choose to frenzy. You can make a single melee weapon attack as a bonus action on each of your turns. When the rage ends, you suffer one level of exhaustion."
      },
      {
        "level": 6,
        "name": "Mindless Rage",
        "description": "You can't be charmed or frightened while raging. If you are charmed or frightened when you enter your rage, the effect is suspended for the duration of the rage."
      }
    ]
  },
  {
    "value": "college-of-lore",
    "label": "College of Lore",
    "parentClass": "bard",
    "subclassLevel": 3,
    "features": [
      {
        "level": 3,
        "name": "Bonus Proficiencies",
        "description": "You gain proficiency with three skills of your choice."
      },
      {
        "level": 3,
        "name": "Cutting Words",
        "description": "When a creature you can see within 60 feet makes an attack roll, ability check, or damage roll, you can use your reaction to expend a Bardic Inspiration die and subtract the result from the roll."
      }
    ]
  },
  {
    "value": "life-domain",
    "label": "Life Domain",
    "parentClass": "cleric",
    "subclassLevel": 1,
    "features": [
      {
        "level": 1,
        "name": "Bonus Proficiency",
        "description": "You gain proficiency with heavy armor."
      },
      {
        "level": 1,
        "name": "Disciple of Life",
        "description": "Whenever you use a spell of 1st level or higher to restore hit points, the creature regains additional hit points equal to 2 + the spell's level."
      }
    ]
  },
  {
    "value": "circle-of-the-land",
    "label": "Circle of the Land",
    "parentClass": "druid",
    "subclassLevel": 2,
    "features": [
      {
        "level": 2,
        "name": "Bonus Cantrip",
        "description": "You learn one additional druid cantrip of your choice."
      },
      {
        "level": 2,
        "name": "Natural Recovery",
        "description": "During a short rest, you can recover expended spell slots with a combined level equal to or less than half your druid level (rounded up). You must finish a long rest before using this again."
      }
    ]
  },
  {
    "value": "champion",
    "label": "Champion",
    "parentClass": "fighter",
    "subclassLevel": 3,
    "features": [
      {
        "level": 3,
        "name": "Improved Critical",
        "description": "Your weapon attacks score a critical hit on a roll of 19 or 20."
      },
      {
        "level": 7,
        "name": "Remarkable Athlete",
        "description": "You can add half your proficiency bonus (rounded up) to any Strength, Dexterity, or Constitution check you make that does not already use your proficiency bonus. Your running long jump distance increases by a number of feet equal to your Strength modifier."
      }
    ]
  },
  {
    "value": "way-of-the-open-hand",
    "label": "Way of the Open Hand",
    "parentClass": "monk",
    "subclassLevel": 3,
    "features": [
      {
        "level": 3,
        "name": "Open Hand Technique",
        "description": "Whenever you hit a creature with a Flurry of Blows attack, you can impose one effect: knock prone (DEX save), push 15 feet (STR save), or prevent reactions until end of your next turn."
      },
      {
        "level": 6,
        "name": "Wholeness of Body",
        "description": "You can use your action to regain hit points equal to three times your monk level. You must finish a long rest before using this again."
      }
    ]
  },
  {
    "value": "oath-of-devotion",
    "label": "Oath of Devotion",
    "parentClass": "paladin",
    "subclassLevel": 3,
    "features": [
      {
        "level": 3,
        "name": "Sacred Weapon",
        "description": "As an action, you imbue one weapon you are holding with positive energy. For 1 minute, you add your Charisma modifier to attack rolls made with that weapon and it emits bright light in a 20-foot radius."
      },
      {
        "level": 3,
        "name": "Turn the Unholy",
        "description": "As an action, each fiend or undead within 30 feet that can hear you must make a Wisdom saving throw or be turned for 1 minute."
      }
    ]
  },
  {
    "value": "hunter",
    "label": "Hunter",
    "parentClass": "ranger",
    "subclassLevel": 3,
    "features": [
      {
        "level": 3,
        "name": "Hunter's Prey",
        "description": "Choose one: Colossus Slayer (extra 1d8 damage to wounded targets once per turn), Giant Killer (reaction attack when Large+ creature misses you), or Horde Breaker (attack a second adjacent creature once per turn)."
      },
      {
        "level": 7,
        "name": "Defensive Tactics",
        "description": "Choose one: Escape the Horde (opportunity attacks against you have disadvantage), Multiattack Defense (+4 AC after being hit), or Steel Will (advantage on saves vs. being frightened)."
      }
    ]
  },
  {
    "value": "thief",
    "label": "Thief",
    "parentClass": "rogue",
    "subclassLevel": 3,
    "features": [
      {
        "level": 3,
        "name": "Fast Hands",
        "description": "You can use the bonus action granted by Cunning Action to make a Dexterity (Sleight of Hand) check, use your thieves' tools to disarm a trap or open a lock, or take the Use an Object action."
      },
      {
        "level": 3,
        "name": "Second-Story Work",
        "description": "You gain the ability to climb faster than normal; climbing no longer costs you extra movement. Additionally, when you make a running jump, the distance you cover increases by a number of feet equal to your Dexterity modifier."
      }
    ]
  },
  {
    "value": "draconic-bloodline",
    "label": "Draconic Bloodline",
    "parentClass": "sorcerer",
    "subclassLevel": 1,
    "features": [
      {
        "level": 1,
        "name": "Dragon Ancestor",
        "description": "You choose one type of dragon as your ancestor. You can speak, read, and write Draconic, and you have advantage on Charisma checks when interacting with dragons."
      },
      {
        "level": 1,
        "name": "Draconic Resilience",
        "description": "Your hit point maximum increases by 1 for each sorcerer level. Additionally, when you are not wearing armor, your AC equals 13 + your Dexterity modifier."
      }
    ]
  },
  {
    "value": "the-fiend",
    "label": "The Fiend",
    "parentClass": "warlock",
    "subclassLevel": 1,
    "features": [
      {
        "level": 1,
        "name": "Dark One's Blessing",
        "description": "When you reduce a hostile creature to 0 hit points, you gain temporary hit points equal to your Charisma modifier + your warlock level (minimum of 1)."
      },
      {
        "level": 6,
        "name": "Dark One's Own Luck",
        "description": "When you make an ability check or a saving throw, you can add a d10 to the roll. You must finish a short or long rest before using this again."
      }
    ]
  },
  {
    "value": "school-of-evocation",
    "label": "School of Evocation",
    "parentClass": "wizard",
    "subclassLevel": 2,
    "features": [
      {
        "level": 2,
        "name": "Evocation Savant",
        "description": "The gold and time you must spend to copy an evocation spell into your spellbook is halved."
      },
      {
        "level": 2,
        "name": "Sculpt Spells",
        "description": "When you cast an evocation spell that affects other creatures you can see, you can choose a number of them equal to 1 + the spell's level. The chosen creatures automatically succeed on their saving throws and take no damage."
      }
    ]
  }
];

// ============================================================
// BACKGROUNDS
// ============================================================

export const BACKGROUNDS: BackgroundData[] = 
[
  {
    "value": "acolyte",
    "label": "Acolyte",
    "skillProficiencies": [
      "insight",
      "religion"
    ],
    "toolProficiencies": [],
    "languages": 2,
    "equipment": [
      "Holy symbol",
      "Prayer book",
      "5 sticks of incense",
      "Vestments",
      "Common clothes",
      "Belt pouch with 15 gp"
    ],
    "feature": {
      "name": "Shelter of the Faithful",
      "description": "As an acolyte, you command the respect of those who share your faith. You and your companions can expect free healing and care at a temple or religious community, and supporters will provide you with a modest lifestyle."
    },
    "personalityTraits": [
      "I idolize a particular hero of my faith and constantly refer to their deeds.",
      "I can find common ground between the fiercest enemies, empathizing with them.",
      "I see omens in every event and action. The gods are speaking to us.",
      "Nothing can shake my optimistic attitude.",
      "I quote sacred texts and proverbs in almost every situation.",
      "I am tolerant or intolerant of other faiths and respect or condemn their worship.",
      "I have enjoyed fine food, drink, and high society among my temple elite.",
      "I have spent so long in the temple that I have little practical experience dealing with people."
    ],
    "ideals": [
      "Tradition. The ancient traditions of worship and sacrifice must be preserved.",
      "Charity. I always try to help those in need, no matter the personal cost.",
      "Change. We must help bring about the changes the gods are constantly working in the world.",
      "Power. I hope to one day rise to the top of my religious hierarchy.",
      "Faith. I trust that my deity will guide my actions. I have faith that if I work hard, things will go well.",
      "Aspiration. I seek to prove myself worthy of my god's favor by matching my actions against their teachings."
    ],
    "bonds": [
      "I would die to recover an ancient relic of my faith that was lost long ago.",
      "I will someday get revenge on the corrupt temple hierarchy who branded me a heretic.",
      "I owe my life to the priest who took me in when my parents died.",
      "Everything I do is for the common people.",
      "I will do anything to protect the temple where I served.",
      "I seek to preserve a sacred text that my enemies seek to destroy."
    ],
    "flaws": [
      "I judge others harshly, and myself even more severely.",
      "I put too much trust in those who wield power within my temple.",
      "My piety sometimes leads me to blindly trust those who profess faith in my god.",
      "I am inflexible in my thinking.",
      "I am suspicious of strangers and expect the worst of them.",
      "Once I pick a goal, I become obsessed with it to the detriment of everything else."
    ]
  },
  {
    "value": "charlatan",
    "label": "Charlatan",
    "skillProficiencies": [
      "deception",
      "sleight-of-hand"
    ],
    "toolProficiencies": [
      "Disguise kit",
      "Forgery kit"
    ],
    "languages": 0,
    "equipment": [
      "Fine clothes",
      "Disguise kit",
      "Tools of the con (bottles, weighted dice, deck of marked cards, or signet ring)",
      "Belt pouch with 15 gp"
    ],
    "feature": {
      "name": "False Identity",
      "description": "You have created a second identity including documentation, established acquaintances, and disguises. You can forge documents including official papers and personal letters if you have seen a similar document."
    },
    "personalityTraits": [
      "I fall in and out of love easily, and am always pursuing someone.",
      "I have a joke for every occasion, especially occasions where humor is inappropriate.",
      "Flattery is my preferred trick for getting what I want.",
      "I am a born gambler who cannot resist taking a risk for a potential payoff.",
      "I lie about almost everything, even when there is no reason to.",
      "Sarcasm and insults are my weapons of choice.",
      "I keep multiple holy symbols on me and invoke whatever deity might come in useful.",
      "I pocket anything I see that might have some value."
    ],
    "ideals": [
      "Independence. I am a free spirit — no one tells me what to do.",
      "Fairness. I never target people who cannot afford to lose a few coins.",
      "Charity. I distribute the money I acquire to the people who really need it.",
      "Creativity. I never run the same con twice.",
      "Friendship. Material goods come and go. Bonds of friendship last forever.",
      "Aspiration. I am determined to make something of myself."
    ],
    "bonds": [
      "I fleeced the wrong person and must work to ensure they never cross paths with me again.",
      "I owe everything to my mentor — a horrible person who is probably rotting in jail.",
      "Somewhere out there, I have a child who does not know me. I want to make the world better for them.",
      "I come from a noble family, and one day I will reclaim my lands and title.",
      "A powerful person killed someone I love. I seek revenge.",
      "I swindled and ruined a person who did not deserve it. I seek to atone."
    ],
    "flaws": [
      "I cannot resist a pretty face.",
      "I am always in debt. I spend my ill-gotten gains on decadent luxuries.",
      "I am convinced that no one could ever fool me the way I fool others.",
      "I am too greedy for my own good. I cannot resist taking risks if there is money involved.",
      "I cannot resist swindling people who are more powerful than me.",
      "I hate to admit it and will hate myself for it, but I will run to preserve my own hide if the going gets tough."
    ]
  },
  {
    "value": "criminal",
    "label": "Criminal",
    "skillProficiencies": [
      "deception",
      "stealth"
    ],
    "toolProficiencies": [
      "Gaming set",
      "Thieves' tools"
    ],
    "languages": 0,
    "equipment": [
      "Crowbar",
      "Dark common clothes with a hood",
      "Belt pouch with 15 gp"
    ],
    "feature": {
      "name": "Criminal Contact",
      "description": "You have a reliable and trustworthy contact who acts as your liaison to a network of other criminals. You know how to get messages to and from your contact, even over great distances."
    },
    "personalityTraits": [
      "I always have a plan for what to do when things go wrong.",
      "I am always calm, no matter what the situation. I never raise my voice or let emotions control me.",
      "The first thing I do in a new place is note the locations of everything valuable.",
      "I would rather make a new friend than a new enemy.",
      "I am incredibly slow to trust. Those who seem the fairest often have the most to hide.",
      "I do not pay attention to the risks in a situation. Never tell me the odds.",
      "The best way to get me to do something is to tell me I cannot do it.",
      "I blow up at the slightest insult."
    ],
    "ideals": [
      "Honor. I do not steal from others in the trade.",
      "Freedom. Chains are meant to be broken, as are those who would forge them.",
      "Charity. I steal from the wealthy so that I can help people in need.",
      "Greed. I will do whatever it takes to become wealthy.",
      "People. I am loyal to my friends, not to any ideals.",
      "Redemption. There is a spark of good in everyone."
    ],
    "bonds": [
      "I am trying to pay off an old debt I owe to a generous benefactor.",
      "My ill-gotten gains go to support my family.",
      "Something important was taken from me, and I aim to steal it back.",
      "I will become the greatest thief that ever lived.",
      "I am guilty of a terrible crime. I hope I can redeem myself for it.",
      "Someone I loved died because of a mistake I made. That will never happen again."
    ],
    "flaws": [
      "When I see something valuable, I cannot think about anything but how to steal it.",
      "When faced with a choice between money and my friends, I usually choose the money.",
      "If there is a plan, I will forget it. If I do not forget it, I will ignore it.",
      "I have a tell that reveals when I am lying.",
      "I turn tail and run when things look bad.",
      "An innocent person is in prison for a crime that I committed. I am okay with that."
    ]
  },
  {
    "value": "entertainer",
    "label": "Entertainer",
    "skillProficiencies": [
      "acrobatics",
      "performance"
    ],
    "toolProficiencies": [
      "Disguise kit",
      "Musical instrument"
    ],
    "languages": 0,
    "equipment": [
      "Musical instrument",
      "The favor of an admirer",
      "Costume",
      "Belt pouch with 15 gp"
    ],
    "feature": {
      "name": "By Popular Demand",
      "description": "You can always find a place to perform. You receive free lodging and food of a modest or comfortable standard, as long as you perform each night. Your performance makes you something of a local figure."
    },
    "personalityTraits": [
      "I know a story relevant to almost every situation.",
      "Whenever I come to a new place, I collect local rumors and spread gossip.",
      "I am a hopeless romantic, always searching for that special someone.",
      "Nobody stays angry at me or around me for long, since I can defuse any tension.",
      "I love a good insult, even one directed at me.",
      "I get bitter if I am not the center of attention.",
      "I will settle for nothing less than perfection.",
      "I change my mood or my mind as quickly as I change key in a song."
    ],
    "ideals": [
      "Beauty. When I perform, I make the world better than it was.",
      "Tradition. The stories, legends, and songs of the past must never be forgotten.",
      "Creativity. The world is in need of new ideas and bold action.",
      "Greed. I am only in it for the money and fame.",
      "People. I like seeing the smiles on people's faces when I perform.",
      "Honesty. Art should reflect the soul; it should come from within and reveal who we really are."
    ],
    "bonds": [
      "My instrument is my most treasured possession, and it reminds me of someone I love.",
      "Someone stole my precious instrument, and someday I will get it back.",
      "I want to be famous, whatever it takes.",
      "I idolize a hero of the old tales and measure my deeds against theirs.",
      "I will do anything to prove myself superior to my hated rival.",
      "I would do anything for the other members of my old troupe."
    ],
    "flaws": [
      "I will do anything to win fame and renown.",
      "I am a sucker for a pretty face.",
      "A scandal prevents me from ever going home again.",
      "I once satirized a noble who still wants my head.",
      "I have trouble keeping my true feelings hidden. My sharp tongue lands me in trouble.",
      "Despite my best efforts, I am unreliable to my friends."
    ]
  },
  {
    "value": "folk-hero",
    "label": "Folk Hero",
    "skillProficiencies": [
      "animal-handling",
      "survival"
    ],
    "toolProficiencies": [
      "Artisan's tools",
      "Vehicles (land)"
    ],
    "languages": 0,
    "equipment": [
      "Artisan's tools",
      "Shovel",
      "Iron pot",
      "Common clothes",
      "Belt pouch with 10 gp"
    ],
    "feature": {
      "name": "Rustic Hospitality",
      "description": "Since you come from the ranks of the common folk, you fit in among them with ease. You can find a place to hide, rest, or recuperate among commoners, unless you have shown yourself to be a danger to them."
    },
    "personalityTraits": [
      "I judge people by their actions, not their words.",
      "If someone is in trouble, I am always ready to lend help.",
      "When I set my mind to something, I follow through no matter what gets in my way.",
      "I have a strong sense of fair play and always try to find the most equitable solution.",
      "I am confident in my own abilities and do what I can to instill confidence in others.",
      "Thinking is for other people. I prefer action.",
      "I misuse long words in an attempt to sound smarter.",
      "I get bored easily. When am I going to get on with my destiny?"
    ],
    "ideals": [
      "Respect. People deserve to be treated with dignity and respect.",
      "Fairness. No one should get preferential treatment before the law.",
      "Freedom. Tyrants must not be allowed to oppress the people.",
      "Might. If I become strong, I can take what I want.",
      "Sincerity. There is no good in pretending to be something I am not.",
      "Destiny. Nothing and no one can steer me away from my higher calling."
    ],
    "bonds": [
      "I have a family, but I have no idea where they are.",
      "I worked the land, I love the land, and I will protect the land.",
      "A proud noble once gave me a horrible beating, and I will take my revenge.",
      "My tools are symbols of my past life, and I carry them so I will never forget.",
      "I protect those who cannot protect themselves.",
      "I wish my childhood sweetheart had come with me to pursue my destiny."
    ],
    "flaws": [
      "The tyrant who rules my land will stop at nothing to see me killed.",
      "I am convinced of the significance of my destiny, and blind to my shortcomings.",
      "The people who knew me when I was young know my shameful secret.",
      "I have a weakness for the vices of the city, especially hard drink.",
      "Secretly, I believe that things would be better if I were a tyrant lording over the land.",
      "I have trouble trusting in my allies."
    ]
  },
  {
    "value": "guild-artisan",
    "label": "Guild Artisan",
    "skillProficiencies": [
      "insight",
      "persuasion"
    ],
    "toolProficiencies": [
      "Artisan's tools"
    ],
    "languages": 1,
    "equipment": [
      "Artisan's tools",
      "Letter of introduction from your guild",
      "Traveler's clothes",
      "Belt pouch with 15 gp"
    ],
    "feature": {
      "name": "Guild Membership",
      "description": "Your guild offers lodging and food if necessary. The guildhall can be a meeting place for you and allies. Guilds often wield tremendous political power; membership can grant access to powerful political figures."
    },
    "personalityTraits": [
      "I believe that anything worth doing is worth doing right.",
      "I am always looking to make a quick coin off an opportunity.",
      "I am horribly jealous of anyone who can outshine my handiwork.",
      "I am full of witty aphorisms and have a proverb for every occasion.",
      "I am rude to people who lack my commitment to hard work.",
      "I like to talk at length about my profession.",
      "I do not part with my money easily and will haggle tirelessly.",
      "I am well known for my work, and I want to make sure everyone appreciates it."
    ],
    "ideals": [
      "Community. It is the duty of all civilized people to strengthen the bonds of community.",
      "Generosity. My talents were given to me so that I could use them to benefit the world.",
      "Freedom. Everyone should be free to pursue their own livelihood.",
      "Greed. I am only in it for the money.",
      "People. I am committed to the people I care about, not to ideals.",
      "Aspiration. I work hard to be the best there is at my craft."
    ],
    "bonds": [
      "The workshop where I learned my trade is the most important place in the world to me.",
      "I created a great work for someone, and then found them unworthy to receive it.",
      "I owe my guild a great debt for forging me into the person I am today.",
      "I pursue wealth to secure someone's love.",
      "One day I will return to my guild and prove that I am the greatest artisan of them all.",
      "I will get revenge on the evil forces that destroyed my place of business."
    ],
    "flaws": [
      "I will do anything to get my hands on something rare or priceless.",
      "I am quick to assume that someone is trying to cheat me.",
      "No one must ever learn that I once stole money from guild coffers.",
      "I am never satisfied with what I have — I always want more.",
      "I would kill to acquire a noble title.",
      "I am horribly jealous of anyone who can outshine my handiwork."
    ]
  },
  {
    "value": "hermit",
    "label": "Hermit",
    "skillProficiencies": [
      "medicine",
      "religion"
    ],
    "toolProficiencies": [
      "Herbalism kit"
    ],
    "languages": 1,
    "equipment": [
      "Scroll case stuffed with notes",
      "Winter blanket",
      "Common clothes",
      "Herbalism kit",
      "5 gp"
    ],
    "feature": {
      "name": "Discovery",
      "description": "The quiet seclusion of your extended hermitage gave you access to a unique and powerful discovery. It might be a great truth, a hidden site, a long-forgotten fact, or unearthed some relic of the past."
    },
    "personalityTraits": [
      "I have been isolated for so long that I rarely speak, preferring gestures and occasional grunts.",
      "I am utterly serene, even in the face of disaster.",
      "The leader of my community had something wise to say on every topic.",
      "I feel tremendous empathy for all who suffer.",
      "I am oblivious to etiquette and social expectations.",
      "I connect everything that happens to me to a grand, cosmic plan.",
      "I often get lost in my own thoughts and contemplation, becoming oblivious to my surroundings.",
      "I am working on a grand philosophical theory and love sharing my ideas."
    ],
    "ideals": [
      "Greater Good. My gifts are meant to be shared with all, not used for my own benefit.",
      "Logic. Emotions must not cloud our sense of what is right and true.",
      "Free Thinking. Inquiry and curiosity are the pillars of progress.",
      "Power. Solitude and contemplation are paths toward mystical or magical power.",
      "Live and Let Live. Meddling in the affairs of others only causes trouble.",
      "Self-Knowledge. If you know yourself, there is nothing left to know."
    ],
    "bonds": [
      "Nothing is more important than the other members of my hermitage, order, or association.",
      "I entered seclusion to hide from the ones who might still be hunting me.",
      "I am still seeking the enlightenment I pursued in my seclusion, and it still eludes me.",
      "I entered seclusion because I loved someone I could not have.",
      "Should my discovery come to light, it could bring ruin to the world.",
      "My isolation gave me great insight into a great evil that only I can destroy."
    ],
    "flaws": [
      "Now that I have returned to the world, I enjoy its delights a little too much.",
      "I harbor dark, bloodthirsty thoughts that my isolation failed to quell.",
      "I am dogmatic in my thoughts and philosophy.",
      "I let my need to win arguments overshadow friendships and harmony.",
      "I would risk too much to uncover a lost bit of knowledge.",
      "I like keeping secrets and will not share them with anyone."
    ]
  },
  {
    "value": "noble",
    "label": "Noble",
    "skillProficiencies": [
      "history",
      "persuasion"
    ],
    "toolProficiencies": [
      "Gaming set"
    ],
    "languages": 1,
    "equipment": [
      "Fine clothes",
      "Signet ring",
      "Scroll of pedigree",
      "Purse with 25 gp"
    ],
    "feature": {
      "name": "Position of Privilege",
      "description": "Thanks to your noble birth, people are inclined to think the best of you. You are welcome in high society. Common folk make every effort to accommodate you and avoid your displeasure."
    },
    "personalityTraits": [
      "My eloquent flattery makes everyone I talk to feel like the most important person in the world.",
      "The common folk love me for my kindness and generosity.",
      "No one could doubt by looking at my regal bearing that I am a cut above the unwashed masses.",
      "I take great pains to always look my best and follow the latest fashions.",
      "I do not like to get my hands dirty, and I will not be caught dead in unsuitable accommodations.",
      "Despite my noble birth, I do not place myself above other folk.",
      "If you do me an injury, I will crush you, ruin your name, and salt your fields.",
      "My favor, once lost, is lost forever."
    ],
    "ideals": [
      "Respect. Respect is due to me because of my position, but all people deserve to be treated with dignity.",
      "Responsibility. It is my duty to respect the authority of those above me, just as those below me must respect mine.",
      "Independence. I must prove that I can handle myself without the coddling of my family.",
      "Power. If I can attain more power, no one will tell me what to do.",
      "Family. Blood runs thicker than water.",
      "Noble Obligation. It is my duty to protect and care for the people beneath me."
    ],
    "bonds": [
      "I will face any challenge to win the approval of my family.",
      "My house's alliance with another noble family must be sustained at all costs.",
      "Nothing is more important than the other members of my family.",
      "I am in love with the heir of a family that my family despises.",
      "My loyalty to my sovereign is unwavering.",
      "The common folk must see me as a hero of the people."
    ],
    "flaws": [
      "I secretly believe that everyone is beneath me.",
      "I hide a truly scandalous secret that could ruin my family forever.",
      "I too often hear veiled insults and threats in every word addressed to me.",
      "I have an insatiable desire for carnal pleasures.",
      "In fact, the world does revolve around me.",
      "By my words and actions, I often bring shame to my family."
    ]
  },
  {
    "value": "outlander",
    "label": "Outlander",
    "skillProficiencies": [
      "athletics",
      "survival"
    ],
    "toolProficiencies": [
      "Musical instrument"
    ],
    "languages": 1,
    "equipment": [
      "Staff",
      "Hunting trap",
      "Trophy from an animal you killed",
      "Traveler's clothes",
      "Belt pouch with 10 gp"
    ],
    "feature": {
      "name": "Wanderer",
      "description": "You have an excellent memory for maps and geography, and you can always recall the general layout of terrain and settlements. You can find food and fresh water for yourself and up to five other people each day, provided the land offers such resources."
    },
    "personalityTraits": [
      "I am driven by a wanderlust that led me away from home.",
      "I watch over my friends as if they were a litter of newborn pups.",
      "I once ran twenty-five miles without stopping to warn my clan of an approaching horde.",
      "I have a lesson for every situation, drawn from observing nature.",
      "I place no stock in wealthy or well-mannered folk.",
      "I am always picking things up, absently fiddling with them, and sometimes accidentally breaking them.",
      "I feel far more comfortable around animals than people.",
      "I was, in fact, raised by wolves."
    ],
    "ideals": [
      "Change. Life is like the seasons, in constant change, and we must change with it.",
      "Greater Good. It is each person's responsibility to make the most happiness for the whole tribe.",
      "Honor. If I dishonor myself, I dishonor my whole clan.",
      "Might. The strongest are meant to rule.",
      "Nature. The natural world is more important than the constructs of civilization.",
      "Glory. I must earn glory in battle, for myself and my clan."
    ],
    "bonds": [
      "My family, clan, or tribe is the most important thing in my life, even when they are far from me.",
      "An injury to the unspoiled wilderness of my home is an injury to me.",
      "I will bring terrible wrath down on the evildoers who destroyed my homeland.",
      "I am the last of my tribe, and it is up to me to ensure their names enter legend.",
      "I suffer awful visions of a coming disaster and will do anything to prevent it.",
      "It is my duty to provide children to sustain my tribe."
    ],
    "flaws": [
      "I am too enamored of ale, wine, and other intoxicants.",
      "There is no room for caution in a life lived to the fullest.",
      "I remember every insult I have received and nurse a silent resentment toward anyone who has wronged me.",
      "I am slow to trust members of other races, tribes, and societies.",
      "Violence is my answer to almost any challenge.",
      "Do not expect me to save those who cannot save themselves."
    ]
  },
  {
    "value": "sage",
    "label": "Sage",
    "skillProficiencies": [
      "arcana",
      "history"
    ],
    "toolProficiencies": [],
    "languages": 2,
    "equipment": [
      "Bottle of black ink",
      "Quill",
      "Small knife",
      "Letter from a dead colleague",
      "Common clothes",
      "Belt pouch with 10 gp"
    ],
    "feature": {
      "name": "Researcher",
      "description": "When you attempt to learn or recall a piece of lore, if you do not know that information, you often know where and from whom you can obtain it. Usually this comes from a library, scriptorium, university, or a sage."
    },
    "personalityTraits": [
      "I use polysyllabic words that convey the impression of great erudition.",
      "I have read every book in the world's greatest libraries — or I like to boast that I have.",
      "I am used to helping out those who are not as smart as I am.",
      "There is nothing I like more than a good mystery.",
      "I am willing to listen to every side of an argument before I make my own judgment.",
      "I speak slowly because I think carefully before I say anything.",
      "I am horribly, horribly awkward in social situations.",
      "I am convinced that people are always trying to steal my secrets."
    ],
    "ideals": [
      "Knowledge. The path to power and self-improvement is through knowledge.",
      "Beauty. What is beautiful points us beyond itself toward what is true.",
      "Logic. Emotions must not cloud our logical thinking.",
      "No Limits. Nothing should fetter the infinite possibility inherent in all existence.",
      "Power. Knowledge is the path to power and domination.",
      "Self-Improvement. The goal of a life of study is the betterment of oneself."
    ],
    "bonds": [
      "It is my duty to protect my students.",
      "I have an ancient text that holds terrible secrets that must not fall into the wrong hands.",
      "I work to preserve a library, university, scriptorium, or monastery.",
      "My life's work is a series of tomes related to a specific field of lore.",
      "I have been searching my whole life for the answer to a certain question.",
      "I sold my soul for knowledge. I hope to do great deeds and win it back."
    ],
    "flaws": [
      "I am easily distracted by the promise of information.",
      "Most people scream and run when they see a demon. I stop and take notes on its anatomy.",
      "Unlocking an ancient mystery is worth the price of a civilization.",
      "I overlook obvious solutions in favor of complicated ones.",
      "I speak without really thinking through my words, invariably insulting others.",
      "I cannot keep a secret to save my life, or anyone else's."
    ]
  },
  {
    "value": "sailor",
    "label": "Sailor",
    "skillProficiencies": [
      "athletics",
      "perception"
    ],
    "toolProficiencies": [
      "Navigator's tools",
      "Vehicles (water)"
    ],
    "languages": 0,
    "equipment": [
      "Belaying pin (club)",
      "50 feet of silk rope",
      "Lucky charm",
      "Common clothes",
      "Belt pouch with 10 gp"
    ],
    "feature": {
      "name": "Ship's Passage",
      "description": "When you need to, you can secure free passage on a sailing ship for yourself and your companions. In return, you are expected to assist the crew during the voyage."
    },
    "personalityTraits": [
      "My friends know they can rely on me, no matter what.",
      "I work hard so that I can play hard when the work is done.",
      "I enjoy sailing into new ports and making new friends over a flagon of ale.",
      "I stretch the truth for the sake of a good story.",
      "To me, a tavern brawl is a nice way to get to know a new city.",
      "I never pass up a friendly wager.",
      "My language is as foul as an otyugh nest.",
      "I like a job well done, especially if I can convince someone else to do it."
    ],
    "ideals": [
      "Respect. The thing that keeps a ship together is mutual respect between captain and crew.",
      "Fairness. We all do the work, so we all share in the rewards.",
      "Freedom. The sea is freedom — the freedom to go anywhere and do anything.",
      "Mastery. I am a predator, and the other ships on the sea are my prey.",
      "People. I am committed to my crewmates, not to ideals.",
      "Aspiration. Someday I will own my own ship and chart my own destiny."
    ],
    "bonds": [
      "I am loyal to my captain first, everything else second.",
      "The ship is most important — crewmates and captains come and go.",
      "I will always remember my first ship.",
      "In a harbor town, I have a paramour whose eyes nearly stole me from the sea.",
      "I was cheated out of my fair share of the profits, and I want to get my due.",
      "Ruthless pirates murdered my captain and crewmates, plundered our ship, and left me to die. Vengeance will be mine."
    ],
    "flaws": [
      "I follow orders, even if I think they are wrong.",
      "I will say anything to avoid having to do extra work.",
      "Once someone questions my courage, I never back down no matter how dangerous the situation.",
      "Once I start drinking, it is hard for me to stop.",
      "I cannot help but pocket loose coins and other trinkets I come across.",
      "My pride will probably lead to my destruction."
    ]
  },
  {
    "value": "soldier",
    "label": "Soldier",
    "skillProficiencies": [
      "athletics",
      "intimidation"
    ],
    "toolProficiencies": [
      "Gaming set",
      "Vehicles (land)"
    ],
    "languages": 0,
    "equipment": [
      "Insignia of rank",
      "Trophy from a fallen enemy",
      "Bone dice or deck of cards",
      "Common clothes",
      "Belt pouch with 10 gp"
    ],
    "feature": {
      "name": "Military Rank",
      "description": "You have a military rank from your career as a soldier. Soldiers loyal to your former military organization still recognize your authority and influence. You can invoke your rank to exert influence over other soldiers."
    },
    "personalityTraits": [
      "I am always polite and respectful.",
      "I am haunted by memories of war. I cannot get the images of violence out of my mind.",
      "I have lost too many friends, and I am slow to make new ones.",
      "I am full of inspiring and cautionary tales from my military experience.",
      "I can stare down a hell hound without flinching.",
      "I enjoy being strong and like breaking things.",
      "I have a crude sense of humor.",
      "I face problems head-on. A simple, direct solution is the best path to success."
    ],
    "ideals": [
      "Greater Good. Our lot is to lay down our lives in defense of others.",
      "Responsibility. I do what I must and obey just authority.",
      "Independence. When people follow orders blindly, they embrace a kind of tyranny.",
      "Might. In life as in war, the stronger force wins.",
      "Live and Let Live. Ideals are not worth killing over or going to war for.",
      "Nation. My city, nation, or people are all that matter."
    ],
    "bonds": [
      "I would still lay down my life for the people I served with.",
      "Someone saved my life on the battlefield. To this day, I will never leave a friend behind.",
      "My honor is my life.",
      "I will never forget the crushing defeat my company suffered or the enemies who dealt it.",
      "Those who fight beside me are those worth dying for.",
      "I fight for those who cannot fight for themselves."
    ],
    "flaws": [
      "The monstrous enemy we faced in battle still leaves me quivering with fear.",
      "I have little respect for anyone who is not a proven warrior.",
      "I made a terrible mistake in battle that cost many lives, and I would do anything to keep that secret.",
      "My hatred of my enemies is blind and unreasoning.",
      "I obey the law, even if the law causes misery.",
      "I would rather eat my armor than admit when I am wrong."
    ]
  },
  {
    "value": "urchin",
    "label": "Urchin",
    "skillProficiencies": [
      "sleight-of-hand",
      "stealth"
    ],
    "toolProficiencies": [
      "Disguise kit",
      "Thieves' tools"
    ],
    "languages": 0,
    "equipment": [
      "Small knife",
      "Map of the city you grew up in",
      "Pet mouse",
      "Token to remember your parents by",
      "Common clothes",
      "Belt pouch with 10 gp"
    ],
    "feature": {
      "name": "City Secrets",
      "description": "You know the secret patterns and flow to cities and can find passages through the urban sprawl that others would miss. When you are not in combat, you and companions you lead can travel between any two locations in the city twice as fast."
    },
    "personalityTraits": [
      "I hide scraps of food and trinkets away in my pockets.",
      "I ask a lot of questions.",
      "I like to squeeze into small places where no one else can get to me.",
      "I sleep with my back to a wall or tree, with everything I own wrapped in a bundle in my arms.",
      "I eat like a pig and have bad manners.",
      "I think anyone who is nice to me is hiding evil intent.",
      "I do not like to bathe.",
      "I bluntly say what other people are hinting at or hiding."
    ],
    "ideals": [
      "Respect. All people, rich or poor, deserve respect.",
      "Community. We have to take care of each other, because no one else is going to do it.",
      "Change. The low are lifted up, and the high and mighty are brought down. Change is the nature of things.",
      "Retribution. The rich need to be shown what life and death are like in the gutters.",
      "People. I help the people who help me — that is what keeps us alive.",
      "Aspiration. I am going to prove that I am worthy of a better life."
    ],
    "bonds": [
      "My town or city is my home, and I will fight to defend it.",
      "I sponsor an orphanage to keep others from enduring what I was forced to endure.",
      "I owe my survival to another urchin who taught me to live on the streets.",
      "I owe a debt I can never repay to the person who took pity on me.",
      "I escaped my life of poverty by robbing an important person, and I am wanted for it.",
      "No one else should have to endure the hardships I have been through."
    ],
    "flaws": [
      "If I am outnumbered, I will run away from a fight.",
      "Gold seems like a lot of money to me, and I will do just about anything for more of it.",
      "I will never fully trust anyone other than myself.",
      "I would rather kill someone in their sleep than fight fair.",
      "It is not stealing if I need it more than someone else.",
      "People who cannot take care of themselves get what they deserve."
    ]
  }
];

// ============================================================
// SKILLS
// ============================================================

export const SKILLS: SkillData[] = 
[
  {
    "value": "acrobatics",
    "label": "Acrobatics",
    "ability": "Dexterity",
    "abilityShort": "DEX",
    "description": "Covers attempts to stay on your feet in tricky situations, such as acrobatic stunts, balance, and tumbling."
  },
  {
    "value": "animal-handling",
    "label": "Animal Handling",
    "ability": "Wisdom",
    "abilityShort": "WIS",
    "description": "Covers calming a domesticated animal, keeping a mount from getting spooked, or intuiting an animal's intentions."
  },
  {
    "value": "arcana",
    "label": "Arcana",
    "ability": "Intelligence",
    "abilityShort": "INT",
    "description": "Measures your ability to recall lore about spells, magic items, eldritch symbols, magical traditions, and the planes of existence."
  },
  {
    "value": "athletics",
    "label": "Athletics",
    "ability": "Strength",
    "abilityShort": "STR",
    "description": "Covers difficult situations you encounter while climbing, jumping, or swimming."
  },
  {
    "value": "deception",
    "label": "Deception",
    "ability": "Charisma",
    "abilityShort": "CHA",
    "description": "Covers attempts to convincingly hide the truth, whether through verbal misdirection or disguise."
  },
  {
    "value": "history",
    "label": "History",
    "ability": "Intelligence",
    "abilityShort": "INT",
    "description": "Measures your ability to recall lore about historical events, legendary people, ancient kingdoms, and past disputes."
  },
  {
    "value": "insight",
    "label": "Insight",
    "ability": "Wisdom",
    "abilityShort": "WIS",
    "description": "Covers determining the true intentions of a creature, such as detecting lies or predicting someone's next move."
  },
  {
    "value": "intimidation",
    "label": "Intimidation",
    "ability": "Charisma",
    "abilityShort": "CHA",
    "description": "Covers attempts to influence someone through overt threats, hostile actions, and physical violence."
  },
  {
    "value": "investigation",
    "label": "Investigation",
    "ability": "Intelligence",
    "abilityShort": "INT",
    "description": "Covers looking for clues, making deductions, and piecing together information to reach conclusions."
  },
  {
    "value": "medicine",
    "label": "Medicine",
    "ability": "Wisdom",
    "abilityShort": "WIS",
    "description": "Covers efforts to stabilize a dying companion or diagnose an illness."
  },
  {
    "value": "nature",
    "label": "Nature",
    "ability": "Intelligence",
    "abilityShort": "INT",
    "description": "Measures your ability to recall lore about terrain, plants, animals, weather, and natural cycles."
  },
  {
    "value": "perception",
    "label": "Perception",
    "ability": "Wisdom",
    "abilityShort": "WIS",
    "description": "Covers your general awareness of your surroundings and the keenness of your senses."
  },
  {
    "value": "performance",
    "label": "Performance",
    "ability": "Charisma",
    "abilityShort": "CHA",
    "description": "Covers delighting an audience with music, dance, acting, storytelling, or some other form of entertainment."
  },
  {
    "value": "persuasion",
    "label": "Persuasion",
    "ability": "Charisma",
    "abilityShort": "CHA",
    "description": "Covers attempts to influence someone or a group through tact, social graces, or good nature."
  },
  {
    "value": "religion",
    "label": "Religion",
    "ability": "Intelligence",
    "abilityShort": "INT",
    "description": "Measures your ability to recall lore about deities, rites, prayers, religious hierarchies, and holy symbols."
  },
  {
    "value": "sleight-of-hand",
    "label": "Sleight of Hand",
    "ability": "Dexterity",
    "abilityShort": "DEX",
    "description": "Covers acts of legerdemain or manual trickery, such as planting something on someone or concealing an object on your person."
  },
  {
    "value": "stealth",
    "label": "Stealth",
    "ability": "Dexterity",
    "abilityShort": "DEX",
    "description": "Covers attempts to conceal yourself from enemies, slink past guards, slip away without being noticed, or sneak up on someone."
  },
  {
    "value": "survival",
    "label": "Survival",
    "ability": "Wisdom",
    "abilityShort": "WIS",
    "description": "Covers following tracks, hunting wild game, guiding your group through wastelands, identifying signs of nearby creatures, predicting weather, or avoiding quicksand."
  }
];

// ============================================================
// CLASS SKILL CHOICES
// ============================================================

export const CLASS_SKILL_CHOICES: Record<string, { count: number; options: string[] }> = 
{
  "barbarian": {
    "count": 2,
    "options": [
      "animal-handling",
      "athletics",
      "intimidation",
      "nature",
      "perception",
      "survival"
    ]
  },
  "bard": {
    "count": 3,
    "options": [
      "acrobatics",
      "animal-handling",
      "arcana",
      "athletics",
      "deception",
      "history",
      "insight",
      "intimidation",
      "investigation",
      "medicine",
      "nature",
      "perception",
      "performance",
      "persuasion",
      "religion",
      "sleight-of-hand",
      "stealth",
      "survival"
    ]
  },
  "cleric": {
    "count": 2,
    "options": [
      "history",
      "insight",
      "medicine",
      "persuasion",
      "religion"
    ]
  },
  "druid": {
    "count": 2,
    "options": [
      "arcana",
      "animal-handling",
      "insight",
      "medicine",
      "nature",
      "perception",
      "religion",
      "survival"
    ]
  },
  "fighter": {
    "count": 2,
    "options": [
      "acrobatics",
      "animal-handling",
      "athletics",
      "history",
      "insight",
      "intimidation",
      "perception",
      "survival"
    ]
  },
  "monk": {
    "count": 2,
    "options": [
      "acrobatics",
      "athletics",
      "history",
      "insight",
      "religion",
      "stealth"
    ]
  },
  "paladin": {
    "count": 2,
    "options": [
      "athletics",
      "insight",
      "intimidation",
      "medicine",
      "persuasion",
      "religion"
    ]
  },
  "ranger": {
    "count": 3,
    "options": [
      "animal-handling",
      "athletics",
      "insight",
      "investigation",
      "nature",
      "perception",
      "stealth",
      "survival"
    ]
  },
  "rogue": {
    "count": 4,
    "options": [
      "acrobatics",
      "athletics",
      "deception",
      "insight",
      "intimidation",
      "investigation",
      "perception",
      "performance",
      "persuasion",
      "sleight-of-hand",
      "stealth"
    ]
  },
  "sorcerer": {
    "count": 2,
    "options": [
      "arcana",
      "deception",
      "insight",
      "intimidation",
      "persuasion",
      "religion"
    ]
  },
  "warlock": {
    "count": 2,
    "options": [
      "arcana",
      "deception",
      "history",
      "intimidation",
      "investigation",
      "nature",
      "religion"
    ]
  },
  "wizard": {
    "count": 2,
    "options": [
      "arcana",
      "history",
      "insight",
      "investigation",
      "medicine",
      "religion"
    ]
  }
};

// ============================================================
// STARTING EQUIPMENT
// ============================================================

export const STARTING_EQUIPMENT: Record<string, EquipmentChoice[]> = 
{
  "barbarian": [
    {
      "label": "Primary Weapon",
      "options": [
        [
          "Greataxe"
        ],
        [
          "Any martial melee weapon"
        ]
      ]
    },
    {
      "label": "Secondary Weapon",
      "options": [
        [
          "Two handaxes"
        ],
        [
          "Any simple weapon"
        ]
      ]
    },
    {
      "label": "Pack & Extras",
      "options": [
        [
          "Explorer's pack",
          "Four javelins"
        ]
      ]
    }
  ],
  "bard": [
    {
      "label": "Weapon",
      "options": [
        [
          "Rapier"
        ],
        [
          "Longsword"
        ],
        [
          "Any simple weapon"
        ]
      ]
    },
    {
      "label": "Pack",
      "options": [
        [
          "Diplomat's pack"
        ],
        [
          "Entertainer's pack"
        ]
      ]
    },
    {
      "label": "Instrument",
      "options": [
        [
          "Lute"
        ],
        [
          "Any musical instrument"
        ]
      ]
    }
  ],
  "cleric": [
    {
      "label": "Weapon",
      "options": [
        [
          "Mace"
        ],
        [
          "Warhammer (if proficient)"
        ]
      ]
    },
    {
      "label": "Armor",
      "options": [
        [
          "Scale mail"
        ],
        [
          "Leather armor"
        ],
        [
          "Chain mail (if proficient)"
        ]
      ]
    },
    {
      "label": "Secondary Weapon",
      "options": [
        [
          "Light crossbow",
          "20 bolts"
        ],
        [
          "Any simple weapon"
        ]
      ]
    }
  ],
  "druid": [
    {
      "label": "Shield or Weapon",
      "options": [
        [
          "Wooden shield"
        ],
        [
          "Any simple weapon"
        ]
      ]
    },
    {
      "label": "Melee Weapon",
      "options": [
        [
          "Scimitar"
        ],
        [
          "Any simple melee weapon"
        ]
      ]
    },
    {
      "label": "Standard Gear",
      "options": [
        [
          "Leather armor",
          "Explorer's pack",
          "Druidic focus"
        ]
      ]
    }
  ],
  "fighter": [
    {
      "label": "Armor",
      "options": [
        [
          "Chain mail"
        ],
        [
          "Leather armor",
          "Longbow",
          "20 arrows"
        ]
      ]
    },
    {
      "label": "Weapons",
      "options": [
        [
          "Martial weapon",
          "Shield"
        ],
        [
          "Two martial weapons"
        ]
      ]
    },
    {
      "label": "Ranged Option",
      "options": [
        [
          "Light crossbow",
          "20 bolts"
        ],
        [
          "Two handaxes"
        ]
      ]
    }
  ],
  "monk": [
    {
      "label": "Weapon",
      "options": [
        [
          "Shortsword"
        ],
        [
          "Any simple weapon"
        ]
      ]
    },
    {
      "label": "Pack",
      "options": [
        [
          "Dungeoneer's pack"
        ],
        [
          "Explorer's pack"
        ]
      ]
    },
    {
      "label": "Standard Gear",
      "options": [
        [
          "10 darts"
        ]
      ]
    }
  ],
  "paladin": [
    {
      "label": "Weapons",
      "options": [
        [
          "Martial weapon",
          "Shield"
        ],
        [
          "Two martial weapons"
        ]
      ]
    },
    {
      "label": "Secondary Weapon",
      "options": [
        [
          "Five javelins"
        ],
        [
          "Any simple melee weapon"
        ]
      ]
    },
    {
      "label": "Pack",
      "options": [
        [
          "Priest's pack"
        ],
        [
          "Explorer's pack"
        ]
      ]
    }
  ],
  "ranger": [
    {
      "label": "Armor",
      "options": [
        [
          "Scale mail"
        ],
        [
          "Leather armor"
        ]
      ]
    },
    {
      "label": "Weapons",
      "options": [
        [
          "Two shortswords"
        ],
        [
          "Two simple melee weapons"
        ]
      ]
    },
    {
      "label": "Pack",
      "options": [
        [
          "Dungeoneer's pack"
        ],
        [
          "Explorer's pack"
        ]
      ]
    }
  ],
  "rogue": [
    {
      "label": "Weapon",
      "options": [
        [
          "Rapier"
        ],
        [
          "Shortsword"
        ]
      ]
    },
    {
      "label": "Ranged Weapon",
      "options": [
        [
          "Shortbow",
          "Quiver of 20 arrows"
        ],
        [
          "Shortsword"
        ]
      ]
    },
    {
      "label": "Pack",
      "options": [
        [
          "Burglar's pack"
        ],
        [
          "Dungeoneer's pack"
        ],
        [
          "Explorer's pack"
        ]
      ]
    }
  ],
  "sorcerer": [
    {
      "label": "Weapon",
      "options": [
        [
          "Light crossbow",
          "20 bolts"
        ],
        [
          "Any simple weapon"
        ]
      ]
    },
    {
      "label": "Focus",
      "options": [
        [
          "Component pouch"
        ],
        [
          "Arcane focus"
        ]
      ]
    },
    {
      "label": "Pack",
      "options": [
        [
          "Dungeoneer's pack"
        ],
        [
          "Explorer's pack"
        ]
      ]
    }
  ],
  "warlock": [
    {
      "label": "Weapon",
      "options": [
        [
          "Light crossbow",
          "20 bolts"
        ],
        [
          "Any simple weapon"
        ]
      ]
    },
    {
      "label": "Focus",
      "options": [
        [
          "Component pouch"
        ],
        [
          "Arcane focus"
        ]
      ]
    },
    {
      "label": "Pack",
      "options": [
        [
          "Scholar's pack"
        ],
        [
          "Dungeoneer's pack"
        ]
      ]
    }
  ],
  "wizard": [
    {
      "label": "Weapon",
      "options": [
        [
          "Quarterstaff"
        ],
        [
          "Dagger"
        ]
      ]
    },
    {
      "label": "Focus",
      "options": [
        [
          "Component pouch"
        ],
        [
          "Arcane focus"
        ]
      ]
    },
    {
      "label": "Pack",
      "options": [
        [
          "Scholar's pack"
        ],
        [
          "Explorer's pack"
        ]
      ]
    }
  ]
};

// ============================================================
// ALIGNMENTS
// ============================================================

export const ALIGNMENTS: { value: string; label: string; description: string }[] = 
[
  {
    "value": "lawful-good",
    "label": "Lawful Good",
    "description": "Creatures that can be counted on to do the right thing as expected by society. Gold dragons and paladins are typically lawful good."
  },
  {
    "value": "neutral-good",
    "label": "Neutral Good",
    "description": "Folk who do the best they can to help others according to their needs. Many celestials are neutral good."
  },
  {
    "value": "chaotic-good",
    "label": "Chaotic Good",
    "description": "Creatures that act as their conscience directs, with little regard for what others expect. Copper dragons and many elves are chaotic good."
  },
  {
    "value": "lawful-neutral",
    "label": "Lawful Neutral",
    "description": "Individuals who act in accordance with law, tradition, or personal codes. Many monks and some wizards are lawful neutral."
  },
  {
    "value": "true-neutral",
    "label": "True Neutral",
    "description": "Those who prefer to steer clear of moral questions and don't take sides, doing what seems best at the time. Lizardfolk and most druids are neutral."
  },
  {
    "value": "chaotic-neutral",
    "label": "Chaotic Neutral",
    "description": "Creatures that follow their whims, holding personal freedom above all else. Many rogues and bards are chaotic neutral."
  },
  {
    "value": "lawful-evil",
    "label": "Lawful Evil",
    "description": "Creatures that methodically take what they want within the limits of a code of tradition or loyalty. Devils and blue dragons are typically lawful evil."
  },
  {
    "value": "neutral-evil",
    "label": "Neutral Evil",
    "description": "Those who do whatever they can get away with, without compassion or qualms. Yugoloths are typically neutral evil."
  },
  {
    "value": "chaotic-evil",
    "label": "Chaotic Evil",
    "description": "Creatures that act with arbitrary violence, spurred by their greed, hatred, or bloodlust. Demons and red dragons are typically chaotic evil."
  }
];

// ============================================================
// LANGUAGES
// ============================================================

export const LANGUAGES: { value: string; label: string; type: 'standard' | 'exotic' }[] = 
[
  {
    "value": "common",
    "label": "Common",
    "type": "standard"
  },
  {
    "value": "dwarvish",
    "label": "Dwarvish",
    "type": "standard"
  },
  {
    "value": "elvish",
    "label": "Elvish",
    "type": "standard"
  },
  {
    "value": "giant",
    "label": "Giant",
    "type": "standard"
  },
  {
    "value": "gnomish",
    "label": "Gnomish",
    "type": "standard"
  },
  {
    "value": "goblin",
    "label": "Goblin",
    "type": "standard"
  },
  {
    "value": "halfling",
    "label": "Halfling",
    "type": "standard"
  },
  {
    "value": "orc",
    "label": "Orc",
    "type": "standard"
  },
  {
    "value": "abyssal",
    "label": "Abyssal",
    "type": "exotic"
  },
  {
    "value": "celestial",
    "label": "Celestial",
    "type": "exotic"
  },
  {
    "value": "deep-speech",
    "label": "Deep Speech",
    "type": "exotic"
  },
  {
    "value": "draconic",
    "label": "Draconic",
    "type": "exotic"
  },
  {
    "value": "infernal",
    "label": "Infernal",
    "type": "exotic"
  },
  {
    "value": "primordial",
    "label": "Primordial",
    "type": "exotic"
  },
  {
    "value": "sylvan",
    "label": "Sylvan",
    "type": "exotic"
  },
  {
    "value": "undercommon",
    "label": "Undercommon",
    "type": "exotic"
  }
] as const;

// ============================================================
// ABILITY SCORE METHODS
// ============================================================

export const POINT_BUY_COSTS: Record<number, number> = { 8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9 };

export const STANDARD_ARRAY: number[] = [15, 14, 13, 12, 10, 8];

export const POINT_BUY_BUDGET = 27;

// ============================================================
// SPELLCASTING CLASSES
// ============================================================

export const SPELLCASTING_CLASSES: Record<string, SpellcastingInfo> = 
{
  "bard": {
    "ability": "CHA",
    "cantripsKnown": 2,
    "spellsKnownOrPrepared": 4,
    "spellSlots": [
      2
    ]
  },
  "cleric": {
    "ability": "WIS",
    "cantripsKnown": 3,
    "spellsKnownOrPrepared": 0,
    "spellSlots": [
      2
    ]
  },
  "druid": {
    "ability": "WIS",
    "cantripsKnown": 2,
    "spellsKnownOrPrepared": 0,
    "spellSlots": [
      2
    ]
  },
  "paladin": {
    "ability": "CHA",
    "cantripsKnown": 0,
    "spellsKnownOrPrepared": 0,
    "spellSlots": []
  },
  "ranger": {
    "ability": "WIS",
    "cantripsKnown": 0,
    "spellsKnownOrPrepared": 0,
    "spellSlots": []
  },
  "sorcerer": {
    "ability": "CHA",
    "cantripsKnown": 4,
    "spellsKnownOrPrepared": 2,
    "spellSlots": [
      2
    ]
  },
  "warlock": {
    "ability": "CHA",
    "cantripsKnown": 2,
    "spellsKnownOrPrepared": 2,
    "spellSlots": [
      1
    ]
  },
  "wizard": {
    "ability": "INT",
    "cantripsKnown": 3,
    "spellsKnownOrPrepared": 6,
    "spellSlots": [
      2
    ]
  }
};

// ============================================================
// RACIAL LANGUAGES
// ============================================================

export const RACIAL_LANGUAGES: Record<string, string[]> = 
{
  "dwarf": [
    "common",
    "dwarvish"
  ],
  "elf": [
    "common",
    "elvish"
  ],
  "halfling": [
    "common",
    "halfling"
  ],
  "human": [
    "common"
  ],
  "dragonborn": [
    "common",
    "draconic"
  ],
  "gnome": [
    "common",
    "gnomish"
  ],
  "half-elf": [
    "common",
    "elvish"
  ],
  "half-orc": [
    "common",
    "orc"
  ],
  "tiefling": [
    "common",
    "infernal"
  ]
};

// ============================================================
// HIT DICE
// ============================================================

export const HIT_DICE: Record<string, number> = 
{
  "barbarian": 12,
  "bard": 8,
  "cleric": 8,
  "druid": 8,
  "fighter": 10,
  "monk": 8,
  "paladin": 10,
  "ranger": 10,
  "rogue": 8,
  "sorcerer": 6,
  "warlock": 8,
  "wizard": 6
};

