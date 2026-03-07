# 03_stateless_rules_engine

## 1. Overview

The stateless rules engine contains pure functions for D&D 5e math, including dice rolling, stat calculation, condition processing, and damage resolution. It relies entirely on immutable parameters and does not mutate engine state directly, returning derived results or calculated contexts for higher-level systems to apply.

## 2. Core Concepts / Mechanics

- **Dice Service (`engine/dice.py`)**: Parses standard dice expressions (e.g., `2d10+8`) and rolls dice, supporting `advantage`, `disadvantage`, and deterministic testing via optional random seeds.
- **Stat Calculator (`engine/stat_calculator.py`)**: Derives an actor's ability modifiers, proficiency bonuses, and computes their final stats (like Armor Class and Speed) by applying active effects. Effect stacking follows a strict order of operations: `SET` (take max) → `BONUS` (additive) → `MULTIPLY` (multiplicative).
- **Condition Engine (`engine/condition_engine.py`)**: Computes the mechanical impact of the 15 PHB conditions and exhaustion levels. It accounts for mutually inclusive/exclusive states, auto-failures, speed reductions to 0, and attack/save contexts (advantage/disadvantage).
- **Damage Pipeline (`engine/damage.py`)**: Resolves damage following the true PHB order:
  1. Immunity check (reduces damage to 0).
  2. Resistance check (halves damage, rounded down).
  3. Vulnerability check (doubles damage).
  4. Temporary HP absorption.
  5. Current HP reduction (floored at 0).
  6. Death/Unconsciousness check based on actor type.

## 3. Key Schemas / Interfaces

**`DiceRoll`** (from `dice.py`)

- `individual_rolls: list[int]` - The raw dice values rolled.
- `modifier: int` - The flat modifier added.
- `total: int` - The final calculated total of the roll.

**`ComputedStats`** (from `stat_calculator.py`)

- `armor_class: int` - The final AC after effects.
- `speed: SpeedBlock` - Computed speeds applied sequentially.

**`ConditionComputedStats`** (from `condition_engine.py`)

- `speed: SpeedBlock` - Final speeds considering conditions (e.g., 0 speed if Grappled).
- `ability_check_disadvantage: bool` - Derived from exhaustion.

**`AttackContext`** / **`SaveContext`** (from `condition_engine.py`)

- `has_advantage` & `has_disadvantage`
- `auto_fail: bool` (for saves, e.g., Paralyzed).

**`DamageResult`** (from `damage.py`)

- `damage_dealt: int` - Effective damage after resistances/immunities.
- `damage_absorbed_by_temp: int` - How much temporary hp was stripped.
- `remaining_hp: int` - New current HP.
- `remaining_temp_hp: int` - New temporary HP.
- `is_dead` / `is_unconscious: bool` - Status flags resulting from the damage.

## 4. Example Usage

```python
from systems.dnd5e.engine.dice import DiceService
from systems.dnd5e.engine.stat_calculator import compute_stats
from systems.dnd5e.engine.damage import apply_damage
from schemas.enums import DamageType

# 1. Roll an attack
roll = DiceService.roll_d20(advantage=True, modifier=5)
print(f"Attack rolled: {roll.total} using role: {roll.roll_used}")

# 2. Compute AC for a target
stats = compute_stats(target_actor)
print(f"Target AC: {stats.armor_class}")

# 3. Apply Damage
damage_result = apply_damage(
    actor=target_actor,
    amount=15,
    damage_type=DamageType.FIRE,
    damage_resistances=[DamageType.FIRE]
)
print(f"Damage taken: {damage_result.damage_dealt}")
print(f"HP remaining: {damage_result.remaining_hp}")
```

## 5. Dependencies

- `schemas/enums.py`: Uses core enumerations like `Ability`, `EffectType`, `DamageType`, and `ConditionType`.
- `schemas/common.py`: Uses `AbilityScores` and `SpeedBlock`.
- `schemas/instances.py`: Requires `ActorInstance`, `EffectInstance`, and `ConditionInstance`.
