# 01 - Core Schemas and Models

## Overview

The D&D 5e engine relies on strict typings provided by `pydantic`. The data layer is divided into two primary categories: **Definitions** (read-only, generic templates) and **Instances** (mutable objects representing live game state). Shared enums and common value types are centralized to ensure consistency across the engine.

## Core Concepts / Mechanics

### Definitions vs Instances

- **Definitions (`definitions.py`)**: These describe what a thing _is_ in the abstract (e.g., the `MonsterDefinition` for an Adult Red Dragon, or the `SpellDefinition` for Fireball). These are never mutated during play and correspond directly to the SRD compendium data. They are hydrated at server start by the `CompendiumLoader`.
- **Instances (`instances.py`)**: These are the instantiated, mutable objects created when something enters the game state (e.g., an `ActorInstance` representing the dragon "Smaug" with current HP, conditions, and position). All runtime logic (damage, healing, effects, state machine progression) operates strictly on `Instance` models.

### Shared Common Types and Enums

- **Enums (`enums.py`)**: Strings are heavily restricted to Enums (e.g., `DamageType`, `ActionType`, `ConditionType`, `EffectType`) to catch structural errors early and provide intellisense.
- **Common Types (`common.py`)**: Sub-schemas like `AbilityScores`, `SpeedBlock`, and `AreaOfEffect` form the composable building blocks used by both Definitions and Instances.

## Key Schemas / Interfaces

### ActorInstance (`instances.py`)

The fundamental unit of combat, representing a PC, NPC, Monster, or Summon. This object holds all localized state.

```python
class ActorInstance(BaseModel):
    id: str
    actor_type: ActorType
    current_hp: int
    max_hp: int
    temp_hp: int
    armor_class: int
    conditions: List[ConditionInstance]
    effects: List[EffectInstance]
    inventory: List[ItemInstance]
    spellcasting: Optional[SpellcastingState]
    concentration: ConcentrationState
```

### EncounterState (`encounter.py`)

The top-level root object that holds the complete snapshot of an isolated combat encounter, including the turn sequence.

```python
class EncounterState(BaseModel):
    id: str
    round_number: int
    turn_phase: str
    active_index: int
    combatants: List[ActorInstance]
    global_effects: List[EffectInstance]
    map: MapState
```

### EffectType (Enum)

Classifies the type of an effect mathematically for the rules engine. Effects power the generic stateless calculation layer.

```python
class EffectType(str, Enum):
    # Stat Modifiers
    BONUS = "BONUS"
    SET = "SET"
    MULTIPLY = "MULTIPLY"
    # Roll Modifiers
    ADVANTAGE = "ADVANTAGE"
    DISADVANTAGE = "DISADVANTAGE"
    # Status Mutations
    GRANT_CONDITION = "GRANT_CONDITION"
    REMOVE_CONDITION = "REMOVE_CONDITION"
    # ... (Damage interaction overrides)
```

## Example Usage

```python
from systems.dnd5e.schemas.instances import ActorInstance
from systems.dnd5e.schemas.enums import ActorType

# Instantiating a live combatant at runtime
target = ActorInstance(
    id="dragon_1",
    name="Smaug",
    actor_type=ActorType.MONSTER,
    current_hp=256,
    max_hp=256,
    armor_class=19
)

# Mutating state during combat
target.current_hp -= 42
```

## Dependencies

This package acts as the absolute foundational data layer for the `dnd5e` system.

- **Requires**: Nothing (only Python standards and `pydantic`).
- **Required By**: `data/`, `engine/`, `core/ws_protocol.py`
