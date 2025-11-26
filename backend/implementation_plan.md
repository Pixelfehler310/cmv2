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

## Phase 2: The "Calculator" (Automation)
Focus: Automating calculations, dice rolls, and basic rules.

### Milestone 2.1: Dice & Basic Rules
- [ ] Implement Dice Rolling Utility/Service
- [ ] Implement Attribute Modifier Calculation Logic
- [ ] Create and run Tests for Milestone 2.1

### Milestone 2.2: Effect Engine V1 (Static Bonuses)
- [ ] Define `EffectModel` JSON Structure
- [ ] Implement `EffectEngine` (Apply static modifiers)
- [ ] Integrate Effect Engine into Character View Model calculation
- [ ] Create and run Tests for Milestone 2.2

### Milestone 2.3: Actions & Combat
- [ ] Define `ActionModel` (JSON structure for Actions)
- [ ] Implement Command Pattern for Actions (e.g., `POST /action/execute`)
- [ ] Implement Combat Logic (Hit/Miss, Damage Calculation)
- [ ] Create and run Tests for Milestone 2.3

### Milestone 2.4: State Machine for the Game itself and the frontend.
- [ ] Implement State Machine for the Game itself and the frontend (webhook based) // TODO plan in detail
- [ ] Requirements: 
- [ ] Action System (Attack, Cast Spell, Use Item, Use Ability, Use Feature)
- [ ] Inventory System (Add and Remove and Use items, Passive Effects)
- [ ] Turn System (End Turn, Pass Turn, Skip Turn)
- [ ] Action / Bonus Action / Reaction System / Rest, ...
- [ ] Instance Management:
    - [ ] Implement `MonsterInstance` Model (linked to `Monster` template, with `current_hp`, `campaign_id`, etc.)
    - [ ] Implement `ItemInstance` logic (within Inventory)
    - [ ] Implement `SpellInstance` logic (Prepared/Known)
- [ ] Create and run Tests for Milestone 2.4

### Milestone 2.5: User, Wiki and Campaign Management (Add Homebrewed Content via Visual, form based Editors)
- [ ] Implement User Management (Authentication, Authorization) ! Relations (Campaigns + Characters)
- [ ] Implement Campaign Management (Create, Read, Update, Delete) ! Relations
- [ ] Implement Character Management (Create, Read, Update, Delete) ! Relations
- [ ] Implement Monster Management (Create, Read, Update, Delete) ! Relations
- [ ] Implement Spell Management (Create, Read, Update, Delete) ! Relations
- [ ] Implement Item Management (Create, Read, Update, Delete) ! Relations
- [ ] Implement Combat / Encounter Designer (Create, Read, Update, Delete) ! Relations
- [ ] Implement Wiki Management (Create, Read, Update, Delete) ! Relations
- [ ] Create and run Tests for Milestone 2.5


## Phase 3: The Platform (Modding & Advanced)
Focus: Modding support, dynamic effects, and community ecosystem.

### Milestone 3.1: Effect Engine V2 (Dynamic)
- [ ] Implement Triggers and Conditions for Effects
- [ ] Integrate `simpleeval` for safe formula evaluation
- [ ] Create and run Tests for Milestone 3.1

### Milestone 3.2: Advanced Features
- [ ] Chat Window with Whisper functionality
- [ ] Implement Dice Roller with more complex dice expressions (e.g., "2d6+3")
- [ ] Campaign Visual Designer (Node Based)
- [ ] Google (and co) - OAuth

### Milestone 3.2: Mod Loader
- [ ] Implement Mod Loading System (File System Watcher/Scanner)
- [ ] Implement Layered Data Merging (Core < Community < Homebrew)
- [ ] Create and run Tests for Milestone 3.2


