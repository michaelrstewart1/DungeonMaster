"""Combat loop — deterministic rules engine drives live combat."""
import json

import pytest

from app.services.game.combat_loop import (
    apply_hp_text,
    classify_combat_text,
    combat_over,
    combat_prompt_brief,
    combatant_from_character,
    combatant_from_enemy,
    correct_borrowed_advantage,
    current_combatant,
    prepare_player_facing_narration,
    resolve_player_action,
    resolve_waiting_monster_turn,
    run_pending_monster_turns,
    settle_narrated_monster_turn,
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

    def test_initiative_totals_come_from_dice_not_seat_order(self, monkeypatch):
        """Order and published totals follow the d20, not 3,2,1 placeholders."""
        from app.services.dice import DiceResult

        totals = [10, 5, 19]

        class FixedRoller:
            def __init__(self, *args, **kwargs):
                self.i = 0

            def roll(self, notation):
                total = totals[self.i]
                self.i += 1
                return DiceResult(notation=notation, rolls=[total], modifier=0, total=total)

        monkeypatch.setattr("app.services.game.combat_loop.DiceRoller", FixedRoller)
        state = start_encounter(
            [_char()], [{"name": "Goblin", "hp": 7, "ac": 15, "cr": 0.25, "count": 2}]
        )
        # DEX 12 and the goblin modifier are both +1, so totals are roll+1.
        assert [c["initiative"] for c in state["combatants"]] == [20, 11, 6]
        assert state["initiative_order"] == ["Goblin 2", "Thorin", "Goblin"]
        assert state["log"][0] == (
            "Initiative: Goblin 2 20 (d20+1), Thorin 11 (d20+1), Goblin 6 (d20+1)"
        )
        assert "roll for initiative" not in state["log"][0].lower()


class TestClassifyCombatText:
    def test_typed_attack_and_button_label_match(self):
        assert classify_combat_text("Kael fires his shortbow at the tall robed leader.") == "attack"
        assert classify_combat_text("⚔️ Attack") == "attack"
        assert classify_combat_text("🛡️ Defend") == "dodge"
        assert classify_combat_text("💊 Use Potion") == "heal"

    def test_dice_report_is_not_an_attack(self):
        assert classify_combat_text("🎲 Kael Shadowstep rolls d20: 15") == "roll"
        assert classify_combat_text("I look around the chamber") is None

    def test_hp_report_is_not_an_attack(self):
        report = "Thorne takes 14 damage (11 slashing + 3 lightning) and is now at 20 of 34 HP."
        assert classify_combat_text(report) is None


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
        state["initiative_order"] = [c["name"] for c in state["combatants"]]
        state["current_turn_index"] = 0
        state["current_turn_id"] = state["combatants"][0]["id"]
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
        assert "It is now Thorin's turn." in result["events"]
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


def _legion_fight():
    player = combatant_from_character(_char(
        id="kael", name="Kael Shadowstep", hp=24, max_hp=24, ac=15, dexterity=18,
    ))
    player["initiative"] = 20
    legion = combatant_from_enemy("Crimson Fang Legionnaire 1", hp=30, ac=16, cr=0.25, index=1)
    legion["initiative"] = 5
    return {
        "round_number": 1,
        "current_turn_index": 0,
        "initiative_order": [player["name"], legion["name"]],
        "combatants": [player, legion],
        "log": [],
    }


class TestMonsterTurnsNeverWait:
    def test_narration_that_hands_off_a_legionnaire_advances_to_the_player(self, monkeypatch):
        from app.services.dice import DiceResult

        class FixedRoller:
            def __init__(self, *args, **kwargs):
                pass

            def roll(self, notation):
                if str(notation).startswith("1d20"):
                    return DiceResult(notation=notation, rolls=[15], modifier=0, total=15)
                return DiceResult(notation=notation, rolls=[5], modifier=2, total=7)

        monkeypatch.setattr("app.services.game.combat_loop.DiceRoller", FixedRoller)
        state = _legion_fight()
        # The healing word already happened; Kael has taken the turn the
        # handoff is closing. An unacted PC must not be advanced this way.
        state["acted_this_round"] = [state["combatants"][0]["id"]]
        narration = (
            "Ashara's healing word closes the wound. "
            "It is now Crimson Fang Legionnaire 1's turn. What do you do?"
        )
        result = resolve_waiting_monster_turn(state, narration)
        assert result["events"]
        current = state["combatants"][state["current_turn_index"]]
        assert current["is_player"] is True
        assert current["name"] == "Kael Shadowstep"
        assert current["hp"] == 17  # 24 - 7, attack 15+3 vs AC 15
        facing = prepare_player_facing_narration(narration, state)
        assert "What do you do" not in facing
        assert "Legionnaire 1's turn" not in facing
        assert "It is now Kael Shadowstep's turn." in facing

    def test_a_monster_already_up_is_resolved_without_a_prompt(self, monkeypatch):
        from app.services.dice import DiceResult

        class FixedRoller:
            def __init__(self, *args, **kwargs):
                pass

            def roll(self, notation):
                if str(notation).startswith("1d20"):
                    return DiceResult(notation=notation, rolls=[15], modifier=0, total=15)
                return DiceResult(notation=notation, rolls=[5], modifier=2, total=7)

        monkeypatch.setattr("app.services.game.combat_loop.DiceRoller", FixedRoller)
        state = _legion_fight()
        state["current_turn_index"] = 1
        result = resolve_waiting_monster_turn(state, None)
        assert result["events"]
        current = state["combatants"][state["current_turn_index"]]
        assert current["is_player"] is True

    def test_an_unknown_name_does_not_skip_the_player(self):
        state = _legion_fight()
        narration = "It is now the innkeeper's turn. What do you do?"
        result = resolve_waiting_monster_turn(state, narration)
        assert result["events"] == []
        assert state["current_turn_index"] == 0
        assert prepare_player_facing_narration(narration, state) == narration

    def test_narrated_fight_without_initiative_resolves_the_legionnaire(self, monkeypatch):
        from app.services.dice import DiceResult

        class FixedRoller:
            def __init__(self, *args, **kwargs):
                pass

            def roll(self, notation):
                if str(notation).startswith("1d20"):
                    return DiceResult(notation=notation, rolls=[15], modifier=0, total=15)
                return DiceResult(notation=notation, rolls=[5], modifier=2, total=7)

        monkeypatch.setattr("app.services.game.combat_loop.DiceRoller", FixedRoller)
        thorne = {"id": "thorne", "name": "Thorne Ironfist", "hp": 34, "max_hp": 34, "ac": 18}
        narration = "It is now Crimson Fang Legionnaire 1's turn. What do you do?"
        updated = settle_narrated_monster_turn(narration, [thorne], actor_id="thorne")
        assert thorne["hp"] == 34  # the helper states the result; it does not mutate
        assert "What do you do" not in updated
        assert "It is now Thorne Ironfist's turn." in updated
        assert "is now at 27 of 34 HP" in updated
        notes = apply_hp_text([thorne], updated, actor_id="thorne")
        assert thorne["hp"] == 27
        assert notes

    def test_quiet_social_turn_is_left_alone(self):
        hero = {"id": "h", "name": "Thorin", "hp": 28, "max_hp": 28, "ac": 16}
        narration = "It is now the innkeeper's turn. What do you do?"
        assert settle_narrated_monster_turn(narration, [hero]) == narration


class TestReportedHp:
    def _thorne(self):
        return {"id": "thorne", "name": "Thorne Ironfist", "hp": 34, "max_hp": 34, "is_player": True}

    def test_absolute_report_wins_over_the_damage_amount(self):
        thorne = self._thorne()
        text = "Thorne takes 14 damage (11 slashing + 3 lightning) and is now at 20 of 34 HP."
        apply_hp_text([thorne], text)
        assert thorne["hp"] == 20

    def test_typed_damage_without_a_total_still_lands(self):
        thorne = self._thorne()
        text = "The Captain hits Thorne for 11 slashing and 3 (1d6) lightning damage."
        apply_hp_text([thorne], text)
        assert thorne["hp"] == 20

    def test_damage_type_without_the_word_damage_still_lands(self):
        thorne = self._thorne()
        text = (
            "Thorne takes 7 slashing from the Ghoul. "
            "Make a DC 10 Constitution saving throw."
        )
        apply_hp_text([thorne], text)
        assert thorne["hp"] == 27

    def test_you_are_now_at_uses_the_actor(self):
        thorne = self._thorne()
        apply_hp_text([thorne], "You are now at 20 of 34 HP.", actor_id="thorne")
        assert thorne["hp"] == 20

    def test_advantage_rolls_two_fresh_d20s_and_a_damage_roll(self, monkeypatch):
        from app.services.dice import DiceResult

        class FixedRoller:
            def __init__(self, *args, **kwargs):
                self.calls: list[str] = []

            def roll(self, notation):
                text = str(notation)
                self.calls.append(text)
                if text.startswith("1d20"):
                    face = 4 if self.calls.count(text) == 1 else 9
                    return DiceResult(notation=text, rolls=[face], modifier=0, total=face)
                if text.startswith("2d6"):
                    return DiceResult(notation=text, rolls=[2, 5], modifier=0, total=7)
                return DiceResult(notation=text, rolls=[3], modifier=4, total=7)

        monkeypatch.setattr("app.services.game.combat_loop.DiceRoller", FixedRoller)
        state = {
            "current_turn_index": 0,
            "combatants": [{
                "id": "kael",
                "name": "Kael Shadowstep",
                "is_player": True,
                "attack_bonus": 6,
                "damage_dice": "1d6+4",
            }],
        }
        # 18 is the earlier Stealth roll. It must not be an input to this check.
        narration = (
            "With advantage, using the higher roll of 18 from the previous turn, "
            "the shot hits for 13 piercing, including Sneak Attack."
        )
        updated = correct_borrowed_advantage(narration, state)
        assert "18" not in updated
        assert "previous" not in updated.lower()
        assert "13" not in updated
        assert "two fresh d20s (4 and 9)" in updated
        assert "using the higher, 9 + 6 = 15" in updated
        assert "Damage roll 1d6+4: [3] + 4 = 7 piercing." in updated
        assert "Sneak Attack roll 2d6: [2, 5] = 7." in updated

    def test_a_normal_hit_line_is_not_rewritten_as_advantage(self):
        text = "The arrow hits for 13 piercing."
        assert correct_borrowed_advantage(text, None) == text

    def test_prompt_brief_forbids_handing_off_monsters_and_asking_for_hp(self):
        state = _legion_fight()
        brief = combat_prompt_brief(state)
        assert "Do not hand an enemy or NPC turn to the players." in brief
        assert "Do not ask players to report their HP" in brief
        assert "Do not skip a player character" in brief


class TestNoSkippedPlayerTurns:
    def test_multi_round_fight_visits_every_living_pc(self, monkeypatch):
        """Kael 20, Grotesques 17, Thorne 16, Grotesques 13, Ashara 11, Lyra 10.

        Round 2 used to drop Thorne after Grotesque 1 died: the DM named
        Grotesques 3 and 4 and then Ashara. The same skip repeated in round 3.
        A scrambled reload, a damage write, and that narration must still
        stop on every living PC, in initiative order, every round.
        """
        from app.services.dice import DiceResult

        class FixedRoller:
            def __init__(self, *args, **kwargs):
                pass

            def roll(self, notation):
                if str(notation).startswith("1d20"):
                    return DiceResult(notation=str(notation), rolls=[10], modifier=0, total=10)
                return DiceResult(notation=str(notation), rolls=[1], modifier=0, total=1)

        monkeypatch.setattr("app.services.game.combat_loop.DiceRoller", FixedRoller)

        def pc(cid: str, name: str, init: int, hp: int = 40) -> dict:
            row = combatant_from_character(_char(id=cid, name=name, hp=hp, max_hp=hp, ac=18))
            row["initiative"] = init
            return row

        def mon(cid: str, name: str, init: int) -> dict:
            row = combatant_from_enemy(name, hp=40, ac=12, cr=0.25, index=1)
            row["id"] = cid
            row["name"] = name
            row["initiative"] = init
            return row

        order = [
            pc("kael", "Kael", 20),
            mon("g1", "Grotesque 1", 17),
            mon("g2", "Grotesque 2", 17),
            pc("thorne", "Thorne", 16, hp=34),
            mon("g3", "Grotesque 3", 13),
            mon("g4", "Grotesque 4", 13),
            pc("ashara", "Ashara", 11),
            pc("lyra", "Lyra", 10),
        ]
        state = {
            "round_number": 1,
            "current_turn_index": 0,
            "current_turn_id": order[0]["id"],
            "initiative_order": [c["name"] for c in order],
            "combatants": order,
            "log": [],
            "acted_this_round": [],
        }
        skip_narration = (
            "Grotesque 3 hits Thorne for 9. Grotesque 4 snaps. "
            "Ashara, what do you do?"
        )
        prompted: list[tuple[int, str]] = []
        removed_g1 = False
        guard = 0
        while state["round_number"] <= 3 and guard < 40:
            guard += 1
            state = json.loads(json.dumps(state))
            actor_id = state.get("current_turn_id")
            if not removed_g1 and state["round_number"] == 2 and actor_id == "thorne":
                # The kill drops the corpse out of the snapshot. The old index
                # then pointed past Thorne at Ashara.
                state["combatants"] = [c for c in state["combatants"] if c["id"] != "g1"]
                removed_g1 = True
            state["combatants"] = list(reversed(state["combatants"]))
            state["current_turn_index"] = 0
            current = current_combatant(state)
            assert current is not None
            assert current["id"] == actor_id
            if not current["is_player"]:
                run_pending_monster_turns(state)
                continue
            prompted.append((state["round_number"], current["name"]))
            apply_hp_text(state["combatants"], "Thorne takes 1 slashing.")
            assert current_combatant(state)["id"] == current["id"]
            resolve_waiting_monster_turn(state, skip_narration)
            assert current_combatant(state)["id"] == current["id"]
            facing = prepare_player_facing_narration(skip_narration, state)
            assert f"It is now {current['name']}'s turn." in facing
            assert "Ashara, what do you do" not in facing
            result = resolve_player_action(state, current["id"], "dodge")
            assert result.get("error") is None

        assert removed_g1
        for rnd in (1, 2, 3):
            names = [name for rnd_no, name in prompted if rnd_no == rnd]
            assert names == ["Kael", "Thorne", "Ashara", "Lyra"], names
        thorne = next(c for c in state["combatants"] if c["id"] == "thorne")
        assert 0 < thorne["hp"] < 34
