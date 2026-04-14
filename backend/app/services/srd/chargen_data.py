"""
Comprehensive D&D 5e character creation data.

Pure data file - no services, no logic. Contains all reference data needed
for character generation: subraces, subclasses, backgrounds, skills,
equipment, languages, and ability score methods.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Subrace:
    """A subrace option for a PHB race."""
    name: str
    parent_race: str
    ability_bonuses: Dict[str, int] = field(default_factory=dict)
    traits: List[str] = field(default_factory=list)
    trait_descriptions: Dict[str, str] = field(default_factory=dict)


@dataclass
class DraconicAncestry:
    """Dragonborn draconic ancestry entry."""
    dragon: str
    damage_type: str
    breath_shape: str


@dataclass
class SubclassFeature:
    """A single subclass feature gained at a specific level."""
    name: str
    level: int
    description: str


@dataclass
class Subclass:
    """A subclass (archetype / path / domain / etc.)."""
    name: str
    parent_class: str
    subclass_level: int
    description: str = ""
    features: List[SubclassFeature] = field(default_factory=list)


@dataclass
class Background:
    """A PHB background."""
    name: str
    skill_proficiencies: List[str] = field(default_factory=list)
    tool_proficiencies: List[str] = field(default_factory=list)
    languages: int = 0
    equipment: List[str] = field(default_factory=list)
    feature_name: str = ""
    feature_description: str = ""
    personality_traits: List[str] = field(default_factory=list)
    ideals: List[str] = field(default_factory=list)
    bonds: List[str] = field(default_factory=list)
    flaws: List[str] = field(default_factory=list)


@dataclass
class Skill:
    """A D&D 5e skill."""
    name: str
    ability: str
    description: str = ""


@dataclass
class ClassSkillChoices:
    """Skill-choice rules for a class."""
    class_name: str
    choose: int
    from_skills: List[str] = field(default_factory=list)


@dataclass
class EquipmentChoice:
    """One option within a starting-equipment choice."""
    items: List[str] = field(default_factory=list)


@dataclass
class ClassStartingEquipment:
    """Starting equipment for a class."""
    class_name: str
    choices: List[List[EquipmentChoice]] = field(default_factory=list)
    guaranteed: List[str] = field(default_factory=list)


@dataclass
class Language:
    """A D&D 5e language."""
    name: str
    type: str  # "Standard" or "Exotic"
    typical_speakers: str = ""


@dataclass
class SpellcastingInfo:
    """Spellcasting metadata for a class."""
    class_name: str
    ability: str
    type: str  # "full", "half", "third", "pact"
    cantrips_known: Optional[int] = None
    learn_style: str = "known"  # "known" or "prepared"


# ===========================================================================
#  SUBRACES
# ===========================================================================

SUBRACES: List[Subrace] = [
    # -- Dwarf
    Subrace(
        name="Hill Dwarf", parent_race="Dwarf",
        ability_bonuses={"WIS": 1},
        traits=["Dwarven Toughness"],
        trait_descriptions={"Dwarven Toughness": "Your hit point maximum increases by 1, and it increases by 1 every time you gain a level."},
    ),
    Subrace(
        name="Mountain Dwarf", parent_race="Dwarf",
        ability_bonuses={"STR": 2},
        traits=["Dwarven Armor Training"],
        trait_descriptions={"Dwarven Armor Training": "You have proficiency with light and medium armor."},
    ),
    # -- Elf
    Subrace(
        name="High Elf", parent_race="Elf",
        ability_bonuses={"INT": 1},
        traits=["Cantrip", "Extra Language"],
        trait_descriptions={
            "Cantrip": "You know one cantrip of your choice from the wizard spell list. Intelligence is your spellcasting ability for it.",
            "Extra Language": "You can speak, read, and write one extra language of your choice.",
        },
    ),
    Subrace(
        name="Wood Elf", parent_race="Elf",
        ability_bonuses={"WIS": 1},
        traits=["Fleet of Foot", "Mask of the Wild"],
        trait_descriptions={
            "Fleet of Foot": "Your base walking speed increases to 35 feet.",
            "Mask of the Wild": "You can attempt to hide even when you are only lightly obscured by foliage, heavy rain, falling snow, mist, and other natural phenomena.",
        },
    ),
    Subrace(
        name="Drow", parent_race="Elf",
        ability_bonuses={"CHA": 1},
        traits=["Superior Darkvision", "Drow Magic", "Sunlight Sensitivity"],
        trait_descriptions={
            "Superior Darkvision": "Your darkvision has a radius of 120 feet.",
            "Drow Magic": "You know the dancing lights cantrip. At 3rd level you can cast faerie fire once per long rest, and at 5th level you can cast darkness once per long rest. Charisma is your spellcasting ability.",
            "Sunlight Sensitivity": "You have disadvantage on attack rolls and Wisdom (Perception) checks that rely on sight when you, the target, or what you are trying to perceive is in direct sunlight.",
        },
    ),
    # -- Halfling
    Subrace(
        name="Lightfoot", parent_race="Halfling",
        ability_bonuses={"CHA": 1},
        traits=["Naturally Stealthy"],
        trait_descriptions={"Naturally Stealthy": "You can attempt to hide even when you are obscured only by a creature that is at least one size larger than you."},
    ),
    Subrace(
        name="Stout", parent_race="Halfling",
        ability_bonuses={"CON": 1},
        traits=["Stout Resilience"],
        trait_descriptions={"Stout Resilience": "You have advantage on saving throws against poison, and you have resistance against poison damage."},
    ),
    # -- Gnome
    Subrace(
        name="Forest Gnome", parent_race="Gnome",
        ability_bonuses={"DEX": 1},
        traits=["Natural Illusionist", "Speak with Small Beasts"],
        trait_descriptions={
            "Natural Illusionist": "You know the minor illusion cantrip. Intelligence is your spellcasting ability for it.",
            "Speak with Small Beasts": "Through sounds and gestures, you can communicate simple ideas with Small or smaller beasts.",
        },
    ),
    Subrace(
        name="Rock Gnome", parent_race="Gnome",
        ability_bonuses={"CON": 1},
        traits=["Artificer's Lore", "Tinker"],
        trait_descriptions={
            "Artificer's Lore": "Whenever you make an Intelligence (History) check related to magic items, alchemical objects, or technological devices, you can add twice your proficiency bonus instead of any proficiency bonus you normally apply.",
            "Tinker": "You have proficiency with artisan's tools (tinker's tools). Using those tools, you can spend 1 hour and 10 gp worth of materials to construct a Tiny clockwork device (AC 5, 1 hp).",
        },
    ),
    # -- Human
    Subrace(
        name="Variant Human", parent_race="Human",
        ability_bonuses={},
        traits=["Ability Score Increase", "Skills", "Feat"],
        trait_descriptions={
            "Ability Score Increase": "Two different ability scores of your choice each increase by 1 (instead of all scores increasing by 1).",
            "Skills": "You gain proficiency in one skill of your choice.",
            "Feat": "You gain one feat of your choice.",
        },
    ),
]

# ===========================================================================
#  DRACONIC ANCESTRIES
# ===========================================================================

DRACONIC_ANCESTRIES: List[DraconicAncestry] = [
    DraconicAncestry(dragon="Black", damage_type="Acid", breath_shape="5 by 30 ft. line (Dex. save)"),
    DraconicAncestry(dragon="Blue", damage_type="Lightning", breath_shape="5 by 30 ft. line (Dex. save)"),
    DraconicAncestry(dragon="Brass", damage_type="Fire", breath_shape="5 by 30 ft. line (Dex. save)"),
    DraconicAncestry(dragon="Bronze", damage_type="Lightning", breath_shape="5 by 30 ft. line (Dex. save)"),
    DraconicAncestry(dragon="Copper", damage_type="Acid", breath_shape="5 by 30 ft. line (Dex. save)"),
    DraconicAncestry(dragon="Gold", damage_type="Fire", breath_shape="15 ft. cone (Dex. save)"),
    DraconicAncestry(dragon="Green", damage_type="Poison", breath_shape="15 ft. cone (Con. save)"),
    DraconicAncestry(dragon="Red", damage_type="Fire", breath_shape="15 ft. cone (Dex. save)"),
    DraconicAncestry(dragon="Silver", damage_type="Cold", breath_shape="15 ft. cone (Con. save)"),
    DraconicAncestry(dragon="White", damage_type="Cold", breath_shape="15 ft. cone (Con. save)"),
]

# ===========================================================================
#  SUBCLASSES
# ===========================================================================

SUBCLASSES: List[Subclass] = [
    Subclass(
        name="Path of the Berserker", parent_class="Barbarian", subclass_level=3,
        description="For some barbarians, rage is a means to an end â€” that end being violence.",
        features=[
            SubclassFeature(name="Frenzy", level=3, description="You can go into a frenzy when you rage. If you do so, for the duration of your rage you can make a single melee weapon attack as a bonus action on each of your turns after this one. When your rage ends, you suffer one level of exhaustion."),
            SubclassFeature(name="Mindless Rage", level=6, description="You can\'t be charmed or frightened while raging. If you are charmed or frightened when you enter your rage, the effect is suspended for the duration of the rage."),
            SubclassFeature(name="Intimidating Presence", level=10, description="You can use your action to frighten someone with your menacing presence. Choose one creature within 60 feet that can see or hear you. The creature must succeed on a Wisdom saving throw (DC equal to 8 + your proficiency bonus + your Charisma modifier) or be frightened of you until the end of your next turn."),
            SubclassFeature(name="Retaliation", level=14, description="When you take damage from a creature that is within 5 feet of you, you can use your reaction to make a melee weapon attack against that creature."),
        ],
    ),
    Subclass(
        name="College of Lore", parent_class="Bard", subclass_level=3,
        description="Bards of the College of Lore know something about most things, collecting bits of knowledge from sources as diverse as scholarly tomes and peasant tales.",
        features=[
            SubclassFeature(name="Bonus Proficiencies", level=3, description="When you join the College of Lore at 3rd level, you gain proficiency with three skills of your choice."),
            SubclassFeature(name="Cutting Words", level=3, description="When a creature that you can see within 60 feet of you makes an attack roll, an ability check, or a damage roll, you can use your reaction to expend one of your uses of Bardic Inspiration, rolling a Bardic Inspiration die and subtracting the number rolled from the creature\'s roll."),
            SubclassFeature(name="Additional Magical Secrets", level=6, description="You learn two spells of your choice from any class. A spell you choose must be of a level you can cast, as shown on the Bard table, or a cantrip. The chosen spells count as bard spells for you."),
            SubclassFeature(name="Peerless Skill", level=14, description="When you make an ability check, you can expend one use of Bardic Inspiration. Roll a Bardic Inspiration die and add the number rolled to your ability check."),
        ],
    ),
    Subclass(
        name="Life Domain", parent_class="Cleric", subclass_level=1,
        description="The Life domain focuses on the vibrant positive energy â€” one of the fundamental forces of the universe â€” that sustains all life.",
        features=[
            SubclassFeature(name="Bonus Proficiency", level=1, description="When you choose this domain at 1st level, you gain proficiency with heavy armor."),
            SubclassFeature(name="Disciple of Life", level=1, description="Your healing spells are more effective. Whenever you use a spell of 1st level or higher to restore hit points to a creature, the creature regains additional hit points equal to 2 + the spell\'s level."),
            SubclassFeature(name="Channel Divinity: Preserve Life", level=2, description="You can use your Channel Divinity to heal the badly injured. As an action, you present your holy symbol and evoke healing energy that can restore a number of hit points equal to five times your cleric level. Choose any creatures within 30 feet of you, and divide those hit points among them."),
            SubclassFeature(name="Blessed Healer", level=6, description="The healing spells you cast on others heal you as well. When you cast a spell of 1st level or higher that restores hit points to a creature other than you, you regain hit points equal to 2 + the spell\'s level."),
            SubclassFeature(name="Divine Strike", level=8, description="You gain the ability to infuse your weapon strikes with divine energy. Once on each of your turns when you hit a creature with a weapon attack, you can cause the attack to deal an extra 1d8 radiant damage to the target."),
            SubclassFeature(name="Supreme Healing", level=17, description="When you would normally roll one or more dice to restore hit points with a spell, you instead use the highest number possible for each die."),
        ],
    ),
    Subclass(
        name="Circle of the Land", parent_class="Druid", subclass_level=2,
        description="The Circle of the Land is made up of mystics and sages who safeguard ancient knowledge and rites through a vast oral tradition.",
        features=[
            SubclassFeature(name="Bonus Cantrip", level=2, description="When you choose this circle at 2nd level, you learn one additional druid cantrip of your choice."),
            SubclassFeature(name="Natural Recovery", level=2, description="During a short rest, you can recover expended spell slots. The spell slots can have a combined level that is equal to or less than half your druid level (rounded up), and none of the slots can be 6th level or higher."),
            SubclassFeature(name="Circle Spells", level=3, description="Your mystical connection to the land infuses you with the ability to cast certain spells. You gain access to circle spells connected to the land where you became a druid. These spells are always prepared and don\'t count against the number of spells you can prepare each day."),
            SubclassFeature(name="Land\'s Stride", level=6, description="Moving through nonmagical difficult terrain costs you no extra movement. You can also pass through nonmagical plants without being slowed by them and without taking damage from them."),
            SubclassFeature(name="Nature\'s Ward", level=10, description="You can\'t be charmed or frightened by elementals or fey, and you are immune to poison and disease."),
            SubclassFeature(name="Nature\'s Sanctuary", level=14, description="Creatures of the natural world sense your connection to nature and become hesitant to attack you. When a beast or plant creature attacks you, that creature must make a Wisdom saving throw against your druid spell save DC."),
        ],
    ),
    Subclass(
        name="Champion", parent_class="Fighter", subclass_level=3,
        description="The archetypal Champion focuses on the development of raw physical power honed to deadly perfection.",
        features=[
            SubclassFeature(name="Improved Critical", level=3, description="Your weapon attacks score a critical hit on a roll of 19 or 20."),
            SubclassFeature(name="Remarkable Athlete", level=7, description="You can add half your proficiency bonus (round up) to any Strength, Dexterity, or Constitution check you make that doesn\'t already use your proficiency bonus."),
            SubclassFeature(name="Additional Fighting Style", level=10, description="You can choose a second option from the Fighting Style class feature."),
            SubclassFeature(name="Superior Critical", level=15, description="Your weapon attacks score a critical hit on a roll of 18, 19, or 20."),
            SubclassFeature(name="Survivor", level=18, description="You attain the pinnacle of resilience in battle. At the start of each of your turns, you regain hit points equal to 5 + your Constitution modifier if you have no more than half of your hit points left. You don\'t gain this benefit if you have 0 hit points."),
        ],
    ),
    Subclass(
        name="Way of the Open Hand", parent_class="Monk", subclass_level=3,
        description="Monks of the Way of the Open Hand are the ultimate masters of martial arts combat.",
        features=[
            SubclassFeature(name="Open Hand Technique", level=3, description="Whenever you hit a creature with one of the attacks granted by your Flurry of Blows, you can impose one of the following effects: it must succeed on a Dexterity saving throw or be knocked prone; it must make a Strength saving throw or be pushed up to 15 feet away from you; it can\'t take reactions until the end of your next turn."),
            SubclassFeature(name="Wholeness of Body", level=6, description="You gain the ability to heal yourself. As an action, you can regain hit points equal to three times your monk level. You must finish a long rest before you can use this feature again."),
            SubclassFeature(name="Tranquility", level=11, description="Beginning at 11th level, you can enter a special meditation that surrounds you with an aura of peace. At the end of a long rest, you gain the effect of a sanctuary spell that lasts until the start of your next long rest."),
            SubclassFeature(name="Quivering Palm", level=17, description="You gain the ability to set up lethal vibrations in someone\'s body. When you hit a creature with an unarmed strike, you can spend 3 ki points to start these imperceptible vibrations. You can then use your action to force the target to make a Constitution saving throw. If it fails, the creature is reduced to 0 hit points. If it succeeds, the creature takes 10d10 necrotic damage."),
        ],
    ),
    Subclass(
        name="Oath of Devotion", parent_class="Paladin", subclass_level=3,
        description="The Oath of Devotion binds a paladin to the loftiest ideals of justice, virtue, and order.",
        features=[
            SubclassFeature(name="Channel Divinity", level=3, description="Sacred Weapon: As an action, you imbue one weapon you are holding with positive energy. For 1 minute, you add your Charisma modifier to attack rolls made with that weapon. Turn the Unholy: As an action, each fiend or undead within 30 feet must make a Wisdom saving throw or be turned for 1 minute."),
            SubclassFeature(name="Aura of Devotion", level=7, description="You and friendly creatures within 10 feet of you can\'t be charmed while you are conscious. At 18th level, the range increases to 30 feet."),
            SubclassFeature(name="Purity of Spirit", level=15, description="You are always under the effects of a protection from evil and good spell."),
            SubclassFeature(name="Holy Nimbus", level=20, description="As an action, you can emanate an aura of sunlight. For 1 minute, bright light shines from you in a 30-foot radius, and dim light shines 30 feet beyond that. Whenever an enemy creature starts its turn in the bright light, the creature takes 10 radiant damage."),
        ],
    ),
    Subclass(
        name="Hunter", parent_class="Ranger", subclass_level=3,
        description="Emulating the Hunter archetype means accepting your place as a bulwark between civilization and the terrors of the wilderness.",
        features=[
            SubclassFeature(name="Hunter\'s Prey", level=3, description="Choose one of the following features: Colossus Slayer (once per turn, extra 1d8 damage to wounded target), Giant Killer (reaction attack when Large+ creature misses you), or Horde Breaker (attack a second creature within 5 feet of first target)."),
            SubclassFeature(name="Defensive Tactics", level=7, description="Choose one: Escape the Horde (opportunity attacks against you are made with disadvantage), Multiattack Defense (+4 AC after being hit until the attacker\'s turn ends), or Steel Will (advantage on saves against being frightened)."),
            SubclassFeature(name="Multiattack", level=11, description="Choose one: Volley (make a ranged attack against any number of creatures within 10 feet of a point you can see within range) or Whirlwind Attack (melee attack against any number of creatures within 5 feet of you)."),
            SubclassFeature(name="Superior Hunter\'s Defense", level=15, description="Choose one: Evasion (Dex saves for half damage become no damage on success, half on fail), Stand Against the Tide (redirect a missed melee attack to another creature), or Uncanny Dodge (halve damage from an attack you can see as a reaction)."),
        ],
    ),
    Subclass(
        name="Thief", parent_class="Rogue", subclass_level=3,
        description="You hone your skills in the larcenous arts. Burglars, bandits, cutpurses, and other criminals typically follow this archetype.",
        features=[
            SubclassFeature(name="Fast Hands", level=3, description="You can use the bonus action granted by your Cunning Action to make a Dexterity (Sleight of Hand) check, use your thieves\' tools to disarm a trap or open a lock, or take the Use an Object action."),
            SubclassFeature(name="Second-Story Work", level=3, description="Climbing no longer costs you extra movement. In addition, when you make a running jump, the distance you cover increases by a number of feet equal to your Dexterity modifier."),
            SubclassFeature(name="Supreme Sneak", level=9, description="You have advantage on a Dexterity (Stealth) check if you move no more than half your speed on the same turn."),
            SubclassFeature(name="Use Magic Device", level=13, description="You have learned enough about the workings of magic that you can improvise the use of items even when they are not intended for you. You ignore all class, race, and level requirements on the use of magic items."),
            SubclassFeature(name="Thief\'s Reflexes", level=17, description="You have become adept at laying ambushes and quickly escaping danger. You can take two turns during the first round of any combat. You take your first turn at your normal initiative and your second turn at your initiative minus 10."),
        ],
    ),
    Subclass(
        name="Draconic Bloodline", parent_class="Sorcerer", subclass_level=1,
        description="Your innate magic comes from draconic magic that was mingled with your blood or that of your ancestors.",
        features=[
            SubclassFeature(name="Dragon Ancestor", level=1, description="You can speak, read, and write Draconic. Additionally, whenever you make a Charisma check when interacting with dragons, your proficiency bonus is doubled if it applies to the check."),
            SubclassFeature(name="Draconic Resilience", level=1, description="Your hit point maximum increases by 1 for each sorcerer level. Additionally, when you aren\'t wearing armor, your AC equals 13 + your Dexterity modifier."),
            SubclassFeature(name="Elemental Affinity", level=6, description="When you cast a spell that deals damage of the type associated with your draconic ancestry, add your Charisma modifier to one damage roll of that spell. You can spend 1 sorcery point to gain resistance to that damage type for 1 hour."),
            SubclassFeature(name="Dragon Wings", level=14, description="You gain the ability to sprout a pair of dragon wings from your back, gaining a flying speed equal to your current walking speed. You can create these wings as a bonus action on your turn."),
            SubclassFeature(name="Draconic Presence", level=18, description="You can channel the dread presence of your dragon ancestor. As an action, you can spend 5 sorcery points to draw on this power and exude an aura of awe or fear (your choice) to a distance of 60 feet. Hostile creatures must succeed on a Wisdom saving throw or be charmed (awe) or frightened (fear) until the aura ends."),
        ],
    ),
    Subclass(
        name="The Fiend", parent_class="Warlock", subclass_level=1,
        description="You have made a pact with a fiend from the lower planes of existence.",
        features=[
            SubclassFeature(name="Dark One\'s Blessing", level=1, description="When you reduce a hostile creature to 0 hit points, you gain temporary hit points equal to your Charisma modifier + your warlock level (minimum of 1)."),
            SubclassFeature(name="Dark One\'s Own Luck", level=6, description="When you make an ability check or a saving throw, you can use this feature to add a d10 to your roll. You can do so after seeing the initial roll but before any of the roll\'s effects occur. Once you use this feature, you can\'t use it again until you finish a short or long rest."),
            SubclassFeature(name="Fiendish Resilience", level=10, description="You can choose one damage type when you finish a short or long rest. You gain resistance to that damage type until you choose a different one with this feature."),
            SubclassFeature(name="Hurl Through Hell", level=14, description="When you hit a creature with an attack, you can use this feature to instantly transport the target through the lower planes. The creature disappears and hurtles through a nightmare landscape. At the end of your next turn, the target returns to the space it previously occupied. If the target is not a fiend, it takes 10d10 psychic damage as it reels from its horrific experience."),
        ],
    ),
    Subclass(
        name="School of Evocation", parent_class="Wizard", subclass_level=2,
        description="You focus your study on magic that creates powerful elemental effects such as bitter cold, searing flame, rolling thunder, crackling lightning, and burning acid.",
        features=[
            SubclassFeature(name="Evocation Savant", level=2, description="The gold and time you must spend to copy an evocation spell into your spellbook is halved."),
            SubclassFeature(name="Sculpt Spells", level=2, description="When you cast an evocation spell that affects other creatures that you can see, you can choose a number of them equal to 1 + the spell\'s level. The chosen creatures automatically succeed on their saving throws against the spell, and they take no damage if they would normally take half damage on a successful save."),
            SubclassFeature(name="Potent Cantrip", level=6, description="When a creature succeeds on a saving throw against your cantrip, the creature takes half the cantrip\'s damage (if any) but suffers no additional effect from the cantrip."),
            SubclassFeature(name="Empowered Evocation", level=10, description="You can add your Intelligence modifier to one damage roll of any wizard evocation spell you cast."),
            SubclassFeature(name="Overchannel", level=14, description="When you cast a wizard spell of 1st through 5th level that deals damage, you can deal maximum damage with that spell. The first time you do so, you suffer no adverse effect. If you use this feature again before you finish a long rest, you take 2d12 necrotic damage for each level of the spell, immediately after you cast it."),
        ],
    ),
]



# ===========================================================================
#  BACKGROUNDS
# ===========================================================================

BACKGROUNDS: List[Background] = [
    Background(
        name="Acolyte",
        skill_proficiencies=["Insight", "Religion"],
        tool_proficiencies=[],
        languages=2,
        equipment=["Holy symbol", "Prayer book", "5 sticks of incense", "Vestments", "Common clothes", "Belt pouch with 15 gp"],
        feature_name="Shelter of the Faithful",
        feature_description="Temples of your faith provide free healing, support, and room and board for you and your adventuring companions.",
        personality_traits=[
            "I idolize a particular hero of my faith, and constantly refer to that person\'s deeds and example.",
            "I can find common ground between the fiercest enemies, empathizing with them and always working toward peace.",
            "I see omens in every event and action. The gods try to speak to us, we just need to listen.",
            "Nothing can shake my optimistic attitude.",
            "I quote (or misquote) sacred texts and proverbs in almost every situation.",
            "I am tolerant (or intolerant) of other faiths and respect (or condemn) the worship of other gods.",
            "I\u2019ve enjoyed fine food, drink, and high society among my temple\u2019s elite. Rough living grates on me.",
            "I\u2019ve spent so long in the temple that I have little practical experience dealing with people in the outside world.",
        ],
        ideals=[
            "Tradition. The ancient traditions of worship and sacrifice must be preserved and upheld.",
            "Charity. I always try to help those in need, no matter what the personal cost.",
            "Change. We must help bring about the changes the gods are constantly working in the world.",
            "Power. I hope to one day rise to the top of my faith\u2019s religious hierarchy.",
            "Faith. I trust that my deity will guide my actions. I have faith that if I work hard, things will go well.",
            "Aspiration. I seek to prove myself worthy of my god\u2019s favor by matching my actions against his or her teachings.",
        ],
        bonds=[
            "I would die to recover an ancient relic of my faith that was lost long ago.",
            "I will someday get revenge on the corrupt temple hierarchy who branded me a heretic.",
            "I owe my life to the priest who took me in when my parents died.",
            "Everything I do is for the common people.",
            "I will do anything to protect the temple where I served.",
            "I seek to preserve a sacred text that my enemies consider heretical and seek to destroy.",
        ],
        flaws=[
            "I judge others harshly, and myself even more severely.",
            "I put too much trust in those who wield power within my temple\u2019s hierarchy.",
            "My piety sometimes leads me to blindly trust those that profess faith in my god.",
            "I am inflexible in my thinking.",
            "I am suspicious of strangers and expect the worst of them.",
            "Once I pick a goal, I become obsessed with it to the detriment of everything else in my life.",
        ],
    ),
    Background(
        name="Charlatan",
        skill_proficiencies=["Deception", "Sleight of Hand"],
        tool_proficiencies=["Disguise kit", "Forgery kit"],
        languages=0,
        equipment=["Fine clothes", "Disguise kit", "Tools of the con (ten stoppered bottles, weighted dice, deck of marked cards, signet ring of an imaginary duke)", "Belt pouch with 15 gp"],
        feature_name="False Identity",
        feature_description="You have a second identity complete with documentation and established acquaintances, allowing you to assume that persona.",
        personality_traits=[
            "I fall in and out of love easily, and am always pursuing someone.",
            "I have a joke for every occasion, especially occasions where humor is inappropriate.",
            "Flattery is my preferred trick for getting what I want.",
            "I\u2019m a born gambler who can\u2019t resist taking a risk for a potential payoff.",
            "I lie about almost everything, even when there\u2019s no good reason to.",
            "Sarcasm and insults are my weapons of choice.",
            "I keep multiple holy symbols on me and invoke whatever deity might come in useful at any given moment.",
            "I pocket anything I see that might have some value.",
        ],
        ideals=[
            "Independence. I am a free spirit\u2014no one tells me what to do.",
            "Fairness. I never target people who can\u2019t afford to lose a few coins.",
            "Charity. I distribute the money I acquire to the people who really need it.",
            "Creativity. I never run the same con twice.",
            "Friendship. Material goods come and go. Bonds of friendship last forever.",
            "Aspiration. I\u2019m determined to make something of myself.",
        ],
        bonds=[
            "I fleeced the wrong person and must work to ensure that this individual never crosses paths with me or those I care about.",
            "I owe everything to my mentor\u2014a horrible person who\u2019s probably rotting in jail somewhere.",
            "Somewhere out there, I have a child who doesn\u2019t know me. I\u2019m making the world better for him or her.",
            "I come from a noble family, and one day I\u2019ll reclaim my lands and title from those who stole them from me.",
            "A powerful person killed someone I love. Some day soon, I\u2019ll have my revenge.",
            "I swindled and ruined a person who didn\u2019t deserve it. I seek to atone for my misdeeds.",
        ],
        flaws=[
            "I can\u2019t resist a pretty face.",
            "I\u2019m always in debt. I spend my ill-gotten gains on decadent luxuries faster than I bring them in.",
            "I\u2019m convinced that no one could ever fool me the way I fool others.",
            "I\u2019m too greedy for my own good. I can\u2019t resist taking a risk if there\u2019s money involved.",
            "I can\u2019t resist swindling people who are more powerful than me.",
            "I hate to admit it and will hate myself for it, but I\u2019ll run and preserve my own hide if the going gets tough.",
        ],
    ),
    Background(
        name="Criminal",
        skill_proficiencies=["Deception", "Stealth"],
        tool_proficiencies=["One type of gaming set", "Thieves\' tools"],
        languages=0,
        equipment=["Crowbar", "Dark common clothes with a hood", "Belt pouch with 15 gp"],
        feature_name="Criminal Contact",
        feature_description="You have a reliable and trustworthy contact who acts as your liaison to a network of other criminals.",
        personality_traits=[
            "I always have a plan for what to do when things go wrong.",
            "I am always calm, no matter what the situation. I never raise my voice or let my emotions control me.",
            "The first thing I do in a new place is note the locations of everything valuable\u2014or where such things could be hidden.",
            "I would rather make a new friend than a new enemy.",
            "I am incredibly slow to trust. Those who seem the fairest often have the most to hide.",
            "I don\u2019t pay attention to the risks in a situation. Never tell me the odds.",
            "The best way to get me to do something is to tell me I can\u2019t do it.",
            "I blow up at the slightest insult.",
        ],
        ideals=[
            "Honor. I don\u2019t steal from others in the trade.",
            "Freedom. Chains are meant to be broken, as are those who would forge them.",
            "Charity. I steal from the wealthy so that I can help people in need.",
            "Greed. I will do whatever it takes to become wealthy.",
            "People. I\u2019m loyal to my friends, not to any ideals, and everyone else can take a trip down the Styx for all I care.",
            "Redemption. There\u2019s a spark of good in everyone.",
        ],
        bonds=[
            "I\u2019m trying to pay off an old debt I owe to a generous benefactor.",
            "My ill-gotten gains go to support my family.",
            "Something important was taken from me, and I aim to steal it back.",
            "I will become the greatest thief that ever lived.",
            "I\u2019m guilty of a terrible crime. I hope I can redeem myself for it.",
            "Someone I loved died because of a mistake I made. That will never happen again.",
        ],
        flaws=[
            "When I see something valuable, I can\u2019t think about anything but how to steal it.",
            "When faced with a choice between money and my friends, I usually choose the money.",
            "If there\u2019s a plan, I\u2019ll forget it. If I don\u2019t forget it, I\u2019ll ignore it.",
            "I have a \u2018tell\u2019 that reveals when I\u2019m lying.",
            "I turn tail and run when things look bad.",
            "An innocent person is in prison for a crime that I committed. I\u2019m okay with that.",
        ],
    ),
    Background(
        name="Entertainer",
        skill_proficiencies=["Acrobatics", "Performance"],
        tool_proficiencies=["Disguise kit", "One type of musical instrument"],
        languages=0,
        equipment=["Musical instrument", "The favor of an admirer", "Costume", "Belt pouch with 15 gp"],
        feature_name="By Popular Demand",
        feature_description="You can always find a place to perform, and you receive free lodging and food of a modest or comfortable standard in exchange.",
        personality_traits=[
            "I know a story relevant to almost every situation.",
            "Whenever I come to a new place, I collect local rumors and spread gossip.",
            "I\u2019m a hopeless romantic, always searching for that \u2018special someone.\u2019",
            "Nobody stays angry at me or around me for long, since I can defuse any amount of tension.",
            "I love a good insult, even one directed at me.",
            "I get bitter if I\u2019m not the center of attention.",
            "I\u2019ll settle for nothing less than perfection.",
            "I change my mood or my mind as quickly as I change key in a song.",
        ],
        ideals=[
            "Beauty. When I perform, I make the world better than it was.",
            "Tradition. The stories, legends, and songs of the past must never be forgotten, for they teach us who we are.",
            "Creativity. The world is in need of new ideas and bold action.",
            "Greed. I\u2019m only in it for the money and fame.",
            "People. I like seeing the smiles on people\u2019s faces when I perform. That\u2019s all that matters.",
            "Honesty. Art should reflect the soul; it should come from within and reveal who we really are.",
        ],
        bonds=[
            "My instrument is my most treasured possession, and it reminds me of someone I love.",
            "Someone stole my precious instrument, and someday I\u2019ll get it back.",
            "I want to be famous, whatever it takes.",
            "I idolize a hero of the old tales and measure my deeds against that person\u2019s.",
            "I will do anything to prove myself superior to my hated rival.",
            "I would do anything for the other members of my old troupe.",
        ],
        flaws=[
            "I\u2019ll do anything to win fame and renown.",
            "I\u2019m a sucker for a pretty face.",
            "A scandal prevents me from ever going home again. That kind of trouble seems to follow me around.",
            "I once satirized a noble who still wants my head. It was a mistake that I will likely repeat.",
            "I have trouble keeping my true feelings hidden. My sharp tongue lands me in trouble.",
            "Despite my best efforts, I am unreliable to my friends.",
        ],
    ),
    Background(
        name="Folk Hero",
        skill_proficiencies=["Animal Handling", "Survival"],
        tool_proficiencies=["One type of artisan\'s tools", "Vehicles (land)"],
        languages=0,
        equipment=["Artisan\'s tools", "Shovel", "Iron pot", "Common clothes", "Belt pouch with 10 gp"],
        feature_name="Rustic Hospitality",
        feature_description="Since you come from the ranks of the common folk, you fit in among them with ease. You can find a place to hide, rest, or recuperate among commoners, unless you have shown yourself to be a danger to them.",
        personality_traits=[
            "I judge people by their actions, not their words.",
            "If someone is in trouble, I\u2019m always ready to lend help.",
            "When I set my mind to something, I follow through no matter what gets in my way.",
            "I have a strong sense of fair play and always try to find the most equitable solution to arguments.",
            "I\u2019m confident in my own abilities and do what I can to instill confidence in others.",
            "Thinking is for other people. I prefer action.",
            "I misuse long words in an attempt to sound smarter.",
            "I get bored easily. When am I going to get on with my destiny?",
        ],
        ideals=[
            "Respect. People deserve to be treated with dignity and respect.",
            "Fairness. No one should get preferential treatment before the law, and no one is above the law.",
            "Freedom. Tyrants must not be allowed to oppress the people.",
            "Might. If I become strong, I can take what I want\u2014what I deserve.",
            "Sincerity. There\u2019s no good in pretending to be something I\u2019m not.",
            "Destiny. Nothing and no one can steer me away from my higher calling.",
        ],
        bonds=[
            "I have a family, but I have no idea where they are. One day, I hope to see them again.",
            "I worked the land, I love the land, and I will protect the land.",
            "A proud noble once gave me a horrible beating, and I will take my revenge on any bully I encounter.",
            "My tools are symbols of my past life, and I carry them so that I will never forget my roots.",
            "I protect those who cannot protect themselves.",
            "I wish my childhood sweetheart had come with me to pursue my destiny.",
        ],
        flaws=[
            "The tyrant who rules my land will stop at nothing to see me killed.",
            "I\u2019m convinced of the significance of my destiny, and blind to my shortcomings and the risk of failure.",
            "The people who knew me when I was young know my shameful secret, so I can never go home again.",
            "I have a weakness for the vices of the city, especially hard drink.",
            "Secretly, I believe that things would be better if I were a tyrant lording over the land.",
            "I have trouble trusting in my allies.",
        ],
    ),
    Background(
        name="Guild Artisan",
        skill_proficiencies=["Insight", "Persuasion"],
        tool_proficiencies=["One type of artisan\'s tools"],
        languages=1,
        equipment=["Artisan\'s tools", "Letter of introduction from guild", "Traveler\'s clothes", "Belt pouch with 15 gp"],
        feature_name="Guild Membership",
        feature_description="Your guild offers lodging, food, and legal support. Guild members will support you in court. You can gain an audience with local political figures through your guild.",
        personality_traits=[
            "I believe that anything worth doing is worth doing right. I can\u2019t help it\u2014I\u2019m a perfectionist.",
            "I\u2019m a snob who looks down on those who can\u2019t appreciate fine art.",
            "I always want to know how things work and what makes people tick.",
            "I\u2019m full of witty aphorisms and have a proverb for every occasion.",
            "I\u2019m rude to people who lack my commitment to hard work and fair play.",
            "I like to talk at length about my profession.",
            "I don\u2019t part with my money easily and will haggle tirelessly to get the best deal possible.",
            "I\u2019m well known for my work, and I want to make sure everyone appreciates it. I\u2019m always taken aback when people haven\u2019t heard of me.",
        ],
        ideals=[
            "Community. It is the duty of all civilized people to strengthen the bonds of community and the security of civilization.",
            "Generosity. My talents were given to me so that I could use them to benefit the world.",
            "Freedom. Everyone should be free to pursue his or her own livelihood.",
            "Greed. I\u2019m only in it for the money.",
            "People. I\u2019m committed to the people I care about, not to ideals.",
            "Aspiration. I work hard to be the best there is at my craft.",
        ],
        bonds=[
            "The workshop where I learned my trade is the most important place in the world to me.",
            "I created a great work for someone, and then found them unworthy to receive it. I\u2019m still looking for someone worthy.",
            "I owe my guild a great debt for forging me into the person I am today.",
            "I pursue wealth to secure someone\u2019s love.",
            "One day I will return to my guild and prove that I am the greatest artisan of them all.",
            "I will get revenge on the evil forces that destroyed my place of business and ruined my livelihood.",
        ],
        flaws=[
            "I\u2019ll do anything to get my hands on something rare or priceless.",
            "I\u2019m quick to assume that someone is trying to cheat me.",
            "No one must ever learn that I once stole money from my guild\u2019s coffers.",
            "I\u2019m never satisfied with what I have\u2014I always want more.",
            "I would kill to acquire a noble title.",
            "I\u2019m horribly jealous of anyone who can outshine my handiwork. Everywhere I go, I\u2019m surrounded by rivals.",
        ],
    ),
    Background(
        name="Hermit",
        skill_proficiencies=["Medicine", "Religion"],
        tool_proficiencies=["Herbalism kit"],
        languages=1,
        equipment=["Scroll case with notes", "Winter blanket", "Common clothes", "Herbalism kit", "5 gp"],
        feature_name="Discovery",
        feature_description="The quiet seclusion of your extended hermitage gave you access to a unique and powerful discovery. It might be a great truth about the cosmos, the deities, or the forces of nature.",
        personality_traits=[
            "I\u2019ve been isolated for so long that I rarely speak, preferring gestures and the occasional grunt.",
            "I am utterly serene, even in the face of disaster.",
            "The leader of my community had something wise to say on every topic, and I am eager to share that wisdom.",
            "I feel tremendous empathy for all who suffer.",
            "I\u2019m oblivious to etiquette and social expectations.",
            "I connect everything that happens to me to a grand, cosmic plan.",
            "I often get lost in my own thoughts and contemplation, becoming oblivious to my surroundings.",
            "I am working on a grand philosophical theory and love sharing my ideas.",
        ],
        ideals=[
            "Greater Good. My gifts are meant to be shared with all, not used for my own benefit.",
            "Logic. Emotions must not cloud our sense of what is right and true, or our logical thinking.",
            "Free Thinking. Inquiry and curiosity are the pillars of progress.",
            "Power. Solitude and contemplation are my paths toward mystical or magical power.",
            "Live and Let Live. Meddling in the affairs of others only causes trouble.",
            "Self-Knowledge. If you know yourself, there\u2019s nothing left to know.",
        ],
        bonds=[
            "Nothing is more important than the other members of my hermitage, order, or association.",
            "I entered seclusion to hide from the ones who might still be hunting me. I must someday confront them.",
            "I\u2019m still seeking the enlightenment I pursued in my seclusion, and it still eludes me.",
            "I entered seclusion because I loved someone I could not have.",
            "Should my discovery come to light, it could bring ruin to the world.",
            "My isolation gave me great insight into a great evil that only I can destroy.",
        ],
        flaws=[
            "Now that I\u2019ve returned to the world, I enjoy its delights a little too much.",
            "I harbor dark, bloodthirsty thoughts that my isolation and meditation failed to quell.",
            "I am dogmatic in my thoughts and philosophy.",
            "I let my need to win arguments overshadow friendships and harmony.",
            "I\u2019d risk too much to uncover a lost bit of knowledge.",
            "I like keeping secrets and won\u2019t share them with anyone.",
        ],
    ),
    Background(
        name="Noble",
        skill_proficiencies=["History", "Persuasion"],
        tool_proficiencies=["One type of gaming set"],
        languages=1,
        equipment=["Fine clothes", "Signet ring", "Scroll of pedigree", "Purse with 25 gp"],
        feature_name="Position of Privilege",
        feature_description="Thanks to your noble birth, people are inclined to think the best of you. You are welcome in high society, and common folk make every effort to accommodate you.",
        personality_traits=[
            "My eloquent flattery makes everyone I talk to feel like the most wonderful and important person in the world.",
            "The common folk love me for my kindness and generosity.",
            "No one could doubt by looking at my regal bearing that I am a cut above the unwashed masses.",
            "I take great pains to always look my best and follow the latest fashions.",
            "I don\u2019t like to get my hands dirty, and I won\u2019t be caught dead in unsuitable accommodations.",
            "Despite my noble birth, I do not place myself above other folk. We all have the same blood.",
            "My favor, once lost, is lost forever.",
            "If you do me an injury, I will crush you, ruin your name, and salt your fields.",
        ],
        ideals=[
            "Respect. Respect is due to me because of my position, but all people regardless of station deserve to be treated with dignity.",
            "Responsibility. It is my duty to respect the authority of those above me, just as those below me must respect mine.",
            "Independence. I must prove that I can handle myself without the coddling of my family.",
            "Power. If I can attain more power, no one will tell me what to do.",
            "Family. Blood runs thicker than water.",
            "Noble Obligation. It is my duty to protect and care for the people beneath me.",
        ],
        bonds=[
            "I will face any challenge to win the approval of my family.",
            "My house\u2019s alliance with another noble family must be sustained at all costs.",
            "Nothing is more important than the other members of my family.",
            "I am in love with the heir of a family that my family despises.",
            "My loyalty to my sovereign is unwavering.",
            "The common folk must see me as a hero of the people.",
        ],
        flaws=[
            "I secretly believe that everyone is beneath me.",
            "I hide a truly scandalous secret that could ruin my family forever.",
            "I too often hear veiled insults and threats in every word addressed to me, and I\u2019m quick to anger.",
            "I have an insatiable desire for carnal pleasures.",
            "In fact, the world does revolve around me.",
            "By my words and actions, I often bring shame to my family.",
        ],
    ),
    Background(
        name="Outlander",
        skill_proficiencies=["Athletics", "Survival"],
        tool_proficiencies=["One type of musical instrument"],
        languages=1,
        equipment=["Staff", "Hunting trap", "Trophy from an animal you killed", "Traveler\'s clothes", "Belt pouch with 10 gp"],
        feature_name="Wanderer",
        feature_description="You have an excellent memory for maps and geography, and you can always recall the general layout of terrain, settlements, and other features around you. In addition, you can find food and fresh water for yourself and up to five other people each day.",
        personality_traits=[
            "I\u2019m driven by a wanderlust that led me away from home.",
            "I watch over my friends as if they were a litter of newborn pups.",
            "I once ran twenty-five miles without stopping to warn my clan of an approaching orc horde. I\u2019d do it again if I had to.",
            "I have a lesson for every situation, drawn from observing nature.",
            "I place no stock in wealthy or well-mannered folk. Money and manners won\u2019t save you from a hungry owlbear.",
            "I\u2019m always picking things up, absently fiddling with them, and sometimes accidentally breaking them.",
            "I feel far more comfortable around animals than people.",
            "I was, in fact, raised by wolves.",
        ],
        ideals=[
            "Change. Life is like the seasons, in constant change, and we must change with it.",
            "Greater Good. It is each person\u2019s responsibility to make the most happiness for the whole tribe.",
            "Honor. If I dishonor myself, I dishonor my whole clan.",
            "Might. The strongest are meant to rule.",
            "Nature. The natural world is more important than all the constructs of civilization.",
            "Glory. I must earn glory in battle, for myself and my clan.",
        ],
        bonds=[
            "My family, clan, or tribe is the most important thing in my life, even when they are far from me.",
            "An injury to the unspoiled wilderness of my home is an injury to me.",
            "I will bring terrible wrath down on the evildoers who destroyed my homeland.",
            "I am the last of my tribe, and it is up to me to ensure their names enter legend.",
            "I suffer awful visions of a coming disaster and will do anything to prevent it.",
            "It is my duty to provide children to sustain my tribe.",
        ],
        flaws=[
            "I am too enamored of ale, wine, and other intoxicants.",
            "There\u2019s no room for caution in a life lived to the fullest.",
            "I remember every insult I\u2019ve received and nurse a silent resentment toward anyone who\u2019s ever wronged me.",
            "I am slow to trust members of other races, tribes, and societies.",
            "Violence is my answer to almost any challenge.",
            "Don\u2019t expect me to save those who can\u2019t save themselves. It is nature\u2019s way that the strong thrive and the weak perish.",
        ],
    ),
    Background(
        name="Sage",
        skill_proficiencies=["Arcana", "History"],
        tool_proficiencies=[],
        languages=2,
        equipment=["Bottle of black ink", "Quill", "Small knife", "Letter from a dead colleague", "Common clothes", "Belt pouch with 10 gp"],
        feature_name="Researcher",
        feature_description="When you attempt to learn or recall a piece of lore, if you do not know that information, you often know where and from whom you can obtain it.",
        personality_traits=[
            "I use polysyllabic words that convey the impression of great erudition.",
            "I\u2019ve read every book in the world\u2019s greatest libraries\u2014or I like to boast that I have.",
            "I\u2019m used to helping out those who aren\u2019t as smart as I am, and I patiently explain anything and everything to others.",
            "There\u2019s nothing I like more than a good mystery.",
            "I\u2019m willing to listen to every side of an argument before I make my own judgment.",
            "I . . . speak . . . slowly . . . when talking . . . to idiots, . . . which . . . almost . . . everyone . . . is . . . compared . . . to me.",
            "I am horribly, horribly awkward in social situations.",
            "I\u2019m convinced that people are always trying to steal my secrets.",
        ],
        ideals=[
            "Knowledge. The path to power and self-improvement is through knowledge.",
            "Beauty. What is beautiful points us beyond itself toward what is true.",
            "Logic. Emotions must not cloud our logical thinking.",
            "No Limits. Nothing should fetter the infinite possibility inherent in all existence.",
            "Power. Knowledge is the path to power and domination.",
            "Self-Improvement. The goal of a life of study is the betterment of oneself.",
        ],
        bonds=[
            "It is my duty to protect my students.",
            "I have an ancient text that holds terrible secrets that must not fall into the wrong hands.",
            "I work to preserve a library, university, scriptorium, or monastery.",
            "My life\u2019s work is a series of tomes related to a specific field of lore.",
            "I\u2019ve been searching my whole life for the answer to a certain question.",
            "I sold my soul for knowledge. I hope to do great deeds and win it back.",
        ],
        flaws=[
            "I am easily distracted by the promise of information.",
            "Most people scream and run when they see a demon. I stop and take notes on its anatomy.",
            "Unlocking an ancient mystery is worth the price of a civilization.",
            "I overlook obvious solutions in favor of complicated ones.",
            "I speak without really thinking through my words, invariably insulting others.",
            "I can\u2019t keep a secret to save my life, or anyone else\u2019s.",
        ],
    ),
    Background(
        name="Sailor",
        skill_proficiencies=["Athletics", "Perception"],
        tool_proficiencies=["Navigator\'s tools", "Vehicles (water)"],
        languages=0,
        equipment=["Belaying pin (club)", "50 feet of silk rope", "Lucky charm", "Common clothes", "Belt pouch with 10 gp"],
        feature_name="Ship\'s Passage",
        feature_description="When you need to, you can secure free passage on a sailing ship for yourself and your adventuring companions.",
        personality_traits=[
            "My friends know they can rely on me, no matter what.",
            "I work hard so that I can play hard when the work is done.",
            "I enjoy sailing into new ports and making new friends over a flagon of ale.",
            "I stretch the truth for the sake of a good story.",
            "To me, a tavern brawl is a nice way to get to know a new city.",
            "I never pass up a friendly wager.",
            "My language is as foul as an otyugh nest.",
            "I like a job well done, especially if I can convince someone else to do it.",
        ],
        ideals=[
            "Respect. The thing that keeps a ship together is mutual respect between captain and crew.",
            "Fairness. We all do the work, so we all share in the rewards.",
            "Freedom. The sea is freedom\u2014the freedom to go anywhere and do anything.",
            "Mastery. I\u2019m a predator, and the other ships on the sea are my prey.",
            "People. I\u2019m committed to my crewmates, not to ideals.",
            "Aspiration. Someday I\u2019ll own my own ship and chart my own destiny.",
        ],
        bonds=[
            "I\u2019m loyal to my captain first, everything else second.",
            "The ship is most important\u2014crewmates and captains come and go.",
            "I\u2019ll always remember my first ship.",
            "In a harbor town, I have a paramour whose eyes nearly stole me from the sea.",
            "I was cheated out of my fair share of the profits, and I want to get my due.",
            "Ruthless pirates murdered my captain and crewmates, plundered our ship, and left me to die. Vengeance will be mine.",
        ],
        flaws=[
            "I follow orders, even if I think they\u2019re wrong.",
            "I\u2019ll say anything to avoid having to do extra work.",
            "Once someone questions my courage, I never back down no matter how dangerous the situation.",
            "Once I start drinking, it\u2019s hard for me to stop.",
            "I can\u2019t help but pocket loose coins and other trinkets I come across.",
            "My pride will probably lead to my destruction.",
        ],
    ),
    Background(
        name="Soldier",
        skill_proficiencies=["Athletics", "Intimidation"],
        tool_proficiencies=["One type of gaming set", "Vehicles (land)"],
        languages=0,
        equipment=["Insignia of rank", "Trophy taken from a fallen enemy", "Set of bone dice or deck of cards", "Common clothes", "Belt pouch with 10 gp"],
        feature_name="Military Rank",
        feature_description="Soldiers loyal to your former military organization still recognize your authority and influence, and they defer to you if they are of a lower rank. You can invoke your rank to exert influence over other soldiers and requisition simple equipment or horses for temporary use.",
        personality_traits=[
            "I\u2019m always polite and respectful.",
            "I\u2019m haunted by memories of war. I can\u2019t get the images of violence out of my mind.",
            "I\u2019ve lost too many friends, and I\u2019m slow to make new ones.",
            "I\u2019m full of inspiring and cautionary tales from my military experience relevant to almost every combat situation.",
            "I can stare down a hell hound without flinching.",
            "I enjoy being strong and like breaking things.",
            "I have a crude sense of humor.",
            "I face problems head-on. A simple, direct solution is the best path to success.",
        ],
        ideals=[
            "Greater Good. Our lot is to lay down our lives in defense of others.",
            "Responsibility. I do what I must and obey just authority.",
            "Independence. When people follow orders blindly, they embrace a kind of tyranny.",
            "Might. In life as in war, the stronger force wins.",
            "Live and Let Live. Ideals aren\u2019t worth killing over or going to war for.",
            "Nation. My city, nation, or people are all that matter.",
        ],
        bonds=[
            "I would still lay down my life for the people I served with.",
            "Someone saved my life on the battlefield. To this day, I will never leave a friend behind.",
            "My honor is my life.",
            "I\u2019ll never forget the crushing defeat my company suffered or the enemies who dealt it.",
            "Those who fight beside me are those worth dying for.",
            "I fight for those who cannot fight for themselves.",
        ],
        flaws=[
            "The monstrous enemy we faced in battle still leaves me quivering with fear.",
            "I have little respect for anyone who is not a proven warrior.",
            "I made a terrible mistake in battle that cost many lives\u2014and I would do anything to keep that secret.",
            "My hatred of my enemies is blind and unreasoning.",
            "I obey the law, even if the law causes misery.",
            "I\u2019d rather eat my armor than admit when I\u2019m wrong.",
        ],
    ),
    Background(
        name="Urchin",
        skill_proficiencies=["Sleight of Hand", "Stealth"],
        tool_proficiencies=["Disguise kit", "Thieves\' tools"],
        languages=0,
        equipment=["Small knife", "Map of the city you grew up in", "Pet mouse", "Token to remember your parents by", "Common clothes", "Belt pouch with 10 gp"],
        feature_name="City Secrets",
        feature_description="You know the secret patterns and flow to cities and can find passages through the urban sprawl that others would miss. When you are not in combat, you and companions you lead can travel between any two locations in the city twice as fast as normal.",
        personality_traits=[
            "I hide scraps of food and trinkets away in my pockets.",
            "I ask a lot of questions.",
            "I like to squeeze into small places where no one else can get to me.",
            "I sleep with my back to a wall or tree, with everything I own wrapped in a bundle in my arms.",
            "I eat like a pig and have bad manners.",
            "I think anyone who\u2019s nice to me is hiding evil intent.",
            "I don\u2019t like to bathe.",
            "I bluntly say what other people are hinting at or hiding.",
        ],
        ideals=[
            "Respect. All people, rich or poor, deserve respect.",
            "Community. We have to take care of each other, because no one else is going to do it.",
            "Change. The low are lifted up, and the high and mighty are brought down. Change is the nature of things.",
            "Retribution. The rich need to be shown what life and death are like in the gutters.",
            "People. I help the people who help me\u2014that\u2019s what keeps us alive.",
            "Aspiration. I\u2019m going to prove that I\u2019m worthy of a better life.",
        ],
        bonds=[
            "My town or city is my home, and I\u2019ll fight to defend it.",
            "I sponsor an orphanage to keep others from enduring what I was forced to endure.",
            "I owe my survival to another urchin who taught me to live on the streets.",
            "I owe a debt I can never repay to the person who took pity on me.",
            "I escaped my life of poverty by robbing an important person, and I\u2019m wanted for it.",
            "No one else should have to endure the hardships I\u2019ve been through.",
        ],
        flaws=[
            "If I\u2019m outnumbered, I will run away from a fight.",
            "Gold seems like a lot of money to me, and I\u2019ll do just about anything for more of it.",
            "I will never fully trust anyone other than myself.",
            "I\u2019d rather kill someone in their sleep than fight fair.",
            "It\u2019s not stealing if I need it more than someone else.",
            "People who can\u2019t take care of themselves get what they deserve.",
        ],
    ),
]


# ===========================================================================
#  SKILLS
# ===========================================================================

SKILLS: List[Skill] = [
    Skill(name="Acrobatics", ability="DEX", description="Covers attempts to stay on your feet in tricky situations, such as acrobatic stunts, dives, rolls, and flips."),
    Skill(name="Animal Handling", ability="WIS", description="Covers calming a domesticated animal, keeping a mount from getting spooked, or intuiting an animal's intentions."),
    Skill(name="Arcana", ability="INT", description="Measures your ability to recall lore about spells, magic items, eldritch symbols, magical traditions, and the planes of existence."),
    Skill(name="Athletics", ability="STR", description="Covers difficult situations you encounter while climbing, jumping, or swimming."),
    Skill(name="Deception", ability="CHA", description="Determines whether you can convincingly hide the truth, whether through verbal or action-based deception."),
    Skill(name="History", ability="INT", description="Measures your ability to recall lore about historical events, legendary people, ancient kingdoms, past disputes, recent wars, and lost civilizations."),
    Skill(name="Insight", ability="WIS", description="Determines whether you can discern the true intentions of a creature, such as detecting a lie or predicting someone's next move."),
    Skill(name="Intimidation", ability="CHA", description="Determines your ability to influence someone through overt threats, hostile actions, and physical violence."),
    Skill(name="Investigation", ability="INT", description="Covers looking for clues and making deductions based on those clues, such as deducing the location of a hidden object or determining what kind of weapon dealt a wound."),
    Skill(name="Medicine", ability="WIS", description="Lets you try to stabilize a dying companion or diagnose an illness."),
    Skill(name="Nature", ability="INT", description="Measures your ability to recall lore about terrain, plants and animals, the weather, and natural cycles."),
    Skill(name="Perception", ability="WIS", description="Lets you spot, hear, or otherwise detect the presence of something. It measures your general awareness of your surroundings."),
    Skill(name="Performance", ability="CHA", description="Determines how well you can delight an audience with music, dance, acting, storytelling, or some other form of entertainment."),
    Skill(name="Persuasion", ability="CHA", description="Covers attempts to influence someone or a group of people with tact, social graces, or good nature."),
    Skill(name="Religion", ability="INT", description="Measures your ability to recall lore about deities, rites and prayers, religious hierarchies, holy symbols, and the practices of secret cults."),
    Skill(name="Sleight of Hand", ability="DEX", description="Covers acts of manual trickery, such as planting something on someone else or concealing an object on your person."),
    Skill(name="Stealth", ability="DEX", description="Covers attempts to conceal yourself from enemies, slink past guards, slip away without being noticed, or sneak up on someone."),
    Skill(name="Survival", ability="WIS", description="Covers following tracks, hunting wild game, guiding your group through frozen wastelands, identifying signs of nearby creatures, predicting the weather, or avoiding quicksand."),
]


# ===========================================================================
#  CLASS SKILL CHOICES
# ===========================================================================

CLASS_SKILL_CHOICES: List[ClassSkillChoices] = [
    ClassSkillChoices(class_name="Barbarian", choose=2, from_skills=["Animal Handling", "Athletics", "Intimidation", "Nature", "Perception", "Survival"]),
    ClassSkillChoices(class_name="Bard", choose=3, from_skills=["Acrobatics", "Animal Handling", "Arcana", "Athletics", "Deception", "History", "Insight", "Intimidation", "Investigation", "Medicine", "Nature", "Perception", "Performance", "Persuasion", "Religion", "Sleight of Hand", "Stealth", "Survival"]),
    ClassSkillChoices(class_name="Cleric", choose=2, from_skills=["History", "Insight", "Medicine", "Persuasion", "Religion"]),
    ClassSkillChoices(class_name="Druid", choose=2, from_skills=["Arcana", "Animal Handling", "Insight", "Medicine", "Nature", "Perception", "Religion", "Survival"]),
    ClassSkillChoices(class_name="Fighter", choose=2, from_skills=["Acrobatics", "Animal Handling", "Athletics", "History", "Insight", "Intimidation", "Perception", "Survival"]),
    ClassSkillChoices(class_name="Monk", choose=2, from_skills=["Acrobatics", "Athletics", "History", "Insight", "Religion", "Stealth"]),
    ClassSkillChoices(class_name="Paladin", choose=2, from_skills=["Athletics", "Insight", "Intimidation", "Medicine", "Persuasion", "Religion"]),
    ClassSkillChoices(class_name="Ranger", choose=3, from_skills=["Animal Handling", "Athletics", "Insight", "Investigation", "Nature", "Perception", "Stealth", "Survival"]),
    ClassSkillChoices(class_name="Rogue", choose=4, from_skills=["Acrobatics", "Athletics", "Deception", "Insight", "Intimidation", "Investigation", "Perception", "Performance", "Persuasion", "Sleight of Hand", "Stealth"]),
    ClassSkillChoices(class_name="Sorcerer", choose=2, from_skills=["Arcana", "Deception", "Insight", "Intimidation", "Persuasion", "Religion"]),
    ClassSkillChoices(class_name="Warlock", choose=2, from_skills=["Arcana", "Deception", "History", "Intimidation", "Investigation", "Nature", "Religion"]),
    ClassSkillChoices(class_name="Wizard", choose=2, from_skills=["Arcana", "History", "Insight", "Investigation", "Medicine", "Religion"]),
]


# ===========================================================================
#  STARTING EQUIPMENT
# ===========================================================================

STARTING_EQUIPMENT: List[ClassStartingEquipment] = [
    ClassStartingEquipment(
        class_name="Barbarian",
        choices=[
            [EquipmentChoice(items=["Greataxe"]), EquipmentChoice(items=["Any martial melee weapon"])],
            [EquipmentChoice(items=["Two handaxes"]), EquipmentChoice(items=["Any simple weapon"])],
        ],
        guaranteed=["Explorer's pack", "Four javelins"],
    ),
    ClassStartingEquipment(
        class_name="Bard",
        choices=[
            [EquipmentChoice(items=["Rapier"]), EquipmentChoice(items=["Longsword"]), EquipmentChoice(items=["Any simple weapon"])],
            [EquipmentChoice(items=["Diplomat's pack"]), EquipmentChoice(items=["Entertainer's pack"])],
            [EquipmentChoice(items=["Lute"]), EquipmentChoice(items=["Any musical instrument"])],
        ],
        guaranteed=["Leather armor", "Dagger"],
    ),
    ClassStartingEquipment(
        class_name="Cleric",
        choices=[
            [EquipmentChoice(items=["Mace"]), EquipmentChoice(items=["Warhammer (if proficient)"])],
            [EquipmentChoice(items=["Scale mail"]), EquipmentChoice(items=["Leather armor"]), EquipmentChoice(items=["Chain mail (if proficient)"])],
            [EquipmentChoice(items=["Light crossbow and 20 bolts"]), EquipmentChoice(items=["Any simple weapon"])],
            [EquipmentChoice(items=["Priest's pack"]), EquipmentChoice(items=["Explorer's pack"])],
        ],
        guaranteed=["Shield", "Holy symbol"],
    ),
    ClassStartingEquipment(
        class_name="Druid",
        choices=[
            [EquipmentChoice(items=["Wooden shield"]), EquipmentChoice(items=["Any simple weapon"])],
            [EquipmentChoice(items=["Scimitar"]), EquipmentChoice(items=["Any simple melee weapon"])],
        ],
        guaranteed=["Leather armor", "Explorer's pack", "Druidic focus"],
    ),
    ClassStartingEquipment(
        class_name="Fighter",
        choices=[
            [EquipmentChoice(items=["Chain mail"]), EquipmentChoice(items=["Leather armor", "Longbow", "20 arrows"])],
            [EquipmentChoice(items=["A martial weapon and a shield"]), EquipmentChoice(items=["Two martial weapons"])],
            [EquipmentChoice(items=["Light crossbow and 20 bolts"]), EquipmentChoice(items=["Two handaxes"])],
            [EquipmentChoice(items=["Dungeoneer's pack"]), EquipmentChoice(items=["Explorer's pack"])],
        ],
        guaranteed=[],
    ),
    ClassStartingEquipment(
        class_name="Monk",
        choices=[
            [EquipmentChoice(items=["Shortsword"]), EquipmentChoice(items=["Any simple weapon"])],
            [EquipmentChoice(items=["Dungeoneer's pack"]), EquipmentChoice(items=["Explorer's pack"])],
        ],
        guaranteed=["10 darts"],
    ),
    ClassStartingEquipment(
        class_name="Paladin",
        choices=[
            [EquipmentChoice(items=["A martial weapon and a shield"]), EquipmentChoice(items=["Two martial weapons"])],
            [EquipmentChoice(items=["Five javelins"]), EquipmentChoice(items=["Any simple melee weapon"])],
            [EquipmentChoice(items=["Priest's pack"]), EquipmentChoice(items=["Explorer's pack"])],
        ],
        guaranteed=["Chain mail", "Holy symbol"],
    ),
    ClassStartingEquipment(
        class_name="Ranger",
        choices=[
            [EquipmentChoice(items=["Scale mail"]), EquipmentChoice(items=["Leather armor"])],
            [EquipmentChoice(items=["Two shortswords"]), EquipmentChoice(items=["Two simple melee weapons"])],
            [EquipmentChoice(items=["Dungeoneer's pack"]), EquipmentChoice(items=["Explorer's pack"])],
        ],
        guaranteed=["Longbow", "Quiver of 20 arrows"],
    ),
    ClassStartingEquipment(
        class_name="Rogue",
        choices=[
            [EquipmentChoice(items=["Rapier"]), EquipmentChoice(items=["Shortsword"])],
            [EquipmentChoice(items=["Shortbow and quiver of 20 arrows"]), EquipmentChoice(items=["Shortsword"])],
            [EquipmentChoice(items=["Burglar's pack"]), EquipmentChoice(items=["Dungeoneer's pack"]), EquipmentChoice(items=["Explorer's pack"])],
        ],
        guaranteed=["Leather armor", "Two daggers", "Thieves' tools"],
    ),
    ClassStartingEquipment(
        class_name="Sorcerer",
        choices=[
            [EquipmentChoice(items=["Light crossbow and 20 bolts"]), EquipmentChoice(items=["Any simple weapon"])],
            [EquipmentChoice(items=["Component pouch"]), EquipmentChoice(items=["Arcane focus"])],
            [EquipmentChoice(items=["Dungeoneer's pack"]), EquipmentChoice(items=["Explorer's pack"])],
        ],
        guaranteed=["Two daggers"],
    ),
    ClassStartingEquipment(
        class_name="Warlock",
        choices=[
            [EquipmentChoice(items=["Light crossbow and 20 bolts"]), EquipmentChoice(items=["Any simple weapon"])],
            [EquipmentChoice(items=["Component pouch"]), EquipmentChoice(items=["Arcane focus"])],
            [EquipmentChoice(items=["Scholar's pack"]), EquipmentChoice(items=["Dungeoneer's pack"])],
        ],
        guaranteed=["Leather armor", "Any simple weapon", "Two daggers"],
    ),
    ClassStartingEquipment(
        class_name="Wizard",
        choices=[
            [EquipmentChoice(items=["Quarterstaff"]), EquipmentChoice(items=["Dagger"])],
            [EquipmentChoice(items=["Component pouch"]), EquipmentChoice(items=["Arcane focus"])],
            [EquipmentChoice(items=["Scholar's pack"]), EquipmentChoice(items=["Explorer's pack"])],
        ],
        guaranteed=["Spellbook"],
    ),
]


# ===========================================================================
#  ALIGNMENTS
# ===========================================================================

ALIGNMENTS: List[Dict[str, str]] = [
    {"abbreviation": "LG", "name": "Lawful Good"},
    {"abbreviation": "NG", "name": "Neutral Good"},
    {"abbreviation": "CG", "name": "Chaotic Good"},
    {"abbreviation": "LN", "name": "Lawful Neutral"},
    {"abbreviation": "N", "name": "True Neutral"},
    {"abbreviation": "CN", "name": "Chaotic Neutral"},
    {"abbreviation": "LE", "name": "Lawful Evil"},
    {"abbreviation": "NE", "name": "Neutral Evil"},
    {"abbreviation": "CE", "name": "Chaotic Evil"},
]


# ===========================================================================
#  LANGUAGES
# ===========================================================================

LANGUAGES: List[Language] = [
    # Standard
    Language(name="Common", type="Standard", typical_speakers="Humans"),
    Language(name="Dwarvish", type="Standard", typical_speakers="Dwarves"),
    Language(name="Elvish", type="Standard", typical_speakers="Elves"),
    Language(name="Giant", type="Standard", typical_speakers="Ogres, Giants"),
    Language(name="Gnomish", type="Standard", typical_speakers="Gnomes"),
    Language(name="Goblin", type="Standard", typical_speakers="Goblinoids"),
    Language(name="Halfling", type="Standard", typical_speakers="Halflings"),
    Language(name="Orc", type="Standard", typical_speakers="Orcs"),
    # Exotic
    Language(name="Abyssal", type="Exotic", typical_speakers="Demons"),
    Language(name="Celestial", type="Exotic", typical_speakers="Celestials"),
    Language(name="Draconic", type="Exotic", typical_speakers="Dragons, Dragonborn"),
    Language(name="Deep Speech", type="Exotic", typical_speakers="Aboleths, Cloakers"),
    Language(name="Infernal", type="Exotic", typical_speakers="Devils"),
    Language(name="Primordial", type="Exotic", typical_speakers="Elementals"),
    Language(name="Sylvan", type="Exotic", typical_speakers="Fey creatures"),
    Language(name="Undercommon", type="Exotic", typical_speakers="Underdark traders"),
]


# ===========================================================================
#  ABILITY SCORE METHODS
# ===========================================================================

POINT_BUY_COSTS: Dict[int, int] = {
    8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9,
}

POINT_BUY_TOTAL: int = 27

STANDARD_ARRAY: List[int] = [15, 14, 13, 12, 10, 8]


# ===========================================================================
#  HIT DICE BY CLASS
# ===========================================================================

HIT_DICE_BY_CLASS: Dict[str, int] = {
    "Barbarian": 12,
    "Bard": 8,
    "Cleric": 8,
    "Druid": 8,
    "Fighter": 10,
    "Monk": 8,
    "Paladin": 10,
    "Ranger": 10,
    "Rogue": 8,
    "Sorcerer": 6,
    "Warlock": 8,
    "Wizard": 6,
}


# ===========================================================================
#  SPELLCASTING CLASSES
# ===========================================================================

SPELLCASTING_CLASSES: List[SpellcastingInfo] = [
    SpellcastingInfo(class_name="Bard", ability="CHA", type="full", cantrips_known=2, learn_style="known"),
    SpellcastingInfo(class_name="Cleric", ability="WIS", type="full", cantrips_known=3, learn_style="prepared"),
    SpellcastingInfo(class_name="Druid", ability="WIS", type="full", cantrips_known=2, learn_style="prepared"),
    SpellcastingInfo(class_name="Paladin", ability="CHA", type="half", cantrips_known=None, learn_style="prepared"),
    SpellcastingInfo(class_name="Ranger", ability="WIS", type="half", cantrips_known=None, learn_style="known"),
    SpellcastingInfo(class_name="Sorcerer", ability="CHA", type="full", cantrips_known=4, learn_style="known"),
    SpellcastingInfo(class_name="Warlock", ability="CHA", type="pact", cantrips_known=2, learn_style="known"),
    SpellcastingInfo(class_name="Wizard", ability="INT", type="full", cantrips_known=3, learn_style="prepared"),
    SpellcastingInfo(class_name="Fighter", ability="INT", type="third", cantrips_known=2, learn_style="known"),
    SpellcastingInfo(class_name="Rogue", ability="INT", type="third", cantrips_known=3, learn_style="known"),
]


# ===========================================================================
#  ABILITY SCORES
# ===========================================================================

ABILITY_SCORES: List[str] = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
