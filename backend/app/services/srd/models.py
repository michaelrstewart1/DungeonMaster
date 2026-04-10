"""
Pydantic models for D&D 5e SRD data types.
"""
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class SRDSpell(BaseModel):
    """Model for a D&D 5e spell."""

    name: str = Field(..., description="Spell name")
    level: int = Field(..., ge=0, le=9, description="Spell level (0-9)")
    school: str = Field(
        ...,
        description="School of magic (Abjuration, Conjuration, Divination, "
        "Enchantment, Evocation, Illusion, Necromancy, Transmutation)",
    )
    casting_time: str = Field(..., description="How long it takes to cast the spell")
    range: str = Field(..., description="Range of the spell")
    components: List[str] = Field(..., description="Components (V, S, M)")
    duration: str = Field(..., description="How long the spell lasts")
    description: str = Field(..., description="Full spell description")
    classes: List[str] = Field(..., description="Classes that can learn this spell")


class SRDMonster(BaseModel):
    """Model for a D&D 5e monster."""

    name: str = Field(..., description="Monster name")
    size: str = Field(..., description="Size (Tiny, Small, Medium, Large, Huge, Gargantuan)")
    type: str = Field(..., description="Type (Humanoid, Beast, etc.)")
    alignment: str = Field(..., description="Alignment")
    ac: int = Field(..., ge=1, description="Armor class")
    hp: int = Field(..., gt=0, description="Hit points")
    speed: str = Field(..., description="Movement speed")
    strength: int = Field(..., ge=1, description="Strength ability score")
    dexterity: int = Field(..., ge=1, description="Dexterity ability score")
    constitution: int = Field(..., ge=1, description="Constitution ability score")
    intelligence: int = Field(..., ge=1, description="Intelligence ability score")
    wisdom: int = Field(..., ge=1, description="Wisdom ability score")
    charisma: int = Field(..., ge=1, description="Charisma ability score")
    challenge_rating: float = Field(..., ge=0, description="Challenge rating")
    actions: str = Field(..., description="Available actions")


class SRDEquipment(BaseModel):
    """Model for D&D 5e equipment."""

    name: str = Field(..., description="Equipment name")
    category: str = Field(..., description="Equipment category")
    cost: str = Field(..., description="Cost in gold pieces")
    weight: float = Field(..., ge=0, description="Weight in pounds")
    properties: Optional[str] = Field(None, description="Special properties")


class SRDClass(BaseModel):
    """Model for a D&D 5e class."""

    name: str = Field(..., description="Class name")
    hit_die: int = Field(..., description="Hit die (d6, d8, d10, d12)")
    primary_ability: str = Field(..., description="Primary ability")
    saving_throws: List[str] = Field(..., description="Saving throw proficiencies")
    proficiencies: List[str] = Field(..., description="Skill proficiencies")


class SRDRace(BaseModel):
    """Model for a D&D 5e race."""

    name: str = Field(..., description="Race name")
    speed: int = Field(..., ge=0, description="Base movement speed in feet")
    size: str = Field(..., description="Size (Tiny, Small, Medium, Large)")
    ability_bonuses: Dict[str, int] = Field(..., description="Ability score bonuses")
    traits: List[str] = Field(..., description="Racial traits")
