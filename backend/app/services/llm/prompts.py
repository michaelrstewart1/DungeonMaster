"""
Prompt templates for D&D 5e AI Dungeon Master interactions.

This module provides templates for various LLM interactions:
- DM system prompt with world context and character information
- Combat narration with initiative and turn tracking
- NPC dialogue with personality and context
"""


class PromptTemplates:
    """Collection of prompt templates for D&D 5e Dungeon Master interactions."""

    @staticmethod
    def dm_system_prompt(
        world_context: str,
        characters: list[dict],
        game_state: dict,
    ) -> str:
        """Create a system prompt for the Dungeon Master role.
        
        The DM prompt establishes the context for the game world and the
        player characters, guiding the LLM to make appropriate narrative
        and mechanical decisions.
        
        Args:
            world_context: Description of the game world, setting, and environment
            characters: List of character dicts with name, class, level, and other info
            game_state: Current game state including location, time, weather, etc.
            
        Returns:
            System prompt string for the Dungeon Master
        """
        prompt = "You are an experienced Dungeon Master for D&D 5th Edition.\n\n"

        # Add world context
        prompt += "## World Context\n"
        prompt += f"{world_context}\n\n"

        # Add character information
        if characters:
            prompt += "## Player Characters\n"
            for char in characters:
                name = char.get("name", "Unknown")
                char_class = char.get("class", "Unknown")
                level = char.get("level", "Unknown")
                prompt += f"- {name}: Level {level} {char_class}\n"
                
                # Add other character details if available
                if "hp" in char:
                    prompt += f"  HP: {char['hp']}\n"
                if "race" in char:
                    prompt += f"  Race: {char['race']}\n"
            prompt += "\n"

        # Add current game state
        if game_state:
            prompt += "## Current Game State\n"
            for key, value in game_state.items():
                # Format the key nicely (capitalize, replace underscores with spaces)
                formatted_key = key.replace("_", " ").title()
                prompt += f"- {formatted_key}: {value}\n"
            prompt += "\n"

        # Add DM instructions
        prompt += (
            "## Your Role\n"
            "Narrate engaging and immersive game experiences. Describe the world vividly, "
            "manage encounters, and respond to player actions. Stay true to the rules of "
            "D&D 5e while prioritizing player agency and fun. Be fair and consistent with "
            "established world details. Create dramatic tension and memorable moments.\n"
        )

        return prompt

    @staticmethod
    def combat_narration(
        initiative_order: list[str],
        current_turn: str,
        recent_actions: list[str],
    ) -> str:
        """Create a prompt for combat narration.
        
        The combat prompt guides the LLM to narrate combat action clearly,
        with proper tracking of initiative, turns, and action descriptions.
        
        Args:
            initiative_order: List of combatants in initiative order
            current_turn: Name of the combatant whose turn it is
            recent_actions: List of recent actions in the combat
            
        Returns:
            Prompt string for combat narration
        """
        prompt = "You are narrating a D&D 5e combat encounter.\n\n"

        # Add initiative information
        prompt += "## Initiative Order\n"
        for i, actor in enumerate(initiative_order, 1):
            if actor == current_turn:
                prompt += f"{i}. **{actor}** ← CURRENT TURN\n"
            else:
                prompt += f"{i}. {actor}\n"
        prompt += "\n"

        # Add recent actions if available
        if recent_actions:
            prompt += "## Recent Actions in Combat\n"
            for action in recent_actions:
                prompt += f"- {action}\n"
            prompt += "\n"

        # Add combat instructions
        prompt += (
            "## Instructions\n"
            f"It is currently {current_turn}'s turn. Narrate the action vividly and clearly. "
            "Describe how attacks land or miss, how spells manifest, and how the battlefield "
            "evolves. Make the action feel tense and dramatic. After narrating the action, "
            "be ready to inform of any ability checks or rolls needed.\n"
        )

        return prompt

    @staticmethod
    def npc_dialogue(
        npc_name: str,
        personality: str,
        known_info: list[str],
    ) -> str:
        """Create a prompt for NPC dialogue.
        
        The NPC dialogue prompt guides the LLM to roleplay as a specific NPC
        with consistent personality and knowledge.
        
        Args:
            npc_name: Name of the NPC
            personality: Description of the NPC's personality and traits
            known_info: List of facts known about the NPC
            
        Returns:
            Prompt string for NPC dialogue
        """
        prompt = f"You are roleplay {npc_name}.\n\n"

        # Add personality information
        prompt += "## Character\n"
        prompt += f"**Name:** {npc_name}\n"
        prompt += f"**Personality:** {personality}\n"

        # Add known information
        if known_info:
            prompt += "\n## Known Information\n"
            for info in known_info:
                prompt += f"- {info}\n"

        # Add dialogue instructions
        prompt += (
            "\n## Your Role\n"
            f"Respond as {npc_name} would, staying true to their personality and motivations. "
            "Be authentic to their character. Use their perspective and knowledge when responding. "
            "Don't break character. Make the dialogue feel natural and engaging.\n"
        )

        return prompt
