# Backend Concept: The Modular Monolith

## 1. Architecture Principle: CQRS Light

We strictly separate between **Acting** and **Displaying**.

*   **Frontend is "Dumb":** It never calculates values (like HP or bonuses). It only sends **Commands** to the backend.
*   **Backend is "Smart":** It holds the state, executes rule logic, and sends back a finished **View Model** including explanations (calculation path).

## 2. Backend Services (Python)

Although implemented in a Monorepo, the backend is conceptually sliced into microservices.

### A. Data Service ("The Librarian")

*   **Responsibility:** Saving and loading static definitions (Items, Spells, Monster Templates).
*   **Feature: Mod Loader & Aggregator:**
    *   Loads JSON files from the file system (`/mods/...`).
    *   Merges them based on a load order (Core < Community < Homebrew).
    *   Delivers the final result via API.
*   **SRD 5.1 Integration:** Uses structured JSON dumps of the SRD as a Base Content Pack.

### B. Logic Service ("The Game Master")

*   **Responsibility:** Campaign state management. Execution of rules.
*   **Data Model (Adaptation):** Porting structures from `libsrd5` (C#) to Pydantic Models. Extending these models with an `effects` field.
*   **Core Piece: The Effect Engine:**
    *   An event-based system using JSON configurations instead of code.
    *   **Structure:** An effect has **Trigger** (WHEN: `ON_DAMAGE`), **Condition** (IF: `HP < 50%`), and **Operation** (THEN: `ADD +2`).
    *   **No-Code Modding:** Allows users to create complex Feats/Items by combining these JSON building blocks without programming Python.
    *   **Safe Eval:** Usage of `simpleeval` for safe evaluation of formula strings ("{level} / 2").

## 3. Development Workflow

*   **Language:** Python 3.11+
*   **Framework:** FastAPI
*   **Validation:** Pydantic v2
*   **Testing:** `pytest` for logic unit tests and API integration tests (`TestClient`).

## 4. Legacy Analysis (`libsrd5`)

We use the existing C# library `libsrd5` as a reference for data structures and logic.

### A. Data Models (Mapping)

| Concept | `libsrd5` (C#) | New Backend (Python/Pydantic) | Notes |
| :--- | :--- | :--- | :--- |
| **Character** | `CharacterSheet.cs` | `CharacterModel` | Inherits from `Combattant`. Logic like `RecalculateAttacks()` moves to Service. |
| **Inventory** | `CharacterInventory` | `InventoryModel` | Manages slots (MainHand, OffHand, etc.) and Bag. |
| **Item** | `Item.cs` | `ItemModel` | Base class. Subtypes: Weapon, Armor, Consumable, Usable, MagicItem. |
| **Effect** | `Effect` (Enum in `Effects.cs`) | `EffectModel` (JSON) | **Major Change:** The hardcoded Enum becomes a dynamic JSON structure. |
| **Monster** | `Monster.cs` | `MonsterModel` | Currently static properties in `Monsters_X.cs`. Will be JSON files. |

### B. The "Effect" Problem

In `libsrd5`, effects are a massive Enum (`Effects.cs`) mixing:
*   **Vulnerabilities/Resistances:** `VULNERABILITY_FIRE`
*   **Stat Changes:** `CONSTITUTION_19`
*   **Spells:** `SPELL_BLESS`
*   **Complex Logic:** `FIGHTING_DEATH` (Death Saves logic)

**Migration Strategy:**
The `EffectExtension.Apply()` method in C# contains the logic. We must extract this logic and convert it into our **Effect Engine** (Trigger/Condition/Operation).

*   **Example:** `HEAVY_ARMOR_SPEED_PENALITY`
    *   **C#:** `combattant.Speed -= 10;`
    *   **JSON:** `{ "trigger": "PASSIVE", "operation": "ADD", "target": "speed", "value": -10 }`

### C. Critique & Solutions (Why we are rewriting)

The user correctly identified major design flaws in `libsrd5` that we will fix:

| Flaw in `libsrd5` | Our Solution (Project Open RPG) |
| :--- | :--- |
| **Giant Effect Enum:** `RESISTANCE_FIRE`, `RESISTANCE_COLD` are separate entries. Adding `RESISTANCE_NEW_TYPE` requires recompiling code. | **Structured Effects:** We use objects: `{ "type": "RESISTANCE", "damage": "fire" }`. This allows infinite combinations without code changes. |
| **One-Dimensional Effects:** Effects are just labels. Logic is hidden in a massive `switch` statement in C#. | **Logic in Data:** The JSON defines the logic (Trigger/Condition/Operation). The backend just executes what the JSON says. |
| **Hardcoded Actions:** Attacks and Spells are hardcoded classes. No generic "Use Item" actions. | **Dynamic Actions:** Items/Spells will have an `actions` list in their JSON (e.g., `[{ "label": "Throw", "type": "ATTACK_RANGED" }]`). The Frontend simply renders this list. |
| **Rigid Stat Changes:** `CONSTITUTION_19` is a specific effect. `STRENGTH_18` would need a new enum. | **Parametric Effects:** `{ "type": "SET_STAT", "stat": "constitution", "value": 19 }`. One effect type covers all stats and values. |

## 5. Data-Driven Design (Scalability)

We will **not** implement specific classes for every item or monster (e.g., no `class Goblin(Monster)`).

*   **Generic Models:** We only have generic models: `MonsterModel`, `ItemModel`, `SpellModel`.
*   **Database as Source of Truth:** The specific data (Goblin stats, Fireball damage) comes from the database.
*   **5e-bits Integration:**
    *   We utilize the open data from [5e-bits/5e-database](https://github.com/5e-bits/5e-database/tree/main).
    *   **Converters:** We will build importers/converters to transform this external JSON data into our internal Pydantic/Database schema.
    *   **Manual Editing:** Where automatic conversion fails, we will manually refine the JSONs, but we never hardcode data into Python classes.
