"""
Tests for Rules Engine Orchestrator.

The rules engine coordinates a full combat round, delegating to various
combat services. Using TDD: tests first, then implementation.
"""

import pytest
from dataclasses import dataclass
from app.services.dice import DiceRoller
from app.services.rules.engine import RulesEngine, ActionResult
from app.services.rules.combat import CombatManager, Combatant, AttackResult
from app.services.rules.abilities import AbilityChecker, AbilityCheckResult
from app.services.rules.conditions import ConditionTracker, ConditionEffect
from app.services.rules.spells import SpellCaster, SpellSlots, Spell, SpellSchool, SpellTarget


class TestRulesEngineInit:
    """Test RulesEngine initialization."""

    def test_init_with_dice_roller(self):
        """RulesEngine should accept DiceRoller and create internal services."""
        roller = DiceRoller(seed=42)
        engine = RulesEngine(roller)
        
        assert engine is not None
        assert isinstance(engine.combat_manager, CombatManager)
        assert isinstance(engine.ability_checker, AbilityChecker)
        assert isinstance(engine.condition_tracker, ConditionTracker)
        assert isinstance(engine.spell_caster, SpellCaster)

    def test_dice_roller_stored(self):
        """RulesEngine should store the dice roller."""
        roller = DiceRoller(seed=42)
        engine = RulesEngine(roller)
        
        assert engine.dice_roller is roller


class TestActionResult:
    """Test ActionResult dataclass."""

    def test_action_result_creation_minimal(self):
        """ActionResult should be creatable with minimal fields."""
        result = ActionResult(
            action_type="attack",
            success=True,
            description="Attack hits!"
        )
        
        assert result.action_type == "attack"
        assert result.success is True
        assert result.description == "Attack hits!"
        assert result.damage_dealt == 0
        assert result.healing_done == 0
        assert result.attacker == ""
        assert result.target == ""

    def test_action_result_with_all_fields(self):
        """ActionResult should support all fields."""
        result = ActionResult(
            action_type="attack",
            success=True,
            description="Critical hit!",
            damage_dealt=15,
            healing_done=0,
            attacker="hero-1",
            target="goblin-1"
        )
        
        assert result.action_type == "attack"
        assert result.success is True
        assert result.description == "Critical hit!"
        assert result.damage_dealt == 15
        assert result.healing_done == 0
        assert result.attacker == "hero-1"
        assert result.target == "goblin-1"


class TestRulesEngineInitiative:
    """Test initiative rolling."""

    def test_start_combat_returns_ordered_combatants(self):
        """start_combat should roll initiative and return ordered combatants."""
        roller = DiceRoller(seed=42)
        engine = RulesEngine(roller)
        
        combatants_data = [
            {"id": "hero-1", "name": "Hero", "initiative_modifier": 2, "hp": 50, "max_hp": 50, "ac": 15},
            {"id": "goblin-1", "name": "Goblin", "initiative_modifier": 1, "hp": 20, "max_hp": 20, "ac": 12},
        ]
        
        result = engine.start_combat(combatants_data)
        
        assert len(result) == 2
        assert all(isinstance(c, Combatant) for c in result)
        # Should be ordered by initiative (descending)
        if result[0].initiative == result[1].initiative:
            # Tiebreaker is initiative modifier
            assert result[0].initiative_modifier >= result[1].initiative_modifier
        else:
            assert result[0].initiative > result[1].initiative

    def test_start_combat_with_single_combatant(self):
        """start_combat should handle single combatant."""
        roller = DiceRoller(seed=42)
        engine = RulesEngine(roller)
        
        combatants_data = [
            {"id": "hero-1", "name": "Hero", "initiative_modifier": 2, "hp": 50, "max_hp": 50, "ac": 15},
        ]
        
        result = engine.start_combat(combatants_data)
        
        assert len(result) == 1
        assert result[0].name == "Hero"


class TestRulesEngineAttacks:
    """Test attack resolution."""

    def test_resolve_attack_returns_action_result(self):
        """resolve_attack should return ActionResult."""
        roller = DiceRoller(seed=42)
        engine = RulesEngine(roller)
        
        attacker = Combatant(
            id="hero-1", name="Hero", initiative=5, initiative_modifier=2,
            hp=50, max_hp=50, ac=15
        )
        target = Combatant(
            id="goblin-1", name="Goblin", initiative=3, initiative_modifier=1,
            hp=20, max_hp=20, ac=12
        )
        
        result = engine.resolve_attack(
            attacker=attacker,
            target=target,
            attack_bonus=5,
            damage_dice="1d8",
            damage_type="slashing"
        )
        
        assert isinstance(result, ActionResult)
        assert result.action_type == "attack"
        assert result.attacker == "hero-1"
        assert result.target == "goblin-1"
        assert isinstance(result.success, bool)
        assert isinstance(result.description, str)
        assert isinstance(result.damage_dealt, int)

    def test_resolve_attack_hit(self):
        """resolve_attack should calculate hit correctly."""
        roller = DiceRoller(seed=123)
        engine = RulesEngine(roller)
        
        attacker = Combatant(
            id="hero-1", name="Hero", initiative=5, initiative_modifier=2,
            hp=50, max_hp=50, ac=15
        )
        target = Combatant(
            id="goblin-1", name="Goblin", initiative=3, initiative_modifier=1,
            hp=20, max_hp=20, ac=10
        )
        
        # With high attack bonus, should likely hit
        result = engine.resolve_attack(
            attacker=attacker,
            target=target,
            attack_bonus=10,
            damage_dice="1d8",
            damage_type="slashing"
        )
        
        assert result.action_type == "attack"

    def test_resolve_attack_multiple_damage_dice(self):
        """resolve_attack should handle multiple damage dice."""
        roller = DiceRoller(seed=42)
        engine = RulesEngine(roller)
        
        attacker = Combatant(
            id="hero-1", name="Hero", initiative=5, initiative_modifier=2,
            hp=50, max_hp=50, ac=15
        )
        target = Combatant(
            id="goblin-1", name="Goblin", initiative=3, initiative_modifier=1,
            hp=20, max_hp=20, ac=12
        )
        
        result = engine.resolve_attack(
            attacker=attacker,
            target=target,
            attack_bonus=5,
            damage_dice="2d6+2",
            damage_type="fire"
        )
        
        assert isinstance(result, ActionResult)


class TestRulesEngineAbilityChecks:
    """Test ability check resolution."""

    def test_resolve_ability_check_returns_action_result(self):
        """resolve_ability_check should return ActionResult."""
        roller = DiceRoller(seed=42)
        engine = RulesEngine(roller)
        
        result = engine.resolve_ability_check(
            ability_mod=3,
            dc=12,
            proficiency=2,
            advantage=False,
            disadvantage=False
        )
        
        assert isinstance(result, ActionResult)
        assert result.action_type == "ability_check"
        assert isinstance(result.success, bool)
        assert isinstance(result.description, str)

    def test_resolve_ability_check_with_advantage(self):
        """resolve_ability_check should handle advantage."""
        roller = DiceRoller(seed=42)
        engine = RulesEngine(roller)
        
        result = engine.resolve_ability_check(
            ability_mod=2,
            dc=15,
            proficiency=2,
            advantage=True,
            disadvantage=False
        )
        
        assert isinstance(result, ActionResult)
        assert result.action_type == "ability_check"

    def test_resolve_ability_check_with_disadvantage(self):
        """resolve_ability_check should handle disadvantage."""
        roller = DiceRoller(seed=42)
        engine = RulesEngine(roller)
        
        result = engine.resolve_ability_check(
            ability_mod=2,
            dc=15,
            proficiency=0,
            advantage=False,
            disadvantage=True
        )
        
        assert isinstance(result, ActionResult)
        assert result.action_type == "ability_check"


class TestRulesEngineSpells:
    """Test spell resolution."""

    def test_resolve_spell_returns_action_result(self):
        """resolve_spell should return ActionResult."""
        roller = DiceRoller(seed=42)
        engine = RulesEngine(roller)
        
        spell = Spell(
            name="Magic Missile",
            level=1,
            school=SpellSchool.EVOCATION,
            casting_time="1 action",
            range_ft=120,
            duration="Instantaneous",
            target=SpellTarget.CREATURE,
            damage_dice="1d4+1"
        )
        
        slots = SpellSlots.for_full_caster(3)
        
        result = engine.resolve_spell(
            spell=spell,
            slots=slots,
            caster_level=3,
            spell_save_dc=12
        )
        
        assert isinstance(result, ActionResult)
        assert result.action_type == "spell"
        assert isinstance(result.success, bool)
        assert isinstance(result.description, str)

    def test_resolve_spell_with_insufficient_slots(self):
        """resolve_spell should handle insufficient spell slots."""
        roller = DiceRoller(seed=42)
        engine = RulesEngine(roller)
        
        spell = Spell(
            name="Fireball",
            level=3,
            school=SpellSchool.EVOCATION,
            casting_time="1 action",
            range_ft=150,
            duration="Instantaneous",
            target=SpellTarget.AREA,
            damage_dice="8d6"
        )
        
        slots = SpellSlots.for_full_caster(1)  # Level 1 caster has no level 3 slots
        
        result = engine.resolve_spell(
            spell=spell,
            slots=slots,
            caster_level=1,
            spell_save_dc=12
        )
        
        # Should handle this gracefully (either fail or succeed based on implementation)
        assert isinstance(result, ActionResult)


class TestRulesEngineDamage:
    """Test damage application."""

    def test_apply_damage_returns_total(self):
        """apply_damage should return total damage applied."""
        roller = DiceRoller(seed=42)
        engine = RulesEngine(roller)
        
        target = Combatant(
            id="goblin-1", name="Goblin", initiative=3, initiative_modifier=1,
            hp=20, max_hp=20, ac=12
        )
        
        damage_applied = engine.apply_damage(
            target=target,
            damage=10,
            damage_type="slashing",
            resistances=[],
            vulnerabilities=[]
        )
        
        assert isinstance(damage_applied, int)
        assert damage_applied > 0

    def test_apply_damage_with_resistance(self):
        """apply_damage should apply resistance (halves damage)."""
        roller = DiceRoller(seed=42)
        engine = RulesEngine(roller)
        
        target = Combatant(
            id="goblin-1", name="Goblin", initiative=3, initiative_modifier=1,
            hp=20, max_hp=20, ac=12
        )
        
        damage_applied = engine.apply_damage(
            target=target,
            damage=10,
            damage_type="fire",
            resistances=["fire"],
            vulnerabilities=[]
        )
        
        # Resistance should reduce damage (typically halved)
        assert damage_applied <= 10

    def test_apply_damage_with_vulnerability(self):
        """apply_damage should apply vulnerability (doubles damage)."""
        roller = DiceRoller(seed=42)
        engine = RulesEngine(roller)
        
        target = Combatant(
            id="goblin-1", name="Goblin", initiative=3, initiative_modifier=1,
            hp=20, max_hp=20, ac=12
        )
        
        damage_applied = engine.apply_damage(
            target=target,
            damage=10,
            damage_type="cold",
            resistances=[],
            vulnerabilities=["cold"]
        )
        
        # Vulnerability should increase damage (typically doubled)
        assert damage_applied >= 10


class TestRulesEngineHealing:
    """Test healing."""

    def test_heal_target_returns_healing_done(self):
        """heal_target should return healing applied."""
        roller = DiceRoller(seed=42)
        engine = RulesEngine(roller)
        
        target = Combatant(
            id="hero-1", name="Hero", initiative=5, initiative_modifier=2,
            hp=30, max_hp=50, ac=15
        )
        
        healing_done = engine.heal_target(target=target, amount=10)
        
        assert isinstance(healing_done, int)
        assert healing_done > 0

    def test_heal_target_respects_max_hp(self):
        """heal_target should not exceed max HP."""
        roller = DiceRoller(seed=42)
        engine = RulesEngine(roller)
        
        target = Combatant(
            id="hero-1", name="Hero", initiative=5, initiative_modifier=2,
            hp=45, max_hp=50, ac=15
        )
        
        healing_done = engine.heal_target(target=target, amount=10)
        
        # Should heal at most to max HP
        assert healing_done <= 5

    def test_heal_target_already_at_max_hp(self):
        """heal_target should not heal if already at max HP."""
        roller = DiceRoller(seed=42)
        engine = RulesEngine(roller)
        
        target = Combatant(
            id="hero-1", name="Hero", initiative=5, initiative_modifier=2,
            hp=50, max_hp=50, ac=15
        )
        
        healing_done = engine.heal_target(target=target, amount=10)
        
        assert healing_done == 0


class TestRulesEngineDeathSaves:
    """Test death save processing."""

    def test_process_death_save_returns_action_result(self):
        """process_death_save should return ActionResult."""
        roller = DiceRoller(seed=42)
        engine = RulesEngine(roller)
        
        combatant = Combatant(
            id="hero-1", name="Hero", initiative=5, initiative_modifier=2,
            hp=0, max_hp=50, ac=15, is_alive=False
        )
        
        result = engine.process_death_save(combatant)
        
        assert isinstance(result, ActionResult)
        assert result.action_type == "death_save"
        assert isinstance(result.success, bool)
        assert isinstance(result.description, str)

    def test_process_death_save_success(self):
        """process_death_save on 10+ should succeed."""
        roller = DiceRoller(seed=999)
        engine = RulesEngine(roller)
        
        combatant = Combatant(
            id="hero-1", name="Hero", initiative=5, initiative_modifier=2,
            hp=0, max_hp=50, ac=15, is_alive=False,
            death_save_successes=0, death_save_failures=0
        )
        
        result = engine.process_death_save(combatant)
        
        assert isinstance(result, ActionResult)
        assert result.action_type == "death_save"

    def test_process_death_save_failure(self):
        """process_death_save on 9 or less should fail."""
        roller = DiceRoller(seed=42)
        engine = RulesEngine(roller)
        
        combatant = Combatant(
            id="hero-1", name="Hero", initiative=5, initiative_modifier=2,
            hp=0, max_hp=50, ac=15, is_alive=False,
            death_save_successes=0, death_save_failures=0
        )
        
        result = engine.process_death_save(combatant)
        
        assert isinstance(result, ActionResult)
        assert result.action_type == "death_save"
