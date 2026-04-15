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


def _strip_action_echo(response: str, player_action: str) -> str:
    """Remove echoed player action from the start of an LLM response.
    
    Smaller models often echo the player's action verbatim, e.g.:
    "You I check my inventory. The cavern..." → "The cavern..."
    "You check my inventory. The cavern..." → "The cavern..."
    """
    if not player_action or not response:
        return response

    action = player_action.strip().rstrip(".")
    text = response.strip()

    # Pattern: "You <exact action>." or "You <exact action>," at start
    for prefix in [f"You {action}", f"You {action.lower()}"]:
        if text.startswith(prefix):
            rest = text[len(prefix):]
            # Strip the connecting punctuation and whitespace
            rest = rest.lstrip(".,;: —–-")
            rest = rest.strip()
            if rest:
                # Capitalize the first letter of the remaining text
                return rest[0].upper() + rest[1:]

    return response

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
        story_bible: str = "",
    ) -> str:
        """Narrate an exploration action.
        
        Args:
            scene: Scene information (name, description, etc.)
            player_action: What the player character is doing
            characters: List of player characters
            world_context: Description of the world
            story_bible: Secret narrative plan for the campaign (optional)
            
        Returns:
            Narration string describing what happens
        """
        try:
            # Build context information
            game_state: dict = {
                "current_scene": scene.get("name", "Unknown"),
                "action": player_action,
            }
            if story_bible:
                game_state["story_bible"] = story_bible

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

            return _strip_action_echo(response.content, player_action)

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

    async def generate_story_bible(
        self,
        campaign_name: str,
        world_context: str = "",
        tone: str = "dark_fantasy",
    ) -> str:
        """Generate a secret story bible for the DM to drive the campaign narrative.

        Called once per campaign and cached in storage. The bible is injected
        into every dm_system_prompt so the DM has a destination and actively
        steers toward it — planting clues, advancing villains, escalating stakes.

        Args:
            campaign_name: Name of the campaign
            world_context: Existing world description (may be empty)
            tone: Narrative tone (dark_fantasy, gritty, comedic, storybook)

        Returns:
            Story bible string (kept secret from players)
        """
        try:
            system_prompt = PromptTemplates.story_bible_generation_prompt(
                campaign_name=campaign_name,
                world_context=world_context,
                tone=tone,
            )
            response = await self._llm.generate(
                messages=[LLMMessage(role="user", content="Generate the story bible now.")],
                system_prompt=system_prompt,
                temperature=0.9,
                max_tokens=800,
            )
            return response.content
        except Exception as e:
            logger.error("Error in generate_story_bible: %s", e)
            return (
                "THE WORLD: Valdris — a realm where the sun sets permanently every winter "
                "solstice, plunging it into a weeks-long dark. The dead grow restless in the dark.\n"
                "THE VILLAIN: Malachar the Undying, a former paladin who discovered the gods "
                "are silent because they are dead. He seeks to replace them with himself — "
                "by completing a ritual that requires 1,000 willing sacrifices.\n"
                "TICKING CLOCK: Malachar's cult has 940 willing followers. They need 60 more. "
                "They are recruiting from desperate towns RIGHT NOW.\n"
                "ACT 1 HOOK: A village healer named Sister Voss has vanished. The players are "
                "asked to find her. She joined the cult willingly — and left a coded message.\n"
                "FORESHADOWING: (1) A silver sun-disk symbol on every cult recruit's wrist. "
                "(2) Villagers whisper 'the quiet god provides'. "
                "(3) Temple records show 12 clerics lost their spells on the same night — 6 months ago.\n"
            )

    async def generate_session_greeting(
        self,
        campaign_name: str,
        characters: list[dict],
        last_summary: str = "",
        world_context: str = "",
    ) -> str:
        """Generate the session-opening greeting and recap.

        Speaks as an old wise wizard DM, recaps the last session, and sets
        the scene for tonight.  On the first session, opens dramatically
        without a recap.

        Args:
            campaign_name: Name of the campaign
            characters: List of player character dicts
            last_summary: Summary from last session (empty = first session)
            world_context: Brief world description

        Returns:
            Greeting narration string
        """
        try:
            system_prompt = PromptTemplates.session_greeting_prompt(
                campaign_name=campaign_name,
                last_summary=last_summary,
                characters=characters,
                world_context=world_context,
            )
            user_message = "Open tonight's session."
            response = await self._llm.generate(
                messages=[LLMMessage(role="user", content=user_message)],
                system_prompt=system_prompt,
                temperature=0.85,
                max_tokens=400,
            )
            # Don't add greeting to persistent history — it's a one-shot preamble
            return response.content
        except Exception as e:
            logger.error("Error in generate_session_greeting: %s", e)
            if last_summary:
                return (
                    f"Welcome back, brave souls. Last we spoke, you faced great trials — "
                    f"{last_summary[:120]}... Tonight, the journey continues. "
                    "Steel yourselves. Destiny waits for no one."
                )
            return (
                "Welcome, adventurers. The world stretches before you, ancient and full of danger. "
                "Your legend begins tonight. What will history remember of you?"
            )

    async def generate_world(
        self,
        theme: str = "dark_fantasy",
        setting: str = "",
        campaign_name: str = "",
        hooks: list[str] | None = None,
    ) -> str:
        """Generate a rich world context for a new campaign.

        Args:
            theme: Tone/theme (dark_fantasy, comedic, gritty, storybook)
            setting: Brief setting description (e.g., 'sunken coastal empire')
            campaign_name: Name of the campaign
            hooks: List of story hooks / major threats

        Returns:
            World context string (stored in campaign's world_state)
        """
        try:
            hook_text = ""
            if hooks:
                hook_text = "\nKey story hooks:\n" + "\n".join(f"- {h}" for h in hooks)

            system_prompt = (
                "You are a world-builder for D&D 5e. Create a vivid, internally consistent "
                f"game world in the {theme} style. Your output will be used as the DM's "
                "world reference — it should cover: the name of the region, its history in "
                "2-3 sentences, the current political / magical situation, 2-3 important "
                "factions with contrasting goals, and 2-3 looming threats. "
                "Be specific and evocative. Avoid generic fantasy clichés. "
                "Keep it under 300 words."
            )
            user_message = (
                f"Campaign: {campaign_name or 'Untitled Campaign'}\n"
                f"Setting: {setting or 'a perilous realm'}{hook_text}"
            )
            response = await self._llm.generate(
                messages=[LLMMessage(role="user", content=user_message)],
                system_prompt=system_prompt,
                temperature=0.9,
                max_tokens=600,
            )
            return response.content
        except Exception as e:
            logger.error("Error in generate_world: %s", e)
            return (
                f"The realm of {setting or 'Valdris'} is a land scarred by ancient wars. "
                "Three factions — the Iron Compact, the Verdant Circle, and the Hollow Court — "
                "vie for dominance while a deeper darkness stirs beneath the earth. "
                "The players have arrived at a crossroads moment in history."
            )

    async def narrate_boss_encounter(
        self,
        boss_name: str,
        boss_description: str,
        arena_features: list[str],
        secondary_objective: str,
        combat_state: dict,
        characters: list[dict],
        player_action: str,
        boss_at_half_hp: bool = False,
    ) -> str:
        """Narrate a boss encounter turn with all 5 dynamic encounter principles.

        Args:
            boss_name: Name of the boss
            boss_description: Personality and abilities summary
            arena_features: Environmental features (pillars, lava, etc.)
            secondary_objective: Mid-fight side objective
            combat_state: Current combat state dict
            characters: Player character list
            player_action: What the player just did
            boss_at_half_hp: True when boss is below 50% HP

        Returns:
            Cinematic boss encounter narration
        """
        try:
            system_prompt = PromptTemplates.boss_encounter(
                boss_name=boss_name,
                boss_description=boss_description,
                arena_features=arena_features,
                secondary_objective=secondary_objective,
                characters=characters,
                round_number=combat_state.get("round_number", 1),
                boss_at_half_hp=boss_at_half_hp,
            )
            round_num = combat_state.get("round_number", 1)
            user_message = f"Round {round_num}: {player_action}"

            messages = self._history.copy()
            messages.append(LLMMessage(role="user", content=user_message))

            response = await self._llm.generate(
                messages=messages,
                system_prompt=system_prompt,
                temperature=0.85,
                max_tokens=400,
            )
            self._add_to_history(
                LLMMessage(role="user", content=user_message),
                LLMMessage(role="assistant", content=response.content),
            )
            return response.content
        except Exception as e:
            logger.error("Error in narrate_boss_encounter: %s", e)
            return FALLBACK_NARRATIONS["combat"]

    async def generate_session_summary(
        self,
        narrative_history: list[str],
        campaign_name: str = "",
    ) -> str:
        """Summarise a completed session for use as next session's recap.

        Args:
            narrative_history: List of narrative events from the session
            campaign_name: Campaign name for context

        Returns:
            2-4 sentence summary of the session
        """
        try:
            history_text = "\n".join(narrative_history[-40:])  # last 40 entries
            system_prompt = (
                "You are summarising a D&D session for the DM's records. "
                "Write a 2-4 sentence summary in past tense covering: where the party went, "
                "the most important event, and how the session ended. "
                "Be specific about names, places, and outcomes. "
                "This will be read aloud at the start of the next session as a recap."
            )
            user_message = (
                f"Campaign: {campaign_name or 'Untitled'}\n\nSession events:\n{history_text}"
            )
            response = await self._llm.generate(
                messages=[LLMMessage(role="user", content=user_message)],
                system_prompt=system_prompt,
                temperature=0.5,
                max_tokens=200,
            )
            return response.content
        except Exception as e:
            logger.error("Error in generate_session_summary: %s", e)
            return "The party ventured forth and faced great challenges. Their deeds shall be remembered."

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
