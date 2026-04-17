"""
Turn Manager for D&D 5e AI Dungeon Master.

Manages the turn-by-turn game loop, processing player actions through
the rules engine and narrator to produce narrated game results.
"""

from dataclasses import dataclass
from typing import Optional
from app.services.rules.engine import RulesEngine, ActionResult
from app.services.rules.combat import Combatant
from app.services.rules.spells import Spell, SpellSchool, SpellTarget
from app.services.llm.narrator import DMNarrator


@dataclass
class TurnResult:
    """Result of processing a single turn."""
    turn_number: int
    action_result: Optional[ActionResult]
    narration: str
    phase: str = "active"


class TurnManager:
    """Manages turn-by-turn game progression."""

    def __init__(self, rules_engine: RulesEngine, narrator: DMNarrator):
        """
        Initialize the TurnManager.
        
        Args:
            rules_engine: RulesEngine for resolving actions
            narrator: DMNarrator for generating narration
        """
        self.rules_engine = rules_engine
        self.narrator = narrator
        self.turn_number = 0
        self.combatants: list[Combatant] = []
        self.current_combatant_index = 0
        self.combat_round = 0

    async def process_player_action(self, action: dict, session_history: list[str] | None = None) -> TurnResult:
        """
        Process a player action through the full pipeline.
        
        Args:
            action: Action dict with type and relevant fields
            
        Returns:
            TurnResult with action resolution and narration
        """
        self.turn_number += 1
        action_type = action.get("type", "")
        action_result = None

        # Resolve the action based on type
        if action_type == "attack":
            action_result = await self._handle_attack(action)
        elif action_type == "cast_spell":
            action_result = await self._handle_spell(action)
        elif action_type == "ability_check":
            action_result = await self._handle_ability_check(action)
        elif action_type == "move":
            action_result = await self._handle_move(action)
        elif action_type == "interact":
            action_result = await self._handle_interact(action)
        elif action_type == "speak":
            action_result = await self._handle_speak(action)
        else:
            action_result = None

        # Get narration
        narration = await self._get_narration(action, action_result, session_history)

        turn_result = TurnResult(
            turn_number=self.turn_number,
            action_result=action_result,
            narration=narration,
            phase="combat" if self.combatants else "exploration"
        )

        return turn_result

    def get_current_turn_info(self) -> dict:
        """
        Get information about the current turn.
        
        Returns:
            Dict with turn info (turn_number, current_combatant, etc)
        """
        info = {
            "turn_number": self.turn_number,
            "phase": "combat" if self.combatants else "exploration",
        }

        if self.combatants:
            info["current_combatant"] = self.combatants[self.current_combatant_index].name
            info["round"] = self.combat_round
            info["combatants"] = [
                {
                    "name": c.name,
                    "hp": c.hp,
                    "max_hp": c.max_hp,
                    "is_alive": c.is_alive
                }
                for c in self.combatants
            ]

        return info

    async def _handle_attack(self, action: dict) -> ActionResult:
        """Handle an attack action."""
        if not self.combatants:
            return ActionResult(
                action_type="attack",
                success=False,
                description="No combat in progress."
            )

        attacker = self.combatants[self.current_combatant_index]
        target_id = action.get("target_id", "")
        
        # Find target
        target = None
        for c in self.combatants:
            if c.id == target_id:
                target = c
                break

        if not target:
            return ActionResult(
                action_type="attack",
                success=False,
                description=f"Target {target_id} not found."
            )

        attack_bonus = action.get("attack_bonus", 0)
        damage_dice = action.get("damage_dice", "1d8")
        damage_type = action.get("damage_type", "slashing")

        result = self.rules_engine.resolve_attack(
            attacker=attacker,
            target=target,
            attack_bonus=attack_bonus,
            damage_dice=damage_dice,
            damage_type=damage_type
        )

        # Apply damage if hit
        if result.success and result.damage_dealt > 0:
            damage_applied = self.rules_engine.apply_damage(
                target=target,
                damage=result.damage_dealt,
                damage_type=damage_type
            )
            result.damage_dealt = damage_applied

        return result

    async def _handle_spell(self, action: dict) -> ActionResult:
        """Handle a spell casting action."""
        spell_name = action.get("spell_name", "")
        
        # Create a basic spell for testing
        spell = Spell(
            name=spell_name,
            level=1,
            school=SpellSchool.EVOCATION,
            casting_time="1 action",
            range_ft=120,
            duration="Instantaneous",
            target=SpellTarget.CREATURE,
            damage_dice="1d4+1"
        )

        from app.services.rules.spells import SpellSlots
        slots = SpellSlots.for_full_caster(3)

        result = self.rules_engine.resolve_spell(
            spell=spell,
            slots=slots,
            caster_level=3,
            spell_save_dc=12
        )

        return result

    async def _handle_ability_check(self, action: dict) -> ActionResult:
        """Handle an ability check action."""
        ability = action.get("ability", "strength")
        dc = action.get("dc", 10)
        
        # Map ability to modifier (simplified - assuming +2 for now)
        ability_mod = action.get("modifier", 2)
        proficiency = action.get("proficiency", 0)
        advantage = action.get("advantage", False)
        disadvantage = action.get("disadvantage", False)

        result = self.rules_engine.resolve_ability_check(
            ability_mod=ability_mod,
            dc=dc,
            proficiency=proficiency,
            advantage=advantage,
            disadvantage=disadvantage
        )

        return result

    async def _handle_move(self, action: dict) -> ActionResult:
        """Handle a move action."""
        direction = action.get("direction", "north")
        
        return ActionResult(
            action_type="move",
            success=True,
            description=f"You move {direction}."
        )

    async def _handle_interact(self, action: dict) -> ActionResult:
        """Handle an interact action."""
        obj = action.get("object", "something")
        
        return ActionResult(
            action_type="interact",
            success=True,
            description=f"You interact with the {obj}."
        )

    async def _handle_speak(self, action: dict) -> ActionResult:
        """Handle a speak action."""
        text = action.get("text", "")
        
        return ActionResult(
            action_type="speak",
            success=True,
            description=f"You say: \"{text}\""
        )

    async def _get_narration(self, action: dict, action_result: Optional[ActionResult], session_history: list[str] | None = None) -> str:
        """Get narration from the DMNarrator."""
        try:
            # Build context for narration
            scene = {
                "name": "The Adventure",
                "description": "A scene unfolds in the game world."
            }

            player_action = action.get("type", "unknown action")
            if action_result:
                player_action = action_result.description

            characters = []
            world_context = "The world of adventure awaits."

            # Use the narrator to generate narration
            narration = await self.narrator.narrate_exploration(
                scene=scene,
                player_action=player_action,
                characters=characters,
                world_context=world_context,
                session_history=session_history,
            )

            return narration
        except Exception:
            # Fallback if narrator fails
            if action_result:
                return action_result.description
            return "The scene continues..."
