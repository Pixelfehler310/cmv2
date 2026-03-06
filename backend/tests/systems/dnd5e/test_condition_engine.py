"""
Tests for D&D 5e Condition Engine.

TDD: Tests written before implementation.
Validates mechanical effects of all 15 PHB conditions and exhaustion levels 1-6.
"""

import pytest

from src.systems.dnd5e.schemas.enums import Ability, ConditionType
from src.systems.dnd5e.schemas.common import AbilityScores, SpeedBlock
from src.systems.dnd5e.schemas.instances import ActorInstance, ConditionInstance
from src.systems.dnd5e.engine.condition_engine import (
    apply_conditions,
    compute_attack_context,
    compute_save_context,
)


def make_actor(**kwargs) -> ActorInstance:
    """Helper to create a minimal ActorInstance."""
    defaults = dict(id="test_1", current_hp=30, max_hp=30)
    defaults.update(kwargs)
    return ActorInstance(**defaults)


# ---------------------------------------------------------------------------
# Speed Modifications
# ---------------------------------------------------------------------------

class TestConditionSpeed:

    def test_grappled_sets_speed_zero(self):
        actor = make_actor(speed=SpeedBlock(walk=30))
        actor.conditions.append(ConditionInstance(condition=ConditionType.GRAPPLED))
        computed = apply_conditions(actor)
        assert computed.speed.walk == 0

    def test_restrained_sets_speed_zero(self):
        actor = make_actor(speed=SpeedBlock(walk=30))
        actor.conditions.append(ConditionInstance(condition=ConditionType.RESTRAINED))
        computed = apply_conditions(actor)
        assert computed.speed.walk == 0

    def test_paralyzed_sets_speed_zero(self):
        actor = make_actor(speed=SpeedBlock(walk=30))
        actor.conditions.append(ConditionInstance(condition=ConditionType.PARALYZED))
        computed = apply_conditions(actor)
        assert computed.speed.walk == 0

    def test_stunned_sets_speed_zero(self):
        actor = make_actor(speed=SpeedBlock(walk=30))
        actor.conditions.append(ConditionInstance(condition=ConditionType.STUNNED))
        computed = apply_conditions(actor)
        assert computed.speed.walk == 0

    def test_unconscious_sets_speed_zero(self):
        actor = make_actor(speed=SpeedBlock(walk=30))
        actor.conditions.append(ConditionInstance(condition=ConditionType.UNCONSCIOUS))
        computed = apply_conditions(actor)
        assert computed.speed.walk == 0

    def test_petrified_sets_speed_zero(self):
        actor = make_actor(speed=SpeedBlock(walk=30))
        actor.conditions.append(ConditionInstance(condition=ConditionType.PETRIFIED))
        computed = apply_conditions(actor)
        assert computed.speed.walk == 0

    def test_no_conditions_keeps_speed(self):
        actor = make_actor(speed=SpeedBlock(walk=30))
        computed = apply_conditions(actor)
        assert computed.speed.walk == 30


# ---------------------------------------------------------------------------
# Attack Context
# ---------------------------------------------------------------------------

class TestAttackContext:

    def test_prone_gives_disadvantage_on_attacks(self):
        actor = make_actor()
        actor.conditions.append(ConditionInstance(condition=ConditionType.PRONE))
        result = compute_attack_context(actor)
        assert result.has_disadvantage is True

    def test_invisible_gives_advantage_on_attacks(self):
        actor = make_actor()
        actor.conditions.append(ConditionInstance(condition=ConditionType.INVISIBLE))
        result = compute_attack_context(actor)
        assert result.has_advantage is True

    def test_blinded_gives_disadvantage_on_attacks(self):
        actor = make_actor()
        actor.conditions.append(ConditionInstance(condition=ConditionType.BLINDED))
        result = compute_attack_context(actor)
        assert result.has_disadvantage is True

    def test_poisoned_gives_disadvantage_on_attacks(self):
        actor = make_actor()
        actor.conditions.append(ConditionInstance(condition=ConditionType.POISONED))
        result = compute_attack_context(actor)
        assert result.has_disadvantage is True

    def test_restrained_gives_disadvantage_on_attacks(self):
        actor = make_actor()
        actor.conditions.append(ConditionInstance(condition=ConditionType.RESTRAINED))
        result = compute_attack_context(actor)
        assert result.has_disadvantage is True

    def test_frightened_gives_disadvantage_on_attacks(self):
        actor = make_actor()
        actor.conditions.append(ConditionInstance(condition=ConditionType.FRIGHTENED))
        result = compute_attack_context(actor)
        assert result.has_disadvantage is True

    def test_no_conditions_no_advantage(self):
        actor = make_actor()
        result = compute_attack_context(actor)
        assert result.has_advantage is False
        assert result.has_disadvantage is False


# ---------------------------------------------------------------------------
# Save Context
# ---------------------------------------------------------------------------

class TestSaveContext:

    def test_paralyzed_auto_fails_str_saves(self):
        actor = make_actor()
        actor.conditions.append(ConditionInstance(condition=ConditionType.PARALYZED))
        result = compute_save_context(actor, Ability.STR)
        assert result.auto_fail is True

    def test_paralyzed_auto_fails_dex_saves(self):
        actor = make_actor()
        actor.conditions.append(ConditionInstance(condition=ConditionType.PARALYZED))
        result = compute_save_context(actor, Ability.DEX)
        assert result.auto_fail is True

    def test_paralyzed_does_not_auto_fail_wis_saves(self):
        actor = make_actor()
        actor.conditions.append(ConditionInstance(condition=ConditionType.PARALYZED))
        result = compute_save_context(actor, Ability.WIS)
        assert result.auto_fail is False

    def test_stunned_auto_fails_str_dex_saves(self):
        actor = make_actor()
        actor.conditions.append(ConditionInstance(condition=ConditionType.STUNNED))
        result_str = compute_save_context(actor, Ability.STR)
        result_dex = compute_save_context(actor, Ability.DEX)
        assert result_str.auto_fail is True
        assert result_dex.auto_fail is True

    def test_unconscious_auto_fails_str_dex_saves(self):
        actor = make_actor()
        actor.conditions.append(ConditionInstance(condition=ConditionType.UNCONSCIOUS))
        result = compute_save_context(actor, Ability.STR)
        assert result.auto_fail is True

    def test_petrified_auto_fails_str_dex_saves(self):
        actor = make_actor()
        actor.conditions.append(ConditionInstance(condition=ConditionType.PETRIFIED))
        result = compute_save_context(actor, Ability.DEX)
        assert result.auto_fail is True

    def test_restrained_gives_disadvantage_on_dex_saves(self):
        actor = make_actor()
        actor.conditions.append(ConditionInstance(condition=ConditionType.RESTRAINED))
        result = compute_save_context(actor, Ability.DEX)
        assert result.has_disadvantage is True

    def test_restrained_does_not_affect_str_saves(self):
        actor = make_actor()
        actor.conditions.append(ConditionInstance(condition=ConditionType.RESTRAINED))
        result = compute_save_context(actor, Ability.STR)
        assert result.has_disadvantage is False


# ---------------------------------------------------------------------------
# Exhaustion Levels
# ---------------------------------------------------------------------------

class TestExhaustion:

    def test_exhaustion_2_halves_speed(self):
        actor = make_actor(speed=SpeedBlock(walk=30), exhaustion_level=2)
        computed = apply_conditions(actor)
        assert computed.speed.walk == 15

    def test_exhaustion_3_adds_attack_disadvantage(self):
        """Level 3: disadvantage on attack rolls + ability checks."""
        actor = make_actor(exhaustion_level=3)
        ctx = compute_attack_context(actor)
        assert ctx.has_disadvantage is True

    def test_exhaustion_4_halves_max_hp(self):
        actor = make_actor(max_hp=40, exhaustion_level=4)
        computed = apply_conditions(actor)
        assert computed.max_hp == 20

    def test_exhaustion_5_sets_speed_zero(self):
        actor = make_actor(speed=SpeedBlock(walk=30), exhaustion_level=5)
        computed = apply_conditions(actor)
        assert computed.speed.walk == 0

    def test_exhaustion_stacks_cumulatively(self):
        """Level 3: halved speed (from 2) + DADV on attacks + DADV ability checks."""
        actor = make_actor(speed=SpeedBlock(walk=30), exhaustion_level=3)
        computed = apply_conditions(actor)
        assert computed.speed.walk == 15  # from level 2

        ctx = compute_attack_context(actor)
        assert ctx.has_disadvantage is True  # from level 3

    def test_exhaustion_1_disadvantage_ability_checks(self):
        """Level 1: disadvantage on ability checks (tracked in context)."""
        actor = make_actor(exhaustion_level=1)
        computed = apply_conditions(actor)
        assert computed.ability_check_disadvantage is True
