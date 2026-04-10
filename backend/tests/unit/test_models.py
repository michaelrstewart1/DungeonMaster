"""
Comprehensive tests for D&D 5e Pydantic data models.
Written FIRST in TDD approach.
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from app.models.schemas import (
    CharacterCreate,
    CharacterResponse,
    CharacterUpdate,
    CampaignCreate,
    CampaignResponse,
    GameStateResponse,
    CombatState,
    MapCreate,
    MapResponse,
    TokenPosition,
)
from app.models.enums import Race, CharacterClass, GamePhase, TerrainType, Condition


class TestCharacterModel:
    """Test suite for Character model."""

    def test_create_character_with_required_fields(self):
        """Test creating a character with all required fields."""
        character = CharacterCreate(
            name="Aragorn",
            race="human",
            class_name="fighter",
            level=5,
        )
        assert character.name == "Aragorn"
        assert character.race == "human"
        assert character.class_name == "fighter"
        assert character.level == 5

    def test_ability_scores_default_to_10(self):
        """Test that ability scores default to 10."""
        character = CharacterCreate(
            name="Test",
            race="elf",
            class_name="wizard",
            level=1,
        )
        assert character.strength == 10
        assert character.dexterity == 10
        assert character.constitution == 10
        assert character.intelligence == 10
        assert character.wisdom == 10
        assert character.charisma == 10

    def test_ability_score_modifiers(self):
        """Test ability modifier calculation: (score - 10) // 2."""
        character = CharacterCreate(
            name="Strong",
            race="human",
            class_name="barbarian",
            level=3,
            strength=16,
            dexterity=8,
            constitution=14,
            intelligence=9,
            wisdom=13,
            charisma=11,
        )
        assert character.strength_mod == 3  # (16 - 10) // 2 = 3
        assert character.dexterity_mod == -1  # (8 - 10) // 2 = -1
        assert character.constitution_mod == 2  # (14 - 10) // 2 = 2
        assert character.intelligence_mod == -1  # (9 - 10) // 2 = -1
        assert character.wisdom_mod == 1  # (13 - 10) // 2 = 1
        assert character.charisma_mod == 0  # (11 - 10) // 2 = 0

    def test_hp_must_be_positive(self):
        """Test that HP must be a positive integer."""
        with pytest.raises(ValidationError):
            CharacterCreate(
                name="Test",
                race="human",
                class_name="rogue",
                level=1,
                hp=0,  # Invalid: must be positive
            )

        with pytest.raises(ValidationError):
            CharacterCreate(
                name="Test",
                race="human",
                class_name="rogue",
                level=1,
                hp=-5,  # Invalid: must be positive
            )

    def test_ac_minimum_is_1(self):
        """Test that AC has a minimum of 1."""
        with pytest.raises(ValidationError):
            CharacterCreate(
                name="Test",
                race="human",
                class_name="rogue",
                level=1,
                ac=0,  # Invalid: minimum is 1
            )

    def test_level_must_be_1_to_20(self):
        """Test that level must be between 1 and 20."""
        # Valid levels
        for level in [1, 10, 20]:
            character = CharacterCreate(
                name="Test",
                race="human",
                class_name="fighter",
                level=level,
            )
            assert character.level == level

        # Invalid levels
        with pytest.raises(ValidationError):
            CharacterCreate(
                name="Test",
                race="human",
                class_name="fighter",
                level=0,
            )

        with pytest.raises(ValidationError):
            CharacterCreate(
                name="Test",
                race="human",
                class_name="fighter",
                level=21,
            )

    def test_proficiency_bonus_calculation(self):
        """Test proficiency bonus calculated from level: ceil(level/4) + 1."""
        test_cases = [
            (1, 2),  # ceil(1/4) + 1 = 2
            (4, 2),  # ceil(4/4) + 1 = 2
            (5, 3),  # ceil(5/4) + 1 = 3
            (8, 3),  # ceil(8/4) + 1 = 3
            (9, 4),  # ceil(9/4) + 1 = 4
            (12, 4),  # ceil(12/4) + 1 = 4
            (13, 5),  # ceil(13/4) + 1 = 5
            (16, 5),  # ceil(16/4) + 1 = 5
            (17, 6),  # ceil(17/4) + 1 = 6
            (20, 6),  # ceil(20/4) + 1 = 6
        ]
        for level, expected_bonus in test_cases:
            character = CharacterCreate(
                name="Test",
                race="human",
                class_name="fighter",
                level=level,
            )
            assert character.proficiency_bonus == expected_bonus

    def test_valid_races(self):
        """Test that only valid SRD races are accepted."""
        valid_races = ["human", "elf", "dwarf", "halfling", "gnome", "half-elf", "half-orc", "tiefling", "dragonborn"]
        
        for race in valid_races:
            character = CharacterCreate(
                name="Test",
                race=race,
                class_name="fighter",
                level=1,
            )
            assert character.race == race

        # Invalid race
        with pytest.raises(ValidationError):
            CharacterCreate(
                name="Test",
                race="invalid_race",
                class_name="fighter",
                level=1,
            )

    def test_valid_classes(self):
        """Test that only valid SRD classes are accepted."""
        valid_classes = ["barbarian", "bard", "cleric", "druid", "fighter", "monk", "paladin", "ranger", "rogue", "sorcerer", "warlock", "wizard"]
        
        for class_name in valid_classes:
            character = CharacterCreate(
                name="Test",
                race="human",
                class_name=class_name,
                level=1,
            )
            assert character.class_name == class_name

        # Invalid class
        with pytest.raises(ValidationError):
            CharacterCreate(
                name="Test",
                race="human",
                class_name="invalid_class",
                level=1,
            )

    def test_conditions_default_to_empty_list(self):
        """Test that conditions default to empty list."""
        character = CharacterCreate(
            name="Test",
            race="human",
            class_name="fighter",
            level=1,
        )
        assert character.conditions == []

    def test_inventory_default_to_empty_list(self):
        """Test that inventory defaults to empty list."""
        character = CharacterCreate(
            name="Test",
            race="human",
            class_name="fighter",
            level=1,
        )
        assert character.inventory == []

    def test_character_serialization(self):
        """Test that character can be serialized to dict and JSON."""
        character = CharacterCreate(
            name="Legolas",
            race="elf",
            class_name="ranger",
            level=10,
            strength=14,
            dexterity=18,
            wisdom=15,
        )
        
        # Serialize to dict
        char_dict = character.model_dump()
        assert isinstance(char_dict, dict)
        assert char_dict["name"] == "Legolas"
        assert char_dict["race"] == "elf"
        
        # Serialize to JSON
        json_str = character.model_dump_json()
        assert isinstance(json_str, str)
        assert "Legolas" in json_str
        assert "elf" in json_str

    def test_character_response_includes_id(self):
        """Test that CharacterResponse includes an ID."""
        char_response = CharacterResponse(
            id="char-001",
            name="Test",
            race="human",
            class_name="fighter",
            level=1,
            strength=10,
            dexterity=10,
            constitution=10,
            intelligence=10,
            wisdom=10,
            charisma=10,
            hp=12,
            ac=10,
            conditions=[],
            inventory=[],
        )
        assert char_response.id == "char-001"


class TestCampaignModel:
    """Test suite for Campaign model."""

    def test_create_campaign_with_required_fields(self):
        """Test creating a campaign with name and description."""
        campaign = CampaignCreate(
            name="Lost Mines of Phandelver",
            description="A classic adventure module",
        )
        assert campaign.name == "Lost Mines of Phandelver"
        assert campaign.description == "A classic adventure module"

    def test_campaign_has_character_ids_list(self):
        """Test that campaign has a list of character IDs."""
        campaign = CampaignCreate(
            name="Test",
            description="Test campaign",
            character_ids=["char-001", "char-002", "char-003"],
        )
        assert campaign.character_ids == ["char-001", "char-002", "char-003"]

    def test_campaign_character_ids_default_empty(self):
        """Test that character_ids defaults to empty list."""
        campaign = CampaignCreate(
            name="Test",
            description="Test campaign",
        )
        assert campaign.character_ids == []

    def test_campaign_has_world_state(self):
        """Test that campaign has world_state dict."""
        campaign = CampaignCreate(
            name="Test",
            description="Test campaign",
            world_state={"level": "5", "time": "afternoon"},
        )
        assert campaign.world_state == {"level": "5", "time": "afternoon"}

    def test_campaign_world_state_default_empty(self):
        """Test that world_state defaults to empty dict."""
        campaign = CampaignCreate(
            name="Test",
            description="Test campaign",
        )
        assert campaign.world_state == {}

    def test_campaign_has_dm_settings(self):
        """Test that campaign has DM settings."""
        campaign = CampaignCreate(
            name="Test",
            description="Test campaign",
            dm_settings={
                "llm_provider": "openai",
                "voice_enabled": True,
                "difficulty": "hard",
            },
        )
        assert campaign.dm_settings["llm_provider"] == "openai"
        assert campaign.dm_settings["voice_enabled"] is True

    def test_campaign_dm_settings_default_empty(self):
        """Test that dm_settings defaults to empty dict."""
        campaign = CampaignCreate(
            name="Test",
            description="Test campaign",
        )
        assert campaign.dm_settings == {}

    def test_campaign_name_must_be_non_empty(self):
        """Test that campaign name must be non-empty string."""
        with pytest.raises(ValidationError):
            CampaignCreate(
                name="",
                description="Test",
            )

    def test_campaign_response_has_timestamps(self):
        """Test that CampaignResponse includes created_at and updated_at timestamps."""
        now = datetime.utcnow()
        campaign = CampaignResponse(
            id="camp-001",
            name="Test",
            description="Test campaign",
            character_ids=[],
            world_state={},
            dm_settings={},
            created_at=now,
            updated_at=now,
        )
        assert campaign.created_at == now
        assert campaign.updated_at == now
        assert campaign.id == "camp-001"


class TestGameStateModel:
    """Test suite for GameState model."""

    def test_game_state_has_phase_enum(self):
        """Test that GameState has current_phase with valid enum values."""
        for phase in ["lobby", "exploration", "combat", "rest", "shopping"]:
            game_state = GameStateResponse(
                id="gs-001",
                campaign_id="camp-001",
                current_phase=phase,
                narrative_history=[],
                current_scene="",
                combat_state=None,
                active_effects=[],
            )
            assert game_state.current_phase == phase

    def test_game_state_invalid_phase(self):
        """Test that invalid phase raises validation error."""
        with pytest.raises(ValidationError):
            GameStateResponse(
                id="gs-001",
                campaign_id="camp-001",
                current_phase="invalid_phase",
                narrative_history=[],
                current_scene="",
                combat_state=None,
                active_effects=[],
            )

    def test_game_state_narrative_history(self):
        """Test that GameState has narrative_history list."""
        history = [
            "The party enters the tavern.",
            "A hooded figure approaches them.",
            "The figure offers a quest.",
        ]
        game_state = GameStateResponse(
            id="gs-001",
            campaign_id="camp-001",
            current_phase="exploration",
            narrative_history=history,
            current_scene="",
            combat_state=None,
            active_effects=[],
        )
        assert game_state.narrative_history == history

    def test_game_state_current_scene(self):
        """Test that GameState has current_scene description."""
        scene = "A dimly lit tavern filled with adventurers."
        game_state = GameStateResponse(
            id="gs-001",
            campaign_id="camp-001",
            current_phase="exploration",
            narrative_history=[],
            current_scene=scene,
            combat_state=None,
            active_effects=[],
        )
        assert game_state.current_scene == scene

    def test_combat_state_structure(self):
        """Test CombatState structure with initiative and turn tracking."""
        combat_state = CombatState(
            initiative_order=["char-001", "enemy-001", "char-002"],
            current_turn_index=1,
            round_number=3,
        )
        assert combat_state.initiative_order == ["char-001", "enemy-001", "char-002"]
        assert combat_state.current_turn_index == 1
        assert combat_state.round_number == 3

    def test_game_state_with_combat_state(self):
        """Test GameState with combat state during combat phase."""
        combat_state = CombatState(
            initiative_order=["char-001", "enemy-001"],
            current_turn_index=0,
            round_number=1,
        )
        game_state = GameStateResponse(
            id="gs-001",
            campaign_id="camp-001",
            current_phase="combat",
            narrative_history=[],
            current_scene="Combat engaged!",
            combat_state=combat_state,
            active_effects=[],
        )
        assert game_state.combat_state is not None
        assert game_state.combat_state.round_number == 1

    def test_game_state_active_effects(self):
        """Test that GameState tracks active_effects."""
        active_effects = [
            {"effect_name": "Fireball", "duration": 3, "source": "char-001"},
            {"effect_name": "Blessing", "duration": 10, "source": "char-002"},
        ]
        game_state = GameStateResponse(
            id="gs-001",
            campaign_id="camp-001",
            current_phase="combat",
            narrative_history=[],
            current_scene="",
            combat_state=None,
            active_effects=active_effects,
        )
        assert len(game_state.active_effects) == 2
        assert game_state.active_effects[0]["effect_name"] == "Fireball"
        assert game_state.active_effects[1]["duration"] == 10


class TestMapModel:
    """Test suite for Map model."""

    def test_map_has_dimensions(self):
        """Test that Map has width and height grid dimensions."""
        map_data = MapCreate(
            width=20,
            height=15,
        )
        assert map_data.width == 20
        assert map_data.height == 15

    def test_map_has_terrain_grid(self):
        """Test that Map has terrain grid (2D array)."""
        terrain_grid = [
            ["empty", "wall", "empty"],
            ["water", "empty", "wall"],
            ["empty", "difficult", "pit"],
        ]
        map_data = MapCreate(
            width=3,
            height=3,
            terrain_grid=terrain_grid,
        )
        assert map_data.terrain_grid == terrain_grid
        assert len(map_data.terrain_grid) == 3

    def test_valid_terrain_types(self):
        """Test that only valid terrain types are accepted."""
        valid_terrains = ["empty", "wall", "water", "difficult", "pit"]
        
        terrain_grid = [[terrain] for terrain in valid_terrains]
        map_data = MapCreate(
            width=1,
            height=len(valid_terrains),
            terrain_grid=terrain_grid,
        )
        assert len(map_data.terrain_grid) == len(valid_terrains)

    def test_map_has_token_positions(self):
        """Test that Map has token_positions dict (entity_id → {x, y})."""
        token_positions = [
            TokenPosition(entity_id="char-001", x=5, y=5),
            TokenPosition(entity_id="char-002", x=10, y=3),
            TokenPosition(entity_id="enemy-001", x=15, y=8),
        ]
        map_data = MapCreate(
            width=20,
            height=20,
            token_positions=token_positions,
        )
        assert len(map_data.token_positions) == 3

    def test_token_position_must_be_within_bounds(self):
        """Test that token position must be within grid bounds."""
        # Valid positions
        map_data = MapCreate(
            width=10,
            height=10,
            token_positions=[
                TokenPosition(entity_id="char-001", x=0, y=0),
                TokenPosition(entity_id="char-002", x=9, y=9),
            ],
        )
        assert len(map_data.token_positions) == 2

        # Invalid positions (out of bounds)
        with pytest.raises(ValidationError):
            MapCreate(
                width=10,
                height=10,
                token_positions=[
                    TokenPosition(entity_id="char-001", x=10, y=5),  # x out of bounds
                ],
            )

        with pytest.raises(ValidationError):
            MapCreate(
                width=10,
                height=10,
                token_positions=[
                    TokenPosition(entity_id="char-001", x=5, y=10),  # y out of bounds
                ],
            )

    def test_map_has_fog_of_war(self):
        """Test that Map has fog_of_war (2D array of booleans)."""
        fog_of_war = [
            [True, False, True],
            [False, True, False],
            [True, True, False],
        ]
        map_data = MapCreate(
            width=3,
            height=3,
            fog_of_war=fog_of_war,
        )
        assert map_data.fog_of_war == fog_of_war

    def test_map_serialization(self):
        """Test that map can be serialized/deserialized."""
        map_data = MapCreate(
            width=10,
            height=10,
            terrain_grid=[["empty"] * 10 for _ in range(10)],
            token_positions=[TokenPosition(entity_id="test", x=5, y=5)],
        )
        
        # Serialize to dict
        map_dict = map_data.model_dump()
        assert isinstance(map_dict, dict)
        assert map_dict["width"] == 10
        
        # Serialize to JSON
        json_str = map_data.model_dump_json()
        assert isinstance(json_str, str)
        assert "10" in json_str

    def test_map_response_includes_id(self):
        """Test that MapResponse includes an ID."""
        map_response = MapResponse(
            id="map-001",
            width=20,
            height=20,
            terrain_grid=[["empty"] * 20 for _ in range(20)],
            token_positions=[],
            fog_of_war=[],
        )
        assert map_response.id == "map-001"


class TestEnums:
    """Test suite for enum values."""

    def test_race_enum_values(self):
        """Test that Race enum has all valid values."""
        valid_races = ["human", "elf", "dwarf", "halfling", "gnome", "half-elf", "half-orc", "tiefling", "dragonborn"]
        for race in valid_races:
            assert race in [r.value for r in Race]

    def test_character_class_enum_values(self):
        """Test that CharacterClass enum has all valid values."""
        valid_classes = ["barbarian", "bard", "cleric", "druid", "fighter", "monk", "paladin", "ranger", "rogue", "sorcerer", "warlock", "wizard"]
        for class_name in valid_classes:
            assert class_name in [c.value for c in CharacterClass]

    def test_game_phase_enum_values(self):
        """Test that GamePhase enum has all valid values."""
        valid_phases = ["lobby", "exploration", "combat", "rest", "shopping"]
        for phase in valid_phases:
            assert phase in [p.value for p in GamePhase]

    def test_terrain_type_enum_values(self):
        """Test that TerrainType enum has all valid values."""
        valid_terrains = ["empty", "wall", "water", "difficult", "pit"]
        for terrain in valid_terrains:
            assert terrain in [t.value for t in TerrainType]

    def test_condition_enum_exists(self):
        """Test that Condition enum exists with expected values."""
        # Common D&D 5e conditions
        assert hasattr(Condition, "__members__")
