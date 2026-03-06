"""
D&D 5e Damage Pipeline.

Pure function for damage resolution following PHB order:
1. Immunity → 0 damage
2. Resistance → halve (floor)
3. Vulnerability → double
4. Temp HP absorbs first
5. Current HP reduced (floor at 0)
6. Death detection (monsters die at 0; PCs go unconscious)
"""

from __future__ import annotations

from typing import Optional, List

from pydantic import BaseModel

from ..schemas.enums import ActorType, DamageType
from ..schemas.instances import ActorInstance


# ---------------------------------------------------------------------------
# Result Model
# ---------------------------------------------------------------------------

class DamageResult(BaseModel):
    """Result of applying damage through the full pipeline."""

    damage_dealt: int  # After immunity/resistance/vulnerability
    damage_absorbed_by_temp: int = 0
    remaining_hp: int
    remaining_temp_hp: int = 0
    is_dead: bool = False
    is_unconscious: bool = False


# ---------------------------------------------------------------------------
# Damage Pipeline
# ---------------------------------------------------------------------------

def apply_damage(
    actor: ActorInstance,
    *,
    amount: int,
    damage_type: DamageType,
    damage_immunities: Optional[List[DamageType]] = None,
    damage_resistances: Optional[List[DamageType]] = None,
    damage_vulnerabilities: Optional[List[DamageType]] = None,
) -> DamageResult:
    """Apply damage through the full PHB pipeline.

    The immunity/resistance/vulnerability lists are passed explicitly
    rather than read from the actor, because MonsterDefinition stores
    them as SRD strings that need parsing at a higher layer.

    Pipeline order:
    1. Immunity check → 0 damage
    2. Resistance → halve (floor)
    3. Vulnerability → double
    4. Temp HP absorbs first
    5. Current HP reduced (floor at 0)
    6. Death check

    Args:
        actor: The target being damaged.
        amount: Raw damage amount.
        damage_type: Type of damage.
        damage_immunities: Types the actor is immune to.
        damage_resistances: Types the actor resists.
        damage_vulnerabilities: Types the actor is vulnerable to.

    Returns:
        DamageResult with final HP and death status.
    """
    immunities = damage_immunities or []
    resistances = damage_resistances or []
    vulnerabilities = damage_vulnerabilities or []

    effective = amount

    # 1. Immunity
    if damage_type in immunities:
        return DamageResult(
            damage_dealt=0,
            remaining_hp=actor.current_hp,
            remaining_temp_hp=actor.temp_hp,
        )

    # 2. Resistance (halve, floor)
    if damage_type in resistances:
        effective = effective // 2

    # 3. Vulnerability (double)
    if damage_type in vulnerabilities:
        effective = effective * 2

    # 4. Temp HP absorbs first
    temp_absorbed = min(actor.temp_hp, effective)
    remaining_damage = effective - temp_absorbed
    new_temp_hp = actor.temp_hp - temp_absorbed

    # 5. Current HP reduced (floor at 0)
    new_hp = max(0, actor.current_hp - remaining_damage)

    # 6. Death / unconsciousness
    is_dead = False
    is_unconscious = False
    if new_hp == 0:
        if actor.actor_type == ActorType.PLAYER_CHARACTER:
            is_unconscious = True
        else:
            is_dead = True

    return DamageResult(
        damage_dealt=effective,
        damage_absorbed_by_temp=temp_absorbed,
        remaining_hp=new_hp,
        remaining_temp_hp=new_temp_hp,
        is_dead=is_dead,
        is_unconscious=is_unconscious,
    )
