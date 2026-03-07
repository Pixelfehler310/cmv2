# 05. Action Resolver

## 1. Overview

The Action Resolver is the high-level orchestration layer that unites the stateless mathematical engines with the combat state machine. It handles the complete pipeline for attacks, saving throws, and healing, taking an action from its initial dice roll down to the precise mutations applied to an actor's hit points and encounter budgets.

## 2. Core Concepts / Mechanics

- **Attack Resolution (`resolve_attack`)**: Computes contextual advantage/disadvantage from both the attacker's and target's conditions (e.g., Blinded or Paralyzed). It handles rolling the d20, applying critical hit logic (including auto-crits against Paralyzed/Unconscious targets in melee), comparing against Armor Class, and doubling damage dice before passing the final sum through the system's damage pipeline.
- **Save-Based Actions (`resolve_save_action`)**: For AoE or save-based spells like Fireball, this single pipeline first rolls the universally shared damage pool. It then individually checks each target's condition modifiers, rolls their saving throw against the spell DC, calculates their half or nullified damage, and applies mutations sequentially.
- **Healing Pipelines (`resolve_healing`)**: Computes healing rolls and explicitly prevents hit points from exceeding the actor's `max_hp`.
- **Encounter Integration (`resolve_and_apply`)**: Wraps the core pipelines to synchronize with the `EncounterState`. Successfully resolving an attack deducts from the initiating actor's `TurnBudget` and triggers automated flags (like concentration checks) on affected combatants.

```mermaid
sequenceDiagram
    participant Resolver as action_resolver
    participant Actor as Attacker
    participant Target
    participant Dice as DiceService
    participant Damage as damage pipeline

    Resolver->>Actor: compute_attack_context() (Adv/Disadv)
    Resolver->>Dice: roll_d20()
    Dice-->>Resolver: natural_roll
    Resolver->>Resolver: Check Nat 1 / Nat 20 / Target AC
    Resolver->>Dice: roll_damage() (Double dice if critical)
    Dice-->>Resolver: total_damage
    Resolver->>Damage: apply_damage(amount, damage_type)
    Damage->>Target: Evaluate Immunities/Resistances/Temp HP
    Damage-->>Resolver: DamageResult
    Resolver-->>Resolver: Consume TurnBudget
```

## 3. Key Schemas / Interfaces

- **`AttackResult`**: Details the outcome of an attack, specifying a boolean `hit`, `is_critical`, the isolated natural `roll_used`, and attaching the downstream `DamageResult`.
- **`SaveTargetResult`**: Represents an individual target's outcome within an AoE or save cast, containing a `passed` boolean, the `save_roll`, and the evaluated `damage` applied.
- **`SaveActionResult`**: A container schema housing a list of `SaveTargetResult` entries for multi-target actions.
- **`HealingResult`**: Exposes the `hp_restored` delta alongside the actor's `new_hp`.

## 4. Example Usage

```python
from systems.dnd5e.engine import action_resolver
from systems.dnd5e.schemas.definitions import ActionDefinition

# Define a basic longsword action
longsword = ActionDefinition(
    name="Longsword",
    action_type="melee_weapon",
    attack_bonus=5,
    damage_dice="1d8",
    damage_bonus=3,
    damage_type="slashing"
)

# Resolve the attack, applying damage and deducting the action from the budget
result = action_resolver.resolve_and_apply(
    encounter_state,
    attacker=fighter,
    target=goblin,
    action_def=longsword,
    advantage=True  # Optional manual override
)

if result.hit:
    print(f"Hit! Dealt {result.total_damage} damage.")
    print(f"Goblin has {goblin.current_hp} HP remaining.")
```

## 5. Dependencies

- `schemas/instances.py` (ActorInstance)
- `schemas/definitions.py` (ActionDefinition)
- `engine/dice.py` (Rolling engine for d20s and dynamic damage strings)
- `engine/damage.py` (The target application pipeline)
- `engine/condition_engine.py` (Context generation for advantage/disadvantage)
- `engine/combat_state.py` (TurnBudget reduction)
- `engine/concentration.py` (Concentration DC logic)
