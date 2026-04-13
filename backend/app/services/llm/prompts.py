"""
Prompt templates for D&D 5e AI Dungeon Master interactions.

This module provides templates for various LLM interactions:
- DM system prompt with world context, tone, and character information
- Combat narration with initiative, creative actions, and nuanced outcomes
- NPC dialogue with personality, secrets, and relationship tracking
- Player join/leave transitions
- Skill check results with degrees of success
- Creative/environmental action resolution
"""

# Tone descriptions injected into the DM system prompt
_TONES: dict[str, str] = {
    "dark_fantasy": (
        "You speak with gravitas and an air of dark mystery. Descriptions are vivid, "
        "atmospheric, and sometimes unsettling. The world is beautiful but dangerous — "
        "shadows hide terrible things and even victories come at a cost. Use evocative, "
        "slightly poetic language. Think Gothic horror meets high fantasy."
    ),
    "comedic": (
        "You are a witty, irreverent DM who loves absurd situations and well-timed humor. "
        "NPCs have quirky personalities and the world is full of ridiculous details. You still "
        "run serious encounters, but there's always a comedic twist. Think Terry Pratchett "
        "meets D&D. Keep it fun and lighthearted."
    ),
    "gritty": (
        "You are a no-nonsense, realistic DM. The world is harsh and unforgiving. Resources "
        "are scarce, enemies are deadly, and consequences are real. Descriptions are terse and "
        "impactful. Think Game of Thrones meets The Witcher. Survival matters."
    ),
    "storybook": (
        "You are a warm, enchanting storyteller. The world is wondrous and magical, full of "
        "fairy-tale imagery and gentle wonder. Even danger feels like an adventure. Descriptions "
        "are colorful and imaginative. Perfect for families and new players."
    ),
}

# Narration length guidance
_NARRATION_MODES: dict[str, str] = {
    "cinematic": (
        "Use rich, detailed descriptions — sounds, smells, lighting, NPC expressions. "
        "Aim for 3-5 sentences for routine interactions and more for major moments."
    ),
    "fast": (
        "Be punchy and action-focused. One or two vivid details, then move on. "
        "Aim for 1-3 sentences. Players want action, not prose."
    ),
}


class PromptTemplates:
    """Collection of prompt templates for D&D 5e Dungeon Master interactions."""

    @staticmethod
    def dm_system_prompt(
        world_context: str,
        characters: list[dict],
        game_state: dict,
        tone: str = "dark_fantasy",
        narration_mode: str = "cinematic",
    ) -> str:
        """Create a system prompt for the Dungeon Master role.

        The DM prompt establishes the context for the game world and the
        player characters, guiding the LLM to make appropriate narrative
        and mechanical decisions.

        Args:
            world_context: Description of the game world, setting, and environment
            characters: List of character dicts with name, class, level, and other info
            game_state: Current game state including location, time, weather, etc.
            tone: Narrative tone — one of dark_fantasy, comedic, gritty, storybook
            narration_mode: Response length — cinematic (rich) or fast (punchy)

        Returns:
            System prompt string for the Dungeon Master
        """
        tone_text = _TONES.get(tone, _TONES["dark_fantasy"])
        mode_text = _NARRATION_MODES.get(narration_mode, _NARRATION_MODES["cinematic"])

        prompt = "You are an experienced Dungeon Master for D&D 5th Edition.\n\n"

        # Tone & style
        prompt += "## Tone & Style\n"
        prompt += f"{tone_text}\n\n"
        prompt += "## Narration Style\n"
        prompt += f"{mode_text}\n\n"

        # Core DM principles
        prompt += (
            "## Core DM Principles\n"
            "- **Everything is interactable**: players can attempt literally anything. "
            "Never say 'you can't do that' — interpret the attempt, call for an appropriate "
            "check if needed, and deliver interesting consequences.\n"
            "- **Creative combat**: when players describe inventive actions ('I swing from "
            "the chandelier', 'I throw sand in his eyes'), embrace it. Assign a fair check "
            "and reward creativity with dramatic results.\n"
            "- **Failure is fun**: failed rolls create new story threads, not dead ends. "
            "A failed stealth roll starts a chase; a failed persuasion spreads rumors. "
            "Make failure interesting.\n"
            "- **Degrees of success**: beyond pass/fail, consider partial success "
            "(barely meets DC → success with complication), strong success (beat DC by 5+ → "
            "clean win with a bonus), and critical failure (nat 1 → entertaining, not punishing).\n"
            "- **Smart NPCs**: every NPC has goals, fears, and secrets. They can lie, betray, "
            "form alliances, and remember past player behavior. Word spreads.\n"
            "- **Living world**: events happen whether players are involved or not. Time of "
            "day matters, factions pursue their own agendas, consequences ripple outward.\n"
            "- **Enforce rules lightly**: fun and story come first. Only call for rolls when "
            "the outcome is uncertain AND interesting. Never roll for trivial actions.\n\n"
        )

        # World context
        prompt += "## World Context\n"
        prompt += f"{world_context}\n\n"

        # Character information
        if characters:
            prompt += "## Player Characters\n"
            for char in characters:
                name = char.get("name", "Unknown")
                char_class = char.get("class", "Unknown")
                level = char.get("level", "Unknown")
                prompt += f"- {name}: Level {level} {char_class}\n"
                if "hp" in char:
                    prompt += f"  HP: {char['hp']}\n"
                if "race" in char:
                    prompt += f"  Race: {char['race']}\n"
                if "ac" in char:
                    prompt += f"  AC: {char['ac']}\n"
            prompt += "\n"

        # Current game state
        if game_state:
            prompt += "## Current Game State\n"
            for key, value in game_state.items():
                formatted_key = key.replace("_", " ").title()
                prompt += f"- {formatted_key}: {value}\n"
            prompt += "\n"

        prompt += (
            "## Your Role\n"
            "Narrate engaging, immersive experiences. Respond to player actions with vivid "
            "descriptions, manage encounters, and keep the story moving. Stay consistent with "
            "established world details. Create dramatic tension and memorable moments. "
            "Prioritize player agency and fun above strict rule adherence.\n"
        )

        return prompt

    @staticmethod
    def combat_narration(
        initiative_order: list[str],
        current_turn: str,
        recent_actions: list[str],
        round_number: int = 1,
    ) -> str:
        """Create a prompt for combat narration.

        The combat prompt guides the LLM to narrate combat action clearly,
        with proper tracking of initiative, turns, and action descriptions.

        Args:
            initiative_order: List of combatants in initiative order
            current_turn: Name of the combatant whose turn it is
            recent_actions: List of recent actions in the combat
            round_number: Current combat round number

        Returns:
            Prompt string for combat narration
        """
        prompt = f"You are narrating Round {round_number} of a D&D 5e combat encounter.\n\n"

        # Initiative order
        prompt += "## Initiative Order\n"
        for i, actor in enumerate(initiative_order, 1):
            marker = " ← CURRENT TURN" if actor == current_turn else ""
            prompt += f"{i}. {actor}{marker}\n"
        prompt += "\n"

        # Recent actions
        if recent_actions:
            prompt += "## Recent Actions\n"
            for action in recent_actions:
                prompt += f"- {action}\n"
            prompt += "\n"

        prompt += (
            "## Instructions\n"
            f"It is {current_turn}'s turn. Narrate the action vividly and dramatically. "
            "Describe how attacks land or miss, how spells manifest, how the battlefield "
            "evolves. Make it tense and cinematic — paint the chaos of combat. "
            "Reward creative or unusual actions with spectacular results. "
            "If the action fails, make the failure entertaining rather than frustrating. "
            "After narrating, indicate any follow-up rolls or reactions needed.\n"
        )

        return prompt

    @staticmethod
    def npc_dialogue(
        npc_name: str,
        personality: str,
        known_info: list[str],
        goals: str = "",
        fears: str = "",
        secrets: str = "",
        relationship_to_party: str = "neutral",
    ) -> str:
        """Create a prompt for NPC dialogue.

        The NPC dialogue prompt guides the LLM to roleplay as a specific NPC
        with consistent personality, hidden motivations, and knowledge.

        Args:
            npc_name: Name of the NPC
            personality: Description of the NPC's personality and traits
            known_info: List of facts the party knows about the NPC
            goals: What the NPC wants (can be hidden from party)
            fears: What the NPC is afraid of (can drive behavior)
            secrets: Things the NPC is hiding (revealed only if appropriate)
            relationship_to_party: How the NPC feels about the party

        Returns:
            Prompt string for NPC dialogue
        """
        prompt = f"You are roleplaying as {npc_name}.\n\n"

        prompt += "## Character\n"
        prompt += f"**Name:** {npc_name}\n"
        prompt += f"**Personality:** {personality}\n"
        prompt += f"**Relationship to party:** {relationship_to_party}\n"

        if goals:
            prompt += f"**Goals:** {goals}\n"
        if fears:
            prompt += f"**Fears:** {fears}\n"
        if secrets:
            prompt += f"**Secrets (don't reveal unless dramatically appropriate):** {secrets}\n"

        if known_info:
            prompt += "\n## What the Party Knows About You\n"
            for info in known_info:
                prompt += f"- {info}\n"

        prompt += (
            "\n## Your Role\n"
            f"Respond as {npc_name} would — authentic to their personality, goals, and fears. "
            "You may lie, deflect, or reveal partial truths based on your relationship with the party. "
            "You remember previous interactions and hold grudges or favors accordingly. "
            "Don't break character. Make the dialogue feel natural and alive.\n"
        )

        return prompt

    @staticmethod
    def player_join(
        character_name: str,
        character_class: str,
        character_race: str,
        current_scene: str = "",
    ) -> str:
        """Create a prompt for introducing a new player mid-session.

        Args:
            character_name: The new character's name
            character_class: The character's D&D class
            character_race: The character's race
            current_scene: Brief description of what's currently happening

        Returns:
            Prompt string for the join narration
        """
        prompt = (
            f"A new adventurer is joining the party mid-session!\n\n"
            f"**New Character:** {character_name}, a {character_race} {character_class}\n"
        )

        if current_scene:
            prompt += f"**Current Scene:** {current_scene}\n"

        prompt += (
            "\n## Instructions\n"
            f"Smoothly introduce {character_name} into the current scene in a way that feels "
            "natural and exciting. Options include: they were already present (a local, a fellow "
            "traveler), they arrive dramatically (crash through a door, emerge from shadows, fall "
            "from the sky), they were trapped and the party just freed them, or they've been "
            "shadowing the party and finally reveal themselves.\n\n"
            "Make the new player feel immediately welcome and involved. Keep it brief — the party "
            "should want to keep moving after the introduction.\n"
        )

        return prompt

    @staticmethod
    def player_leave(
        character_name: str,
        character_class: str,
        current_scene: str = "",
    ) -> str:
        """Create a prompt for writing out a departing player mid-session.

        Args:
            character_name: The departing character's name
            character_class: The character's D&D class
            current_scene: Brief description of what's currently happening

        Returns:
            Prompt string for the departure narration
        """
        prompt = (
            f"A player needs to leave the game. Their character is "
            f"{character_name} ({character_class}).\n"
        )

        if current_scene:
            prompt += f"**Current Scene:** {current_scene}\n"

        prompt += (
            "\n## Instructions\n"
            f"Smoothly write {character_name} out of the current scene in a way that:\n"
            "- Does NOT kill or permanently harm the character\n"
            "- Feels natural given the situation (stays behind to guard, goes to scout ahead, "
            "receives an urgent message, needs to tend to a wound)\n"
            "- Leaves the door open for them to return next session\n"
            "- Doesn't disrupt the current action for the remaining players\n\n"
            "Keep it brief. One or two sentences, then move focus back to the remaining party.\n"
        )

        return prompt

    @staticmethod
    def skill_check_result(
        character_name: str,
        skill: str,
        dc: int,
        roll_total: int,
        action_attempted: str,
    ) -> str:
        """Create a prompt for narrating a skill check result with degrees of success.

        Args:
            character_name: Name of the character who rolled
            skill: The skill or ability used (e.g., 'Perception', 'Stealth')
            dc: The difficulty class of the check
            roll_total: The total result of the roll (including modifiers)
            action_attempted: What the character was trying to do

        Returns:
            Prompt string for skill check narration
        """
        difference = roll_total - dc

        if roll_total == 1:
            outcome = "CRITICAL FAILURE (natural 1)"
            guidance = (
                "Something goes spectacularly wrong — but make it entertaining, not just punishing. "
                "The failure should create a new interesting situation or complication."
            )
        elif difference >= 10:
            outcome = f"EXCEPTIONAL SUCCESS (beat DC by {difference})"
            guidance = (
                "The character succeeds beyond all expectation. Give them a significant bonus "
                "or extra information/advantage beyond what they asked for."
            )
        elif difference >= 5:
            outcome = f"CLEAN SUCCESS (beat DC by {difference})"
            guidance = "The character succeeds cleanly with no complications."
        elif difference >= 0:
            outcome = f"BARE SUCCESS (met DC exactly or by {difference})"
            guidance = (
                "The character succeeds, but with a minor complication or cost. "
                "They get what they wanted, but something small goes slightly wrong."
            )
        elif difference >= -3:
            outcome = f"NEAR MISS (missed DC by {abs(difference)})"
            guidance = (
                "Partial success — the character achieves something, but not fully what they intended. "
                "Or: they succeed but at a significant cost or with a notable complication."
            )
        else:
            outcome = f"FAILURE (missed DC by {abs(difference)})"
            guidance = (
                "The character fails — but make the failure create a new story situation rather "
                "than just blocking progress. What new problem or complication does this create?"
            )

        prompt = (
            f"## Skill Check Result\n"
            f"**Character:** {character_name}\n"
            f"**Action:** {action_attempted}\n"
            f"**Skill/Ability:** {skill}\n"
            f"**DC:** {dc} | **Roll:** {roll_total} → **{outcome}**\n\n"
            f"## Narration Guidance\n"
            f"{guidance}\n\n"
            f"Narrate the result vividly. Make {character_name}'s attempt feel dramatic and "
            f"consequential regardless of success or failure.\n"
        )

        return prompt

    @staticmethod
    def creative_action(
        character_name: str,
        action_description: str,
        environment: str = "",
    ) -> str:
        """Create a prompt for resolving a creative or unusual player action.

        Used when a player attempts something outside normal game mechanics —
        using the environment, improvised weapons, clever tricks, etc.

        Args:
            character_name: Name of the character attempting the action
            action_description: What the player said they want to do
            environment: Description of the current environment/scene

        Returns:
            Prompt string for creative action resolution
        """
        prompt = (
            f"## Creative Action\n"
            f"**Character:** {character_name}\n"
            f"**Attempted Action:** {action_description}\n"
        )

        if environment:
            prompt += f"**Environment:** {environment}\n"

        prompt += (
            "\n## Instructions\n"
            "This is a creative, unconventional action. Your job is to:\n"
            "1. Determine if it's plausible given the environment and circumstances\n"
            "2. Decide what skill check (if any) is appropriate — or if it just works\n"
            "3. Consider the risk/reward: creative actions should be rewarded when clever\n"
            "4. Narrate the attempt and outcome dramatically\n\n"
            "Never refuse a creative attempt outright. If it's implausible, it fails "
            "entertainingly. If it's clever and plausible, reward the creativity with "
            "a spectacular result. Make the player feel like a genius or a lovable fool — "
            "never just blocked.\n"
        )

        return prompt
