"""
Tests for D&D 5e Stat Calculator.

TDD: Tests written before implementation.
Validates ability modifiers, proficiency bonuses, effect stacking, and spell save DCs.
"""

import pytest

from src.systems.dnd5e.schemas.enums import Ability, EffectType
from src.systems.dnd5e.schemas.common import AbilityScores, SpeedBlock
from src.systems.dnd5e.schemas.instances import ActorInstance, EffectInstance
from src.systems.dnd5e.engine.stat_calculator import (
    calculate_modifier,
    calculate_proficiency_bonus,
    compute_stats,
    compute_spell_save_dc,
)


def make_actor(**kwargs) -> ActorInstance:
    """Helper to create a minimal ActorInstance."""
    defaults = dict(id="test_1", current_hp=30, max_hp=30)
    defaults.update(kwargs)
    return ActorInstance(**defaults)


# ---------------------------------------------------------------------------
# Ability Modifier
# ---------------------------------------------------------------------------

class TestAbilityModifier:

    def test_modifier_10_is_0(self):
        assert calculate_modifier(10) == 0

    def test_modifier_11_is_0(self):
        assert calculate_modifier(11) == 0

    def test_modifier_18_is_4(self):
        assert calculate_modifier(18) == 4

    def test_modifier_7_is_minus_2(self):
        assert calculate_modifier(7) == -2

    def test_modifier_1_is_minus_5(self):
        assert calculate_modifier(1) == -5

    def test_modifier_20_is_5(self):
        assert calculate_modifier(20) == 5

    def test_modifier_30_is_10(self):
        assert calculate_modifier(30) == 10


# ---------------------------------------------------------------------------
# Proficiency Bonus
# ---------------------------------------------------------------------------

class TestProficiencyBonus:

    def test_level_1(self):
        assert calculate_proficiency_bonus(1) == 2

    def test_level_4(self):
        assert calculate_proficiency_bonus(4) == 2

    def test_level_5(self):
        assert calculate_proficiency_bonus(5) == 3

    def test_level_8(self):
        assert calculate_proficiency_bonus(8) == 3

    def test_level_9(self):
        assert calculate_proficiency_bonus(9) == 4

    def test_level_13(self):
        assert calculate_proficiency_bonus(13) == 5

    def test_level_17(self):
        assert calculate_proficiency_bonus(17) == 6

    def test_level_20(self):
        assert calculate_proficiency_bonus(20) == 6


# ---------------------------------------------------------------------------
# Effect Stacking: compute_stats
# ---------------------------------------------------------------------------

class TestComputeStats:

    def test_no_effects_returns_base(self):
        """No effects → computed AC equals base AC."""
        actor = make_actor(armor_class=15)
        computed = compute_stats(actor)
        assert computed.armor_class == 15

    def test_ac_with_bonus_effect(self):
        """Base AC 15 + Shield (+2 BONUS) = 17."""
        actor = make_actor(armor_class=15)
        actor.effects.append(
            EffectInstance(
                id="shield_1",
                type=EffectType.BONUS,
                target_stat="armor_class",
                value=2,
            )
        )
        computed = compute_stats(actor)
        assert computed.armor_class == 17

    def test_ac_with_set_overrides_lower_base(self):
        """Barkskin (SET AC 16) on actor with AC 12 → AC 16."""
        actor = make_actor(armor_class=12)
        actor.effects.append(
            EffectInstance(
                id="barkskin_1",
                type=EffectType.SET,
                target_stat="armor_class",
                value=16,
            )
        )
        computed = compute_stats(actor)
        assert computed.armor_class == 16

    def test_set_does_not_override_higher_base(self):
        """Barkskin (SET 16) on actor with AC 18 → stays 18 (use higher)."""
        actor = make_actor(armor_class=18)
        actor.effects.append(
            EffectInstance(
                id="barkskin_1",
                type=EffectType.SET,
                target_stat="armor_class",
                value=16,
            )
        )
        computed = compute_stats(actor)
        assert computed.armor_class == 18

    def test_set_then_bonus_stacks(self):
        """SET 16 (overrides base 12) + BONUS +2 = 18."""
        actor = make_actor(armor_class=12)
        actor.effects.extend([
            EffectInstance(id="barkskin_1", type=EffectType.SET, target_stat="armor_class", value=16),
            EffectInstance(id="shield_1", type=EffectType.BONUS, target_stat="armor_class", value=2),
        ])
        computed = compute_stats(actor)
        assert computed.armor_class == 18

    def test_multiple_bonuses_stack(self):
        """Two BONUS effects stack additively."""
        actor = make_actor(armor_class=14)
        actor.effects.extend([
            EffectInstance(id="e1", type=EffectType.BONUS, target_stat="armor_class", value=1),
            EffectInstance(id="e2", type=EffectType.BONUS, target_stat="armor_class", value=2),
        ])
        computed = compute_stats(actor)
        assert computed.armor_class == 17


# ---------------------------------------------------------------------------
# Spell Save DC
# ---------------------------------------------------------------------------

class TestSpellSaveDC:

    def test_spell_save_dc(self):
        """DC = 8 + proficiency + ability_mod."""
        # level=5 → prof=3, INT=18 → mod=4 → DC = 8 + 3 + 4 = 15
        actor = make_actor(
            proficiency_bonus=3,
            abilities=AbilityScores(intelligence=18),
        )
        assert compute_spell_save_dc(actor, Ability.INT) == 15

    def test_spell_save_dc_low_ability(self):
        """DC = 8 + prof(2) + WIS mod(0) = 10."""
        actor = make_actor(
            proficiency_bonus=2,
            abilities=AbilityScores(wisdom=10),
        )
        assert compute_spell_save_dc(actor, Ability.WIS) == 10
