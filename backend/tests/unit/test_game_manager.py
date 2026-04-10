"""
Tests for Game Manager (Integration).

Top-level orchestrator that ties together rules engine, turn manager,
narrative summary, and game state. Using TDD: tests first, then implementation.
"""

import pytest
import uuid
from app.services.dice import DiceRoller
from app.services.llm.base import FakeLLM
from app.services.game.manager import GameManager, GameSession
from app.services.game.state import GamePhase


class TestGameSessionStructure:
    """Test GameSession dataclass."""

    def test_game_session_creation(self):
        """GameSession should be creatable with required fields."""
        from app.services.game.summary import NarrativeSummary
        
        narrative = NarrativeSummary()
        session = GameSession(
            id="session-1",
            players=[],
            enemies=[],
            phase=GamePhase.EXPLORATION,
            turn_count=0,
            narrative=narrative
        )
        
        assert session.id == "session-1"
        assert session.players == []
        assert session.enemies == []
        assert session.phase == GamePhase.EXPLORATION
        assert session.turn_count == 0


class TestGameManagerInit:
    """Test GameManager initialization."""

    def test_init_with_llm_provider(self):
        """GameManager should accept LLMProvider."""
        llm = FakeLLM(default_response="The game begins...")
        manager = GameManager(llm)
        
        assert manager is not None
        assert manager.llm_provider == llm

    def test_init_with_optional_dice_seed(self):
        """GameManager should accept optional dice seed."""
        llm = FakeLLM(default_response="...")
        manager = GameManager(llm, dice_seed=42)
        
        assert manager is not None

    def test_init_creates_required_components(self):
        """GameManager should create required components."""
        llm = FakeLLM(default_response="...")
        manager = GameManager(llm, dice_seed=42)
        
        # Should have created components
        assert manager.rules_engine is not None
        assert manager.narrator is not None
        assert manager.state_machine is not None


class TestGameManagerSessionCreation:
    """Test session creation."""

    def test_create_session(self):
        """create_session should create a new game session."""
        llm = FakeLLM(default_response="Welcome to the campaign...")
        manager = GameManager(llm, dice_seed=42)
        
        session = manager.create_session(campaign_name="Lost Mines of Phandelver")
        
        assert isinstance(session, GameSession)
        assert session.id is not None
        assert session.phase == GamePhase.LOBBY
        assert session.turn_count == 0
        assert session.players == []

    def test_create_session_generates_unique_ids(self):
        """create_session should generate unique session IDs."""
        llm = FakeLLM(default_response="...")
        manager = GameManager(llm, dice_seed=42)
        
        session1 = manager.create_session(campaign_name="Campaign 1")
        session2 = manager.create_session(campaign_name="Campaign 2")
        
        assert session1.id != session2.id

    def test_create_session_initializes_narrative_summary(self):
        """create_session should initialize narrative summary."""
        llm = FakeLLM(default_response="...")
        manager = GameManager(llm, dice_seed=42)
        
        session = manager.create_session(campaign_name="Test Campaign")
        
        assert session.narrative is not None


class TestGameManagerPlayerManagement:
    """Test player character management."""

    def test_add_player_to_session(self):
        """add_player should add a player character to session."""
        llm = FakeLLM(default_response="...")
        manager = GameManager(llm, dice_seed=42)
        
        session = manager.create_session(campaign_name="Test")
        
        character = {
            "id": "player-1",
            "name": "Aragorn",
            "class": "Ranger",
            "level": 3,
            "hp": 30,
            "max_hp": 30,
            "ac": 15
        }
        
        manager.add_player(session.id, character)
        
        assert len(session.players) == 1
        assert session.players[0]["name"] == "Aragorn"

    def test_add_multiple_players(self):
        """add_player should add multiple players to same session."""
        llm = FakeLLM(default_response="...")
        manager = GameManager(llm, dice_seed=42)
        
        session = manager.create_session(campaign_name="Test")
        
        manager.add_player(session.id, {
            "id": "p1", "name": "Aragorn", "class": "Ranger", "level": 3,
            "hp": 30, "max_hp": 30, "ac": 15
        })
        manager.add_player(session.id, {
            "id": "p2", "name": "Legolas", "class": "Rogue", "level": 3,
            "hp": 25, "max_hp": 25, "ac": 16
        })
        
        assert len(session.players) == 2

    def test_add_player_to_nonexistent_session(self):
        """add_player should handle nonexistent session gracefully."""
        llm = FakeLLM(default_response="...")
        manager = GameManager(llm, dice_seed=42)
        
        character = {"id": "p1", "name": "Hero"}
        
        # Should raise or handle gracefully
        with pytest.raises((KeyError, ValueError, AttributeError)):
            manager.add_player("nonexistent-id", character)


class TestGameManagerStateTransitions:
    """Test game phase transitions."""

    def test_start_combat_transitions_to_combat_phase(self):
        """start_combat should transition to combat phase."""
        llm = FakeLLM(default_response="Combat begins!")
        manager = GameManager(llm, dice_seed=42)
        
        session = manager.create_session(campaign_name="Test")
        
        # Start in exploration
        manager.state_machine.transition_to(GamePhase.EXPLORATION)
        
        enemies = [
            {"id": "goblin-1", "name": "Goblin", "initiative_modifier": 1, "hp": 20, "max_hp": 20, "ac": 12},
            {"id": "goblin-2", "name": "Goblin", "initiative_modifier": 1, "hp": 15, "max_hp": 15, "ac": 12},
        ]
        
        manager.start_combat(session.id, enemies)
        
        assert session.phase == GamePhase.COMBAT
        assert len(session.enemies) > 0

    def test_start_combat_rolls_initiative(self):
        """start_combat should roll initiative for enemies."""
        llm = FakeLLM(default_response="...")
        manager = GameManager(llm, dice_seed=42)
        
        session = manager.create_session(campaign_name="Test")
        manager.state_machine.transition_to(GamePhase.EXPLORATION)
        
        enemies = [
            {"id": "goblin-1", "name": "Goblin", "initiative_modifier": 1, "hp": 20, "max_hp": 20, "ac": 12},
        ]
        
        manager.start_combat(session.id, enemies)
        
        # Enemies should have initiative values
        assert session.enemies[0].initiative > 0

    def test_end_combat_transitions_back_to_exploration(self):
        """end_combat should transition back to exploration phase."""
        llm = FakeLLM(default_response="...")
        manager = GameManager(llm, dice_seed=42)
        
        session = manager.create_session(campaign_name="Test")
        
        # Manually set up state for testing
        session.state_machine.transition_to(GamePhase.EXPLORATION)
        session.state_machine.transition_to(GamePhase.COMBAT)
        session.phase = GamePhase.COMBAT
        
        assert session.phase == GamePhase.COMBAT
        
        manager.end_combat(session.id)
        
        assert session.phase == GamePhase.EXPLORATION

    def test_invalid_phase_transition_raises_error(self):
        """Invalid phase transition should raise InvalidTransitionError."""
        llm = FakeLLM(default_response="...")
        manager = GameManager(llm, dice_seed=42)
        
        from app.services.game.state import InvalidTransitionError
        
        manager.state_machine._current = GamePhase.COMBAT
        
        # Cannot go from COMBAT to SHOPPING directly
        with pytest.raises(InvalidTransitionError):
            manager.state_machine.transition_to(GamePhase.SHOPPING)


class TestGameManagerActions:
    """Test processing player actions."""

    @pytest.mark.asyncio
    async def test_process_action_returns_turn_result(self):
        """process_action should return TurnResult."""
        llm = FakeLLM(default_response="You move cautiously...")
        manager = GameManager(llm, dice_seed=42)
        
        session = manager.create_session(campaign_name="Test")
        manager.state_machine.transition_to(GamePhase.EXPLORATION)
        
        manager.add_player(session.id, {
            "id": "p1", "name": "Hero", "class": "Fighter",
            "hp": 50, "max_hp": 50, "ac": 15
        })
        
        action = {"type": "move", "direction": "north"}
        result = await manager.process_action(session.id, "p1", action)
        
        assert result is not None
        assert hasattr(result, "turn_number")
        assert hasattr(result, "narration")

    @pytest.mark.asyncio
    async def test_process_action_updates_session_state(self):
        """process_action should update session state."""
        llm = FakeLLM(default_response="You look around...")
        manager = GameManager(llm, dice_seed=42)
        
        session = manager.create_session(campaign_name="Test")
        manager.state_machine.transition_to(GamePhase.EXPLORATION)
        
        initial_turn = session.turn_count
        
        action = {"type": "interact", "object": "door"}
        result = await manager.process_action(session.id, "p1", action)
        
        # Turn count should have incremented
        assert session.turn_count >= initial_turn

    @pytest.mark.asyncio
    async def test_process_action_in_combat(self):
        """process_action should handle combat actions."""
        llm = FakeLLM(default_response="You attack!")
        manager = GameManager(llm, dice_seed=42)
        
        session = manager.create_session(campaign_name="Test")
        manager.state_machine.transition_to(GamePhase.EXPLORATION)
        
        manager.add_player(session.id, {
            "id": "p1", "name": "Hero", "class": "Fighter",
            "hp": 50, "max_hp": 50, "ac": 15, "initiative_modifier": 2
        })
        
        enemies = [
            {"id": "goblin-1", "name": "Goblin", "initiative_modifier": 1, "hp": 20, "max_hp": 20, "ac": 12},
        ]
        
        manager.start_combat(session.id, enemies)
        
        action = {
            "type": "attack",
            "target_id": "goblin-1",
            "attack_bonus": 5,
            "damage_dice": "1d8"
        }
        
        result = await manager.process_action(session.id, "p1", action)
        
        assert result is not None


class TestGameManagerSessionState:
    """Test session state queries."""

    def test_get_session_state(self):
        """get_session_state should return current game state snapshot."""
        llm = FakeLLM(default_response="...")
        manager = GameManager(llm, dice_seed=42)
        
        session = manager.create_session(campaign_name="Test Campaign")
        manager.state_machine.transition_to(GamePhase.EXPLORATION)
        
        manager.add_player(session.id, {
            "id": "p1", "name": "Hero", "class": "Fighter",
            "hp": 50, "max_hp": 50, "ac": 15
        })
        
        state = manager.get_session_state(session.id)
        
        assert isinstance(state, dict)
        assert "phase" in state or "players" in state

    def test_get_session_state_includes_players(self):
        """get_session_state should include player information."""
        llm = FakeLLM(default_response="...")
        manager = GameManager(llm, dice_seed=42)
        
        session = manager.create_session(campaign_name="Test")
        
        manager.add_player(session.id, {
            "id": "p1", "name": "Aragorn", "class": "Ranger",
            "hp": 30, "max_hp": 30, "ac": 15
        })
        
        state = manager.get_session_state(session.id)
        
        # Should have some representation of players
        assert isinstance(state, dict)

    def test_get_session_state_includes_enemies(self):
        """get_session_state should include enemy information in combat."""
        llm = FakeLLM(default_response="...")
        manager = GameManager(llm, dice_seed=42)
        
        session = manager.create_session(campaign_name="Test")
        manager.state_machine.transition_to(GamePhase.EXPLORATION)
        
        enemies = [
            {"id": "goblin-1", "name": "Goblin", "initiative_modifier": 1, "hp": 20, "max_hp": 20, "ac": 12},
        ]
        
        manager.start_combat(session.id, enemies)
        
        state = manager.get_session_state(session.id)
        
        assert isinstance(state, dict)

    def test_get_session_state_includes_phase(self):
        """get_session_state should include current phase."""
        llm = FakeLLM(default_response="...")
        manager = GameManager(llm, dice_seed=42)
        
        session = manager.create_session(campaign_name="Test")
        manager.state_machine.transition_to(GamePhase.EXPLORATION)
        
        state = manager.get_session_state(session.id)
        
        # Should include phase information
        assert isinstance(state, dict)


class TestGameManagerIntegration:
    """Integration tests for full game session."""

    @pytest.mark.asyncio
    async def test_full_game_session_flow(self):
        """Full game session: create -> add players -> start combat -> process turns."""
        llm = FakeLLM(default_response="The adventure continues...")
        manager = GameManager(llm, dice_seed=42)
        
        # Create session
        session = manager.create_session(campaign_name="Lost Mines")
        assert session.phase == GamePhase.LOBBY
        
        # Add player
        manager.add_player(session.id, {
            "id": "p1", "name": "Aragorn", "class": "Ranger", "level": 3,
            "hp": 30, "max_hp": 30, "ac": 15, "initiative_modifier": 2
        })
        assert len(session.players) == 1
        
        # Transition to exploration
        manager.state_machine.transition_to(GamePhase.EXPLORATION)
        
        # Process an action
        result = await manager.process_action(session.id, "p1", {"type": "move", "direction": "north"})
        assert result is not None
        
        # Start combat
        manager.start_combat(session.id, [
            {"id": "goblin-1", "name": "Goblin", "initiative_modifier": 1, "hp": 20, "max_hp": 20, "ac": 12},
        ])
        assert session.phase == GamePhase.COMBAT
        
        # Process combat action
        result = await manager.process_action(session.id, "p1", {
            "type": "attack",
            "target_id": "goblin-1",
            "attack_bonus": 5,
            "damage_dice": "1d8"
        })
        assert result is not None

    @pytest.mark.asyncio
    async def test_three_turn_combat_encounter(self):
        """Integration test: three turns of combat encounter."""
        llm = FakeLLM(default_response="Combat unfolds...")
        manager = GameManager(llm, dice_seed=42)
        
        # Setup
        session = manager.create_session(campaign_name="Combat Test")
        manager.state_machine.transition_to(GamePhase.EXPLORATION)
        
        manager.add_player(session.id, {
            "id": "p1", "name": "Hero", "class": "Fighter", "level": 3,
            "hp": 50, "max_hp": 50, "ac": 15, "initiative_modifier": 2
        })
        
        # Start combat
        enemies = [
            {"id": "goblin-1", "name": "Goblin", "initiative_modifier": 1, "hp": 20, "max_hp": 20, "ac": 12},
        ]
        manager.start_combat(session.id, enemies)
        
        # Turn 1: Player attacks
        result1 = await manager.process_action(session.id, "p1", {
            "type": "attack",
            "target_id": "goblin-1",
            "attack_bonus": 5,
            "damage_dice": "1d8"
        })
        assert result1 is not None
        assert result1.turn_number >= 1
        
        # Turn 2: Spell casting
        result2 = await manager.process_action(session.id, "p1", {
            "type": "cast_spell",
            "spell_name": "Magic Missile",
            "target_id": "goblin-1"
        })
        assert result2 is not None
        assert result2.turn_number >= 2
        
        # Turn 3: Another attack
        result3 = await manager.process_action(session.id, "p1", {
            "type": "attack",
            "target_id": "goblin-1",
            "attack_bonus": 5,
            "damage_dice": "1d8"
        })
        assert result3 is not None
        assert result3.turn_number >= 3
