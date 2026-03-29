# V2 Action & Mechanics Specification

Provides the exact schemas for `ActionOperationSpec` and `ModifierSpec` used within V05 content objects (`ItemDefinition`, `AbilityDefinition`, `SpellDefinition`). The definitions here bridge static data with the V2 interactive execution graphs.

## 1. Executive Summary & V2 Philosophy

The V2 combat execution engine abandons the concept of "monolithic" actions (e.g., "The player attacks and deals 5 damage"). Instead, V2 relies on **Operation Graphs**. A single action (like casting *Fireball* or triggering a *Divine Smite*) consists of sequential steps: deducting budgets, rolling saves, confirming choices, applying effects, and managing states.

The `ActionOperationSpec` and `ModifierSpec` payloads defined here are the **instructions** the V2 engine uses to dynamically build and execute those graphs deterministically across the network, resolving problems like reaction triggers, reactive saving throws, and condition lifecycles.

---

## 2. Modifier & Passive Effect Contracts (`ModifierSpec`)

A `ModifierSpec` defines a persistent or temporary passive effect applied to an `ExecutableActorRuntime`. 

### A. Core Types
A modifier can alter a numerical statistic, a dice roll rule (Advantage/Disadvantage), or apply a boolean state.

```json
// Flat Numerical Bonus (e.g., Ring of Protection)
{
  "modifier_type": "flat",
  "target_stat": "ac",
  "value": 1,
  "stack_group": "unique" // Determines if multiple identical buffs stack
}
```

```json
// Dice-Based Modification (e.g., Bless)
{
  "modifier_type": "dice",
  "target_stat": "attack_roll",
  "dice_notation": "1d4",
  "condition_gate": null // Applied unconditionally
}
```

```json
// Execution Rule Change (e.g., Cloak of Elvenkind)
{
  "modifier_type": "rule_override",
  "target_stat": "stealth_check",
  "override_value": "advantage"
}
```

---

## 3. Action Operation Contracts (`ActionOperationSpec`)

An `ActionOperationSpec` defines the rules for activating a feature. Every spec contains universal metadata (the cost of doing it) and heavily polymorphic payload mechanics.

### A. Universal Schema Properties
These exist on *every* `ActionOperationSpec` regardless of what it actually does.

```json
{
  "activation_cost": "action", // action, bonus_action, reaction, free
  "activation_trigger": null, // Required if cost is 'reaction' (e.g., "on_attacked")
  "resource_consumption": {
    "resource_type": "spell_slot_level", // spell_slot, ki_point, charge, custom
    "count": 3 
  },
  "targeting_spec": {
    "type": "single", // single, self, aoe_sphere, aoe_cone, line
    "range_feet": 150,
    "max_targets": 1,
    "radius_feet": 20 // Required for AoE
  },
  "operation_type": "save", // attack_roll, save, heal, effect_application
  "payload": { ... } // See specific execution mechanics below
}
```

### B. Execution Mechanics (The Poly-Payloads)

#### 1. Attack Roll (`operation_type: attack_roll`)
Used for weapons and targeting spells (e.g., Longsword, Firebolt). It requires V2 to execute an AC contest.

```json
// Payload for a Longsword
{
  "attack_type": "melee_weapon", // melee_weapon, ranged_weapon, melee_spell, ranged_spell
  "stat_override": null, // If null, uses STR/DEX dynamically based on finesse
  "damage_instances": [
    {
      "dice_notation": "1d8",
      "damage_type": "slashing",
      "add_stat_modifier": true
    }
  ],
  "on_hit_effects": [], // e.g., applying poison
  "critical_threshold": 20
}
```
**V2 Engine Process:** 
1. Deduct action budget. 
2. Ask player for target. 
3. Roll 1d20 + Stat + Prof. 
4. Compare against Target AC. 
5. If hit, roll `damage_instances` and deduct Target HP.

#### 2. Saving Throw Area of Effect (`operation_type: save`)
Used for explosions, breath weapons, etc. Requires V2 to spawn a save request for multiple receivers.

```json
// Payload for a Fireball
{
  "save_stat": "dex",
  "save_dc_override": null, // If null, uses caster's spell save DC
  "failure_damage": [
    {
      "dice_notation": "8d6",
      "damage_type": "fire"
    }
  ],
  "success_rule": "half_damage", // half_damage, no_damage
  "apply_conditions_on_fail": [] 
}
```
**V2 Engine Process:** 
1. Deduct spell slot. 
2. Determine targets in AoE. 
3. Emit `SAVE_REQUEST` event to target clients. 
4. Await deterministic dice rolls from targets (or server auto-roll). 
5. Calculate partial/full damage matrix and apply recursively.

#### 3. Healing / Utility (`operation_type: heal`)
```json
// Payload for Cure Wounds
{
  "heal_dice": "1d8",
  "add_stat_modifier": true,
  "stat_used": "spellcasting_modifier",
  "temp_hp": false,
  "removes_conditions": []
}
```

#### 4. Effect Application (`operation_type: effect_application`)
Used for buffs, curses, and control spells. 
```json
// Payload for casting Haste or bestowing a Condition
{
  "applied_condition_id": "cond_haste_001", // References a ConditionDefinition
  "duration_rounds": 10,
  "requires_concentration": true,
  "allow_save_ends": false
}
```

---

## 4. Complex V2 Problems Solved by this Schema

### 1. The Reactive Execution Flow (Aura & Smites)
Because `ActionOperationSpec` separates the "Trigger" from the "Payload", Paladins do not need hard-coded smite logic. A Divine Smite is simply:
*   `activation_cost: free`
*   `activation_trigger: on_melee_weapon_hit`
*   `operation_type: effect_application` (adding radiant damage to the current dice pool).
V2 natively halts the attack resolution graph, checks for triggers, and prompts the paladin before completing the damage phase.

### 2. Condition Validation & Cleanup
By forcing buffs and debuffs into `ConditionDefinition` records containing strict `ModifierSpec` payloads, V2 can easily purge them. If a Mage fails concentration, V2 retrieves the `applied_condition_id`, traverses all target actors, and reverses the `ModifierSpec` maths safely.

### 3. Extra Attack and Multi-Stage Weapons
Because `damage_instances` is an array, we can safely model weapons like the Flame Tongue (1d8 slashing + 2d6 fire) without writing custom parsing scripts. V2 iterates over the array, creating distinct damage packets that trigger resistances correctly.
