# Module 06 — Action Resolver

> **As-Is Documentation** | File: `systems/dnd5e/engine/action_resolver.py`

## Overview

The Action Resolver is the highest-level pure rules engine component. It **composes** all the stateless engines (dice, damage, condition, concentration, combat_state) into three complete resolution pipelines: **attack**, **save-based action**, and **healing**. A fourth convenience wrapper `resolve_and_apply()` integrates with the `EncounterState`.

---

## Pipeline Composition Map

```mermaid
graph TD
    AR["action_resolver.py"]
    DICE["DiceService\n(roll_d20, roll)"]
    DMG["apply_damage()"]
    COND["compute_attack_context()\ncompute_save_context()"]
    CONCDC["concentration_dc()"]
    BUDGET["get_turn_budget()\n.use_action()"]
    STATCALC["calculate_modifier()"]

    AR --> DICE
    AR --> DMG
    AR --> COND
    AR --> CONCDC
    AR --> BUDGET
    AR --> STATCALC
```

---

## Result Models

```python
class AttackResult(BaseModel):
    hit: bool
    is_critical: bool = False
    roll_used: int = 0        # Natural d20 value used
    roll_count: int = 1       # 1 for normal, 2 for adv/disadv
    total_damage: int = 0
    damage_result: Optional[DamageResult] = None

class SaveTargetResult(BaseModel):
    target_id: str
    passed: bool
    save_roll: int            # Natural d20 value
    damage: int               # Effective damage applied

class SaveActionResult(BaseModel):
    results: List[SaveTargetResult]

class HealingResult(BaseModel):
    hp_restored: int
    new_hp: int
```

---

## `resolve_attack()` Pipeline

```mermaid
flowchart TD
    A["resolve_attack(attacker, target, action_def)"]
    B["1. compute_attack_context(attacker)\n→ AttackContext (adv/disadv from conditions)"]
    C["2. DiceService.roll_d20(\n  advantage=has_adv | param,\n  disadvantage=has_disadv | param\n)"]
    D{natural_roll == 1?}
    E["Return AttackResult(hit=False)"]
    F["natural_roll == 20 → is_critical = True"]
    G{Is melee action?\nTarget is Paralyzed/Unconscious?}
    H["is_critical = True (auto-crit)"]
    I{total_roll >= target.armor_class OR is_critical?}
    J["Return AttackResult(hit=False)"]
    K["_roll_damage(dice_expr, bonus, is_critical)\n→ On crit: double dice count, don't double bonus"]
    L["apply_damage(target, amount, damage_type)"]
    M["Mutate target.current_hp & temp_hp"]
    N["Return AttackResult(hit=True, ...)"]

    A --> B --> C --> D
    D -- Yes --> E
    D -- No --> F --> G
    G -- Yes --> H
    G -- No --> I
    H --> I
    I -- Miss --> J
    I -- Hit --> K --> L --> M --> N
```

### PHB Critical Hit Rules
- Natural 20: always a critical hit
- Paralyzed or Unconscious target in melee: auto-crit
- On crit: **dice count** is doubled; the flat damage bonus is NOT doubled

---

## `resolve_save_action()` Pipeline

Used for AoE spells, breath weapons, and any save-based effect (e.g. Fireball, Dragon Breath).

```mermaid
sequenceDiagram
    participant Action as action_resolver
    participant Dice as DiceService
    participant CondEngine as condition_engine
    participant DmgPipeline as damage.py

    Action->>Dice: roll(damage_dice) → total_damage (ONCE for all targets)
    loop For each target
        Action->>CondEngine: compute_save_context(target, ability)
        alt auto_fail
            Action->>Action: passed = False, save_roll = 0
        else Normal save
            Action->>Dice: roll_d20(adv=ctx.adv, disadv=ctx.disadv)
            Action->>Action: save_total = roll + ability_mod + proficiency
            Action->>Action: passed = save_total >= action_def.save.dc
        end
        alt passed and on_success="half_damage"
            Action->>Action: effective_damage = floor(total_damage / 2)
        else passed and on_success="no_damage"
            Action->>Action: effective_damage = 0
        else failed
            Action->>Action: effective_damage = total_damage
        end
        Action->>DmgPipeline: apply_damage(target, effective_damage, type)
        Action->>Action: mutate target hp
    end
```

### Save Calculation Detail
```
save_total = save_roll + ability_modifier(target, save.ability) + target.proficiency_bonus
```

> [!NOTE]
> Proficiency bonus is **always** added here. Proper proficiency tracking (where only proficient saves add the bonus) is a known gap — see `backend_todos.md`.

---

## `resolve_healing()` Pipeline

```python
def resolve_healing(target, action_def, *, dice_override=None) -> HealingResult:
    heal_total = DiceService.roll(action_def.damage_dice).total + (action_def.damage_bonus or 0)
    target.current_hp = min(target.max_hp, target.current_hp + heal_total)
    # Returns HealingResult with hp_restored and new_hp
```

HP is capped at `max_hp`. Cannot over-heal.

---

## `resolve_and_apply()` — Encounter Integration

The `resolve_and_apply()` wrapper ties the pure attack resolver into the encounter state:

1. Calls `resolve_attack()`
2. Calls `get_turn_budget(encounter, attacker.id).use_action()`
3. If the target took damage AND is concentrating: computes `concentration_dc(damage)` — **currently only flagged; the actual CON save is not auto-resolved**

> [!WARNING]
> The CON save for concentration checks inside `resolve_and_apply()` is **stubbed with a `pass`**. The ws_handler is expected to trigger the save separately. This is tracked in `backend_todos.md`.

---

## Dependencies

```mermaid
graph LR
    action_resolver --> dice
    action_resolver --> damage
    action_resolver --> condition_engine
    action_resolver --> combat_state
    action_resolver --> concentration
    action_resolver --> stat_calculator
    action_resolver --> ActorInstance
    action_resolver --> ActionDefinition
    action_resolver --> EncounterState
```
