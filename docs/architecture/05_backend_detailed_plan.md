# Backend Detailed Implementation Plan

## 1. Directory Structure (Refactored)
We will restructure `backend/src` to enforce strict modularity. We introduce an **Identity** module for user management, separate from the **Game** logic.

```
backend/src/
├── common/                 # Shared utilities (types, helpers)
├── data/                   # MODULE: "The Librarian" (Static Definitions)
│   ├── models.py           # Pydantic Models (ItemDef, SpellDef)
│   ├── loader.py           # JSON File Loader
│   └── interface.py        # Public Python API
├── engine/                 # MODULE: "The Core" (Pure Rules Engine)
│   ├── models.py           # Pure State Models (Character, Stats)
│   ├── calculator.py       # Stat calculation logic
│   └── effects.py          # Effect processing
├── identity/               # MODULE: "The Gatekeeper" (Users & Auth)
│   ├── models.py           # User, FriendRequest DB Models
│   ├── auth.py             # JWT, OAuth logic
│   └── router.py           # API: /auth, /users, /friends
├── game/                   # APP: "The Game Master" (Campaign State)
│   ├── db/                 # Database Layer (Campaigns, Characters)
│   ├── api/                # FastAPI Routers (/campaigns)
│   └── main.py             # Game Server Logic
└── main.py                 # App Entrypoint (Mounts Identity & Game routers)
```

## 2. Module: Data ("The Librarian")
*   **Purpose:** A standalone library to access static game content.
*   **Usage:** Can be imported by the Wiki generator or the Game Engine.
*   **Key Components:**
    *   `models.py`: `ItemDefinition`, `MonsterDefinition`.
    *   `loader.py`: Loads JSONs from disk.
    *   `interface.py`: `DataClient` class to query data.

## 3. Module: Engine ("The Core")
*   **Purpose:** A pure Python library for D&D 5e rules. **No Database, No API.**
*   **Usage:** Can be imported by the Service, a CLI tool, or a Simulator.
*   **Key Components:**
    *   `models.py`: `CharacterSheet` (Pydantic). This is the "In-Memory" state used for calculation.
    *   `calculator.py`: `calculate_ac(sheet, items)`, `calculate_to_hit(...)`.
    *   `effects.py`: Applies `PassiveEffect` to `CharacterSheet`.

## 4. Module: Identity ("The Gatekeeper")
*   **Purpose:** Manages Users, Authentication, and Social features.
*   **Responsibility:**
    *   User Registration/Login (JWT).
    *   OAuth Integration (Google) - *Future*.
    *   Friend System / User Search.
    *   User Settings.
*   **Separation:** Has its own DB tables (`users`, `friendships`).

## 5. App: Game ("The Game Master")
*   **Purpose:** Manages persistent campaign state and exposes the game via HTTP/WS.
*   **Responsibility:**
    1.  Load State from DB (`game.db`).
    2.  Load Definitions from Data Module (`src.data`).
    3.  Convert to Engine Models (`src.engine.models`).
    4.  Run Calculation (`src.engine.calculator`).
    5.  Return View Model to Frontend.

## 6. Implementation Steps (Phase 1)

1.  **Refactor Folder Structure:** Create `src/data`, `src/engine`, `src/identity`, `src/game`.
2.  **Implement Data Module:**
    *   Move Definition Models.
    *   Implement JSON Loader.
3.  **Implement Engine Module:**
    *   Create Pure Pydantic State Models.
    *   Implement basic AC/HP calculation logic.
4.  **Implement Identity Module:**
    *   Setup User DB Model.
    *   Implement Basic Auth (Login/Register).
5.  **Implement Game Module:**
    *   Setup Campaign/Character DB Models.
    *   Create API Routers.
6.  **Connect Frontend:** Update API calls.
