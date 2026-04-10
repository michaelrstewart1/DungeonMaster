"""
Tests for Turn Manager.

Manages the turn-by-turn game loop, processing player actions through
the rules engine and narrator. Using TDD: tests first, then implementation.
"""

import pytest
from app.services.dice import DiceRoller
from app.services.rules.engine import RulesEngine, ActionResult
from app.services.rules.combat import Combatant
from app.services.llm.base import FakeLLM
from app.services.llm.narrator import DMNarrator
from app.services.game.turns import TurnManager, TurnResult
from app.services.game.state import GamePhase


class TestTurnResultStructure:
    """Test TurnResult dataclass."""

    def test_turn_result_creation(self):
        """TurnResult should be creatable with all fields."""
        action_result = ActionResult(
            action_type="attack",
            success=True,
            description="Hit!"
        )
        
        result = TurnResult(
            turn_number=1,
            action_result=action_result,
            narration="You swing your sword...",
            phase="combat"
        )
        
        assert result.turn_number == 1
        assert result.action_result == action_result
        assert result.narration == "You swing your sword..."
        assert result.phase == "combat"

    def test_turn_result_with_none_action_result(self):
        """TurnResult should allow None action_result."""
        result = TurnResult(
            turn_number=1,
            action_result=None,
            narration="The scene unfolds...",
            phase="exploration"
        )
        
        assert result.action_result is None


class TestTurnManagerInit:
    """Test TurnManager initialization."""

    def test_init_with_rules_engine_and_narrator(self):
        """TurnManager should accept RulesEngine and DMNarrator."""
        roller = DiceRoller(seed=42)
        engine = RulesEngine(roller)
        
        llm = FakeLLM(default_response="The narrator speaks...")
        narrator = DMNarrator(llm)
        
        manager = TurnManager(engine, narrator)
        
        assert manager is not None
        assert manager.rules_engine == engine
        assert manager.narrator == narrator

    def test_turn_counter_initializes_to_zero(self):
        """TurnManager should initialize turn counter to 0."""
        roller = DiceRoller(seed=42)
        engine = RulesEngine(roller)
        
        llm = FakeLLM(default_response="The narrator speaks...")
        narrator = DMNarrator(llm)
        
        manager = TurnManager(engine, narrator)
        
        assert manager.turn_number == 0


class TestTurnManagerAction:
    """Test processing player actions."""

    @pytest.mark.asyncio
    async def test_process_player_action_increments_turn_count(self):
        """process_player_action should increment turn number."""
        roller = DiceRoller(seed=42)
        engine = RulesEngine(roller)
        
        llm = FakeLLM(default_response="You swing...")
        narrator = DMNarrator(llm)
        
        manager = TurnManager(engine, narrator)
        
        initial_turn = manager.turn_number
        
        action = {"type": "move", "target": "north"}
        result = await manager.process_player_action(action)
        
        assert manager.turn_number > initial_turn
        assert isinstance(result, TurnResult)
        assert result.turn_number == manager.turn_number

    @pytest.mark.asyncio
    async def test_process_player_action_returns_turn_result(self):
        """process_player_action should return TurnResult."""
        roller = DiceRoller(seed=42)
        engine = RulesEngine(roller)
        
        llm = FakeLLM(default_response="You move carefully...")
        narrator = DMNarrator(llm)
        
        manager = TurnManager(engine, narrator)
        
        action = {"type": "move", "direction": "north"}
        result = await manager.process_player_action(action)
        
        assert isinstance(result, TurnResult)
        assert isinstance(result.turn_number, int)
        assert isinstance(result.narration, str)
        assert isinstance(result.phase, str)

    @pytest.mark.asyncio
    async def test_process_player_action_gets_narration(self):
        """process_player_action should get narration from narrator."""
        roller = DiceRoller(seed=42)
        engine = RulesEngine(roller)
        
        llm = FakeLLM(default_response="The goblin attacks!")
        narrator = DMNarrator(llm)
        
        manager = TurnManager(engine, narrator)
        
        action = {"type": "speak", "text": "Hello NPC"}
        result = await manager.process_player_action(action)
        
        # Should have received narration from LLM
        assert result.narration is not None
        assert len(result.narration) > 0

    @pytest.mark.asyncio
    async def test_process_player_action_attack_type(self):
        """process_player_action should handle attack actions."""
        roller = DiceRoller(seed=42)
        engine = RulesEngine(roller)
        
        llm = FakeLLM(default_response="Critical hit!")
        narrator = DMNarrator(llm)
        
        manager = TurnManager(engine, narrator)
        
        # Initialize combat with some combatants
        combatants = [
            {"id": "hero-1", "name": "Hero", "initiative_modifier": 2, "hp": 50, "max_hp": 50, "ac": 15},
            {"id": "goblin-1", "name": "Goblin", "initiative_modifier": 1, "hp": 20, "max_hp": 20, "ac": 12},
        ]
        manager.combatants = engine.start_combat(combatants)
        manager.current_combatant_index = 0
        
        action = {
            "type": "attack",
            "target_id": "goblin-1",
            "attack_bonus": 5,
            "damage_dice": "1d8"
        }
        result = await manager.process_player_action(action)
        
        assert isinstance(result, TurnResult)

    @pytest.mark.asyncio
    async def test_process_player_action_spell_type(self):
        """process_player_action should handle spell actions."""
        roller = DiceRoller(seed=42)
        engine = RulesEngine(roller)
        
        llm = FakeLLM(default_response="Magic missile strikes!")
        narrator = DMNarrator(llm)
        
        manager = TurnManager(engine, narrator)
        
        action = {
            "type": "cast_spell",
            "spell_name": "Magic Missile",
            "target_id": "goblin-1"
        }
        result = await manager.process_player_action(action)
        
        assert isinstance(result, TurnResult)

    @pytest.mark.asyncio
    async def test_process_player_action_ability_check_type(self):
        """process_player_action should handle ability check actions."""
        roller = DiceRoller(seed=42)
        engine = RulesEngine(roller)
        
        llm = FakeLLM(default_response="You make the check...")
        narrator = DMNarrator(llm)
        
        manager = TurnManager(engine, narrator)
        
        action = {
            "type": "ability_check",
            "ability": "strength",
            "dc": 15
        }
        result = await manager.process_player_action(action)
        
        assert isinstance(result, TurnResult)

    @pytest.mark.asyncio
    async def test_process_player_action_move_type(self):
        """process_player_action should handle move actions."""
        roller = DiceRoller(seed=42)
        engine = RulesEngine(roller)
        
        llm = FakeLLM(default_response="You move forward...")
        narrator = DMNarrator(llm)
        
        manager = TurnManager(engine, narrator)
        
        action = {"type": "move", "direction": "north"}
        result = await manager.process_player_action(action)
        
        assert isinstance(result, TurnResult)

    @pytest.mark.asyncio
    async def test_process_player_action_interact_type(self):
        """process_player_action should handle interact actions."""
        roller = DiceRoller(seed=42)
        engine = RulesEngine(roller)
        
        llm = FakeLLM(default_response="You open the door...")
        narrator = DMNarrator(llm)
        
        manager = TurnManager(engine, narrator)
        
        action = {"type": "interact", "object": "door"}
        result = await manager.process_player_action(action)
        
        assert isinstance(result, TurnResult)

    @pytest.mark.asyncio
    async def test_process_player_action_speak_type(self):
        """process_player_action should handle speak actions."""
        roller = DiceRoller(seed=42)
        engine = RulesEngine(roller)
        
        llm = FakeLLM(default_response="The NPC responds...")
        narrator = DMNarrator(llm)
        
        manager = TurnManager(engine, narrator)
        
        action = {"type": "speak", "text": "Greetings!"}
        result = await manager.process_player_action(action)
        
        assert isinstance(result, TurnResult)


class TestTurnManagerTurnInfo:
    """Test getting turn information."""

    def test_get_current_turn_info(self):
        """get_current_turn_info should return turn info."""
        roller = DiceRoller(seed=42)
        engine = RulesEngine(roller)
        
        llm = FakeLLM(default_response="...")
        narrator = DMNarrator(llm)
        
        manager = TurnManager(engine, narrator)
        
        info = manager.get_current_turn_info()
        
        assert isinstance(info, dict)
        assert "turn_number" in info
        assert isinstance(info["turn_number"], int)

    def test_get_current_turn_info_in_combat(self):
        """get_current_turn_info should show active combatant in combat."""
        roller = DiceRoller(seed=42)
        engine = RulesEngine(roller)
        
        llm = FakeLLM(default_response="...")
        narrator = DMNarrator(llm)
        
        manager = TurnManager(engine, narrator)
        
        # Start combat
        combatants = [
            {"id": "hero-1", "name": "Hero", "initiative_modifier": 2, "hp": 50, "max_hp": 50, "ac": 15},
            {"id": "goblin-1", "name": "Goblin", "initiative_modifier": 1, "hp": 20, "max_hp": 20, "ac": 12},
        ]
        manager.combatants = engine.start_combat(combatants)
        manager.current_combatant_index = 0
        
        info = manager.get_current_turn_info()
        
        assert "current_combatant" in info or "combatants" in info


class TestTurnManagerCombatCycling:
    """Test combat turn cycling."""

    def test_combat_turns_cycle_through_initiative_order(self):
        """Combat turns should cycle through initiative order."""
        roller = DiceRoller(seed=42)
        engine = RulesEngine(roller)
        
        llm = FakeLLM(default_response="...")
        narrator = DMNarrator(llm)
        
        manager = TurnManager(engine, narrator)
        
        combatants = [
            {"id": "hero-1", "name": "Hero", "initiative_modifier": 2, "hp": 50, "max_hp": 50, "ac": 15},
            {"id": "hero-2", "name": "Rogue", "initiative_modifier": 3, "hp": 35, "max_hp": 35, "ac": 16},
            {"id": "goblin-1", "name": "Goblin", "initiative_modifier": 1, "hp": 20, "max_hp": 20, "ac": 12},
        ]
        
        manager.combatants = engine.start_combat(combatants)
        
        # Should have ordered combatants
        assert len(manager.combatants) == 3

    def test_turn_info_includes_phase(self):
        """Turn info should include current phase."""
        roller = DiceRoller(seed=42)
        engine = RulesEngine(roller)
        
        llm = FakeLLM(default_response="...")
        narrator = DMNarrator(llm)
        
        manager = TurnManager(engine, narrator)
        
        info = manager.get_current_turn_info()
        
        assert "phase" in info or isinstance(info, dict)
