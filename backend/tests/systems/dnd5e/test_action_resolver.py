"""
Phase 4 — Action Resolver Tests (TDD).

Tests for the complete action resolution pipeline: attack rolls,
save-based actions, healing, and EncounterState integration.

All tests use roll_override / roll_overrides for deterministic results.
"""

import pytest

from src.systems.dnd5e.schemas.enums import (
    ActionType,
    ActorType,
    Ability,
    ConditionType,
    DamageType,
)
from src.systems.dnd5e.schemas.common import (
    AbilityScores,
    SaveRequirement,
    SpeedBlock,
)
from src.systems.dnd5e.schemas.instances import (
    ActorInstance,
    ConditionInstance,
)
from src.systems.dnd5e.schemas.definitions import ActionDefinition
from src.systems.dnd5e.schemas.encounter import EncounterState
from src.systems.dnd5e.engine.initiative import InitiativeEntry
from src.systems.dnd5e.engine.combat_state import (
    start_combat,
    get_active_combatant,
    get_turn_budget,
)
from src.systems.dnd5e.engine.action_resolver import (
    resolve_attack,
    resolve_save_action,
    resolve_healing,
    resolve_and_apply,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_actor(**kwargs) -> ActorInstance:
    defaults = dict(
        id="test_1",
        name="Test Actor",
        current_hp=30,
        max_hp=30,
        armor_class=15,
        abilities=AbilityScores(
            strength=16, dexterity=14, constitution=14,
            intelligence=10, wisdom=12, charisma=8,
        ),
        proficiency_bonus=2,
    )
    defaults.update(kwargs)
    return ActorInstance(**defaults)


def make_action(**kwargs) -> ActionDefinition:
    defaults = dict(
        name="Test Attack",
        action_type=ActionType.MELEE_WEAPON,
        attack_bonus=6,
        damage_dice="2d10",
        damage_bonus=8,
        damage_type=DamageType.PIERCING,
        reach=5,
    )
    defaults.update(kwargs)
    return ActionDefinition(**defaults)


def make_save_action(**kwargs) -> ActionDefinition:
    defaults = dict(
        name="Fire Breath",
        action_type=ActionType.SAVE_EFFECT,
        damage_dice="18d6",
        damage_type=DamageType.FIRE,
        save=SaveRequirement(
            ability=Ability.DEX,
            dc=21,
            on_fail="full_damage",
            on_success="half_damage",
        ),
    )
    defaults.update(kwargs)
    return ActionDefinition(**defaults)


def make_healing_action(**kwargs) -> ActionDefinition:
    defaults = dict(
        name="Cure Wounds",
        action_type=ActionType.HEALING,
        damage_dice="1d8",
        damage_bonus=3,
    )
    defaults.update(kwargs)
    return ActionDefinition(**defaults)


# ---------------------------------------------------------------------------
# Attack Roll: Hit / Miss
# ---------------------------------------------------------------------------

class TestAttackRollHitMiss:

    def test_attack_roll_hit(self):
        """Roll 18 + bonus 6 = 24 vs AC 15 → hit."""
        attacker = make_actor(id="attacker")
        target = make_actor(id="target", armor_class=15)
        action = make_action(attack_bonus=6)

        result = resolve_attack(attacker, target, action, roll_override=18)
        assert result.hit is True

    def test_attack_roll_miss(self):
        """Roll 3 + bonus 6 = 9 vs AC 15 → miss."""
        attacker = make_actor(id="attacker")
        target = make_actor(id="target", armor_class=15)
        action = make_action(attack_bonus=6)

        result = resolve_attack(attacker, target, action, roll_override=3)
        assert result.hit is False

    def test_natural_20_always_hits(self):
        """Nat 20 hits regardless of AC."""
        attacker = make_actor(id="attacker")
        target = make_actor(id="target", armor_class=30)
        action = make_action(attack_bonus=0)

        result = resolve_attack(attacker, target, action, roll_override=20)
        assert result.hit is True
        assert result.is_critical is True

    def test_natural_1_always_misses(self):
        """Nat 1 misses regardless of AC."""
        attacker = make_actor(id="attacker")
        target = make_actor(id="target", armor_class=5)
        action = make_action(attack_bonus=10)

        result = resolve_attack(attacker, target, action, roll_override=1)
        assert result.hit is False


# ---------------------------------------------------------------------------
# Critical Hits
# ---------------------------------------------------------------------------

class TestCriticalHits:

    def test_critical_hit_doubles_damage_dice(self):
        """Crit: 2d10 becomes 4d10 (PHB rule). Bonus is NOT doubled."""
        attacker = make_actor(id="attacker")
        target = make_actor(id="target", armor_class=10, current_hp=100, max_hp=100)
        action = make_action(damage_dice="2d10", damage_bonus=8)

        result = resolve_attack(attacker, target, action, roll_override=20)
        assert result.is_critical is True
        # 4d10 range: [4, 40] + 8 = [12, 48]
        assert 12 <= result.total_damage <= 48

    def test_attack_against_paralyzed_auto_crits_in_melee(self):
        """Any hit against a paralyzed target in melee is a critical hit."""
        attacker = make_actor(id="attacker")
        target = make_actor(id="target", armor_class=10, current_hp=100, max_hp=100)
        target.conditions.append(ConditionInstance(condition=ConditionType.PARALYZED))
        action = make_action(action_type=ActionType.MELEE_WEAPON)

        result = resolve_attack(attacker, target, action, roll_override=12)
        assert result.hit is True
        assert result.is_critical is True


# ---------------------------------------------------------------------------
# Advantage / Disadvantage
# ---------------------------------------------------------------------------

class TestAdvantageDisadvantage:

    def test_advantage_takes_higher_roll(self):
        attacker = make_actor(id="attacker")
        target = make_actor(id="target", armor_class=15)
        action = make_action()

        result = resolve_attack(
            attacker, target, action,
            advantage=True, roll_overrides=[8, 15],
        )
        assert result.roll_used == 15

    def test_disadvantage_takes_lower_roll(self):
        attacker = make_actor(id="attacker")
        target = make_actor(id="target", armor_class=15)
        action = make_action()

        result = resolve_attack(
            attacker, target, action,
            disadvantage=True, roll_overrides=[8, 15],
        )
        assert result.roll_used == 8

    def test_advantage_and_disadvantage_cancel(self):
        """If both present, roll normally (single d20)."""
        attacker = make_actor(id="attacker")
        target = make_actor(id="target", armor_class=15)
        action = make_action()

        result = resolve_attack(
            attacker, target, action,
            advantage=True, disadvantage=True,
            roll_override=12,
        )
        assert result.roll_count == 1


# ---------------------------------------------------------------------------
# Condition Effects on Attacks
# ---------------------------------------------------------------------------

class TestConditionEffects:

    def test_attack_while_blinded_has_disadvantage(self):
        """Blinded attacker gets disadvantage → lower roll used."""
        attacker = make_actor(id="attacker")
        attacker.conditions.append(ConditionInstance(condition=ConditionType.BLINDED))
        target = make_actor(id="target", armor_class=15)
        action = make_action()

        result = resolve_attack(
            attacker, target, action,
            roll_overrides=[15, 8],
        )
        assert result.roll_used == 8  # disadvantage → lower roll


# ---------------------------------------------------------------------------
# Save-Based Actions
# ---------------------------------------------------------------------------

class TestSaveActions:

    def test_save_action_full_damage_on_fail(self):
        """Fire Breath: DC 21 DEX save. Roll 8 → fail → full damage."""
        caster = make_actor(id="caster")
        target = make_actor(id="target", current_hp=100, max_hp=100)
        action = make_save_action()

        result = resolve_save_action(
            caster, [target], action,
            damage_roll_override=63,
            save_overrides=[8],
        )
        assert result.results[0].passed is False
        assert result.results[0].damage == 63

    def test_save_action_half_damage_on_success(self):
        """Fire Breath: roll 22 → pass → half damage (31 = floor(63/2))."""
        caster = make_actor(id="caster")
        target = make_actor(id="target", current_hp=100, max_hp=100)
        action = make_save_action()

        result = resolve_save_action(
            caster, [target], action,
            damage_roll_override=63,
            save_overrides=[22],
        )
        assert result.results[0].passed is True
        assert result.results[0].damage == 31  # floor(63/2)

    def test_save_action_multiple_targets(self):
        """Multi-target save: each target rolls independently."""
        caster = make_actor(id="caster")
        target_a = make_actor(id="target_a", current_hp=100, max_hp=100)
        target_b = make_actor(id="target_b", current_hp=100, max_hp=100)
        action = make_save_action()

        result = resolve_save_action(
            caster, [target_a, target_b], action,
            damage_roll_override=40,
            save_overrides=[8, 22],  # A fails, B passes
        )
        assert result.results[0].passed is False
        assert result.results[0].damage == 40
        assert result.results[1].passed is True
        assert result.results[1].damage == 20  # floor(40/2)


# ---------------------------------------------------------------------------
# Healing
# ---------------------------------------------------------------------------

class TestHealing:

    def test_healing_action_restores_hp(self):
        actor = make_actor(id="target", current_hp=20, max_hp=45)
        action = make_healing_action(damage_dice="1d8", damage_bonus=3)

        result = resolve_healing(actor, action, dice_override=9)
        # 9 + 3 = 12 healed → 20 + 12 = 32
        assert actor.current_hp == 32
        assert result.hp_restored == 12

    def test_healing_cannot_exceed_max_hp(self):
        actor = make_actor(id="target", current_hp=40, max_hp=45)
        action = make_healing_action(damage_dice="1d8", damage_bonus=3)

        result = resolve_healing(actor, action, dice_override=20)
        # Would heal 23, but capped at 45
        assert actor.current_hp == 45
        assert result.hp_restored == 5


# ---------------------------------------------------------------------------
# TurnBudget Integration
# ---------------------------------------------------------------------------

class TestTurnBudgetIntegration:

    def test_action_consumes_turn_budget(self):
        """resolve_and_apply() should consume the attacker's action."""
        enc = EncounterState(id="test_enc")
        attacker = make_actor(id="attacker", name="Attacker")
        target = make_actor(id="target", name="Target")
        enc.combatants = [attacker, target]

        initiatives = [
            InitiativeEntry(actor_id="attacker", roll=18, dex_score=14),
            InitiativeEntry(actor_id="target", roll=10, dex_score=10),
        ]
        start_combat(enc, initiatives)

        action = make_action()
        resolve_and_apply(enc, attacker, target, action, roll_override=15)

        budget = get_turn_budget(enc, "attacker")
        assert budget.action_available is False
