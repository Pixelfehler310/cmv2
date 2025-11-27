# Data Models & Shared Types

## 1. Philosophy: Ideals vs. Reality

We strictly separate **Definitions** (static data) from **Instances** (dynamic state).

### A. Definitions (Data Service)

- **Concept:** The "Platonic Ideal" of an object. What is a "Longsword"?
- **Characteristics:** Static, Immutable during a session, Versioned.
- **Examples:**
  - `ItemDefinition`: Name, Description, Base Damage, Weight, Icon.
  - `MonsterDefinition`: Name, Base Stats, Default Actions.
  - `SpellDefinition`: Name, Level, Range, Effect Instructions.

### B. Instances (Logic Service)

- **Concept:** A concrete object existing in the game world. "Aragorn's Longsword".
- **Characteristics:** Dynamic, Stateful, Unique ID.
- **Structure:**
  - `definition_id`: Reference to the Definition.
  - `instance_id`: Unique UUID.
  - `state`: Current Charges, Custom Name (if renamed), Durability (optional).
  - `overrides`: Specific changes to base stats (e.g., a Masterwork version).

## 2. The Shared Contract (`@rpg/types`)

- **Location:** `frontend/packages/types`.
- **Content:** TypeScript Interfaces generated from Backend Models.
- **Rule:** The Backend Pydantic Models are the **Source of Truth**.

## 3. Synchronization Workflow (Generator)

To ensure type safety across the stack, we use an automated pipeline:

1.  **Define:** Developer updates a Pydantic Model in `backend/src/models`.
2.  **Generate:** A script (`scripts/generate_types.py`) runs:
    - Exports Pydantic Models to JSON Schema.
    - Converts JSON Schema to TypeScript Interfaces (using `json-schema-to-typescript` or similar).
    - Writes output to `frontend/packages/types/src/generated.ts`.
3.  **Consume:** Frontend imports types from `@rpg/types`.

## 4. Model Hierarchy (Draft)

### Item

- **Definition:** `id`, `name`, `type` (weapon/armor), `weight`, `value`, `effects` (passive).
- **Instance:** `uuid`, `def_id`, `equipped` (bool), `quantity`.

### Character

- **State (Logic):** `id`, `name`, `hp_current`, `position` (x,y), `inventory` (List[ItemInstance]).
- **View Model (Computed):** The Logic Service calculates the final stats (AC, Attack Bonus) based on State + Definitions + Effects and sends a "Ready to Render" object to the Frontend.
