# Backend Implementation Plan

This document outlines the step-by-step plan to build the Open RPG Engine backend, following the "Modular Monolith" architecture.

## Phase 1: Foundation & The "Digital Filing Cabinet" (MVP)
Focus: Administration, Data Persistence, and serving static content (SRD).

### Milestone 1.1: Project Setup & Infrastructure
- [x] Initialize Python project structure
- [x] Setup FastAPI basic application (`main.py`)
- [ ] Setup Docker/Docker Compose for Database (PostgreSQL)
- [ ] Configure Database Connection (SQLAlchemy/AsyncPG)
- [ ] Create Base Pydantic Models & DB Models structure

### Milestone 1.2: Data Service ("The Librarian") - Basic
- [ ] Implement `ItemModel` (Pydantic & DB)
- [ ] Implement `SpellModel` (Pydantic & DB)
- [ ] Implement `MonsterModel` (Pydantic & DB)
- [ ] Create JSON Loader Service (for SRD data)
- [ ] Create API Endpoints: List/Get Items
- [ ] Create API Endpoints: List/Get Spells
- [ ] Create API Endpoints: List/Get Monsters

### Milestone 1.3: Logic Service ("The Game Master") - State Management
- [ ] Implement `CharacterModel` (Pydantic & DB)
- [ ] Implement `CampaignModel` (Pydantic & DB)
- [ ] Create API Endpoints: Character CRUD (Create, Read, Update, Delete)
- [ ] Create API Endpoints: Campaign CRUD

## Phase 2: The "Calculator" (Automation)
Focus: Automating calculations, dice rolls, and basic rules.

### Milestone 2.1: Dice & Basic Rules
- [ ] Implement Dice Rolling Utility/Service
- [ ] Implement Attribute Modifier Calculation Logic

### Milestone 2.2: Effect Engine V1 (Static Bonuses)
- [ ] Define `EffectModel` JSON Structure
- [ ] Implement `EffectEngine` (Apply static modifiers)
- [ ] Integrate Effect Engine into Character View Model calculation

### Milestone 2.3: Actions & Combat
- [ ] Define `ActionModel` (JSON structure for Actions)
- [ ] Implement Command Pattern for Actions (e.g., `POST /action/execute`)
- [ ] Implement Combat Logic (Hit/Miss, Damage Calculation)

## Phase 3: The Platform (Modding & Advanced)
Focus: Modding support, dynamic effects, and community ecosystem.

### Milestone 3.1: Mod Loader
- [ ] Implement Mod Loading System (File System Watcher/Scanner)
- [ ] Implement Layered Data Merging (Core < Community < Homebrew)

### Milestone 3.2: Effect Engine V2 (Dynamic)
- [ ] Implement Triggers and Conditions for Effects
- [ ] Integrate `simpleeval` for safe formula evaluation
