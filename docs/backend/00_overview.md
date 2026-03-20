# Backend Architecture — Overview

> **As-Is Documentation** — Reflects the actual codebase state as of March 2026.

## System Summary

The CMV2 backend is a Python/FastAPI application serving a D&D 5e Virtual Tabletop engine over WebSockets with a supporting REST API. All game logic is strictly typed via `Pydantic` v2 models. The system is divided into two conceptual layers:

| Layer | Purpose |
|---|---|
| **Core Transport** | System-agnostic WebSocket connection management, JWT auth, session management, outbound broadcasting |
| **D&D 5e Engine** | All game rules, schemas, state machines, resolvers, and compendium data — specific to the `dnd5e` game system |

---

## High-Level Module Map

```mermaid
graph TD
    Client["Browser Client"]
    WSD["core/ws_dispatcher.py\n(WS Endpoint)"]
    SM["core/sessions/\n(SessionManager)"]
    WH["systems/dnd5e/ws_handler.py\n(Dnd5eWsHandler)"]
    CS["systems/dnd5e/services/\n(CombatService)"]
    AR["engine/action_resolver.py"]
    CSM["engine/combat_state.py"]
    EE["engine/effect_engine.py"]
    CONC["engine/concentration.py"]
    INIT["engine/initiative.py"]
    DICE["engine/dice.py"]
    STAT["engine/stat_calculator.py"]
    DMG["engine/damage.py"]
    COND["engine/condition_engine.py"]
    CB["engine/character_builder.py"]
    SCHEMAS["systems/dnd5e/schemas/\n(All Pydantic Models)"]
    DATA["systems/dnd5e/data/\n(Loader + Registry)"]
    CAMP["campaigns/routers/\n(REST API)"]
    IDENT["identity/\n(Auth/JWT)"]
    DB[("PostgreSQL DB")]

    Client -->|JWT + WS| WSD
    WSD --> SM
    WSD --> WH
    WH --> CS
    WH --> EE
    WH --> INIT
    WH --> DICE
    CS --> AR
    CS --> CSM
    AR --> DICE
    AR --> DMG
    AR --> COND
    AR --> CONC
    CSM --> INIT
    EE --> CONC
    CB --> DATA
    CS --> DATA
    CS --> DB
    CAMP --> DB
    IDENT --> DB
    WSD -->|HTTP| IDENT
    WH --> SCHEMAS
    CS --> SCHEMAS
```

---

## Module Index

| # | File | Area | Purpose |
|---|---|---|---|
| [01](./01_core_transport.md) | `core/ws_protocol.py`, `core/ws_dispatcher.py`, `core/sessions/` | Core Transport | WS connection handling, JWT auth, session registry, broadcast |
| [02](./02_schemas.md) | `systems/dnd5e/schemas/` | D&D 5e Schemas | All Pydantic models: enums, definitions, instances, encounter |
| [03](./03_data_compendium.md) | `systems/dnd5e/data/` | Data/Compendium | Loader (JSON → pydantic), Registry (in-memory lookup) |
| [04](./04_stateless_rules_engine.md) | `engine/dice.py`, `stat_calculator.py`, `damage.py`, `condition_engine.py` | Rules Engine | Pure-function math: dice, stat derivation, damage pipeline, conditions |
| [05](./05_combat_state_machine.md) | `engine/initiative.py`, `combat_state.py`, `effect_engine.py`, `concentration.py` | Combat State | Initiative, turn budget, effect ticking, concentration management |
| [06](./06_action_resolver.md) | `engine/action_resolver.py` | Action Resolver | Orchestrates attacks, saves, and healing pipelines end-to-end |
| [07](./07_character_builder.md) | `engine/character_builder.py` | Character Builder | Blueprint → combat-ready ActorInstance |
| [08](./08_websocket_handler.md) | `systems/dnd5e/ws_handler.py`, `permissions.py`, `state_filter.py`, `event_types.py` | WS Handler | D&D event dispatch, Fog of War filtering, permission enforcement |
| [09](./09_campaign_api.md) | `campaigns/routers/`, `systems/dnd5e/services/`, `encounter_router.py` | Campaign REST API | Campaign/character CRUD, session persistence, encounter management |
| [10](./10_identity_and_auth.md) | `identity/`, `config.py`, `database.py` | Identity & Auth | JWT auth, user model, DB sessions |

---

## Data Flow: WebSocket Request Lifecycle

```mermaid
sequenceDiagram
    participant C as Client
    participant WSD as ws_dispatcher
    participant SM as SessionManager
    participant WH as Dnd5eWsHandler
    participant CS as CombatService
    participant ENG as Engine (rules)

    C->>WSD: connect /ws/{campaign_id}?token=JWT
    WSD->>WSD: validate JWT
    WSD->>SM: register_connection()
    WSD->>WH: on_connect() → state_sync
    WSD-->>C: state_sync (filtered by role)

    C->>WSD: {"type":"action", "request_id":"x", "payload":{...}}
    WSD->>WH: handle(envelope, ctx, mgr)
    WH->>WH: check_permission(event_type, ctx)
    WH->>CS: check_can_act()
    CS-->>WH: AuthResult
    WH->>ENG: resolve_attack() / resolve_healing() / etc.
    ENG-->>WH: AttackResult / HealingResult
    WH->>SM: broadcast([WsOutbound, ...])
    SM-->>C: {type: "action_authorized", ...}
    SM-->>C: {type: "actor_damaged", ...}
```
