# Project Roadmap

## Phase 1: The Foundation & Digital Filing Cabinet (MVP)

**Goal:** A stable system for hybrid play. Replaces paper. GM has full control. No automation.

### Backend (Python/FastAPI)

- [ ] Monorepo Setup & Docker Compose (PostgreSQL).
- [ ] **Data Service V1:** Pydantic Models for Definitions. Import Script for SRD 5.1 subset. API `GET /definitions`.
- [ ] **Logic Service V1:** Pydantic Models for State (Campaign, Character). CRUD Endpoints. Database Setup.

### Frontend (React/Vite)

- [ ] Workspace Setup (Host + Remotes).
- [ ] **App Shell:** Layout (FlexLayout), Login (Dummy), API Client.
- [ ] **Player Sheet MFE:** Read-only view of stats/inventory.
- [ ] **DM Tools MFE:** List of characters/monsters. "God Mode" editing (PATCH on blur). Monster Spawner.

## Phase 2: Automation & Interaction

**Goal:** Speed up play. Backend handles math/rules. Real-time updates.

### Backend

- [ ] **WebSocket:** `STATE_UPDATE` events.
- [ ] **Effect Engine V1:** Passive Effects (Static Bonuses). Calculation Manager.
- [ ] **Command API:** `POST /command/roll`.

### Frontend

- [ ] **Comm Center MFE:** Chat & Log. Display Roll Results.
- [ ] **Interactive Sheet:** Click-to-roll (dispatch Command).
- [ ] **Cartographer MFE:** Map MVP (Grid, Tokens, Drag & Drop).

## Phase 3: Ecosystem (Scaling & Modding)

**Goal:** The Platform.

- [ ] **Infrastructure:** Docker Containers for Services.
- [ ] **Data Service V2:** Full Mod Loader.
- [ ] **Logic Service V2:** Complex Effects (Triggers/Conditions).
- [ ] **Frontend V2:** Mod Launcher, External MFEs.
- [ ] **AI Integration:** AI Service as NPC.
