"""
Tests for prompt templates for D&D 5e Dungeon Master.

This module tests prompt templates for various LLM interactions:
- DM system prompt with world context and character information
- Combat narration with initiative and turn tracking
- NPC dialogue with personality and context
"""

import pytest
from app.services.llm.prompts import PromptTemplates


class TestDMSystemPrompt:
    """Tests for the Dungeon Master system prompt template."""

    def test_dm_system_prompt_includes_world_context(self):
        """DM system prompt includes the world context."""
        world_context = "A mystical forest filled with ancient magic"
        template = PromptTemplates.dm_system_prompt(
            world_context=world_context,
            characters=[],
            game_state={},
        )
        assert world_context in template

    def test_dm_system_prompt_includes_character_summaries(self):
        """DM system prompt includes character summaries."""
        characters = [
            {"name": "Thrall", "class": "Barbarian", "level": 5},
            {"name": "Eldara", "class": "Wizard", "level": 5},
        ]
        template = PromptTemplates.dm_system_prompt(
            world_context="Forest",
            characters=characters,
            game_state={},
        )
        assert "Thrall" in template
        assert "Barbarian" in template
        assert "Eldara" in template
        assert "Wizard" in template

    def test_dm_system_prompt_includes_current_game_state(self):
        """DM system prompt includes current game state."""
        game_state = {
            "location": "Tavern",
            "time": "Evening",
            "weather": "Rainy",
            "npc_count": 3,
        }
        template = PromptTemplates.dm_system_prompt(
            world_context="Forest",
            characters=[],
            game_state=game_state,
        )
        assert "Tavern" in template
        assert "Evening" in template
        assert "Rainy" in template

    def test_dm_system_prompt_with_empty_characters(self):
        """DM system prompt handles empty character list."""
        template = PromptTemplates.dm_system_prompt(
            world_context="World",
            characters=[],
            game_state={},
        )
        assert isinstance(template, str)
        assert len(template) > 0

    def test_dm_system_prompt_with_empty_game_state(self):
        """DM system prompt handles empty game state gracefully."""
        template = PromptTemplates.dm_system_prompt(
            world_context="World",
            characters=[{"name": "Hero"}],
            game_state={},
        )
        assert isinstance(template, str)
        assert len(template) > 0

    def test_dm_system_prompt_instructs_dm_role(self):
        """DM system prompt contains instructions for DM role."""
        template = PromptTemplates.dm_system_prompt(
            world_context="World",
            characters=[],
            game_state={},
        )
        # Should contain some instruction about being a DM
        text_lower = template.lower()
        assert (
            "dungeon master" in text_lower
            or "dm" in text_lower
            or "narrate" in text_lower
            or "describe" in text_lower
        )

    def test_dm_system_prompt_is_string(self):
        """DM system prompt returns a string."""
        result = PromptTemplates.dm_system_prompt(
            world_context="World",
            characters=[],
            game_state={},
        )
        assert isinstance(result, str)

    def test_dm_system_prompt_multiple_characters(self):
        """DM system prompt includes all character information."""
        characters = [
            {"name": "Thorgrim", "class": "Fighter", "level": 3, "hp": 28},
            {"name": "Zephyr", "class": "Rogue", "level": 3, "hp": 22},
            {"name": "Mirabel", "class": "Cleric", "level": 3, "hp": 24},
        ]
        template = PromptTemplates.dm_system_prompt(
            world_context="Underground",
            characters=characters,
            game_state={"location": "Mines"},
        )
        for char in characters:
            assert char["name"] in template


class TestCombatNarrationPrompt:
    """Tests for combat narration prompt template."""

    def test_combat_narration_includes_initiative_order(self):
        """Combat narration includes initiative order."""
        initiative_order = ["Barbarian", "Goblin", "Wizard", "Orc"]
        template = PromptTemplates.combat_narration(
            initiative_order=initiative_order,
            current_turn="Barbarian",
            recent_actions=[],
        )
        for actor in initiative_order:
            assert actor in template

    def test_combat_narration_includes_current_turn(self):
        """Combat narration indicates whose turn it is."""
        current_turn = "Wizard"
        template = PromptTemplates.combat_narration(
            initiative_order=["Wizard", "Orc"],
            current_turn=current_turn,
            recent_actions=[],
        )
        assert current_turn in template

    def test_combat_narration_includes_recent_actions(self):
        """Combat narration includes recent actions in combat."""
        recent_actions = [
            "Barbarian attacked Goblin with greataxe",
            "Goblin missed the counter-attack",
            "Wizard cast Magic Missile",
        ]
        template = PromptTemplates.combat_narration(
            initiative_order=["Barbarian"],
            current_turn="Barbarian",
            recent_actions=recent_actions,
        )
        for action in recent_actions:
            assert action in template

    def test_combat_narration_with_empty_recent_actions(self):
        """Combat narration handles empty recent actions."""
        template = PromptTemplates.combat_narration(
            initiative_order=["Fighter", "Goblin"],
            current_turn="Fighter",
            recent_actions=[],
        )
        assert isinstance(template, str)
        assert len(template) > 0

    def test_combat_narration_describes_combat(self):
        """Combat narration prompt emphasizes combat/action."""
        template = PromptTemplates.combat_narration(
            initiative_order=["Barbarian"],
            current_turn="Barbarian",
            recent_actions=[],
        )
        text_lower = template.lower()
        assert (
            "combat" in text_lower
            or "turn" in text_lower
            or "action" in text_lower
            or "initiative" in text_lower
        )

    def test_combat_narration_is_string(self):
        """Combat narration template returns a string."""
        result = PromptTemplates.combat_narration(
            initiative_order=["Fighter"],
            current_turn="Fighter",
            recent_actions=[],
        )
        assert isinstance(result, str)


class TestNPCDialoguePrompt:
    """Tests for NPC dialogue prompt template."""

    def test_npc_dialogue_includes_npc_name(self):
        """NPC dialogue prompt includes NPC name."""
        npc_name = "Barnabus the Innkeeper"
        template = PromptTemplates.npc_dialogue(
            npc_name=npc_name,
            personality="Gruff but kind-hearted",
            known_info=[],
        )
        assert npc_name in template

    def test_npc_dialogue_includes_personality(self):
        """NPC dialogue prompt includes personality description."""
        personality = "Cunning merchant with a silver tongue"
        template = PromptTemplates.npc_dialogue(
            npc_name="Merchant",
            personality=personality,
            known_info=[],
        )
        assert personality in template

    def test_npc_dialogue_includes_known_information(self):
        """NPC dialogue prompt includes known facts about NPC."""
        known_info = [
            "Collects rare artifacts",
            "Once betrayed by a companion",
            "Seeks the Crown of Kings",
        ]
        template = PromptTemplates.npc_dialogue(
            npc_name="Seller",
            personality="Mysterious",
            known_info=known_info,
        )
        for info in known_info:
            assert info in template

    def test_npc_dialogue_with_empty_known_info(self):
        """NPC dialogue handles empty known information."""
        template = PromptTemplates.npc_dialogue(
            npc_name="Soldier",
            personality="Disciplined",
            known_info=[],
        )
        assert isinstance(template, str)
        assert len(template) > 0

    def test_npc_dialogue_includes_dialogue_instruction(self):
        """NPC dialogue prompt indicates this is for NPC speech."""
        template = PromptTemplates.npc_dialogue(
            npc_name="Guard",
            personality="Strict",
            known_info=[],
        )
        text_lower = template.lower()
        assert (
            "dialogue" in text_lower
            or "speak" in text_lower
            or "respond" in text_lower
            or "npc" in text_lower
            or "say" in text_lower
        )

    def test_npc_dialogue_is_string(self):
        """NPC dialogue template returns a string."""
        result = PromptTemplates.npc_dialogue(
            npc_name="NPC",
            personality="Neutral",
            known_info=[],
        )
        assert isinstance(result, str)

    def test_npc_dialogue_with_complex_personality(self):
        """NPC dialogue handles complex personality descriptions."""
        personality = (
            "An old wizard who has seen empires rise and fall. "
            "Cynical but not cruel, speaks in riddles and proverbs. "
            "Seeks redemption for past mistakes."
        )
        template = PromptTemplates.npc_dialogue(
            npc_name="Elven Sage",
            personality=personality,
            known_info=["Lived 300 years", "Knows lost magic"],
        )
        assert personality in template

    def test_npc_dialogue_multiple_known_facts(self):
        """NPC dialogue includes all provided known facts."""
        known_info = [
            "Has a secret family",
            "Fears the dark",
            "Loves ancient books",
            "Was once a thief",
        ]
        template = PromptTemplates.npc_dialogue(
            npc_name="Zephyr",
            personality="Mysterious",
            known_info=known_info,
        )
        for fact in known_info:
            assert fact in template


class TestPromptTemplatesIntegration:
    """Integration tests for all prompt templates."""

    def test_all_templates_return_strings(self):
        """All prompt templates return string content."""
        dm_prompt = PromptTemplates.dm_system_prompt("World", [], {})
        combat_prompt = PromptTemplates.combat_narration(["Fighter"], "Fighter", [])
        npc_prompt = PromptTemplates.npc_dialogue("NPC", "Neutral", [])
        
        assert isinstance(dm_prompt, str)
        assert isinstance(combat_prompt, str)
        assert isinstance(npc_prompt, str)

    def test_all_templates_produce_non_empty_output(self):
        """All prompt templates produce non-empty output."""
        dm_prompt = PromptTemplates.dm_system_prompt("World", [], {})
        combat_prompt = PromptTemplates.combat_narration(["Fighter"], "Fighter", [])
        npc_prompt = PromptTemplates.npc_dialogue("NPC", "Neutral", [])
        
        assert len(dm_prompt) > 0
        assert len(combat_prompt) > 0
        assert len(npc_prompt) > 0


class TestPromptTemplateFormatting:
    """Tests for prompt template formatting and handling edge cases."""

    def test_dm_prompt_handles_special_characters_in_context(self):
        """DM prompt handles special characters in world context."""
        world_context = "The Temple of L'Zar (The Void) - 5th level"
        template = PromptTemplates.dm_system_prompt(
            world_context=world_context,
            characters=[],
            game_state={},
        )
        # Should not raise an error
        assert isinstance(template, str)

    def test_npc_dialogue_handles_apostrophes_in_name(self):
        """NPC dialogue handles apostrophes in NPC names."""
        npc_name = "D'Zar the Mysterious"
        template = PromptTemplates.npc_dialogue(
            npc_name=npc_name,
            personality="Quiet",
            known_info=[],
        )
        assert npc_name in template

    def test_combat_narration_handles_unicode_characters(self):
        """Combat narration handles unicode in actor names."""
        initiative_order = ["Ëldrick", "Thorn", "Zephyr"]
        template = PromptTemplates.combat_narration(
            initiative_order=initiative_order,
            current_turn="Ëldrick",
            recent_actions=[],
        )
        assert "Ëldrick" in template
