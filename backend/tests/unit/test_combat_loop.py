"""Combat loop — deterministic rules engine drives live combat."""
import pytest

from app.services.game.combat_loop import (
    combat_over,
    combatant_from_character,
    combatant_from_enemy,
    resolve_player_action,
    run_pending_monster_turns,
    start_encounter,
)


def _char(**overrides) -> dict:
    base = {
        "id": "char-1",
        "name": "Thorin",
        "class_name": "fighter",
        "level": 3,
        "strength": 16,
        "dexterity": 12,
        "hp": 28,
        "max_hp": 28,
        "ac": 16,
    }
    base.update(overrides)
    return base


class TestCombatantBuilders:
    def test_character_combatant_derives_attack_profile(self):
        c = combatant_from_character(_char())
        assert c["is_player"] is True
        assert c["attack_bonus"] == 3 + 2  # STR mod + prof(level 3)
        assert c["damage_dice"] == "1d10+3"
        assert c["initiative_modifier"] == 1  # DEX 12
        assert c["hp"] == 28 and c["ac"] == 16

    def test_caster_uses_casting_stat(self):
        c = combatant_from_character(_char(class_name="wizard", intelligence=17, strength=8))
        assert c["attack_bonus"] == 3 + 2
        assert c["damage_dice"] == "1d10+3"

    def test_enemy_combatant_scales_with_cr(self):
        e = combatant_from_enemy("Goblin", hp=7, ac=15, cr=0.25, index=1)
        assert e["is_player"] is False
        assert e["hp"] == 7
        assert e["attack_bonus"] == 3
        e2 = combatant_from_enemy("Ogre", hp=59, ac=11, cr=2, index=2)
        assert e2["attack_bonus"] == 4
        assert e2["damage_dice"] == "1d6+2"


class TestStartEncounter:
    def test_initiative_includes_everyone(self):
        state = start_encounter([_char()], [{"name": "Goblin", "hp": 7, "ac": 15, "cr": 0.25, "count": 2}])
        assert len(state["combatants"]) == 3
        assert len(state["initiative_order"]) == 3
        assert state["round_number"] == 1
        names = state["initiative_order"]
        assert "Thorin" in names
        # Duplicate monsters are numbered
        assert any(n.startswith("Goblin") for n in names)
        assert len(set(names)) == 3

    def test_initiative_sorted_descending(self):
        state = start_encounter([_char()], [{"name": "Goblin", "hp": 7, "ac": 15, "cr": 0.25, "count": 3}])
        inits = [c["initiative"] for c in state["combatants"]]
        assert inits == sorted(inits, reverse=True)


class TestPendingMonsterTurns:
    def test_monster_first_initiative_no_longer_deadlocks(self):
        """If monsters win initiative, run_pending_monster_turns advances the
        fight to the first player's turn — previously combat stalled forever
        because phones only act on a player turn and monster turns only ran
        inside resolve_player_action."""
        state = start_encounter(
            [_char()], [{"name": "Goblin", "hp": 7, "ac": 15, "cr": 0.25, "count": 2}]
        )
        result = run_pending_monster_turns(state)
        assert "events" in result and "combat_over" in result
        if not result["combat_over"]:
            current = state["combatants"][state["current_turn_index"]]
            assert current["is_player"] is True

    def test_player_first_initiative_is_untouched(self):
        state = start_encounter(
            [_char()], [{"name": "Goblin", "hp": 7, "ac": 15, "cr": 0.25}]
        )
        # Force a player-first order
        state["combatants"].sort(key=lambda e: not e["is_player"])
        state["current_turn_index"] = 0
        result = run_pending_monster_turns(state)
        assert result["events"] == []
        assert state["current_turn_index"] == 0
        assert result["combat_over"] is False


class TestResolveAction:
    def _state_player_first(self):
        """Deterministic state: player at index 0, one weak goblin."""
        player = combatant_from_character(_char())
        player["initiative"] = 20
        goblin = combatant_from_enemy("Goblin", hp=1, ac=1, cr=0.25, index=1)
        goblin["initiative"] = 5
        return {
            "round_number": 1,
            "current_turn_index": 0,
            "initiative_order": [player["name"], goblin["name"]],
            "combatants": [player, goblin],
            "log": [],
        }

    def test_attack_kills_weak_goblin_and_ends_combat(self):
        state = self._state_player_first()
        # AC 1 → guaranteed hit unless nat 1; retry a few times to dodge fumbles
        for _ in range(20):
            result = resolve_player_action(state, "char-1", "attack", "enemy-1")
            if result.get("combat_over"):
                break
            state = self._state_player_first()
        assert result["combat_over"] is True
        assert result["victory"] is True
        assert result["xp_awarded"] == 25
        assert any("falls" in ev or "Victory" in ev for ev in result["events"])

    def test_wrong_turn_rejected_when_other_player_up(self):
        state = self._state_player_first()
        # Add a second player who is currently up
        other = combatant_from_character(_char(id="char-2", name="Elara"))
        other["initiative"] = 25
        state["combatants"].insert(0, other)
        state["initiative_order"].insert(0, "Elara")
        result = resolve_player_action(state, "char-1", "attack", "enemy-1")
        assert "turn" in result["error"]

    def test_unknown_actor_rejected(self):
        state = self._state_player_first()
        assert "Unknown" in resolve_player_action(state, "nope", "attack")["error"]

    def test_monster_cannot_act_via_endpoint(self):
        state = self._state_player_first()
        state["current_turn_index"] = 1
        result = resolve_player_action(state, "enemy-1", "attack")
        assert result["error"]

    def test_dodge_passes_turn_and_monster_acts(self):
        state = self._state_player_first()
        state["combatants"][1]["hp"] = 30  # goblin survives
        result = resolve_player_action(state, "char-1", "dodge")
        assert result["combat_over"] is False
        # The goblin took its turn (attack event logged) and play returned to the player
        assert result["next_turn"] == "Thorin"
        assert len(result["events"]) >= 2
        assert state["round_number"] == 2

    def test_heal_restores_hp(self):
        state = self._state_player_first()
        state["combatants"][0]["hp"] = 5
        state["combatants"][1]["hp"] = 30
        result = resolve_player_action(state, "char-1", "heal", "char-1")
        assert result.get("error") is None
        assert any("heals Thorin" in ev for ev in result["events"])

    def test_unconscious_player_rolls_death_save(self):
        state = self._state_player_first()
        state["combatants"][0]["hp"] = 0
        state["combatants"][1]["hp"] = 30
        result = resolve_player_action(state, "char-1", "attack", "enemy-1")
        assert any("death save" in ev.lower() or "stabilize" in ev.lower() or "consciousness" in ev.lower() or "succumb" in ev.lower() or "failures" in ev.lower() for ev in result["events"])


class TestCombatOver:
    def test_all_monsters_dead_is_victory(self):
        state = {
            "combatants": [
                {**combatant_from_character(_char()), "hp": 10},
                {**combatant_from_enemy("Goblin", 7, 15, 0.25, 1), "hp": 0, "is_alive": False},
            ]
        }
        assert combat_over(state) == (True, True)

    def test_all_players_dead_is_defeat(self):
        state = {
            "combatants": [
                {**combatant_from_character(_char()), "hp": 0, "is_alive": False},
                {**combatant_from_enemy("Goblin", 7, 15, 0.25, 1), "hp": 7},
            ]
        }
        assert combat_over(state) == (True, False)

    def test_unconscious_player_keeps_combat_going(self):
        state = {
            "combatants": [
                {**combatant_from_character(_char()), "hp": 0},  # dying, not dead
                {**combatant_from_enemy("Goblin", 7, 15, 0.25, 1), "hp": 7},
            ]
        }
        assert combat_over(state) == (False, False)

    def test_ongoing(self):
        state = {
            "combatants": [
                {**combatant_from_character(_char()), "hp": 10},
                {**combatant_from_enemy("Goblin", 7, 15, 0.25, 1), "hp": 7},
            ]
        }
        assert combat_over(state) == (False, False)
