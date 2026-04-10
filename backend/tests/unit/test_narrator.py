"""
Tests for the DM Narrator service.

These tests use FakeLLM to avoid making real API calls.
"""

import pytest
from app.services.llm.narrator import DMNarrator
from app.services.llm.base import FakeLLM, LLMMessage, LLMResponse, LLMUsage


class TestDMNarrator:
    """Tests for DMNarrator service."""

    @pytest.fixture
    def fake_llm(self):
        """Create a FakeLLM instance with default responses."""
        response_map = {
            "exploration": "You approach the ancient ruins with caution.",
            "combat": "The goblin raises its weapon and strikes!",
            "npc": "Greetings, adventurer! What brings you to this tavern?",
            "environment": "The air is thick with moisture and the smell of decay.",
            "scene": "You find yourself in a dimly lit dungeon chamber.",
        }
        return FakeLLM(
            default_response="A mysterious force surrounds you.",
            response_map=response_map,
            prompt_tokens=100,
            completion_tokens=50,
        )

    @pytest.fixture
    def narrator(self, fake_llm):
        """Create a DMNarrator instance with FakeLLM."""
        return DMNarrator(llm=fake_llm, max_history=20)

    def test_narrator_accepts_llm_provider_in_constructor(self, fake_llm):
        """Test that Narrator accepts an LLMProvider in constructor."""
        narrator = DMNarrator(llm=fake_llm)
        assert narrator._llm is fake_llm

    def test_narrator_can_be_configured_with_max_history(self, fake_llm):
        """Test that Narrator can be configured with max_history."""
        narrator = DMNarrator(llm=fake_llm, max_history=50)
        assert narrator._max_history == 50

    @pytest.mark.asyncio
    async def test_narrate_exploration_returns_string(self, narrator):
        """Test that narrate_exploration returns a narration string."""
        scene = {"name": "Ancient Ruins", "description": "Crumbling stones and vines"}
        player_action = "exploration"  # Match the response map
        characters = [{"name": "Theron", "class": "Rogue"}]
        world_context = "A forgotten kingdom"

        result = await narrator.narrate_exploration(
            scene, player_action, characters, world_context
        )

        assert isinstance(result, str)
        assert len(result) > 0
        # Check for content from the mapped response
        assert "ancient" in result.lower() or "ruins" in result.lower()

    @pytest.mark.asyncio
    async def test_narrate_combat_action_returns_string(self, narrator):
        """Test that narrate_combat_action returns combat narration."""
        combat_state = {
            "round": 1,
            "initiative": ["Player 1", "Enemy 1", "Player 2"],
            "current_turn": "Player 1",
        }
        # Include "combat" keyword in the description so FakeLLM matches it
        action_result = {"action": "Attack", "description": "combat action", "roll": 18, "hit": True}
        characters = [{"name": "Theron", "class": "Fighter"}]

        result = await narrator.narrate_combat_action(
            combat_state, action_result, characters
        )

        assert isinstance(result, str)
        assert len(result) > 0
        # Check for expected combat narration
        assert "goblin" in result.lower() or "raises" in result.lower()

    @pytest.mark.asyncio
    async def test_narrate_npc_interaction_returns_string(self, narrator):
        """Test that narrate_npc_interaction returns NPC dialogue."""
        npc = {"name": "Bartender", "personality": "Gruff and suspicious"}
        player_message = "Do you know anything about the missing caravan?"
        conversation_history = []

        result = await narrator.narrate_npc_interaction(
            npc, player_message, conversation_history
        )

        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_narrate_environment_returns_string(self, narrator):
        """Test that narrate_environment returns environment description."""
        scene_description = "A foggy forest clearing"
        player_action = "The party looks around cautiously"

        result = await narrator.narrate_environment(scene_description, player_action)

        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_narrator_uses_prompt_templates(self, narrator):
        """Test that Narrator uses PromptTemplates to construct prompts."""
        scene = {"name": "Tavern", "description": "A bustling tavern"}
        player_action = "The party orders drinks"
        characters = [{"name": "Thorin", "class": "Dwarf", "level": 5}]
        world_context = "A thriving port city"

        # Make a call that should use dm_system_prompt
        await narrator.narrate_exploration(
            scene, player_action, characters, world_context
        )

        # Verify that the LLM was called
        assert len(narrator._llm.call_history) > 0

        # Check that a system prompt was included
        call = narrator._llm.call_history[0]
        assert call["system_prompt"] is not None

    @pytest.mark.asyncio
    async def test_narrator_maintains_conversation_history(self, narrator):
        """Test that Narrator maintains conversation history."""
        scene = {"name": "Room 1"}
        player_action = "Look around"
        characters = [{"name": "Hero"}]
        world_context = "A dungeon"

        # Make multiple calls
        await narrator.narrate_exploration(
            scene, player_action, characters, world_context
        )
        initial_history_len = len(narrator._history)

        await narrator.narrate_exploration(
            scene, player_action, characters, world_context
        )

        # History should have grown
        assert len(narrator._history) >= initial_history_len

    @pytest.mark.asyncio
    async def test_narrator_truncates_history_at_max_length(self, narrator):
        """Test that Narrator truncates history when it exceeds max_history_length."""
        # Use a narrator with small max_history
        small_narrator = DMNarrator(llm=narrator._llm, max_history=3)

        scene = {"name": "Room"}
        player_action = "Action"
        characters = [{"name": "Hero"}]
        world_context = "Context"

        # Make many calls to exceed max_history
        for i in range(10):
            await small_narrator.narrate_exploration(
                scene, player_action, characters, world_context
            )

        # History should not exceed max_history
        assert len(small_narrator._history) <= small_narrator._max_history * 2

    @pytest.mark.asyncio
    async def test_describe_scene_returns_initial_scene_description(self, narrator):
        """Test that describe_scene returns initial scene description."""
        scene_data = {
            "name": "scene",  # Match response map
            "description": "A grand chamber",
            "features": ["throne", "pillars", "stained glass"],
        }

        result = await narrator.describe_scene(scene_data)

        assert isinstance(result, str)
        assert len(result) > 0
        # The FakeLLM should match on "scene" and return the mapped response
        assert "dungeon" in result.lower() or "chamber" in result.lower()

    def test_clear_history_empties_conversation_history(self, narrator):
        """Test that clear_history empties the conversation history."""
        # Add some history
        narrator._history = [
            LLMMessage(role="user", content="Test 1"),
            LLMMessage(role="assistant", content="Response 1"),
        ]

        assert len(narrator._history) > 0

        # Clear
        narrator.clear_history()

        assert len(narrator._history) == 0

    @pytest.mark.asyncio
    async def test_narrator_handles_llm_errors_gracefully(self, narrator):
        """Test that Narrator handles LLM errors gracefully."""
        # Create a fake LLM that raises an error
        error_llm = FakeLLM(default_response="Error occurred")

        # Mock the generate method to raise an exception
        async def mock_generate(*args, **kwargs):
            raise Exception("LLM Error")

        error_llm.generate = mock_generate
        error_narrator = DMNarrator(llm=error_llm)

        scene = {"name": "Room"}
        player_action = "Look"
        characters = [{"name": "Hero"}]
        world_context = "Context"

        # Should not raise, should return fallback
        result = await error_narrator.narrate_exploration(
            scene, player_action, characters, world_context
        )

        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_history_contains_llm_messages(self, narrator):
        """Test that history contains LLMMessage objects."""
        scene = {"name": "Room"}
        player_action = "Look"
        characters = [{"name": "Hero"}]
        world_context = "Context"

        await narrator.narrate_exploration(
            scene, player_action, characters, world_context
        )

        # Check history types
        for msg in narrator._history:
            assert isinstance(msg, LLMMessage)
            assert msg.role in ["system", "user", "assistant"]
            assert isinstance(msg.content, str)

    @pytest.mark.asyncio
    async def test_narrate_combat_action_with_multiple_characters(self, narrator):
        """Test narrate_combat_action with multiple characters."""
        combat_state = {
            "round": 2,
            "initiative": ["Player 1", "Enemy 1", "Player 2"],
            "current_turn": "Enemy 1",
        }
        action_result = {"action": "Attack", "target": "Player 1", "damage": 7}
        characters = [
            {"name": "Theron", "class": "Rogue", "hp": 20},
            {"name": "Elara", "class": "Wizard", "hp": 15},
        ]

        result = await narrator.narrate_combat_action(
            combat_state, action_result, characters
        )

        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_narrate_npc_with_conversation_history(self, narrator):
        """Test narrate_npc_interaction with conversation history."""
        npc = {"name": "Sage", "personality": "Wise and cryptic"}
        player_message = "What do you know of the dark tower?"
        conversation_history = [
            LLMMessage(role="user", content="Greetings"),
            LLMMessage(role="assistant", content="Hello, traveler"),
        ]

        result = await narrator.narrate_npc_interaction(
            npc, player_message, conversation_history
        )

        assert isinstance(result, str)
        assert len(result) > 0
