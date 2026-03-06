"""
Phase 3 — Effect Engine Tests (TDD).

Tests for effect lifecycle: apply, remove, tick durations, and
condition cleanup when linked effects expire.
"""

import pytest

from src.systems.dnd5e.schemas.enums import (
    ConditionType,
    DurationType,
    EffectType,
)
from src.systems.dnd5e.schemas.common import AbilityScores
from src.systems.dnd5e.schemas.instances import (
    ActorInstance,
    ConditionInstance,
    EffectInstance,
)
from src.systems.dnd5e.schemas.encounter import EncounterState
from src.systems.dnd5e.engine.effect_engine import (
    add_effect,
    remove_effect,
    tick_effects,
    has_effect,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_actor(id: str, name: str = "Test Actor") -> ActorInstance:
    return ActorInstance(
        id=id,
        name=name,
        current_hp=20,
        max_hp=20,
    )


def _make_encounter(*actors: ActorInstance) -> EncounterState:
    enc = EncounterState(id="test_enc")
    enc.combatants = list(actors)
    return enc


def _make_effect(
    id: str,
    name: str = "Test Effect",
    source_id: str = "caster",
    target_id: str = "target",
    remaining_rounds: int | None = None,
    requires_concentration: bool = False,
    **kwargs,
) -> EffectInstance:
    return EffectInstance(
        id=id,
        name=name,
        source_id=source_id,
        target_id=target_id,
        duration_type=DurationType.ROUNDS if remaining_rounds is not None else DurationType.UNTIL_DISPELLED,
        remaining_rounds=remaining_rounds,
        requires_concentration=requires_concentration,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# Apply / Remove
# ---------------------------------------------------------------------------

class TestEffectApplyRemove:
    def test_add_effect_to_actor(self):
        actor = _make_actor("hero")
        enc = _make_encounter(actor)
        effect = _make_effect("bless_1", target_id="hero")

        add_effect(enc, effect)

        target = next(a for a in enc.combatants if a.id == "hero")
        assert has_effect(target, "bless_1")

    def test_remove_effect_from_actor(self):
        actor = _make_actor("hero")
        enc = _make_encounter(actor)
        effect = _make_effect("bless_1", target_id="hero")

        add_effect(enc, effect)
        remove_effect(enc, "bless_1")

        target = next(a for a in enc.combatants if a.id == "hero")
        assert not has_effect(target, "bless_1")

    def test_remove_nonexistent_effect_is_noop(self):
        actor = _make_actor("hero")
        enc = _make_encounter(actor)
        # Should not raise
        remove_effect(enc, "nonexistent")


# ---------------------------------------------------------------------------
# Duration Ticking
# ---------------------------------------------------------------------------

class TestEffectDuration:
    def test_effect_duration_ticks_down(self):
        actor = _make_actor("hero")
        enc = _make_encounter(actor)
        effect = _make_effect(
            "bless_1", source_id="cleric", target_id="hero",
            remaining_rounds=3,
        )
        add_effect(enc, effect)

        tick_effects(enc, source_id="cleric")

        target = next(a for a in enc.combatants if a.id == "hero")
        remaining = next(e for e in target.effects if e.id == "bless_1")
        assert remaining.remaining_rounds == 2

    def test_effect_removed_at_zero_rounds(self):
        actor = _make_actor("hero")
        enc = _make_encounter(actor)
        effect = _make_effect(
            "bless_1", source_id="cleric", target_id="hero",
            remaining_rounds=1,
        )
        add_effect(enc, effect)

        tick_effects(enc, source_id="cleric")

        target = next(a for a in enc.combatants if a.id == "hero")
        assert not has_effect(target, "bless_1")

    def test_tick_only_affects_matching_source(self):
        """Only effects from the ticking source are decremented."""
        actor = _make_actor("hero")
        enc = _make_encounter(actor)

        bless = _make_effect("bless_1", source_id="cleric", target_id="hero", remaining_rounds=2)
        hex_e = _make_effect("hex_1", source_id="warlock", target_id="hero", remaining_rounds=2)

        add_effect(enc, bless)
        add_effect(enc, hex_e)

        tick_effects(enc, source_id="cleric")

        target = next(a for a in enc.combatants if a.id == "hero")
        bless_eff = next(e for e in target.effects if e.id == "bless_1")
        hex_eff = next(e for e in target.effects if e.id == "hex_1")
        assert bless_eff.remaining_rounds == 1
        assert hex_eff.remaining_rounds == 2  # Unchanged

    def test_permanent_effects_not_ticked(self):
        """Effects with no remaining_rounds are not decremented."""
        actor = _make_actor("hero")
        enc = _make_encounter(actor)
        effect = _make_effect(
            "rage_1", source_id="barbarian", target_id="hero",
            remaining_rounds=None,
        )
        add_effect(enc, effect)

        tick_effects(enc, source_id="barbarian")

        target = next(a for a in enc.combatants if a.id == "hero")
        assert has_effect(target, "rage_1")


# ---------------------------------------------------------------------------
# Condition Cleanup
# ---------------------------------------------------------------------------

class TestConditionCleanup:
    def test_condition_attached_to_effect_removed_together(self):
        """When an effect expires, any condition it granted is also removed."""
        actor = _make_actor("hero")
        # Pre-attach a condition linked to the effect
        actor.conditions.append(
            ConditionInstance(
                condition=ConditionType.CHARMED,
                source_id="fey",
                source_effect_id="charm_1",
            )
        )
        enc = _make_encounter(actor)
        effect = _make_effect(
            "charm_1", source_id="fey", target_id="hero",
            remaining_rounds=1,
        )
        add_effect(enc, effect)

        tick_effects(enc, source_id="fey")

        target = next(a for a in enc.combatants if a.id == "hero")
        assert not has_effect(target, "charm_1")
        assert not any(c.condition == ConditionType.CHARMED for c in target.conditions)

    def test_unrelated_conditions_not_removed(self):
        """Conditions from other sources should not be touched."""
        actor = _make_actor("hero")
        actor.conditions.append(
            ConditionInstance(
                condition=ConditionType.PRONE,
                source_id="self",
                source_effect_id="",
            )
        )
        actor.conditions.append(
            ConditionInstance(
                condition=ConditionType.CHARMED,
                source_id="fey",
                source_effect_id="charm_1",
            )
        )
        enc = _make_encounter(actor)
        effect = _make_effect(
            "charm_1", source_id="fey", target_id="hero",
            remaining_rounds=1,
        )
        add_effect(enc, effect)

        tick_effects(enc, source_id="fey")

        target = next(a for a in enc.combatants if a.id == "hero")
        # Charm should be removed, prone should remain
        assert any(c.condition == ConditionType.PRONE for c in target.conditions)
        assert not any(c.condition == ConditionType.CHARMED for c in target.conditions)
