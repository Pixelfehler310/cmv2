# Backend Implementation Plan

This document outlines the step-by-step plan to build the Open RPG Engine backend, following the "Modular Monolith" architecture.

## Phase 1: Foundation & The "Digital Filing Cabinet" (MVP)
Focus: Administration, Data Persistence, and serving static content (SRD).

### Milestone 1.1: Project Setup & Infrastructure
- [x] Initialize Python project structure
- [x] Setup FastAPI basic application (`main.py`)
- [x] Setup Docker/Docker Compose for Database (PostgreSQL)
- [x] Configure Database Connection (SQLAlchemy/AsyncPG)
- [x] Create Base Pydantic Models & DB Models structure

### Milestone 1.2: Data Service ("The Librarian") - Basic
- [x] Implement `ItemModel` (Pydantic & DB)
- [x] Implement `SpellModel` (Pydantic & DB)
- [x] Implement `MonsterModel` (Pydantic & DB)
- [x] Create JSON Loader Service (for SRD data)
- [x] Create API Endpoints: List/Get Items
- [x] Create API Endpoints: List/Get Spells
- [x] Create API Endpoints: List/Get Monsters

### Milestone 1.3: Logic Service ("The Game Master") - State Management
- [x] Implement `CharacterModel` (Pydantic & DB)
- [x] Implement `CampaignModel` (Pydantic & DB)
- [x] Create API Endpoints: Character CRUD (Create, Read, Update, Delete)
- [x] Create API Endpoints: Campaign CRUD
- [x] Create and run Tests for Milestone 1.3

### Milestone 1.4: Data Service ("The Librarian") - Advanced Testing
- [x] Create and run Tests for `MonsterModel` with associated `Actions`
- [x] Create and run Tests for `CharacterModel` with associated `Actions`
- [x] Create and run Tests for `MonsterModel` with `Inventory`
- [x] Create and run Tests for `CharacterModel` with `Inventory`
- [x] Create and run Tests for `MonsterModel` implicit `Actions` (from Items, Spells, Effects)
- [x] Create and run Tests for `CharacterModel` implicit `Actions` (from Items, Spells, Effects)

## Phase 2: The "Calculator" (Core Rules & Instances)
Focus: Automating calculations, managing specific instances of data, and the static effect engine. This ensures the "View Model" sent to the frontend is fully calculated.

### Milestone 2.1: Dice & Core Mechanics
- [x] **Dice Service:** Implement `DiceRoller` (parse "1d20+5", return result + breakdown).
- [x] **Rules Engine:** Implement Attribute Modifier logic (`(Score - 10) // 2`).
- [x] **Rules Engine:** Implement Proficiency Bonus logic based on Level/CR.
- [x] **Tests:** Verify dice parsing and basic rule calculations.

### Milestone 2.2: Instance Management (Inventory & State)
- [x] **Item Instances:** Implement logic for items *inside* an inventory (equipped status, quantity, attunement).
- [x] **Spell Instances:** Implement logic for Prepared Spells and Spell Slots.
- [x] **Monster Instances:** Create `MonsterInstance` Model (linked to Template, but with unique ID, current HP, position).
- [x] **Inventory Manager:** Logic to Add/Remove/Equip items on Characters/Monsters.
- [x] **Tests:** Verify inventory operations and instance state tracking.

### Milestone 2.3: Effect Engine V1 (Static Modifiers)
- [x] **Effect Model:** Define the JSON structure for Effects (Trigger, Condition, Operation).
- [x] **Effect Processor:** Implement the engine to apply *static* modifiers (e.g., "+1 AC", "Resistance to Fire").
- [x] **Integration:** Apply effects to `CharacterModel` and `MonsterInstance` to generate the final View Model.
- [x] **Tests:** Verify that equipping a shield increases AC, etc.

### Milestone 2.4: Character & Entity Model Refinement
- [x] **Refactor `CharacterModel`:**
    - [x] Extract `Species` (Race) into its own model (Name, Traits, Speed, Size, Ability Bonuses).
    - [x] Extract `Class` into its own model (Name, Hit Die, Proficiencies, Features).
    - [x] Extract `Background` into its own model (Name, Skills, Tools, Equipment).
    - [x] Update `CharacterModel` to reference these via Foreign Keys.
- [x] **Implement Feats & Features:**
    - [x] Create `FeatModel` (Name, Description, Effects).
    - [x] Create `FeatureModel` (for Class/Species features).
- [x] **Implement Factions:**
    - [x] Create `FactionModel` (Name, Description, Reputation tracking).
- [ ] **Custom Actions:**
    - [ ] Implement support for `Custom Actions` on `CharacterModel`.
- [x] **Update Tests:**
    - [x] Update `test_logic_routers.py` to handle new Character creation flow (seed Species/Class first).
    - [x] Update `test_schemas.py` to validate new nested structures or ID references.
    - [x] Add tests for `Species`, `Class`, and `Background` CRUD and integrity.

### Milestone 2.5: Data Ingestion (SRD & D&D 5e API)
- [ ] Convert `libsrd5` data into JSON.
- [ ] Write adapters to convert `dnd5e-api` JSON data into the internal data types for each entity (Items, Spells, Monsters, etc.).
- [ ] Implement a setup request/script that ingests all relevant D&D 5e data into the database using these adapters.

## Phase 3: The "Game Master" (State & Simulation)
Focus: Managing the game flow, combat, turns, and user interactions. This handles the "Commands" coming from the frontend.

### Milestone 3.1: Action System (The Command Pattern)
- [ ] **Action Model:** Define the structure for Actions (Attack, Cast, Dash, etc.).
- [ ] **Command Handler:** Implement the endpoint/logic to receive commands (`POST /action/execute`).
- [ ] **Action Resolver:** Logic to resolve generic actions (Attack Roll -> Hit/Miss -> Damage).
- [ ] **Tests:** Verify that sending an attack command results in correct HP deduction.

### Milestone 3.2: Combat & Turn System
- [ ] **Initiative Tracker:** Logic to roll and sort initiative.
- [ ] **Turn Manager:** Track Current Turn, Round, and Phase (Start/End of turn).
- [ ] **Action Economy:** Track usage of Action, Bonus Action, Reaction per turn.
- [ ] **Tests:** Verify turn passing and action economy restrictions.

### Milestone 3.3: Real-Time Session State
- [ ] **WebSocket Manager:** Implement broadcasting of state changes to connected clients.
- [ ] **Session State:** Manage active users and their selected characters.
- [ ] **Synchronization:** Ensure frontend receives updated View Models after every action.

## Phase 4: The Platform (Management & Expansion)
Focus: User management, advanced modding, and content creation tools.

### Milestone 4.1: User & Campaign Management
- [ ] **User Auth:** Implement Authentication and Authorization.
- [ ] **Campaign Management:** Full CRUD for Campaigns (invites, GM assignment).
- [ ] **Wiki/Notes:** Implement a system for campaign notes and wiki entries.

### Milestone 4.2: Effect Engine V2 (Dynamic & Scripting)
- [ ] **Dynamic Effects:** Implement Triggers (ON_HIT, ON_TURN_START) and Conditions.
- [ ] **Safe Evaluation:** Integrate `simpleeval` for formula parsing.
- [ ] **Tests:** Verify complex effects (e.g., "Deal extra 1d6 damage if target is wounded").

### Milestone 4.3: Modding System
- [ ] **Mod Loader:** File system watcher for `/mods` directory.
- [ ] **Data Merging:** Logic to merge Core < Community < Homebrew data.
- [ ] **Export/Import:** Tools to export campaign data as modules.
