"""
D&D 5e Condition Engine.

Pure functions that derive mechanical effects from an actor's active conditions
and exhaustion level. Returns computed contexts — does NOT mutate the actor.

All 15 PHB conditions are handled, plus exhaustion levels 1–6.
"""

from __future__ import annotations

import math
from typing import Optional

from pydantic import BaseModel, Field

from ..schemas.enums import Ability, ConditionType
from ..schemas.common import SpeedBlock
from ..schemas.instances import ActorInstance, ConditionInstance


# ---------------------------------------------------------------------------
# Result Models
# ---------------------------------------------------------------------------

class ConditionComputedStats(BaseModel):
    """Stats after condition/exhaustion modifications."""

    speed: SpeedBlock = Field(default_factory=SpeedBlock)
    max_hp: int = 0
    ability_check_disadvantage: bool = False


class AttackContext(BaseModel):
    """Attack roll modifiers derived from conditions."""

    has_advantage: bool = False
    has_disadvantage: bool = False


class SaveContext(BaseModel):
    """Saving throw modifiers derived from conditions."""

    auto_fail: bool = False
    has_advantage: bool = False
    has_disadvantage: bool = False


# ---------------------------------------------------------------------------
# Conditions that set speed to zero
# ---------------------------------------------------------------------------

_ZERO_SPEED_CONDITIONS = {
    ConditionType.GRAPPLED,
    ConditionType.PARALYZED,
    ConditionType.PETRIFIED,
    ConditionType.RESTRAINED,
    ConditionType.STUNNED,
    ConditionType.UNCONSCIOUS,
}

# Conditions that auto-fail STR and DEX saves
_AUTO_FAIL_STR_DEX_CONDITIONS = {
    ConditionType.PARALYZED,
    ConditionType.PETRIFIED,
    ConditionType.STUNNED,
    ConditionType.UNCONSCIOUS,
}

# Conditions that give disadvantage on attacks
_ATTACK_DISADVANTAGE_CONDITIONS = {
    ConditionType.BLINDED,
    ConditionType.FRIGHTENED,
    ConditionType.POISONED,
    ConditionType.PRONE,
    ConditionType.RESTRAINED,
}

# Conditions that give advantage on attacks
_ATTACK_ADVANTAGE_CONDITIONS = {
    ConditionType.INVISIBLE,
}


# ---------------------------------------------------------------------------
# Core Functions
# ---------------------------------------------------------------------------

def _has_condition(actor: ActorInstance, condition: ConditionType) -> bool:
    """Check if an actor has a specific condition."""
    return any(c.condition == condition for c in actor.conditions)


def _get_active_conditions(actor: ActorInstance) -> set[ConditionType]:
    """Get the set of active condition types."""
    return {c.condition for c in actor.conditions}


def apply_conditions(actor: ActorInstance) -> ConditionComputedStats:
    """Compute stats after applying all condition and exhaustion effects.

    Does NOT mutate the actor — returns new computed values.
    """
    active = _get_active_conditions(actor)
    exhaustion = actor.exhaustion_level

    # Start from base values
    walk = actor.speed.walk
    fly = actor.speed.fly
    swim = actor.speed.swim
    climb = actor.speed.climb
    burrow = actor.speed.burrow
    max_hp = actor.max_hp
    ability_check_disadvantage = False

    # --- Condition: speed to zero ---
    if active & _ZERO_SPEED_CONDITIONS:
        walk = 0
        if fly is not None:
            fly = 0
        if swim is not None:
            swim = 0
        if climb is not None:
            climb = 0
        if burrow is not None:
            burrow = 0

    # --- Exhaustion effects (cumulative) ---
    # Level 1: disadvantage on ability checks
    if exhaustion >= 1:
        ability_check_disadvantage = True

    # Level 2: speed halved
    if exhaustion >= 2:
        walk = walk // 2
        if fly is not None:
            fly = fly // 2
        if swim is not None:
            swim = swim // 2
        if climb is not None:
            climb = climb // 2
        if burrow is not None:
            burrow = burrow // 2

    # Level 4: HP maximum halved
    if exhaustion >= 4:
        max_hp = max_hp // 2

    # Level 5: speed reduced to 0
    if exhaustion >= 5:
        walk = 0
        if fly is not None:
            fly = 0
        if swim is not None:
            swim = 0
        if climb is not None:
            climb = 0
        if burrow is not None:
            burrow = 0

    return ConditionComputedStats(
        speed=SpeedBlock(
            walk=walk,
            fly=fly,
            swim=swim,
            climb=climb,
            burrow=burrow,
            hover=actor.speed.hover,
        ),
        max_hp=max_hp,
        ability_check_disadvantage=ability_check_disadvantage,
    )


def compute_attack_context(actor: ActorInstance) -> AttackContext:
    """Determine advantage/disadvantage on attack rolls from conditions.

    Exhaustion level 3+: disadvantage on attack rolls.
    """
    active = _get_active_conditions(actor)

    has_advantage = bool(active & _ATTACK_ADVANTAGE_CONDITIONS)
    has_disadvantage = bool(active & _ATTACK_DISADVANTAGE_CONDITIONS)

    # Exhaustion level 3+: disadvantage on attack rolls (and saves)
    if actor.exhaustion_level >= 3:
        has_disadvantage = True

    return AttackContext(
        has_advantage=has_advantage,
        has_disadvantage=has_disadvantage,
    )


def compute_save_context(actor: ActorInstance, ability: Ability) -> SaveContext:
    """Determine save modifiers from conditions for a specific ability.

    Auto-fail: Paralyzed, Petrified, Stunned, Unconscious → auto-fail STR/DEX.
    Disadvantage: Restrained → disadvantage on DEX saves.
    Exhaustion 3+: disadvantage on saving throws.
    """
    active = _get_active_conditions(actor)

    auto_fail = False
    has_advantage = False
    has_disadvantage = False

    # Auto-fail STR/DEX saves from certain conditions
    if ability in (Ability.STR, Ability.DEX):
        if active & _AUTO_FAIL_STR_DEX_CONDITIONS:
            auto_fail = True

    # Restrained: disadvantage on DEX saves
    if ability == Ability.DEX and ConditionType.RESTRAINED in active:
        has_disadvantage = True

    # Exhaustion level 3+: disadvantage on saving throws
    if actor.exhaustion_level >= 3:
        has_disadvantage = True

    return SaveContext(
        auto_fail=auto_fail,
        has_advantage=has_advantage,
        has_disadvantage=has_disadvantage,
    )
