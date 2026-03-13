---
title: Concept - Dynamic Encounter Seed Strategy
description: Proposed architecture for seeding the game engine with dynamic JSON payload directories for comprehensive testing and development.
status: Draft
type: Architecture Concept
---

# Concept: Dynamic Encounter Seed Strategy

## 1. Executive Summary & Motivation
Presently, the process for bootstrapping the DM View development relies on a single static file (`backend/data/fixtures/seed_encounter.json`). While effective as a "walking skeleton," an expanding codebase requires more robust test data management. 

Our proposed solution shifts from a monolithic static payload to a dynamic directory-based parsing mechanism. This approach scales seamlessly as testing complexity increases, implicitly providing continuous integration tests for the stability of JSON import and export mechanisms across various data schemas.

---

## 2. Architecture & Data Flow Overview

The proposed design establishes a deterministic data repository explicitly decoupled from the core runtime database, designed to be hydrated into memory selectively during test execution or local development setups.

1. **The Repository:** A dedicated directory scheme `backend/data/fixtures/encounters/`.
2. **The Loader:** A specialized backend loader scanning the directory.
3. **The Hydration Endpoint:** A development-only route `POST /api/dev/load-seeds` acting as the trigger.

---

## 3. Directory Structure

We will restructure the current fixtures to clearly differentiate environments and object types:

```text
backend/
└── data/
    └── fixtures/
        └── encounters/                 <- New directory for dynamically loaded seeds
            ├── 01_basic_combat.json
            ├── 02_large_map_test.json
            ├── 03_complex_terrain.json
            └── broken_schema_test.json <- Intentional schema testing files
```

---

## 4. Loader Implementation (Backend)

The loader logic fundamentally upgrades `backend/src/routers/dev.py`.

### 4.1. Refactored `load_seed` Logic
Instead of explicitly targeting one filename, the endpoint must intelligently crawl the directory, parsing sequentially, and catching validation errors without halting execution.

- Iterate over all `.json` files in `backend/data/fixtures/encounters/`.
- Employ `EncounterState.model_validate(data)` upon each discovered payload.
- Consolidate successes and failures. Let valid payloads pass into engine memory via `set_encounter()`, while failures are caught and logged efficiently.

### 4.2 API Response Design
The `POST /api/dev/load-seeds` response schema must comprehensively list the status of the run, providing immediate developer feedback.

```json
{
  "status": "partial_success",
  "summary": {
    "total_found": 4,
    "loaded": 3,
    "failed": 1
  },
  "loaded": [
    "01_basic_combat.json",
    "02_large_map_test.json",
    "03_complex_terrain.json"
  ],
  "errors": {
    "broken_schema_test.json": "Validation Error: 'map' field missing in EncounterState payload."
  }
}
```

---

## 5. Security and Environment Constraints

Pumping random JSON fixtures into core application memory poses severe risks if accidentally deployed to production. 

Implementation requirements:
- The parser module and specific `POST /api/dev/load-seeds` must be strictly decoupled from public router assemblies.
- Ensure the dev router (`app.include_router(dev_router)`) is conditionally registered in `backend/src/main.py`. It should strictly evaluate an environment flag (e.g., `LOAD_MOCK_DATA=true` or checking that `ENV=development`) before ever exposing the hook.
