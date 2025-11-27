# Backend Detailed Implementation Plan

## 1. Directory Structure (Refactored)

We will restructure `backend/src` to enforce strict modularity. Each module is a self-contained unit with its own **Logic** and **API**.

```
backend/src/
├── common/                 # Shared utilities (types, helpers)
├── data/                   # MODULE: "The Librarian"
│   ├── lib/                # Internal Logic (Loader, Models)
│   ├── router.py           # FastAPI Router (The API)
│   ├── interface.py        # Abstract Client Interface
│   └── client.py           # Local & Remote Client Implementations
├── engine/                 # MODULE: "The Core"
│   ├── lib/                # Internal Logic (Calculator, Effects)
│   ├── router.py           # FastAPI Router (Stateless Calculation API)
│   ├── calculator.py       # Stat calculation logic
│   ├── effects.py          # Effect processing
│   └── ...
├── identity/               # MODULE: "The Gatekeeper"
│   ├── lib/                # Internal Logic (Auth, DB)
│   ├── models.py           # User, FriendRequest DB Models
│   ├── auth.py             # JWT, OAuth logic
│   └── router.py           # API: /auth, /users, /friends
│   ├── router.py           # FastAPI Router (Auth Endpoints)
│   └── ...
├── game/                   # APP: "The Game Master"
│   ├── lib/                # Internal Logic (Campaign State)
│   ├── router.py           # FastAPI Router (Campaign Endpoints)
│   └── ...
└── main.py                 # MONOLITH ENTRYPOINT (Mounts all routers)
```

## 2. The "Microservice-Ready" Pattern

### A. Structure: Library + API

Every module is built as if it were already a microservice.

1.  **The Library (`lib/`):** Pure Python logic. No dependency on FastAPI context.
2.  **The API (`router.py`):** A FastAPI `APIRouter` that wraps the Library.
3.  **The Entrypoint (`main.py`):**
    - **Phase 1 (Monolith):** One global `main.py` imports and mounts **all** routers (`/data`, `/auth`, `/game`).
    - **Phase 3 (Microservices):** We create a tiny `main.py` inside each module that mounts **only** that module's router.

### B. Communication: The Swappable Client

Modules communicate via **Interfaces**.

- **Interface:** `IDataClient` (Protocol).
- **Implementation A (`LocalDataClient`):** Imports `src.data.lib` directly. Used in Phase 1 for performance.
- **Implementation B (`RemoteDataClient`):** Calls `http://data-service/api`. Used in Phase 3.
- **Dependency Injection:** The Game Module receives an instance of `IDataClient` at startup. We simply swap the instance to switch architectures.

## 3. Module: Data ("The Librarian")

- **Purpose:** Static Content.
- **API:** `GET /data/items`, `GET /data/monsters`.
- **Client:** `LocalDataClient` (reads in-memory dict), `RemoteDataClient` (calls API).

## 4. Module: Engine ("The Core")

- **Purpose:** Pure Rules.
- **API:** `POST /engine/calculate_ac` (Stateless).
  - _Why an API?_ Allows external tools (simulators) to use our rules without importing Python code.
- **Client:** `LocalEngineClient` (direct call), `RemoteEngineClient` (HTTP).

## 5. Module: Identity ("The Gatekeeper")

- **Purpose:** Users & Auth.
- **API:** `POST /auth/login`, `GET /auth/me`.
- **Client:** `LocalIdentityClient` (direct DB access), `RemoteIdentityClient` (HTTP).

## 6. App: Game ("The Game Master")

- **Purpose:** Campaign State.
- **API:** `GET /game/campaigns`.
- **Dependencies:** Uses `IDataClient`, `IEngineClient`, `IIdentityClient`.

## 7. Implementation Steps (Phase 1)

1.  **Refactor Folder Structure:** Create the `lib/` + `router.py` structure for each module.
2.  **Implement Data Module:**
    - Build `lib/loader.py`.
    - Build `router.py` exposing definitions.
    - Build `client.py` (Local/Remote).
3.  **Implement Engine Module:**
    - Build `lib/calculator.py`.
    - Build `router.py` (optional for now, but good practice).
4.  **Implement Identity Module:**
    - Build `lib/auth.py`.
    - Build `router.py`.
5.  **Implement Game Module:**
    - Build `lib/manager.py`.
    - Build `router.py`.
    - **Inject Local Clients.**
6.  **Setup Monolith Entrypoint:** `src/main.py` mounts all routers.
