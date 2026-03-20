# Backend Architecture and Functionality
This document acts as the single source of truth for the CMV2 D&D 5e Backend Engine. It outlines the supported architecture, explicit capabilities (what the backend CAN do), unsupported or missing features (what it CAN NOT do), and the core business logic.

## 1. System Architecture
The backend is fundamentally designed as a strict, strongly-typed D&D 5e API decoupled from the frontend, relying heavily on `pydantic` schemas representing Definitions (read-only game data) and Instances (live combat state). 

### Core Flow
1. **Data Ingestion**: A `CompendiumLoader` parses system JSONs (like the Open5e SRD data) into a `CompendiumRegistry` at server start.
2. **Stateless Rules Engines**: Pure functional math engines determine dice results, stat calculation, conditions, and damage application.
3. **Session & WebSocket API**: Client connections synchronize the live state of an `EncounterState`, receiving updates based on visibility requirements (Fog of War) via strict `WsEnvelope` and `WsOutbound` payload typing.
4. **Action Resolver**: Serves as the high-level orchestration layer uniting rules engines with the current combat state to mutate the Encounter.

## 2. What the Backend CAN Do (Implemented Functionality)

### A. Core Data & Rules Models
- **Compendium Parsing**: Natively translates external JSON entities (Monsters, Spells, Items) into strict schemas. It supports full validation checks on relationships.
- **Stat Calculation**: Recursively calculates derived stats (like Armor Class, current speeds) while respecting a rigorous order-of-operation effect stacking mechanism (`SET` -> `BONUS` -> `MULTIPLY`). 
- **Dice Engine**: Parses complex standard dice string formats (e.g., `2d10+8`), applying advantage/disadvantage contexts and optionally taking pre-seeded inputs for determinism.
- **Damage Pipeline**: Completely resolves damage cascades. It considers immunities (0x), resistances (0.5x), vulnerabilities (2x), and absorbs applied damage through Temporary Hit Points prior to current HP reduction.
- **Condition Engine**: Mathematically applies the PHB's 15 standard conditions (e.g. Paralyzed rendering speed 0 and causing auto-crits in melee).

### B. Combat Orchestration
- **Combat State Machine**: Accurately tracks `TurnBudgets` (Actions, Bonus Actions, Movement, Reactions) that replenish systematically at the top of an actor's turn. 
- **Initiative Resolution**: Can reliably start encounters and break initiative ties internally via base DEX scores.
- **Effect Ticking**: At the end/start of turns, it ticks duration-bound effects (`remaining_rounds`), truncating them and removing associated conditions globally. 
- **Concentration**: Tracks and manages spell concentration, dynamically computing saving throw DCs `max(10, damage / 2)` when a concentrating actor sustains damage, or breaking it automatically upon incapacitating conditions.
- **Character Builder**: Capable of ingesting a loose blueprint (`CharacterCreationBlueprint`) of race, background, class, and raw stats, and mutating it into a battle-ready `ActorInstance` comprising spellcasting slots, saving throw proficiencies, hit point calculations, and features.
- **Action Resolver**: Orchestrates full combat maneuvers from initial roll to target AC verification, critical hit detection, saving throw propagation for AoE, and healing applications.

### C. Permissions & Syncing (WebSocket)
- **Role Scoping (State Filter)**: Filters all payloads globally based on an individual client's observer/DM standing (e.g., masking enemy exact HP).
- **Execution Scoping**: Automatically checks budgets, preview validations, and DM limitations securely on the server prior to granting an action payload an execution pipeline.

## 3. What the Backend CAN NOT Do (Missing & Outdated Functionality)

These are explicit functional gaps representing legacy code structures or technical debt that will be removed or refactored:

- **Complete separation of WebSocket Connection and Business Logic**: The current `systems/dnd5e/ws_handler.py` massively breaches SRP (Single Responsibility Principle). It stands at nearly 100KB because it directly validates action previews, deduplicates IDs, requests template dimensions, and calculates budgets internally before passing directly to the `CombatService/action_resolver`. **It cannot currently act purely as a transport router.**
- **Integration with the default Campaign Sub-Router (`campaigns/router.py`)**: The raw campaign system acts isolated from the Phase 2-4 D&D Engine rules. It relies on a hardcoded legacy `MockEncounterState` using outdated properties (`hp_current` instead of `current_hp`) and relies on arbitrary socket events (`STATE_UPDATE`) rather than the modernized `WsEnvelope` standard. **It cannot act as a proper system facade.** 
- **Persistence Layer Synchronization**: While the `CombatService` is intended to use `AsyncSessionLocal` to save the state, the MVP engine currently resorts to caching encounters manually in a local `_encounters` dictionary singleton in memory for tests.
- **In-Depth Nested Inventory and Spellcasting Resource Logic**: While it tracks basic `spell_slots` usage, complex localized resource pools (like Sorcery Points or Battlemaster Superiority Dice) or complex item attunement limits are not fully bridged to the automated rules engines.
