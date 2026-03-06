"""
D&D 5e Stat Calculator.

Pure functions for deriving ability modifiers, proficiency bonuses,
and computed stats from an ActorInstance with applied effects.

Effect stacking order: SET → BONUS → MULTIPLY → Conditions.
"""

from __future__ import annotations

import math
from typing import Optional

from pydantic import BaseModel, Field

from ..schemas.enums import Ability, EffectType
from ..schemas.common import AbilityScores, SpeedBlock
from ..schemas.instances import ActorInstance, EffectInstance


# ---------------------------------------------------------------------------
# Result Models
# ---------------------------------------------------------------------------

class ComputedStats(BaseModel):
    """Derived stats after applying all effects."""

    armor_class: int = 10
    speed: SpeedBlock = Field(default_factory=SpeedBlock)
    attack_bonus: int = 0
    save_bonuses: dict[str, int] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Core Calculations
# ---------------------------------------------------------------------------

def calculate_modifier(score: int) -> int:
    """Calculate the ability modifier from an ability score.

    PHB: modifier = floor((score - 10) / 2)
    """
    return math.floor((score - 10) / 2)


def calculate_proficiency_bonus(level: int) -> int:
    """Calculate proficiency bonus from character/CR level.

    PHB table:
      1-4  → +2
      5-8  → +3
      9-12 → +4
      13-16 → +5
      17-20 → +6
    """
    return math.ceil(level / 4) + 1


# ---------------------------------------------------------------------------
# Effect Stacking
# ---------------------------------------------------------------------------

def _get_ability_score(actor: ActorInstance, ability: Ability) -> int:
    """Get the raw ability score for a given ability."""
    mapping = {
        Ability.STR: actor.abilities.strength,
        Ability.DEX: actor.abilities.dexterity,
        Ability.CON: actor.abilities.constitution,
        Ability.INT: actor.abilities.intelligence,
        Ability.WIS: actor.abilities.wisdom,
        Ability.CHA: actor.abilities.charisma,
    }
    return mapping[ability]


def _compute_stat(
    base_value: int,
    effects: list[EffectInstance],
    stat_name: str,
) -> int:
    """Apply effects to a base stat in the correct stacking order.

    Order: SET (take max of base vs set values) → BONUS → MULTIPLY
    """
    relevant = [e for e in effects if e.target_stat == stat_name]

    # 1. SET: take the highest between base and all SET values
    set_effects = [e for e in relevant if e.type == EffectType.SET]
    value = base_value
    for effect in set_effects:
        effect_val = int(effect.value)
        value = max(value, effect_val)

    # 2. BONUS: additive
    bonus_effects = [e for e in relevant if e.type == EffectType.BONUS]
    for effect in bonus_effects:
        value += int(effect.value)

    # 3. MULTIPLY: multiplicative
    multiply_effects = [e for e in relevant if e.type == EffectType.MULTIPLY]
    for effect in multiply_effects:
        value = math.floor(value * float(effect.value))

    return value


def compute_stats(actor: ActorInstance) -> ComputedStats:
    """Compute derived stats for an actor after applying all effects.

    Applies effects in order: SET → BONUS → MULTIPLY.
    Does NOT apply condition effects — use condition_engine for that.
    """
    computed_ac = _compute_stat(actor.armor_class, actor.effects, "armor_class")

    computed_speed = SpeedBlock(
        walk=_compute_stat(actor.speed.walk, actor.effects, "speed_walk"),
        fly=_compute_stat(actor.speed.fly or 0, actor.effects, "speed_fly") or actor.speed.fly,
        swim=_compute_stat(actor.speed.swim or 0, actor.effects, "speed_swim") or actor.speed.swim,
        climb=_compute_stat(actor.speed.climb or 0, actor.effects, "speed_climb") or actor.speed.climb,
        burrow=_compute_stat(actor.speed.burrow or 0, actor.effects, "speed_burrow") or actor.speed.burrow,
        hover=actor.speed.hover,
    )

    return ComputedStats(
        armor_class=computed_ac,
        speed=computed_speed,
    )


# ---------------------------------------------------------------------------
# Spell Save DC
# ---------------------------------------------------------------------------

def compute_spell_save_dc(actor: ActorInstance, ability: Ability) -> int:
    """Compute spell save DC.

    PHB: DC = 8 + proficiency bonus + ability modifier.
    """
    ability_mod = calculate_modifier(_get_ability_score(actor, ability))
    return 8 + actor.proficiency_bonus + ability_mod
