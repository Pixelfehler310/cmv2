# Backend Documentation Strategy & Split Plan

## 1. Context & Motivation

Phases 1-6 of the D&D 5e engine implementation are fully complete. The backend now features a robust stateless rules engine, a working combat state machine, character generation, and a real-time WebSocket session layer.

To ensure AI context windows remain efficient and human developers can easily navigate the project, we must comprehensively document the system. Trying to fit all engine mechanics, schema definitions, and WebSocket API payloads into a single document will overwhelm context limits and cause degradation in generation quality.

Therefore, **we will split the documentation strictly by the architectural boundaries of the phases.** Every major system component gets its own isolated reference document.

## 2. Directory Structure

All implementation documentation will reside in a new dedicated reference folder:
`docs/backend/reference/`

_Note: The current `docs/architecture/backend/` folder contains the historical, high-level planning records. The new `reference` folder will contain the "reality" of the written code—acting as the live manual._

## 3. Documentation Splits & Scopes

We will create the following 7 Markdown documents. Each document should be self-contained, specifically targeting one aspect of the engine.

### `01_core_schemas_and_models.md`

- **Scope**: `schemas/` directory (Enums, Common, Definitions, Instances, Encounter).
- **Contents**:
  - The hierarchy of Data Models (e.g., `Definition` vs `Instance`).
  - Key interfaces: `ActorInstance`, `SpellDefinition`, `EncounterState`.
  - Explanation of how Pydantic is leveraged for strict typing.
- **Why here**: Provides the foundational vocabulary required before explaining any engine logic.

### `02_compendium_and_loader.md`

- **Scope**: `data/` directory.
- **Contents**:
  - How Open5e/SRD JSON is parsed into the Definition models.
  - The `CompendiumRegistry` in-memory lookup system.
  - Validating and referencing data via unique "slugs" across the system.
- **Why here**: Isolates data ingestion from runtime logic.

### `03_stateless_rules_engine.md`

- **Scope**: `engine/dice.py`, `engine/stat_calculator.py`, `engine/condition_engine.py`, `engine/damage.py`.
- **Contents**:
  - The pure functional approach to D&D math.
  - **Stat Calculation**: Order of operations for Effect stacking (SET, BONUS, MULTIPLY) and AC computation.
  - **Conditions**: The mechanical impact of the 15 PHB conditions and exhaustion levels.
  - **Damage Pipeline**: The exact resolution order of immunity, resistance, vulnerability, and temporary HP.
- **Why here**: Contains the heaviest pure-math logic. Keeping this separate ensures an AI handling UI doesn't need to load the complex damage pipeline rules.

### `04_combat_state_machine.md`

- **Scope**: `engine/initiative.py`, `engine/combat_state.py`, `engine/effect_engine.py`, `engine/concentration.py`.
- **Contents**:
  - `TurnBudget` management: resetting actions, bonus actions, and reactions.
  - The turn/round advancement cycle.
  - Managing ticking effect durations and removing expired effects.
  - Concentration rules: when it breaks (damage threshold, conditions, overriding spells).
- **Why here**: Separates state mutation and temporal logic (turns/rounds) from the stateless math.

### `05_action_resolver.md`

- **Scope**: `engine/action_resolver.py`.
- **Contents**:
  - The attack resolution pipeline (Advantage/Disadvantage, crits, condition modifiers).
  - Save-based action resolution and half-damage calculations.
  - Healing pipelines.
  - How the resolver interacts with the `EncounterState` to consume turn budgets.
- **Why here**: This is the "glue" that combines the stateless engine and combat state machine to actually execute a monster's attack or player's spell.

### `06_character_builder.md`

- **Scope**: `schemas/creation.py`, `engine/character_builder.py`.
- **Contents**:
  - The `CharacterCreationBlueprint` schema.
  - How `CharacterBuilder` parses Race + Class + Background to assemble a full `ActorInstance`.
  - Application of proficiencies, ability score bonuses, and spell slot generation.
- **Why here**: PC generation is a standalone feature not directly involved in runtime combat resolution.

### `07_websocket_api_and_sessions.md` (The API Documentation)

- **Scope**: `core/ws_protocol.py`, `core/sessions/`, `systems/dnd5e/ws_handler.py`, `systems/dnd5e/event_types.py`.
- **Contents**:
  - Connection lifecycle & JWT Authentication.
  - The generic `WsEnvelope` structure.
  - Role-based permissions (DM vs. Player logic).
  - **Event Dictionary**: Exhaustive list of all incoming and outgoing WebSocket events (e.g., `action`, `state_sync`, `attack_result`) and their JSON payloads.
  - **State Filtering**: How Fog of War and sensitive DM data is scrubbed before broadcasting to players.
- **Why here**: This is the contract for the Frontend. Frontend developers (or AI) only need to read this file to build the React application, without loading the Python engine mathematics.

## 4. Standard Document Format

To maintain consistency and high utility, each of the above `.md` files will adhere to this structure:

1. **Overview**: 2-3 sentences max on what the component does.
2. **Core Concepts / Mechanics**: The written explanation of the logic.
3. **Key Schemas / Interfaces**: Only the most critical fields (do not dump thousands of lines of raw Pydantic classes; use summarized definitions).
4. **Example Usage**: A short code block showing how to call the function or an example JSON payload (for the WebSocket API).
5. **Dependencies**: What other modules this document relies on.

## 5. Next Steps for Execution

1. Create the `docs/backend/reference/` directory.
2. Generate each of the 7 Markdown files sequentially.
3. Once completed, update the main `README.md` or the `docs/index.md` to link to these 7 new reference guides.
