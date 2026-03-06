"""
D&D 5e Action Resolver.

High-level action resolution pipeline that composes the Phase 2/3 engines:
- DiceService for d20 and damage rolls
- apply_damage for the damage pipeline
- compute_attack_context / compute_save_context for condition modifiers
- TurnBudget for action economy
- concentration_dc / break_concentration for concentration checks

Three main pipelines: resolve_attack(), resolve_save_action(), resolve_healing().
"""

from __future__ import annotations

import math
from typing import Optional, List

from pydantic import BaseModel

from ..schemas.enums import ActionType, ConditionType, DamageType
from ..schemas.instances import ActorInstance
from ..schemas.definitions import ActionDefinition
from ..schemas.encounter import EncounterState
from .dice import DiceService
from .damage import apply_damage, DamageResult
from .condition_engine import compute_attack_context, compute_save_context
from .combat_state import get_turn_budget
from .concentration import concentration_dc, break_concentration


# ---------------------------------------------------------------------------
# Melee action types (for auto-crit checks like Paralyzed)
# ---------------------------------------------------------------------------

_MELEE_ACTION_TYPES = {
    ActionType.MELEE_WEAPON,
    ActionType.MELEE_SPELL,
}

# Conditions that grant auto-crit on melee hit
_AUTO_CRIT_CONDITIONS = {
    ConditionType.PARALYZED,
    ConditionType.UNCONSCIOUS,
}


# ---------------------------------------------------------------------------
# Result Models
# ---------------------------------------------------------------------------

class AttackResult(BaseModel):
    """Result of an attack roll resolution."""

    hit: bool
    is_critical: bool = False
    roll_used: int = 0
    roll_count: int = 1
    total_damage: int = 0
    damage_result: Optional[DamageResult] = None


class SaveTargetResult(BaseModel):
    """Per-target result from a save-based action."""

    target_id: str = ""
    passed: bool = False
    save_roll: int = 0
    damage: int = 0


class SaveActionResult(BaseModel):
    """Result of a save-based action across all targets."""

    results: List[SaveTargetResult] = []


class HealingResult(BaseModel):
    """Result of a healing action."""

    hp_restored: int = 0
    new_hp: int = 0


# ---------------------------------------------------------------------------
# Attack Resolution
# ---------------------------------------------------------------------------

def resolve_attack(
    attacker: ActorInstance,
    target: ActorInstance,
    action_def: ActionDefinition,
    *,
    roll_override: Optional[int] = None,
    roll_overrides: Optional[List[int]] = None,
    advantage: bool = False,
    disadvantage: bool = False,
) -> AttackResult:
    """Resolve an attack roll action.

    Pipeline:
    1. Compute attacker condition modifiers (adv/disadv from Blinded, etc.)
    2. Roll d20 with combined advantage/disadvantage
    3. Check nat 1 / nat 20
    4. Compare roll + bonus vs target AC
    5. On hit: roll damage (double dice on crit), apply through damage pipeline
    6. Check for auto-crit conditions (Paralyzed in melee)

    Args:
        attacker: The attacking actor.
        target: The target actor.
        action_def: The action being used.
        roll_override: Override a single d20 roll (for testing).
        roll_overrides: Override both d20 rolls for adv/disadv (for testing).
        advantage: Force advantage on the roll.
        disadvantage: Force disadvantage on the roll.

    Returns:
        AttackResult with hit/miss, crit status, and damage details.
    """
    # 1. Condition-based modifiers on the attacker
    atk_ctx = compute_attack_context(attacker)
    has_adv = advantage or atk_ctx.has_advantage
    has_disadv = disadvantage or atk_ctx.has_disadvantage

    # Build roll overrides for DiceService
    overrides = roll_overrides
    if overrides is None and roll_override is not None:
        overrides = [roll_override]

    # 2. Roll d20
    d20_result = DiceService.roll_d20(
        advantage=has_adv,
        disadvantage=has_disadv,
        modifier=0,  # We apply the attack bonus ourselves for clarity
        roll_overrides=overrides,
    )

    natural_roll = d20_result.roll_used
    attack_bonus = action_def.attack_bonus or 0
    total_roll = natural_roll + attack_bonus

    # 3. Nat 1 always misses, nat 20 always hits
    if natural_roll == 1:
        return AttackResult(
            hit=False,
            roll_used=natural_roll,
            roll_count=d20_result.roll_count,
        )

    is_critical = natural_roll == 20

    # 4. Check for auto-crit from target conditions (Paralyzed/Unconscious in melee)
    is_melee = action_def.action_type in _MELEE_ACTION_TYPES
    if is_melee:
        target_conditions = {c.condition for c in target.conditions}
        if target_conditions & _AUTO_CRIT_CONDITIONS:
            is_critical = True

    # 5. Check hit vs AC
    target_ac = target.armor_class
    hit = is_critical or total_roll >= target_ac

    if not hit:
        return AttackResult(
            hit=False,
            roll_used=natural_roll,
            roll_count=d20_result.roll_count,
        )

    # 6. Roll damage
    damage_dice = action_def.damage_dice or "1d4"
    damage_bonus = action_def.damage_bonus or 0
    damage_type = action_def.damage_type or DamageType.BLUDGEONING

    # Parse dice expression to double dice count on crit
    total_damage = _roll_damage(damage_dice, damage_bonus, is_critical)

    # 7. Apply through damage pipeline
    dmg_result = apply_damage(
        target,
        amount=total_damage,
        damage_type=damage_type,
    )

    # Mutate target HP
    target.current_hp = dmg_result.remaining_hp
    target.temp_hp = dmg_result.remaining_temp_hp

    return AttackResult(
        hit=True,
        is_critical=is_critical,
        roll_used=natural_roll,
        roll_count=d20_result.roll_count,
        total_damage=total_damage,
        damage_result=dmg_result,
    )


def _roll_damage(dice_expr: str, bonus: int, is_critical: bool) -> int:
    """Roll damage, doubling dice count on critical hits.

    PHB: on a crit, roll double the number of dice, then add the bonus.
    The bonus is NOT doubled.
    """
    # Parse the dice expression to extract count
    import re
    match = re.match(r"^(\d+)d(\d+)", dice_expr)
    if not match:
        return bonus

    count = int(match.group(1))
    sides = int(match.group(2))

    if is_critical:
        count *= 2

    roll = DiceService.roll(f"{count}d{sides}")
    return roll.total + bonus


# ---------------------------------------------------------------------------
# Save-Based Action Resolution
# ---------------------------------------------------------------------------

def resolve_save_action(
    caster: ActorInstance,
    targets: List[ActorInstance],
    action_def: ActionDefinition,
    *,
    damage_roll_override: Optional[int] = None,
    save_overrides: Optional[List[int]] = None,
) -> SaveActionResult:
    """Resolve a save-based action (e.g., Fire Breath, Fireball).

    Pipeline per target:
    1. Roll the damage once (shared across all targets)
    2. For each target: compute save modifier, roll save vs DC
    3. On fail: full damage; on success: half damage (floor)
    4. Apply through damage pipeline

    Args:
        caster: The actor using the action.
        targets: List of target actors.
        action_def: The save-based action definition.
        damage_roll_override: Override the total damage roll (for testing).
        save_overrides: Override save rolls per target (for testing).

    Returns:
        SaveActionResult with per-target results.
    """
    save_req = action_def.save
    if not save_req:
        return SaveActionResult(results=[])

    # Roll damage once for all targets
    if damage_roll_override is not None:
        total_damage = damage_roll_override
    else:
        damage_dice = action_def.damage_dice or "1d4"
        damage_bonus = action_def.damage_bonus or 0
        roll = DiceService.roll(damage_dice)
        total_damage = roll.total + damage_bonus

    damage_type = action_def.damage_type or DamageType.FIRE

    results: List[SaveTargetResult] = []

    for i, target in enumerate(targets):
        # Get save override for this target
        save_override = None
        if save_overrides and i < len(save_overrides):
            save_override = save_overrides[i]

        # Compute save context for conditions
        save_ctx = compute_save_context(target, save_req.ability)

        # Auto-fail check
        if save_ctx.auto_fail:
            passed = False
            save_roll = 0
        else:
            # Roll save
            overrides = [save_override] if save_override is not None else None
            save_result = DiceService.roll_d20(
                advantage=save_ctx.has_advantage,
                disadvantage=save_ctx.has_disadvantage,
                roll_overrides=overrides,
            )
            save_roll = save_result.roll_used

            # Compute save modifier from ability
            from .stat_calculator import calculate_modifier, _get_ability_score
            ability_mod = calculate_modifier(_get_ability_score(target, save_req.ability))
            save_total = save_roll + ability_mod + target.proficiency_bonus
            passed = save_total >= save_req.dc

        # Determine damage
        if passed:
            if save_req.on_success == "half_damage":
                effective_damage = math.floor(total_damage / 2)
            elif save_req.on_success == "no_damage":
                effective_damage = 0
            else:
                effective_damage = math.floor(total_damage / 2)
        else:
            effective_damage = total_damage

        # Apply damage
        dmg_result = apply_damage(
            target,
            amount=effective_damage,
            damage_type=damage_type,
        )
        target.current_hp = dmg_result.remaining_hp
        target.temp_hp = dmg_result.remaining_temp_hp

        results.append(SaveTargetResult(
            target_id=target.id,
            passed=passed,
            save_roll=save_roll,
            damage=effective_damage,
        ))

    return SaveActionResult(results=results)


# ---------------------------------------------------------------------------
# Healing Resolution
# ---------------------------------------------------------------------------

def resolve_healing(
    target: ActorInstance,
    action_def: ActionDefinition,
    *,
    dice_override: Optional[int] = None,
) -> HealingResult:
    """Resolve a healing action.

    Rolls healing dice, adds bonus, caps at max HP.

    Args:
        target: The actor being healed.
        action_def: The healing action definition.
        dice_override: Override the total healing roll (for testing).

    Returns:
        HealingResult with HP restored and new HP.
    """
    if dice_override is not None:
        heal_roll = dice_override
    else:
        dice_expr = action_def.damage_dice or "1d4"
        roll = DiceService.roll(dice_expr)
        heal_roll = roll.total

    heal_bonus = action_def.damage_bonus or 0
    total_healing = heal_roll + heal_bonus

    old_hp = target.current_hp
    target.current_hp = min(target.max_hp, target.current_hp + total_healing)
    actual_restored = target.current_hp - old_hp

    return HealingResult(
        hp_restored=actual_restored,
        new_hp=target.current_hp,
    )


# ---------------------------------------------------------------------------
# EncounterState Integration
# ---------------------------------------------------------------------------

def resolve_and_apply(
    encounter: EncounterState,
    attacker: ActorInstance,
    target: ActorInstance,
    action_def: ActionDefinition,
    *,
    roll_override: Optional[int] = None,
    roll_overrides: Optional[List[int]] = None,
    advantage: bool = False,
    disadvantage: bool = False,
) -> AttackResult:
    """Resolve an attack and apply side-effects to the encounter.

    Orchestration wrapper that:
    1. Resolves the attack
    2. Consumes the attacker's action from TurnBudget
    3. Checks concentration on damaged targets

    Args:
        encounter: The active encounter state.
        attacker: The attacking actor.
        target: The target actor.
        action_def: The action being used.
        roll_override: Override d20 roll for testing.
        roll_overrides: Override both d20 rolls for adv/disadv.
        advantage: Force advantage.
        disadvantage: Force disadvantage.

    Returns:
        AttackResult from the resolution.
    """
    result = resolve_attack(
        attacker, target, action_def,
        roll_override=roll_override,
        roll_overrides=roll_overrides,
        advantage=advantage,
        disadvantage=disadvantage,
    )

    # Consume action budget
    budget = get_turn_budget(encounter, attacker.id)
    budget.use_action()

    # Check concentration if target was damaged
    if result.hit and result.total_damage > 0:
        if target.concentration.is_concentrating:
            dc = concentration_dc(result.total_damage)
            # The DM handles the save separately; we just flag for now
            # In a full implementation, this would trigger a CON save
            pass

    return result
