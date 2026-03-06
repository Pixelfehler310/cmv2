# D&D 5e Combat & Action System Architecture

This document defines the combat lifecycle, action economy, and the data-driven action resolution pipeline for the D&D 5e system module. All logic lives inside `src/systems/dnd5e/engine/`.

---

## 1. Combat Lifecycle

### State Machine

Combat moves through a strict sequence of phases. The DM explicitly starts and ends combat; turn progression is automatic.

```mermaid
stateDiagram-v2
    [*] --> Idle

    Idle --> RollingInitiative : DM starts encounter
    RollingInitiative --> Combat : All initiatives set

    state Combat {
        [*] --> StartOfTurn
        StartOfTurn --> MainPhase : Trigger start-of-turn effects
        MainPhase --> EndOfTurn : Actor ends turn / no actions left
        EndOfTurn --> StartOfTurn : Advance to next combatant
        EndOfTurn --> NewRound : Last combatant in order
        NewRound --> StartOfTurn : Increment round, reset to first
    }

    Combat --> Idle : DM ends encounter
```

### Phase Responsibilities

| Phase                  | What Happens                                                                            |
| ---------------------- | --------------------------------------------------------------------------------------- |
| **Idle**               | No active combat. Actors can still be on the map.                                       |
| **Rolling Initiative** | DM rolls or sets initiative for each actor. Order is computed.                          |
| **Start of Turn**      | Effect durations tick. Conditions re-evaluated. Action economy reset. Recharge rolls.   |
| **Main Phase**         | Active actor takes actions, bonus actions, moves, uses reactions (out-of-turn).         |
| **End of Turn**        | End-of-turn save re-rolls (e.g., Frightened). Per-turn damage (e.g., standing in fire). |
| **New Round**          | Round counter increments. Lair actions (if any).                                        |

---

## 2. Action Economy

Each combatant has the following resource budget per turn:

```mermaid
classDiagram
    class TurnBudget {
        +bool action_available
        +bool bonus_action_available
        +bool reaction_available
        +float movement_remaining
        +int free_object_interaction
        +use_action() void
        +use_bonus_action() void
        +use_reaction() void
        +spend_movement(feet: float) void
        +reset_for_new_turn() void
        +reset_reaction_for_new_round() void
    }
```

### Rules

| Resource                    | Refreshes            | Notes                                                                                                                                    |
| --------------------------- | -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **Action**                  | Start of turn        | 1 per turn. Can be swapped for Dash, Dodge, Help, Hide, Disengage, Use Object, or any action-costed ability                              |
| **Bonus Action**            | Start of turn        | 1 per turn. Only available if something _grants_ a bonus action (spell, feature, TWF)                                                    |
| **Reaction**                | Start of _your_ turn | 1 per round. Persists between turns. Used for Opportunity Attacks, Shield, Counterspell, etc.                                            |
| **Movement**                | Start of turn        | Speed in feet. Can be split before/after actions. Reduced by difficult terrain (2× cost). Set to 0 by Grappled/Restrained/Paralyzed/etc. |
| **Free Object Interaction** | Start of turn        | 1 per turn. Draw/sheathe weapon, open door, etc.                                                                                         |

### Legendary Actions (Monsters)

Legendary actions are a **separate resource pool**, tracked on the monster's `ActorInstance`. They reset at the **start of the monster's turn**, and can only be used at the **end of another creature's turn**.

```python
class LegendaryActionBudget:
    max_actions: int         # e.g., 3 for Adult Red Dragon
    remaining_actions: int

    def use(self, cost: int) -> bool: ...
    def reset(self) -> None: ...
```

---

## 3. Action Resolution Pipeline

Every action — whether a sword swing, a Fireball, or Frightful Presence — flows through the same generic pipeline. The engine never knows "what" is being done; it only follows the `ActionDefinition` data.

### Sequence: Attack Roll Action (e.g., Bite +14)

```mermaid
sequenceDiagram
    participant DM as DM Client
    participant WS as WS Dispatcher
    participant Handler as dnd5e Handler
    participant Engine as ActionResolver
    participant State as EncounterState
    participant FX as EffectEngine

    DM->>WS: {type: "action", actor: "dragon_1", action: "Bite", target: "fighter_1"}
    WS->>Handler: dispatch(event)
    Handler->>State: get_actor("dragon_1"), get_actor("fighter_1")
    Handler->>Engine: resolve_attack(attacker, target, action_def)

    Engine->>FX: compute_attack_modifiers(attacker)
    Note over FX: Checks: Advantage/Disadvantage flags,<br/>conditions (Blinded, Invisible, Restrained),<br/>stat bonuses

    Engine->>Engine: roll_d20(modifiers)
    Engine->>FX: compute_target_ac(target)

    alt Hit
        Engine->>Engine: roll_damage("2d10+8 piercing, 2d6 fire")
        Engine->>FX: apply_resistances(target, damage_rolls)
        Engine->>State: apply_damage(target, final_damage)
        Engine->>State: check_concentration(target)
        Engine-->>Handler: AttackResult{hit: true, damage: 26, ...}
    else Miss
        Engine-->>Handler: AttackResult{hit: false}
    end

    Handler->>State: consume_action(dragon_1)
    Handler-->>WS: broadcast(AttackResultEvent)
    WS-->>DM: {type: "attack_result", ...}
```

### Sequence: Save-Based Action (e.g., Fire Breath DC 21)

```mermaid
sequenceDiagram
    participant DM as DM Client
    participant Handler as dnd5e Handler
    participant Engine as ActionResolver
    participant State as EncounterState
    participant FX as EffectEngine

    DM->>Handler: {type: "action", actor: "dragon_1", action: "Fire Breath", targets: ["fighter_1", "rogue_1", "wizard_1"]}

    Handler->>Engine: resolve_save_action(caster, targets, action_def)

    loop for each target
        Engine->>FX: compute_save_modifier(target, "DEX")
        Engine->>Engine: roll_save(modifier) vs DC 21

        alt Failed Save
            Engine->>Engine: roll_damage("18d6 fire")
            Engine->>FX: apply_resistances(target, damage)
            Engine->>State: apply_damage(target, full_damage)
        else Successful Save
            Engine->>Engine: damage = full_damage / 2
            Engine->>FX: apply_resistances(target, half_damage)
            Engine->>State: apply_damage(target, half_damage)
        end
    end

    Engine-->>Handler: SaveActionResult{results: [...]}
    Handler->>State: set_recharge_used("Fire Breath", dragon_1)
```

---

## 4. The Effect Engine

The Effect Engine sits alongside the action resolver and computes derived stats dynamically. It never stores computed values — it recomputes on demand.

### Stat Computation Flow

```mermaid
flowchart TD
    A["Base Stats\n(from Definition)"] --> B["Apply SET effects\n(e.g., Gauntlets: STR = 19)"]
    B --> C["Apply BONUS effects\n(e.g., Shield: +2 AC)"]
    C --> D["Apply MULTIPLY effects\n(e.g., Haste: Speed × 2)"]
    D --> E["Apply Condition Overrides"]

    E --> F{"Check Conditions"}
    F -->|Grappled/Paralyzed/etc.| G["Speed = 0"]
    F -->|Exhaustion ≥ 2| H["Speed halved"]
    F -->|Exhaustion ≥ 4| I["HP max halved"]
    F -->|None| J["No override"]

    G --> K["Final Computed Stats"]
    H --> K
    I --> K
    J --> K
```

### Condition Mechanical Effects Matrix

All 15 SRD conditions and their mechanical impacts:

| Condition         | Speed                 | Attack Rolls          | Saves             | Other                                             |
| ----------------- | --------------------- | --------------------- | ----------------- | ------------------------------------------------- |
| **Blinded**       | —                     | Disadvantage          | —                 | Auto-fail sight checks. Attacks against have ADV  |
| **Charmed**       | —                     | Can't attack charmer  | —                 | Charmer has ADV on social checks                  |
| **Deafened**      | —                     | —                     | —                 | Auto-fail hearing checks                          |
| **Exhaustion 1**  | —                     | —                     | —                 | DADV on ability checks                            |
| **Exhaustion 2**  | Halved                | —                     | —                 | + all lower levels                                |
| **Exhaustion 3**  | Halved                | Disadvantage          | Disadvantage      | + all lower levels                                |
| **Exhaustion 4**  | Halved                | Disadvantage          | Disadvantage      | HP max halved + all lower                         |
| **Exhaustion 5**  | 0                     | Disadvantage          | Disadvantage      | HP max halved + all lower                         |
| **Exhaustion 6**  | —                     | —                     | —                 | **Death**                                         |
| **Frightened**    | Can't approach source | Disadvantage (in LoS) | —                 | Disadvantage ability checks (in LoS)              |
| **Grappled**      | 0                     | —                     | —                 | Ends if grappler incapacitated                    |
| **Incapacitated** | —                     | No actions/reactions  | —                 | —                                                 |
| **Invisible**     | —                     | Advantage             | —                 | Attacks against have DIS                          |
| **Paralyzed**     | 0                     | —                     | Auto-fail STR/DEX | Attacks against ADV. Melee hits are crits         |
| **Petrified**     | 0                     | —                     | Auto-fail STR/DEX | Resistance to all damage. Immune poison           |
| **Poisoned**      | —                     | Disadvantage          | —                 | Disadvantage ability checks                       |
| **Prone**         | Crawl only (half)     | Disadvantage          | —                 | Melee attacks ADV, ranged attacks DIS             |
| **Restrained**    | 0                     | Disadvantage          | Disadvantage DEX  | Attacks against have ADV                          |
| **Stunned**       | 0                     | —                     | Auto-fail STR/DEX | Attacks against have ADV                          |
| **Unconscious**   | 0                     | —                     | Auto-fail STR/DEX | Drop held items, fall prone. Melee hits are crits |

---

## 5. Damage Pipeline

Damage processing is multi-step and must be evaluated in order:

```mermaid
flowchart TD
    A["Raw Damage Roll\n(e.g., 18d6 = 63 fire)"] --> B{"Target has\nIMMUNITY to damage type?"}
    B -->|Yes| C["Damage = 0"]
    B -->|No| D{"Target has\nRESISTANCE?"}
    D -->|Yes| E["Damage = floor(damage / 2)"]
    D -->|No| F{"Target has\nVULNERABILITY?"}
    F -->|Yes| G["Damage = damage × 2"]
    F -->|No| H["Damage unchanged"]

    E --> I["Apply to Temp HP first"]
    G --> I
    H --> I

    I --> J{"Temp HP > 0?"}
    J -->|Yes| K["Reduce Temp HP.\nOverflow to Current HP"]
    J -->|No| L["Reduce Current HP"]

    K --> M{"HP ≤ 0?"}
    L --> M
    M -->|Yes, PC| N["Death Saving Throws"]
    M -->|Yes, Monster| O["Dead / Dying"]
    M -->|No| P{"Was concentrating?"}
    P -->|Yes| Q["CON Save DC = max(10, damage/2)"]
    P -->|No| R["Done"]
    Q --> R
```

---

## 6. Concentration

Concentration is a critical sub-system that connects damage, saving throws, and effect management.

### Rules

- Only one concentration spell at a time.
- Taking damage triggers a CON save: DC = max(10, floor(damage_taken / 2)).
- Gaining a condition (Incapacitated, Stunned, etc.) automatically breaks concentration.
- Casting a new concentration spell ends the previous one.

### Implementation

```python
class ConcentrationManager:
    def on_damage(self, actor: ActorInstance, damage: int) -> ConcentrationCheckResult:
        """Returns the DC and whether the save passed/failed."""
        ...

    def on_condition_gained(self, actor: ActorInstance, condition: ConditionType) -> bool:
        """Returns True if concentration was broken."""
        BREAKS_CONCENTRATION = {
            ConditionType.INCAPACITATED,
            ConditionType.STUNNED,
            ConditionType.PARALYZED,
            ConditionType.UNCONSCIOUS,
            ConditionType.PETRIFIED,
        }
        ...

    def on_new_concentration_spell(self, actor: ActorInstance, new_effect_id: str) -> str | None:
        """Ends old concentration, starts new. Returns removed effect_id."""
        ...
```

---

## 7. Engine Module File Map

All files inside `src/systems/dnd5e/engine/`:

| File                  | Responsibility                                                                    |
| --------------------- | --------------------------------------------------------------------------------- |
| `action_resolver.py`  | The main pipeline: receives `ActionDefinition` + actors → produces `ActionResult` |
| `dice.py`             | d20 rolls, damage rolls, advantage/disadvantage logic                             |
| `stat_calculator.py`  | Computes derived stats from base + effects + conditions                           |
| `effect_engine.py`    | Manages active effects: apply, remove, tick, query                                |
| `condition_engine.py` | Condition-specific mechanical overrides (the matrix above)                        |
| `concentration.py`    | Concentration save triggers and spell replacement                                 |
| `damage.py`           | Damage pipeline: immunities → resistances → temp HP → current HP                  |
| `initiative.py`       | Initiative rolling, ordering, turn advancement                                    |
| `combat_state.py`     | `EncounterState` management, turn progression state machine                       |
