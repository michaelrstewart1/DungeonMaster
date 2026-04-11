"""
Pydantic schemas for D&D 5e data models.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from math import ceil
from pydantic import BaseModel, Field, field_validator

from app.models.enums import Race, CharacterClass, GamePhase, TerrainType, Condition


# ============================================================================
# Character Models
# ============================================================================

class CharacterCreate(BaseModel):
    """Schema for creating a new character."""
    name: str = Field(..., min_length=1, description="Character name")
    race: str = Field(..., description="Character race")
    class_name: str = Field(..., description="Character class")
    level: int = Field(..., ge=1, le=20, description="Character level (1-20)")
    campaign_id: Optional[str] = Field(None, description="Campaign to add this character to")
    
    # Ability scores
    strength: int = Field(default=10, ge=3, le=20, description="Strength ability score")
    dexterity: int = Field(default=10, ge=3, le=20, description="Dexterity ability score")
    constitution: int = Field(default=10, ge=3, le=20, description="Constitution ability score")
    intelligence: int = Field(default=10, ge=3, le=20, description="Intelligence ability score")
    wisdom: int = Field(default=10, ge=3, le=20, description="Wisdom ability score")
    charisma: int = Field(default=10, ge=3, le=20, description="Charisma ability score")
    
    # Other attributes
    hp: int = Field(default=8, gt=0, description="Hit points (must be positive)")
    ac: int = Field(default=10, ge=1, description="Armor class (minimum 1)")
    
    # Collections
    conditions: List[str] = Field(default_factory=list, description="Active conditions")
    inventory: List[str] = Field(default_factory=list, description="Inventory items")

    @field_validator("race", mode="before")
    @classmethod
    def validate_race(cls, v):
        """Validate that race is a valid SRD race."""
        valid_races = {r.value for r in Race}
        if v not in valid_races:
            raise ValueError(f"Invalid race. Must be one of: {', '.join(valid_races)}")
        return v

    @field_validator("class_name", mode="before")
    @classmethod
    def validate_class(cls, v):
        """Validate that class is a valid SRD class."""
        valid_classes = {c.value for c in CharacterClass}
        if v not in valid_classes:
            raise ValueError(f"Invalid class. Must be one of: {', '.join(valid_classes)}")
        return v

    @property
    def strength_mod(self) -> int:
        """Calculate strength modifier."""
        return (self.strength - 10) // 2

    @property
    def dexterity_mod(self) -> int:
        """Calculate dexterity modifier."""
        return (self.dexterity - 10) // 2

    @property
    def constitution_mod(self) -> int:
        """Calculate constitution modifier."""
        return (self.constitution - 10) // 2

    @property
    def intelligence_mod(self) -> int:
        """Calculate intelligence modifier."""
        return (self.intelligence - 10) // 2

    @property
    def wisdom_mod(self) -> int:
        """Calculate wisdom modifier."""
        return (self.wisdom - 10) // 2

    @property
    def charisma_mod(self) -> int:
        """Calculate charisma modifier."""
        return (self.charisma - 10) // 2

    @property
    def proficiency_bonus(self) -> int:
        """Calculate proficiency bonus from level: ceil(level/4) + 1."""
        return ceil(self.level / 4) + 1


class CharacterResponse(CharacterCreate):
    """Schema for character responses (includes ID)."""
    id: str = Field(..., description="Character unique identifier")


class CharacterUpdate(BaseModel):
    """Schema for updating an existing character."""
    name: Optional[str] = Field(None, min_length=1)
    level: Optional[int] = Field(None, ge=1, le=20)
    strength: Optional[int] = Field(None, ge=3, le=20)
    dexterity: Optional[int] = Field(None, ge=3, le=20)
    constitution: Optional[int] = Field(None, ge=3, le=20)
    intelligence: Optional[int] = Field(None, ge=3, le=20)
    wisdom: Optional[int] = Field(None, ge=3, le=20)
    charisma: Optional[int] = Field(None, ge=3, le=20)
    hp: Optional[int] = Field(None, gt=0)
    ac: Optional[int] = Field(None, ge=1)
    conditions: Optional[List[str]] = None
    inventory: Optional[List[str]] = None


# ============================================================================
# Campaign Models
# ============================================================================

class CampaignCreate(BaseModel):
    """Schema for creating a new campaign."""
    name: str = Field(..., min_length=1, description="Campaign name")
    description: str = Field(..., description="Campaign description")
    character_ids: List[str] = Field(default_factory=list, description="List of character IDs in campaign")
    world_state: Dict[str, Any] = Field(default_factory=dict, description="Campaign world state")
    dm_settings: Dict[str, Any] = Field(default_factory=dict, description="Dungeon Master settings")


class CampaignResponse(CampaignCreate):
    """Schema for campaign responses (includes ID and timestamps)."""
    id: str = Field(..., description="Campaign unique identifier")
    created_at: datetime = Field(..., description="Campaign creation timestamp")
    updated_at: datetime = Field(..., description="Campaign last update timestamp")


# ============================================================================
# GameState Models
# ============================================================================

class CombatState(BaseModel):
    """Combat state tracking during combat phase."""
    initiative_order: List[str] = Field(..., description="Order of combatants in initiative")
    current_turn_index: int = Field(..., ge=0, description="Current turn index in initiative order")
    round_number: int = Field(..., ge=1, description="Current combat round number")


class GameStateResponse(BaseModel):
    """Schema for game state responses."""
    id: str = Field(..., description="GameState unique identifier")
    campaign_id: str = Field(..., description="Associated campaign ID")
    current_phase: str = Field(..., description="Current game phase")
    narrative_history: List[str] = Field(..., description="History of narration")
    current_scene: str = Field(..., description="Description of current scene")
    combat_state: Optional[CombatState] = Field(None, description="Combat state (if in combat)")
    active_effects: List[Dict[str, Any]] = Field(default_factory=list, description="Active effects/spells")

    @field_validator("current_phase", mode="before")
    @classmethod
    def validate_phase(cls, v):
        """Validate that phase is a valid GamePhase."""
        valid_phases = {p.value for p in GamePhase}
        if v not in valid_phases:
            raise ValueError(f"Invalid phase. Must be one of: {', '.join(valid_phases)}")
        return v


# ============================================================================
# Map Models
# ============================================================================

class TokenPosition(BaseModel):
    """Position of a token on the map."""
    entity_id: str = Field(..., description="Entity ID (character or NPC)")
    x: int = Field(..., ge=0, description="X coordinate")
    y: int = Field(..., ge=0, description="Y coordinate")


class CharacterImportRequest(BaseModel):
    """Schema for importing a character from external formats."""
    format: str = Field(..., description="Import format: 'r20' or 'generic'")
    data: Dict[str, Any] = Field(..., description="Character data in the specified format")

    @field_validator("format", mode="before")
    @classmethod
    def validate_format(cls, v):
        """Validate that format is supported."""
        valid_formats = {"r20", "generic"}
        if v not in valid_formats:
            raise ValueError(f"Invalid format '{v}'. Must be one of: {', '.join(valid_formats)}")
        return v


# ============================================================================
# Map Models
# ============================================================================

class MapCreate(BaseModel):
    """Schema for creating a new map."""
    width: int = Field(..., gt=0, description="Map width in tiles")
    height: int = Field(..., gt=0, description="Map height in tiles")
    terrain_grid: List[List[str]] = Field(default_factory=list, description="2D grid of terrain types")
    token_positions: List[TokenPosition] = Field(default_factory=list, description="Token positions on map")
    fog_of_war: List[List[bool]] = Field(default_factory=list, description="Fog of war visibility grid")

    @field_validator("terrain_grid")
    @classmethod
    def validate_terrain_grid(cls, v, info):
        """Validate terrain grid dimensions and terrain types."""
        if not v:
            return v
        
        # Validate terrain types
        valid_terrains = {t.value for t in TerrainType}
        for row in v:
            for terrain in row:
                if terrain not in valid_terrains:
                    raise ValueError(f"Invalid terrain type '{terrain}'. Must be one of: {', '.join(valid_terrains)}")
        
        return v

    @field_validator("token_positions")
    @classmethod
    def validate_token_positions(cls, v, info):
        """Validate that token positions are within grid bounds."""
        if info.data.get("width") is None or info.data.get("height") is None:
            return v
        
        width = info.data["width"]
        height = info.data["height"]
        
        for token in v:
            if token.x >= width:
                raise ValueError(f"Token x position {token.x} is out of bounds (width: {width})")
            if token.y >= height:
                raise ValueError(f"Token y position {token.y} is out of bounds (height: {height})")
        
        return v


class MapResponse(MapCreate):
    """Schema for map responses (includes ID)."""
    id: str = Field(..., description="Map unique identifier")
