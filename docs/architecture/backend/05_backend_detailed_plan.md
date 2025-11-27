# Backend Detailed Implementation Plan

## 1. Directory Structure (Refactored)

We will restructure `backend/src` to enforce strict modularity. Each module is a self-contained unit with its own **Logic** and **API**.

```
backend/src/
├── common/                 # Shared utilities (types, helpers)
├── data/                   # MODULE: "The Librarian" (Static Content)
│   ├── lib/                # Internal Logic
│   │   ├── loader.py       # JSON/YAML Parsing
│   │   ├── registry.py     # In-Memory Storage
│   │   └── provider.py     # Search & Filtering
│   ├── router.py           # API: /data/items, /data/monsters
│   ├── interface.py        # Protocol: IDataClient
│   └── client.py           # LocalDataClient, RemoteDataClient
├── engine/                 # MODULE: "The Core" (Pure Rules)
│   ├── lib/                # Internal Logic
│   │   ├── mechanics.py    # D20 Logic (Advantage, Crits)
│   │   ├── calculator.py   # Stat Derivation (AC, HP, Bonuses)
│   │   └── resolver.py     # Action Outcomes (Hit/Miss, Save/Fail)
│   ├── router.py           # API: /engine/calculate
│   └── ...
├── identity/               # MODULE: "The Gatekeeper" (Users & Config)
│   ├── lib/                # Internal Logic
│   │   ├── auth.py         # JWT, OAuth
│   │   ├── users.py        # User Management
│   │   └── preferences.py  # UI Config (FlexLayout)
│   ├── router.py           # API: /auth, /users, /preferences
│   └── ...
├── campaigns/              # APP: "The State Manager" (Formerly 'Game')
│   ├── lib/                # Internal Logic
│   │   ├── session.py      # Connection Handling
│   │   ├── actors.py       # Character/Monster Instances (HP, Slots)
│   │   ├── encounters.py   # Initiative, Turn Order
│   │   └── scenes.py       # Maps, Tokens, Fog of War
│   ├── router.py           # API: /campaigns/{id}/...
│   └── ...
└── main.py                 # MONOLITH ENTRYPOINT (Mounts all routers)
```

## 2. The "Microservice-Ready" Pattern

### A. Structure: Library + API

Every module is built as if it were already a microservice.

1.  **The Library (`lib/`):** Pure Python logic. No dependency on FastAPI context.
2.  **The API (`router.py`):** A FastAPI `APIRouter` that wraps the Library.
3.  **The Entrypoint (`main.py`):**
    - **Phase 1 (Monolith):** One global `main.py` imports and mounts **all** routers (`/data`, `/auth`, `/campaigns`).
    - **Phase 3 (Microservices):** We create a tiny `main.py` inside each module that mounts **only** that module's router.

### B. Communication: The Swappable Client

Modules communicate via **Interfaces**.

- **Interface:** `IDataClient` (Protocol).
- **Implementation A (`LocalDataClient`):** Imports `src.data.lib` directly. Used in Phase 1 for performance.
- **Implementation B (`RemoteDataClient`):** Calls `http://data-service/api`. Used in Phase 3.
- **Dependency Injection:** The Campaigns Module receives an instance of `IDataClient` at startup. We simply swap the instance to switch architectures.

## 3. Module: Data ("The Librarian")

- **Purpose:** Static Content (SRD, Homebrew).
- **Submodules:**
  - `loader`: Parses JSON/YAML files from disk.
  - `registry`: In-memory storage for fast lookups.
  - `provider`: Search, filtering, and retrieval logic.
- **API:** `GET /data/items`, `GET /data/monsters`.
- **Client:** `LocalDataClient` (reads in-memory dict), `RemoteDataClient` (calls API).

## 4. Module: Engine ("The Core")

- **Purpose:** Pure Rules & Math. **Stateless.**
- **Submodules:**
  - `mechanics`: Core d20 logic (Advantage, Crits, Proficiency).
  - `calculator`: Stat derivation (AC, HP, Attack Bonuses).
  - `resolver`: Action outcomes (Hit/Miss, Save/Fail, Damage application logic).
- **API:** `POST /engine/calculate` (Stateless).
  - _Why an API?_ Allows external tools (simulators) to use our rules without importing Python code.
- **Client:** `LocalEngineClient` (direct call), `RemoteEngineClient` (HTTP).

## 5. Module: Identity ("The Gatekeeper")

- **Purpose:** Users, Auth, & Configuration.
- **Submodules:**
  - `auth`: JWT handling, OAuth, Login/Register.
  - `users`: User profile management, Friend lists.
  - `preferences`: Stores UI configuration (FlexLayout JSON) per user.
- **API:** `POST /auth/login`, `GET /auth/me`, `GET /users/preferences`.
- **Client:** `LocalIdentityClient` (direct DB access), `RemoteIdentityClient` (HTTP).

## 6. App: Campaigns ("The State Manager")

- **Purpose:** Manages the active state of games. **Stateful.**
- **Submodules:**
  - `session`: Manages active WebSocket connections and user presence.
  - `actors`: Manages instances of Characters and Monsters (Current HP, Spell Slots, Conditions).
  - `encounters`: Manages Initiative, Turn Order, and Active Combat state.
  - `scenes`: Manages Maps, Tokens, Fog of War, and Drawings.
  - `chat`: Manages dice roll history and messages.
- **API:** `GET /campaigns/{id}`, `WS /campaigns/{id}/ws`.
- **Dependencies:** Uses `IDataClient`, `IEngineClient`, `IIdentityClient`.

## 7. Boundary: Engine vs. Campaigns

| Feature            | **Engine** (The Rulebook)                    | **Campaigns** (The Table)                                   |
| :----------------- | :------------------------------------------- | :---------------------------------------------------------- |
| **State**          | Stateless. Knows nothing about "Campaign 1". | Stateful. Knows "Goblin A" has 5 HP left.                   |
| **Logic**          | "Does 18 hit AC 15?" -> `True`               | "Goblin A attacks Player B." -> Calls Engine -> Updates DB. |
| **Data**           | Input: `(Roll=18, AC=15)`                    | Input: `(AttackerID, TargetID)`                             |
| **Responsibility** | Math & Validation.                           | Orchestration & Persistence.                                |

## 8. Implementation Steps (Phase 1)

1.  **Refactor Folder Structure:** Create the `lib/` + `router.py` structure for each module.
2.  **Implement Data Module:**
    - Build `lib/loader.py`, `lib/registry.py`.
    - Build `router.py` exposing definitions.
    - Build `client.py` (Local/Remote).
3.  **Implement Engine Module:**
    - Build `lib/mechanics.py`, `lib/calculator.py`.
    - Build `router.py`.
4.  **Implement Identity Module:**
    - Build `lib/auth.py`, `lib/preferences.py`.
    - Build `router.py`.
5.  **Implement Campaigns Module:**
    - Build `lib/session.py`, `lib/actors.py`, `lib/scenes.py`.
    - Build `router.py`.
    - **Inject Local Clients.**
6.  **Setup Monolith Entrypoint:** `src/main.py` mounts all routers.
