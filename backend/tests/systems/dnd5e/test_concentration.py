"""
Phase 3 — Concentration Tests (TDD).

Tests for concentration save DC, breaking mechanics, and
new-spell-replaces-previous behavior.
"""

import pytest

from src.systems.dnd5e.schemas.enums import (
    ConditionType,
    DurationType,
)
from src.systems.dnd5e.schemas.common import AbilityScores
from src.systems.dnd5e.schemas.instances import (
    ActorInstance,
    ConditionInstance,
    ConcentrationState,
    EffectInstance,
)
from src.systems.dnd5e.schemas.encounter import EncounterState
from src.systems.dnd5e.engine.effect_engine import add_effect, has_effect
from src.systems.dnd5e.engine.concentration import (
    concentration_dc,
    break_concentration,
    start_concentration,
    check_incapacitated_breaks_concentration,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_actor(id: str, name: str = "Caster") -> ActorInstance:
    return ActorInstance(
        id=id,
        name=name,
        current_hp=30,
        max_hp=30,
    )


def _make_concentrating_actor(
    id: str = "cleric",
    effect_id: str = "bless_1",
) -> ActorInstance:
    actor = _make_actor(id)
    actor.concentration = ConcentrationState(
        is_concentrating=True,
        effect_id=effect_id,
    )
    return actor


def _make_encounter(*actors: ActorInstance) -> EncounterState:
    enc = EncounterState(id="test_enc")
    enc.combatants = list(actors)
    return enc


# ---------------------------------------------------------------------------
# Concentration DC
# ---------------------------------------------------------------------------

class TestConcentrationDC:
    def test_dc_minimum_is_10(self):
        """DC = max(10, floor(damage/2)). Small damage → DC 10."""
        assert concentration_dc(8) == 10   # floor(8/2) = 4 → max(10,4) = 10

    def test_dc_scales_with_damage(self):
        """DC = max(10, floor(damage/2)). Large damage → half."""
        assert concentration_dc(30) == 15  # floor(30/2) = 15 → max(10,15) = 15

    def test_dc_at_boundary(self):
        """20 damage → floor(20/2) = 10 → max(10,10) = 10."""
        assert concentration_dc(20) == 10

    def test_dc_odd_damage(self):
        """21 damage → floor(21/2) = 10 → max(10,10) = 10."""
        assert concentration_dc(21) == 10

    def test_dc_edge_1_damage(self):
        """1 damage → floor(1/2) = 0 → max(10,0) = 10."""
        assert concentration_dc(1) == 10

    def test_dc_large_damage(self):
        """100 damage → floor(100/2) = 50 → max(10,50) = 50."""
        assert concentration_dc(100) == 50


# ---------------------------------------------------------------------------
# Break Concentration
# ---------------------------------------------------------------------------

class TestBreakConcentration:
    def test_break_removes_effect(self):
        """Breaking concentration removes the linked effect from the encounter."""
        actor = _make_concentrating_actor(effect_id="bless_1")
        enc = _make_encounter(actor)

        effect = EffectInstance(
            id="bless_1", name="Bless", source_id="cleric", target_id="cleric",
            duration_type=DurationType.ROUNDS, remaining_rounds=10,
            requires_concentration=True,
        )
        add_effect(enc, effect)

        break_concentration(actor, enc)

        assert actor.concentration.is_concentrating is False
        assert actor.concentration.effect_id is None
        target = next(a for a in enc.combatants if a.id == "cleric")
        assert not has_effect(target, "bless_1")

    def test_break_when_not_concentrating_is_noop(self):
        """Breaking concentration on non-concentrating actor doesn't error."""
        actor = _make_actor("fighter")
        enc = _make_encounter(actor)
        break_concentration(actor, enc)
        assert actor.concentration.is_concentrating is False


# ---------------------------------------------------------------------------
# Incapacitating Conditions
# ---------------------------------------------------------------------------

class TestIncapacitatedBreaks:
    def test_stunned_breaks_concentration(self):
        actor = _make_concentrating_actor(effect_id="bless_1")
        enc = _make_encounter(actor)
        effect = EffectInstance(
            id="bless_1", name="Bless", source_id="cleric", target_id="cleric",
            duration_type=DurationType.ROUNDS, remaining_rounds=10,
            requires_concentration=True,
        )
        add_effect(enc, effect)

        actor.conditions.append(ConditionInstance(condition=ConditionType.STUNNED))
        check_incapacitated_breaks_concentration(actor, enc)

        assert actor.concentration.is_concentrating is False

    def test_paralyzed_breaks_concentration(self):
        actor = _make_concentrating_actor(effect_id="hold_1")
        enc = _make_encounter(actor)
        effect = EffectInstance(
            id="hold_1", name="Hold Person", source_id="cleric", target_id="cleric",
            duration_type=DurationType.ROUNDS, remaining_rounds=10,
            requires_concentration=True,
        )
        add_effect(enc, effect)

        actor.conditions.append(ConditionInstance(condition=ConditionType.PARALYZED))
        check_incapacitated_breaks_concentration(actor, enc)

        assert actor.concentration.is_concentrating is False

    def test_unconscious_breaks_concentration(self):
        actor = _make_concentrating_actor(effect_id="bless_1")
        enc = _make_encounter(actor)
        effect = EffectInstance(
            id="bless_1", name="Bless", source_id="cleric", target_id="cleric",
            duration_type=DurationType.ROUNDS, remaining_rounds=10,
            requires_concentration=True,
        )
        add_effect(enc, effect)

        actor.conditions.append(ConditionInstance(condition=ConditionType.UNCONSCIOUS))
        check_incapacitated_breaks_concentration(actor, enc)

        assert actor.concentration.is_concentrating is False

    def test_non_incapacitating_condition_keeps_concentration(self):
        actor = _make_concentrating_actor(effect_id="bless_1")
        enc = _make_encounter(actor)
        effect = EffectInstance(
            id="bless_1", name="Bless", source_id="cleric", target_id="cleric",
            duration_type=DurationType.ROUNDS, remaining_rounds=10,
            requires_concentration=True,
        )
        add_effect(enc, effect)

        actor.conditions.append(ConditionInstance(condition=ConditionType.FRIGHTENED))
        check_incapacitated_breaks_concentration(actor, enc)

        assert actor.concentration.is_concentrating is True


# ---------------------------------------------------------------------------
# New Concentration Replaces Previous
# ---------------------------------------------------------------------------

class TestNewConcentration:
    def test_new_concentration_spell_ends_previous(self):
        """Casting a new concentration spell breaks the old one."""
        actor = _make_concentrating_actor(effect_id="bless_1")
        enc = _make_encounter(actor)

        # Add old effect
        old_effect = EffectInstance(
            id="bless_1", name="Bless", source_id="cleric", target_id="cleric",
            duration_type=DurationType.ROUNDS, remaining_rounds=10,
            requires_concentration=True,
        )
        add_effect(enc, old_effect)

        # Add new effect
        new_effect = EffectInstance(
            id="hold_person_1", name="Hold Person", source_id="cleric", target_id="enemy",
            duration_type=DurationType.ROUNDS, remaining_rounds=10,
            requires_concentration=True,
        )

        # Need enemy to be in encounter for the new effect target
        enemy = ActorInstance(id="enemy", name="Enemy", current_hp=20, max_hp=20)
        enc.combatants.append(enemy)

        start_concentration(actor, new_effect, enc)

        # Old effect should be removed
        target = next(a for a in enc.combatants if a.id == "cleric")
        assert not has_effect(target, "bless_1")

        # New concentration should be active
        assert actor.concentration.is_concentrating is True
        assert actor.concentration.effect_id == "hold_person_1"

        # New effect should exist on target
        enemy_actor = next(a for a in enc.combatants if a.id == "enemy")
        assert has_effect(enemy_actor, "hold_person_1")

    def test_start_concentration_when_not_concentrating(self):
        """Starting concentration from scratch works cleanly."""
        actor = _make_actor("wizard")
        enemy = ActorInstance(id="enemy", name="Enemy", current_hp=20, max_hp=20)
        enc = _make_encounter(actor, enemy)

        new_effect = EffectInstance(
            id="web_1", name="Web", source_id="wizard", target_id="enemy",
            duration_type=DurationType.ROUNDS, remaining_rounds=10,
            requires_concentration=True,
        )
        start_concentration(actor, new_effect, enc)

        assert actor.concentration.is_concentrating is True
        assert actor.concentration.effect_id == "web_1"
        enemy_actor = next(a for a in enc.combatants if a.id == "enemy")
        assert has_effect(enemy_actor, "web_1")
