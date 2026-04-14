// D&D 5e SRD Character Creation Data
// All data sourced from the SRD 5.1 (Creative Commons)

// ============================================================================
// Types
// ============================================================================
export interface SubraceData {
  value: string
  label: string
  parentRace: string
  abilityBonuses: Record<string, number>
  traits: string[]
  speed?: number
}

export interface SubclassData {
  value: string
  label: string
  parentClass: string
  levelAvailable: number
  features: { name: string; description: string }[]
}

export interface BackgroundData {
  value: string
  label: string
  skillProficiencies: string[]
  toolProficiencies: string[]
  languages: number
  equipment: string[]
  feature: { name: string; description: string }
  personalityTraits: string[]
  ideals: string[]
  bonds: string[]
  flaws: string[]
}

export interface SkillData {
  value: string
  label: string
  ability: string
  abilityShort: string
}

export interface LanguageData {
  value: string
  label: string
  type: 'standard' | 'exotic'
}

export interface SpellcasterInfo {
  cantripsKnown: number
  spellsKnownOrPrepared: number
  spellSlots: number[]
}

export interface EquipmentChoice {
  label: string
  options: string[][]
}

// ============================================================================
// Subraces
// ============================================================================
export const SUBRACES: SubraceData[] = [
  // Dwarf
  { value: 'hill-dwarf', label: 'Hill Dwarf', parentRace: 'dwarf', abilityBonuses: { constitution: 2, wisdom: 1 }, traits: ['Dwarven Toughness (+1 HP/level)'] },
  { value: 'mountain-dwarf', label: 'Mountain Dwarf', parentRace: 'dwarf', abilityBonuses: { constitution: 2, strength: 2 }, traits: ['Dwarven Armor Training'] },
  // Elf
  { value: 'high-elf', label: 'High Elf', parentRace: 'elf', abilityBonuses: { dexterity: 2, intelligence: 1 }, traits: ['Elf Weapon Training', 'Extra Cantrip', 'Extra Language'] },
  { value: 'wood-elf', label: 'Wood Elf', parentRace: 'elf', abilityBonuses: { dexterity: 2, wisdom: 1 }, traits: ['Elf Weapon Training', 'Fleet of Foot (35ft)', 'Mask of the Wild'], speed: 35 },
  { value: 'dark-elf', label: 'Dark Elf (Drow)', parentRace: 'elf', abilityBonuses: { dexterity: 2, charisma: 1 }, traits: ['Superior Darkvision (120ft)', 'Drow Magic', 'Sunlight Sensitivity'] },
  // Halfling
  { value: 'lightfoot-halfling', label: 'Lightfoot Halfling', parentRace: 'halfling', abilityBonuses: { dexterity: 2, charisma: 1 }, traits: ['Naturally Stealthy'] },
  { value: 'stout-halfling', label: 'Stout Halfling', parentRace: 'halfling', abilityBonuses: { dexterity: 2, constitution: 1 }, traits: ['Stout Resilience'] },
  // Gnome
  { value: 'forest-gnome', label: 'Forest Gnome', parentRace: 'gnome', abilityBonuses: { intelligence: 2, dexterity: 1 }, traits: ['Natural Illusionist', 'Speak with Small Beasts'] },
  { value: 'rock-gnome', label: 'Rock Gnome', parentRace: 'gnome', abilityBonuses: { intelligence: 2, constitution: 1 }, traits: ["Artificer's Lore", 'Tinker'] },
  // Dragonborn (subraces by ancestry)
  { value: 'black-dragonborn', label: 'Black Dragonborn', parentRace: 'dragonborn', abilityBonuses: { strength: 2, charisma: 1 }, traits: ['Acid Breath (5x30 ft line)'] },
  { value: 'blue-dragonborn', label: 'Blue Dragonborn', parentRace: 'dragonborn', abilityBonuses: { strength: 2, charisma: 1 }, traits: ['Lightning Breath (5x30 ft line)'] },
  { value: 'brass-dragonborn', label: 'Brass Dragonborn', parentRace: 'dragonborn', abilityBonuses: { strength: 2, charisma: 1 }, traits: ['Fire Breath (5x30 ft line)'] },
  { value: 'bronze-dragonborn', label: 'Bronze Dragonborn', parentRace: 'dragonborn', abilityBonuses: { strength: 2, charisma: 1 }, traits: ['Lightning Breath (5x30 ft line)'] },
  { value: 'copper-dragonborn', label: 'Copper Dragonborn', parentRace: 'dragonborn', abilityBonuses: { strength: 2, charisma: 1 }, traits: ['Acid Breath (5x30 ft line)'] },
  { value: 'gold-dragonborn', label: 'Gold Dragonborn', parentRace: 'dragonborn', abilityBonuses: { strength: 2, charisma: 1 }, traits: ['Fire Breath (15 ft cone)'] },
  { value: 'green-dragonborn', label: 'Green Dragonborn', parentRace: 'dragonborn', abilityBonuses: { strength: 2, charisma: 1 }, traits: ['Poison Breath (15 ft cone)'] },
  { value: 'red-dragonborn', label: 'Red Dragonborn', parentRace: 'dragonborn', abilityBonuses: { strength: 2, charisma: 1 }, traits: ['Fire Breath (15 ft cone)'] },
  { value: 'silver-dragonborn', label: 'Silver Dragonborn', parentRace: 'dragonborn', abilityBonuses: { strength: 2, charisma: 1 }, traits: ['Cold Breath (15 ft cone)'] },
  { value: 'white-dragonborn', label: 'White Dragonborn', parentRace: 'dragonborn', abilityBonuses: { strength: 2, charisma: 1 }, traits: ['Cold Breath (15 ft cone)'] },
  // Human (variant)
  { value: 'variant-human', label: 'Variant Human', parentRace: 'human', abilityBonuses: {}, traits: ['+1 to two abilities of choice', 'Extra Skill', 'Extra Feat'] },
  // Half-Elf (no subraces in SRD but include for completeness)
  // Half-Orc (no subraces)
  // Tiefling (no subraces in SRD)
]

// ============================================================================
// Subclasses
// ============================================================================
export const SUBCLASSES: SubclassData[] = [
  // Barbarian (Level 3)
  { value: 'berserker', label: 'Path of the Berserker', parentClass: 'barbarian', levelAvailable: 3, features: [{ name: 'Frenzy', description: 'Bonus action attack while raging' }] },
  // Bard (Level 3)
  { value: 'lore', label: 'College of Lore', parentClass: 'bard', levelAvailable: 3, features: [{ name: 'Cutting Words', description: 'Use Bardic Inspiration to subtract from enemy rolls' }] },
  // Cleric (Level 1)
  { value: 'life', label: 'Life Domain', parentClass: 'cleric', levelAvailable: 1, features: [{ name: 'Disciple of Life', description: 'Healing spells restore extra HP' }] },
  // Druid (Level 2)
  { value: 'land', label: 'Circle of the Land', parentClass: 'druid', levelAvailable: 2, features: [{ name: 'Natural Recovery', description: 'Recover spell slots during short rest' }] },
  // Fighter (Level 3)
  { value: 'champion', label: 'Champion', parentClass: 'fighter', levelAvailable: 3, features: [{ name: 'Improved Critical', description: 'Critical hit on 19-20' }] },
  // Monk (Level 3)
  { value: 'open-hand', label: 'Way of the Open Hand', parentClass: 'monk', levelAvailable: 3, features: [{ name: 'Open Hand Technique', description: 'Extra effects on Flurry of Blows' }] },
  // Paladin (Level 3)
  { value: 'devotion', label: 'Oath of Devotion', parentClass: 'paladin', levelAvailable: 3, features: [{ name: 'Sacred Weapon', description: 'Channel Divinity to enchant weapon' }] },
  // Ranger (Level 3)
  { value: 'hunter', label: 'Hunter', parentClass: 'ranger', levelAvailable: 3, features: [{ name: "Hunter's Prey", description: 'Choose a combat specialty' }] },
  // Rogue (Level 3)
  { value: 'thief', label: 'Thief', parentClass: 'rogue', levelAvailable: 3, features: [{ name: 'Fast Hands', description: 'Bonus action Use Object, thieves\' tools, or Sleight of Hand' }] },
  // Sorcerer (Level 1)
  { value: 'draconic', label: 'Draconic Bloodline', parentClass: 'sorcerer', levelAvailable: 1, features: [{ name: 'Draconic Resilience', description: 'Extra HP and natural AC' }] },
  // Warlock (Level 1)
  { value: 'fiend', label: 'The Fiend', parentClass: 'warlock', levelAvailable: 1, features: [{ name: "Dark One's Blessing", description: 'Gain temp HP when reducing a creature to 0' }] },
  // Wizard (Level 2)
  { value: 'evocation', label: 'School of Evocation', parentClass: 'wizard', levelAvailable: 2, features: [{ name: 'Sculpt Spells', description: 'Protect allies from your evocation spells' }] },
]

// ============================================================================
// Backgrounds
// ============================================================================
export const BACKGROUNDS: BackgroundData[] = [
  {
    value: 'acolyte', label: 'Acolyte',
    skillProficiencies: ['Insight', 'Religion'], toolProficiencies: [], languages: 2,
    equipment: ['Holy symbol', 'Prayer book', '5 sticks of incense', 'Vestments', '15 gp'],
    feature: { name: 'Shelter of the Faithful', description: 'You and your companions can receive free healing and care at temples of your faith.' },
    personalityTraits: ['I idolize a particular hero of my faith.', 'Nothing can shake my optimistic attitude.', 'I quote sacred texts in almost every situation.', 'I see omens in every event.'],
    ideals: ['Tradition. The ancient traditions must be preserved.', 'Charity. I always try to help those in need.', 'Faith. I trust that my deity will guide my actions.'],
    bonds: ['I would die to recover an ancient relic of my faith.', 'I owe my life to the priest who took me in.'],
    flaws: ['I judge others harshly, and myself even more severely.', 'I put too much trust in those who wield power.'],
  },
  {
    value: 'charlatan', label: 'Charlatan',
    skillProficiencies: ['Deception', 'Sleight of Hand'], toolProficiencies: ['Disguise kit', 'Forgery kit'], languages: 0,
    equipment: ['Fine clothes', 'Disguise kit', 'Tools of the con', '15 gp'],
    feature: { name: 'False Identity', description: 'You have a second identity with documentation, established acquaintances, and disguises.' },
    personalityTraits: ['I fall in and out of love easily.', 'I have a joke for every occasion.', 'Flattery is my preferred trick.', 'I lie about almost everything.'],
    ideals: ['Independence. I am a free spirit.', 'Fairness. I never target people who can\'t afford to lose.', 'Creativity. I never run the same con twice.'],
    bonds: ['I fleeced the wrong person and must work to ensure they never cross paths with me again.'],
    flaws: ['I can\'t resist swindling people who are more powerful than me.', 'I\'m convinced no one could ever fool me.'],
  },
  {
    value: 'criminal', label: 'Criminal',
    skillProficiencies: ['Deception', 'Stealth'], toolProficiencies: ["Thieves' tools", 'One type of gaming set'], languages: 0,
    equipment: ['Crowbar', 'Dark common clothes with hood', '15 gp'],
    feature: { name: 'Criminal Contact', description: 'You have a reliable and trustworthy contact who acts as your liaison to a criminal network.' },
    personalityTraits: ['I always have a plan for what to do when things go wrong.', 'I am always calm, no matter the situation.'],
    ideals: ['Honor. I don\'t steal from others in the trade.', 'Freedom. Chains are meant to be broken.'],
    bonds: ['I\'m trying to pay off an old debt.', 'Someone I loved died because of a mistake I made.'],
    flaws: ['When I see something valuable, I can\'t think about anything but how to steal it.'],
  },
  {
    value: 'entertainer', label: 'Entertainer',
    skillProficiencies: ['Acrobatics', 'Performance'], toolProficiencies: ['Disguise kit', 'One musical instrument'], languages: 0,
    equipment: ['Musical instrument', 'Favor of an admirer', 'Costume', '15 gp'],
    feature: { name: 'By Popular Demand', description: 'You can always find a place to perform and receive free lodging and food.' },
    personalityTraits: ['I know a story relevant to almost every situation.', 'Nobody stays angry at me for long.', 'I love a good insult, even one directed at me.'],
    ideals: ['Beauty. When I perform, I make the world better.', 'Tradition. The stories of old must be preserved.'],
    bonds: ['I want to be famous, whatever it takes.', 'My instrument is my most treasured possession.'],
    flaws: ['I\'ll do anything to win fame and renown.', 'A scandal prevents me from returning home.'],
  },
  {
    value: 'folk-hero', label: 'Folk Hero',
    skillProficiencies: ['Animal Handling', 'Survival'], toolProficiencies: ["Artisan's tools", 'Vehicles (land)'], languages: 0,
    equipment: ["Artisan's tools", 'Shovel', 'Iron pot', 'Common clothes', '10 gp'],
    feature: { name: 'Rustic Hospitality', description: 'Common folk will shield you from the law or dangerous situations.' },
    personalityTraits: ['I judge people by their actions, not their words.', 'If someone is in trouble, I\'m always ready to help.'],
    ideals: ['Respect. People deserve to be treated with dignity.', 'Sincerity. There\'s no good in pretending to be something I\'m not.'],
    bonds: ['I protect those who cannot protect themselves.', 'I have a family I would do anything for.'],
    flaws: ['I\'m convinced of the significance of my destiny.', 'I have a weakness for vices of the city.'],
  },
  {
    value: 'guild-artisan', label: 'Guild Artisan',
    skillProficiencies: ['Insight', 'Persuasion'], toolProficiencies: ["Artisan's tools"], languages: 1,
    equipment: ["Artisan's tools", 'Letter of introduction from guild', "Traveler's clothes", '15 gp'],
    feature: { name: 'Guild Membership', description: 'Your guild provides lodging, legal help, and political connections.' },
    personalityTraits: ['I believe that anything worth doing is worth doing right.', 'I\'m well known for my work and want to be recognized.'],
    ideals: ['Community. My obligations are to my guild first.', 'Generosity. My talents were given to me to benefit the world.'],
    bonds: ['I created a great work for someone and they took it.', 'I owe my guild a great debt.'],
    flaws: ['I\'m horribly jealous of anyone with greater skill.', 'I\'ll do anything to get my hands on rare materials.'],
  },
  {
    value: 'hermit', label: 'Hermit',
    skillProficiencies: ['Medicine', 'Religion'], toolProficiencies: ['Herbalism kit'], languages: 1,
    equipment: ['Scroll case with notes', 'Winter blanket', 'Herbalism kit', 'Common clothes', '5 gp'],
    feature: { name: 'Discovery', description: 'You have discovered a unique and powerful truth about the cosmos, the deities, or some other aspect of reality.' },
    personalityTraits: ['I\'ve been isolated so long that I rarely speak.', 'I am utterly serene, even in the face of disaster.', 'I connect everything that happens to a grand cosmic plan.'],
    ideals: ['Knowledge. The path to power is through knowledge.', 'Self-Knowledge. Know thyself.'],
    bonds: ['Nothing is more important than the discovery I made.', 'I entered seclusion to hide from those who might still be hunting me.'],
    flaws: ['Now that I\'ve returned to the world, I enjoy its delights too much.', 'I harbor dark, bloodthirsty thoughts.'],
  },
  {
    value: 'noble', label: 'Noble',
    skillProficiencies: ['History', 'Persuasion'], toolProficiencies: ['One type of gaming set'], languages: 1,
    equipment: ['Fine clothes', 'Signet ring', 'Scroll of pedigree', '25 gp'],
    feature: { name: 'Position of Privilege', description: 'People are inclined to think the best of you due to your noble birth.' },
    personalityTraits: ['My eloquent flattery makes everyone feel important.', 'I take great pains to always look my best.', 'The common folk love me for my kindness.'],
    ideals: ['Responsibility. It is my duty to respect the authority of those above me.', 'Noble Obligation. It is my duty to protect my people.'],
    bonds: ['I will face any challenge to win the approval of my family.', 'My house\'s alliance with another noble family must be sustained.'],
    flaws: ['I secretly believe that everyone is beneath me.', 'I hide a truly scandalous secret.'],
  },
  {
    value: 'outlander', label: 'Outlander',
    skillProficiencies: ['Athletics', 'Survival'], toolProficiencies: ['One musical instrument'], languages: 1,
    equipment: ['Staff', 'Hunting trap', 'Trophy', "Traveler's clothes", '10 gp'],
    feature: { name: 'Wanderer', description: 'You have an excellent memory for maps and geography and can always find food and water for yourself and up to five others.' },
    personalityTraits: ['I\'m driven by a wanderlust that led me away from home.', 'I watch over my friends as if they were newborns.'],
    ideals: ['Change. Life is like the seasons, in constant change.', 'Nature. The natural world is more important than civilization.'],
    bonds: ['My family, clan, or tribe is the most important thing.', 'I suffer awful visions and must find their meaning.'],
    flaws: ['I am slow to trust members of other races.', 'Violence is my answer to almost any challenge.'],
  },
  {
    value: 'sage', label: 'Sage',
    skillProficiencies: ['Arcana', 'History'], toolProficiencies: [], languages: 2,
    equipment: ['Bottle of black ink', 'Quill', 'Small knife', 'Letter from dead colleague', 'Common clothes', '10 gp'],
    feature: { name: 'Researcher', description: 'When you attempt to learn something, you know where to find the information.' },
    personalityTraits: ['I use polysyllabic words to convey the impression of great erudition.', 'I\'ve read every book in the world\'s greatest libraries.', 'There\'s nothing I like more than a good mystery.'],
    ideals: ['Knowledge. The path to power is through knowledge.', 'No Limits. Nothing should fetter the possibilities of existence.'],
    bonds: ['I have a great library I must protect.', 'My life\'s work is a series of tomes related to a specific field.'],
    flaws: ['I am easily distracted by the promise of information.', 'Most people scream and run when they see a demon. I stop and take notes.'],
  },
  {
    value: 'sailor', label: 'Sailor',
    skillProficiencies: ['Athletics', 'Perception'], toolProficiencies: ["Navigator's tools", 'Vehicles (water)'], languages: 0,
    equipment: ['Belaying pin (club)', '50 ft silk rope', 'Lucky charm', 'Common clothes', '10 gp'],
    feature: { name: 'Ship\'s Passage', description: 'You can secure free passage on a sailing ship for yourself and your party.' },
    personalityTraits: ['My friends know they can rely on me, no matter what.', 'I stretch the truth for the sake of a good story.'],
    ideals: ['Freedom. The sea is freedom.', 'Mastery. I\'m a predator, and other ships are my prey.'],
    bonds: ['My ship comes first.', 'I was cheated out of my fair share of profits.'],
    flaws: ['I follow orders, even if I think they\'re wrong.', 'Once I start drinking, it\'s hard for me to stop.'],
  },
  {
    value: 'soldier', label: 'Soldier',
    skillProficiencies: ['Athletics', 'Intimidation'], toolProficiencies: ['One type of gaming set', 'Vehicles (land)'], languages: 0,
    equipment: ['Insignia of rank', 'Trophy from fallen enemy', 'Dice set', 'Common clothes', '10 gp'],
    feature: { name: 'Military Rank', description: 'Soldiers loyal to your former military organization still recognize your authority.' },
    personalityTraits: ['I\'m always polite and respectful.', 'I can stare down a hell hound without flinching.', 'I face problems head-on.'],
    ideals: ['Greater Good. Our lot is to lay down our lives in defense of others.', 'Might. In life as in war, the stronger force wins.'],
    bonds: ['I would still lay down my life for the people I served with.', 'Someone saved my life on the battlefield. I will never leave a friend behind.'],
    flaws: ['I obey the law, even if it causes misery.', 'I made a terrible mistake in battle that haunts me.'],
  },
  {
    value: 'urchin', label: 'Urchin',
    skillProficiencies: ['Sleight of Hand', 'Stealth'], toolProficiencies: ['Disguise kit', "Thieves' tools"], languages: 0,
    equipment: ['Small knife', 'Map of city', 'Pet mouse', 'Token of parents', 'Common clothes', '10 gp'],
    feature: { name: 'City Secrets', description: 'You know the secret patterns and flow of cities and can travel twice as fast through them.' },
    personalityTraits: ['I hide scraps of food and trinkets away in my pockets.', 'I ask a lot of questions.', 'I bluntly say what other people are hinting at.'],
    ideals: ['Respect. All people deserve to be treated with dignity.', 'Community. We have to take care of each other.'],
    bonds: ['I owe my survival to another urchin who taught me to live on the streets.', 'No one else should have to endure the hardships I\'ve been through.'],
    flaws: ['I\'d rather kill someone in their sleep than fight fair.', 'It\'s not stealing if I need it more than someone else.'],
  },
]

// ============================================================================
// Skills
// ============================================================================
export const SKILLS: SkillData[] = [
  { value: 'acrobatics', label: 'Acrobatics', ability: 'dexterity', abilityShort: 'DEX' },
  { value: 'animal-handling', label: 'Animal Handling', ability: 'wisdom', abilityShort: 'WIS' },
  { value: 'arcana', label: 'Arcana', ability: 'intelligence', abilityShort: 'INT' },
  { value: 'athletics', label: 'Athletics', ability: 'strength', abilityShort: 'STR' },
  { value: 'deception', label: 'Deception', ability: 'charisma', abilityShort: 'CHA' },
  { value: 'history', label: 'History', ability: 'intelligence', abilityShort: 'INT' },
  { value: 'insight', label: 'Insight', ability: 'wisdom', abilityShort: 'WIS' },
  { value: 'intimidation', label: 'Intimidation', ability: 'charisma', abilityShort: 'CHA' },
  { value: 'investigation', label: 'Investigation', ability: 'intelligence', abilityShort: 'INT' },
  { value: 'medicine', label: 'Medicine', ability: 'wisdom', abilityShort: 'WIS' },
  { value: 'nature', label: 'Nature', ability: 'intelligence', abilityShort: 'INT' },
  { value: 'perception', label: 'Perception', ability: 'wisdom', abilityShort: 'WIS' },
  { value: 'performance', label: 'Performance', ability: 'charisma', abilityShort: 'CHA' },
  { value: 'persuasion', label: 'Persuasion', ability: 'charisma', abilityShort: 'CHA' },
  { value: 'religion', label: 'Religion', ability: 'intelligence', abilityShort: 'INT' },
  { value: 'sleight-of-hand', label: 'Sleight of Hand', ability: 'dexterity', abilityShort: 'DEX' },
  { value: 'stealth', label: 'Stealth', ability: 'dexterity', abilityShort: 'DEX' },
  { value: 'survival', label: 'Survival', ability: 'wisdom', abilityShort: 'WIS' },
]

// ============================================================================
// Class Skill Choices
// ============================================================================
export const CLASS_SKILL_CHOICES: Record<string, { count: number; options: string[] }> = {
  barbarian: { count: 2, options: ['animal-handling', 'athletics', 'intimidation', 'nature', 'perception', 'survival'] },
  bard: { count: 3, options: SKILLS.map(s => s.value) }, // Any 3
  cleric: { count: 2, options: ['history', 'insight', 'medicine', 'persuasion', 'religion'] },
  druid: { count: 2, options: ['arcana', 'animal-handling', 'insight', 'medicine', 'nature', 'perception', 'religion', 'survival'] },
  fighter: { count: 2, options: ['acrobatics', 'animal-handling', 'athletics', 'history', 'insight', 'intimidation', 'perception', 'survival'] },
  monk: { count: 2, options: ['acrobatics', 'athletics', 'history', 'insight', 'religion', 'stealth'] },
  paladin: { count: 2, options: ['athletics', 'insight', 'intimidation', 'medicine', 'persuasion', 'religion'] },
  ranger: { count: 3, options: ['animal-handling', 'athletics', 'insight', 'investigation', 'nature', 'perception', 'stealth', 'survival'] },
  rogue: { count: 4, options: ['acrobatics', 'athletics', 'deception', 'insight', 'intimidation', 'investigation', 'perception', 'performance', 'persuasion', 'sleight-of-hand', 'stealth'] },
  sorcerer: { count: 2, options: ['arcana', 'deception', 'insight', 'intimidation', 'persuasion', 'religion'] },
  warlock: { count: 2, options: ['arcana', 'deception', 'history', 'intimidation', 'investigation', 'nature', 'religion'] },
  wizard: { count: 2, options: ['arcana', 'history', 'insight', 'investigation', 'medicine', 'religion'] },
}

// ============================================================================
// Alignments
// ============================================================================
export const ALIGNMENTS = [
  { value: 'lawful-good', label: 'Lawful Good' },
  { value: 'neutral-good', label: 'Neutral Good' },
  { value: 'chaotic-good', label: 'Chaotic Good' },
  { value: 'lawful-neutral', label: 'Lawful Neutral' },
  { value: 'true-neutral', label: 'True Neutral' },
  { value: 'chaotic-neutral', label: 'Chaotic Neutral' },
  { value: 'lawful-evil', label: 'Lawful Evil' },
  { value: 'neutral-evil', label: 'Neutral Evil' },
  { value: 'chaotic-evil', label: 'Chaotic Evil' },
]

// ============================================================================
// Languages
// ============================================================================
export const LANGUAGES: LanguageData[] = [
  { value: 'Common', label: 'Common', type: 'standard' },
  { value: 'Dwarvish', label: 'Dwarvish', type: 'standard' },
  { value: 'Elvish', label: 'Elvish', type: 'standard' },
  { value: 'Giant', label: 'Giant', type: 'standard' },
  { value: 'Gnomish', label: 'Gnomish', type: 'standard' },
  { value: 'Goblin', label: 'Goblin', type: 'standard' },
  { value: 'Halfling', label: 'Halfling', type: 'standard' },
  { value: 'Orc', label: 'Orc', type: 'standard' },
  { value: 'Abyssal', label: 'Abyssal', type: 'exotic' },
  { value: 'Celestial', label: 'Celestial', type: 'exotic' },
  { value: 'Draconic', label: 'Draconic', type: 'exotic' },
  { value: 'Deep Speech', label: 'Deep Speech', type: 'exotic' },
  { value: 'Infernal', label: 'Infernal', type: 'exotic' },
  { value: 'Primordial', label: 'Primordial', type: 'exotic' },
  { value: 'Sylvan', label: 'Sylvan', type: 'exotic' },
  { value: 'Undercommon', label: 'Undercommon', type: 'exotic' },
]

export const RACIAL_LANGUAGES: Record<string, string[]> = {
  human: ['Common'],
  elf: ['Common', 'Elvish'],
  dwarf: ['Common', 'Dwarvish'],
  halfling: ['Common', 'Halfling'],
  gnome: ['Common', 'Gnomish'],
  'half-elf': ['Common', 'Elvish'],
  'half-orc': ['Common', 'Orc'],
  tiefling: ['Common', 'Infernal'],
  dragonborn: ['Common', 'Draconic'],
}

// ============================================================================
// Hit Dice per class
// ============================================================================
export const HIT_DICE: Record<string, number> = {
  barbarian: 12,
  bard: 8,
  cleric: 8,
  druid: 8,
  fighter: 10,
  monk: 8,
  paladin: 10,
  ranger: 10,
  rogue: 8,
  sorcerer: 6,
  warlock: 8,
  wizard: 6,
}

// ============================================================================
// Point Buy System
// ============================================================================
export const POINT_BUY_COSTS: Record<number, number> = {
  8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9,
}

export const STANDARD_ARRAY = [15, 14, 13, 12, 10, 8]
export const POINT_BUY_BUDGET = 27

// ============================================================================
// Spellcasting Classes (Level 1 info)
// ============================================================================
export const SPELLCASTING_CLASSES: Record<string, SpellcasterInfo> = {
  bard: { cantripsKnown: 2, spellsKnownOrPrepared: 4, spellSlots: [2] },
  cleric: { cantripsKnown: 3, spellsKnownOrPrepared: 0, spellSlots: [2] }, // prepares from full list
  druid: { cantripsKnown: 2, spellsKnownOrPrepared: 0, spellSlots: [2] }, // prepares from full list
  sorcerer: { cantripsKnown: 4, spellsKnownOrPrepared: 2, spellSlots: [2] },
  warlock: { cantripsKnown: 2, spellsKnownOrPrepared: 2, spellSlots: [1] },
  wizard: { cantripsKnown: 3, spellsKnownOrPrepared: 0, spellSlots: [2] }, // prepares from spellbook
}

// ============================================================================
// Starting Equipment Choices
// ============================================================================
export const STARTING_EQUIPMENT: Record<string, EquipmentChoice[]> = {
  barbarian: [
    { label: 'Primary Weapon', options: [['Greataxe'], ['Any martial melee weapon']] },
    { label: 'Secondary Weapon', options: [['Two handaxes'], ['Any simple weapon']] },
    { label: 'Pack', options: [["Explorer's pack"]] },
  ],
  bard: [
    { label: 'Weapon', options: [['Rapier'], ['Longsword'], ['Any simple weapon']] },
    { label: 'Pack', options: [["Diplomat's pack"], ["Entertainer's pack"]] },
    { label: 'Instrument', options: [['Lute'], ['Any musical instrument']] },
  ],
  cleric: [
    { label: 'Weapon', options: [['Mace'], ['Warhammer (if proficient)']] },
    { label: 'Armor', options: [['Scale mail'], ['Leather armor'], ['Chain mail (if proficient)']] },
    { label: 'Secondary', options: [['Light crossbow & 20 bolts'], ['Any simple weapon']] },
    { label: 'Pack', options: [["Priest's pack"], ["Explorer's pack"]] },
  ],
  druid: [
    { label: 'Shield or Weapon', options: [['Wooden shield'], ['Any simple weapon']] },
    { label: 'Weapon', options: [['Scimitar'], ['Any simple melee weapon']] },
    { label: 'Pack', options: [["Explorer's pack"]] },
  ],
  fighter: [
    { label: 'Armor', options: [['Chain mail'], ['Leather armor, longbow & 20 arrows']] },
    { label: 'Weapon & Shield', options: [['Martial weapon & shield'], ['Two martial weapons']] },
    { label: 'Ranged', options: [['Light crossbow & 20 bolts'], ['Two handaxes']] },
    { label: 'Pack', options: [["Dungeoneer's pack"], ["Explorer's pack"]] },
  ],
  monk: [
    { label: 'Weapon', options: [['Shortsword'], ['Any simple weapon']] },
    { label: 'Pack', options: [["Dungeoneer's pack"], ["Explorer's pack"]] },
  ],
  paladin: [
    { label: 'Weapon', options: [['Martial weapon & shield'], ['Two martial weapons']] },
    { label: 'Secondary', options: [['Five javelins'], ['Any simple melee weapon']] },
    { label: 'Pack', options: [["Priest's pack"], ["Explorer's pack"]] },
  ],
  ranger: [
    { label: 'Armor', options: [['Scale mail'], ['Leather armor']] },
    { label: 'Weapons', options: [['Two shortswords'], ['Two simple melee weapons']] },
    { label: 'Pack', options: [["Dungeoneer's pack"], ["Explorer's pack"]] },
  ],
  rogue: [
    { label: 'Weapon', options: [['Rapier'], ['Shortsword']] },
    { label: 'Secondary', options: [['Shortbow & 20 arrows'], ['Shortsword']] },
    { label: 'Pack', options: [["Burglar's pack"], ["Dungeoneer's pack"], ["Explorer's pack"]] },
  ],
  sorcerer: [
    { label: 'Weapon', options: [['Light crossbow & 20 bolts'], ['Any simple weapon']] },
    { label: 'Focus', options: [['Component pouch'], ['Arcane focus']] },
    { label: 'Pack', options: [["Dungeoneer's pack"], ["Explorer's pack"]] },
  ],
  warlock: [
    { label: 'Weapon', options: [['Light crossbow & 20 bolts'], ['Any simple weapon']] },
    { label: 'Focus', options: [['Component pouch'], ['Arcane focus']] },
    { label: 'Pack', options: [["Scholar's pack"], ["Dungeoneer's pack"]] },
  ],
  wizard: [
    { label: 'Weapon', options: [['Quarterstaff'], ['Dagger']] },
    { label: 'Focus', options: [['Component pouch'], ['Arcane focus']] },
    { label: 'Pack', options: [["Scholar's pack"], ["Explorer's pack"]] },
  ],
}
