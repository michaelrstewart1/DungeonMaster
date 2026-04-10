"""
DM Narrator service for D&D 5e AI Dungeon Master.

The narrator orchestrates LLM interactions to produce contextual narration
for the game, maintaining conversation history and using prompt templates
to guide the LLM's responses.
"""

import logging
from typing import Optional

from .base import LLMProvider, LLMMessage, LLMResponse
from .prompts import PromptTemplates

logger = logging.getLogger(__name__)

# Fallback narrations when LLM fails
FALLBACK_NARRATIONS = {
    "exploration": (
        "You take a moment to observe your surroundings. The area seems quiet for now. "
        "What would you like to do next?"
    ),
    "combat": (
        "The encounter intensifies! Your enemies press their advantage. "
        "What is your next move?"
    ),
    "npc": (
        "The NPC regards you thoughtfully before responding. "
        "What do you do?"
    ),
    "environment": (
        "The environment around you feels alive with possibility. "
        "You sense there is more to discover."
    ),
    "scene": (
        "You find yourself in a new location. The air carries unfamiliar scents, "
        "and your eyes adjust to the surroundings."
    ),
}


class DMNarrator:
    """Dungeon Master Narrator for D&D 5e AI.
    
    The narrator uses an LLM provider to generate contextual narration for
    the game. It maintains conversation history for consistency and uses
    prompt templates to guide the LLM's responses.
    """

    def __init__(self, llm: LLMProvider, max_history: int = 20):
        """Initialize the DMNarrator.
        
        Args:
            llm: An LLMProvider instance to use for generating narration
            max_history: Maximum number of messages to maintain in history
        """
        self._llm = llm
        self._max_history = max_history
        self._history: list[LLMMessage] = []

    async def narrate_exploration(
        self,
        scene: dict,
        player_action: str,
        characters: list[dict],
        world_context: str,
    ) -> str:
        """Narrate an exploration action.
        
        Args:
            scene: Scene information (name, description, etc.)
            player_action: What the player character is doing
            characters: List of player characters
            world_context: Description of the world
            
        Returns:
            Narration string describing what happens
        """
        try:
            # Build context information
            game_state = {
                "current_scene": scene.get("name", "Unknown"),
                "action": player_action,
            }

            # Create system prompt
            system_prompt = PromptTemplates.dm_system_prompt(
                world_context=world_context,
                characters=characters,
                game_state=game_state,
            )

            # Create user message
            user_message = (
                f"The party is in {scene.get('name', 'a mysterious place')}. "
                f"Scene: {scene.get('description', 'There is a strange feeling here.')} "
                f"\n\nPlayer Action: {player_action}"
            )

            messages = self._history.copy()
            messages.append(LLMMessage(role="user", content=user_message))

            # Generate narration
            response = await self._llm.generate(
                messages=messages,
                system_prompt=system_prompt,
                temperature=0.8,
                max_tokens=500,
            )

            # Update history
            self._add_to_history(
                LLMMessage(role="user", content=user_message),
                LLMMessage(role="assistant", content=response.content),
            )

            return response.content

        except Exception as e:
            logger.error(f"Error in narrate_exploration: {e}")
            return FALLBACK_NARRATIONS["exploration"]

    async def narrate_combat_action(
        self,
        combat_state: dict,
        action_result: dict,
        characters: list[dict],
    ) -> str:
        """Narrate a combat action.
        
        Args:
            combat_state: Current combat state (round, initiative, current turn)
            action_result: Result of the action (what happened)
            characters: List of characters in combat
            
        Returns:
            Narration string describing the combat action
        """
        try:
            # Extract combat information
            initiative_order = combat_state.get("initiative", [])
            current_turn = combat_state.get("current_turn", "Unknown")
            round_num = combat_state.get("round", 1)

            # Build recent actions
            recent_actions = [
                f"{action_result.get('action', 'Attack')}: "
                f"{action_result.get('description', 'An action occurs')}"
            ]

            # Create combat narration prompt
            combat_prompt = PromptTemplates.combat_narration(
                initiative_order=initiative_order,
                current_turn=current_turn,
                recent_actions=recent_actions,
            )

            # Create user message
            action_text = action_result.get("description", "An action occurs")
            user_message = (
                f"Round {round_num}: {current_turn}'s turn. "
                f"Action: {action_text}"
            )

            messages = self._history.copy()
            messages.append(LLMMessage(role="user", content=user_message))

            # Generate narration
            response = await self._llm.generate(
                messages=messages,
                system_prompt=combat_prompt,
                temperature=0.7,
                max_tokens=300,
            )

            # Update history
            self._add_to_history(
                LLMMessage(role="user", content=user_message),
                LLMMessage(role="assistant", content=response.content),
            )

            return response.content

        except Exception as e:
            logger.error(f"Error in narrate_combat_action: {e}")
            return FALLBACK_NARRATIONS["combat"]

    async def narrate_npc_interaction(
        self,
        npc: dict,
        player_message: str,
        conversation_history: list[LLMMessage],
    ) -> str:
        """Narrate an NPC interaction.
        
        Args:
            npc: NPC information (name, personality, etc.)
            player_message: What the player character says
            conversation_history: Previous messages in the conversation
            
        Returns:
            NPC's response as a narration string
        """
        try:
            npc_name = npc.get("name", "Unknown NPC")
            personality = npc.get("personality", "neutral")
            known_info = npc.get("known_info", [])

            # Create NPC dialogue prompt
            npc_prompt = PromptTemplates.npc_dialogue(
                npc_name=npc_name,
                personality=personality,
                known_info=known_info,
            )

            # Combine conversation history with new message
            messages = conversation_history.copy()
            messages.append(LLMMessage(role="user", content=player_message))

            # Generate response
            response = await self._llm.generate(
                messages=messages,
                system_prompt=npc_prompt,
                temperature=0.8,
                max_tokens=200,
            )

            return response.content

        except Exception as e:
            logger.error(f"Error in narrate_npc_interaction: {e}")
            return FALLBACK_NARRATIONS["npc"]

    async def narrate_environment(
        self,
        scene_description: str,
        player_action: str,
    ) -> str:
        """Narrate an environmental description or interaction.
        
        Args:
            scene_description: Description of the environment
            player_action: What the player is doing with the environment
            
        Returns:
            Narration of the environmental interaction
        """
        try:
            user_message = (
                f"Environment: {scene_description}\n"
                f"Player Action: {player_action}"
            )

            messages = self._history.copy()
            messages.append(LLMMessage(role="user", content=user_message))

            system_prompt = (
                "You are a Dungeon Master describing environmental interactions. "
                "Narrate what happens when the player interacts with their surroundings. "
                "Be vivid and descriptive."
            )

            # Generate narration
            response = await self._llm.generate(
                messages=messages,
                system_prompt=system_prompt,
                temperature=0.8,
                max_tokens=300,
            )

            # Update history
            self._add_to_history(
                LLMMessage(role="user", content=user_message),
                LLMMessage(role="assistant", content=response.content),
            )

            return response.content

        except Exception as e:
            logger.error(f"Error in narrate_environment: {e}")
            return FALLBACK_NARRATIONS["environment"]

    async def describe_scene(self, scene_data: dict) -> str:
        """Generate an initial description for a new scene.
        
        Args:
            scene_data: Information about the scene to describe
            
        Returns:
            Initial scene description
        """
        try:
            scene_name = scene_data.get("name", "A mysterious place")
            scene_description = scene_data.get("description", "")
            features = scene_data.get("features", [])

            # Build feature list
            features_text = ""
            if features:
                features_text = "Notable features: " + ", ".join(features)

            user_message = f"Describe the scene: {scene_name}"

            messages = self._history.copy()
            messages.append(LLMMessage(role="user", content=user_message))

            system_prompt = (
                "You are a Dungeon Master. Provide vivid, immersive descriptions "
                "of the scene when the party enters a new location. Paint a picture "
                "with words, highlighting important details and atmosphere."
            )

            # Generate description
            response = await self._llm.generate(
                messages=messages,
                system_prompt=system_prompt,
                temperature=0.8,
                max_tokens=400,
            )

            # Update history
            self._add_to_history(
                LLMMessage(role="user", content=user_message),
                LLMMessage(role="assistant", content=response.content),
            )

            return response.content

        except Exception as e:
            logger.error(f"Error in describe_scene: {e}")
            return FALLBACK_NARRATIONS["scene"]

    def clear_history(self) -> None:
        """Clear the conversation history."""
        self._history = []

    def _add_to_history(
        self, user_message: LLMMessage, assistant_message: LLMMessage
    ) -> None:
        """Add messages to history, maintaining max_history limit.
        
        Args:
            user_message: The user/player message
            assistant_message: The assistant/LLM response
        """
        self._history.append(user_message)
        self._history.append(assistant_message)

        # Truncate history if it exceeds max length
        # Keep only the most recent messages
        if len(self._history) > self._max_history:
            # Calculate how many messages to remove
            # Remove in pairs (user + assistant)
            messages_to_remove = len(self._history) - self._max_history
            # Round up to nearest even number to maintain user/assistant pairs
            if messages_to_remove % 2 != 0:
                messages_to_remove += 1
            self._history = self._history[messages_to_remove:]
