"""
D&D 5e Concentration Engine.

Handles concentration save DC, breaking concentration, and
the rule that casting a new concentration spell ends the previous one.
"""

from __future__ import annotations

import math

from ..schemas.enums import ConditionType
from ..schemas.instances import ActorInstance, EffectInstance, ConcentrationState
from ..schemas.encounter import EncounterState
from .effect_engine import add_effect, remove_effect


# ---------------------------------------------------------------------------
# Incapacitating conditions that break concentration
# ---------------------------------------------------------------------------

_INCAPACITATING_CONDITIONS = {
    ConditionType.INCAPACITATED,
    ConditionType.PARALYZED,
    ConditionType.PETRIFIED,
    ConditionType.STUNNED,
    ConditionType.UNCONSCIOUS,
}


# ---------------------------------------------------------------------------
# Core Functions
# ---------------------------------------------------------------------------

def concentration_dc(damage: int) -> int:
    """Calculate the concentration save DC from damage taken.

    PHB: DC = max(10, floor(damage / 2)).

    Args:
        damage: The damage dealt to the concentrating caster.

    Returns:
        The DC for the Constitution saving throw.
    """
    return max(10, math.floor(damage / 2))


def break_concentration(actor: ActorInstance, encounter: EncounterState) -> None:
    """Break an actor's concentration, removing the linked effect.

    If the actor is not concentrating, this is a no-op.

    Args:
        actor: The concentrating actor.
        encounter: The active encounter (to remove the effect from).
    """
    if not actor.concentration.is_concentrating:
        return

    effect_id = actor.concentration.effect_id
    if effect_id:
        remove_effect(encounter, effect_id)

    actor.concentration = ConcentrationState(
        is_concentrating=False,
        effect_id=None,
    )


def start_concentration(
    actor: ActorInstance,
    effect: EffectInstance,
    encounter: EncounterState,
) -> None:
    """Start concentrating on a new effect.

    If already concentrating, the previous concentration is broken first.
    The new effect is added to the encounter and the actor's concentration
    state is updated.

    Args:
        actor: The caster.
        effect: The new concentration effect to apply.
        encounter: The active encounter.
    """
    # Break previous concentration if any
    if actor.concentration.is_concentrating:
        break_concentration(actor, encounter)

    # Add the new effect
    add_effect(encounter, effect)

    # Update concentration state
    actor.concentration = ConcentrationState(
        is_concentrating=True,
        effect_id=effect.id,
    )


def check_incapacitated_breaks_concentration(
    actor: ActorInstance,
    encounter: EncounterState,
) -> None:
    """Check if any incapacitating condition should break concentration.

    Per PHB: being Incapacitated, Paralyzed, Petrified, Stunned,
    or Unconscious breaks concentration automatically.

    Args:
        actor: The actor to check.
        encounter: The active encounter.
    """
    if not actor.concentration.is_concentrating:
        return

    active_conditions = {c.condition for c in actor.conditions}
    if active_conditions & _INCAPACITATING_CONDITIONS:
        break_concentration(actor, encounter)
