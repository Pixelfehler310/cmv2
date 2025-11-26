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
- [ ] Implement `CharacterModel` (Pydantic & DB)
- [ ] Implement `CampaignModel` (Pydantic & DB)
- [ ] Create API Endpoints: Character CRUD (Create, Read, Update, Delete)
- [ ] Create API Endpoints: Campaign CRUD
- [ ] Create and run Tests for Milestone 1.3

// TODO: Test Monsters and Characters with Actions
// TODO: Test Monsters and Characters with Inventory
// TODO: Test Monsters and Characters implicit Actions (from Items, Spells, Effects)

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

// Phase 2B: State Machine for the Game itself and the frontend.
// TODO: Implement State Machine for the Game itself and the frontend.
// Requirements: 
// - Action System
// - Inventory System
// - Turn System
// - Action / Bonus Action / Reaction System / End Turn
// - Instance Management of Characters, Monsters, Items, Spells


## Phase 3: The Platform (Modding & Advanced)
Focus: Modding support, dynamic effects, and community ecosystem.

### Milestone 3.1: Effect Engine V2 (Dynamic)
- [ ] Implement Triggers and Conditions for Effects
- [ ] Integrate `simpleeval` for safe formula evaluation
- [ ] Create and run Tests for Milestone 3.1

### Milestone 3.2: Mod Loader
- [ ] Implement Mod Loading System (File System Watcher/Scanner)
- [ ] Implement Layered Data Merging (Core < Community < Homebrew)
- [ ] Create and run Tests for Milestone 3.2


