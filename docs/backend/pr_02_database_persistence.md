# PR Concept: Database Persistence for Encounters

> [!CAUTION]
> **WARNING - CRITICAL ARCHITECTURAL FLAW**
> The application currently manages live game data via an in-memory dictionary `_encounters: dict[str, EncounterState]` defined within the singleton footprint of `ws_handler.py`. This is an acceptable MVP stub, but a structurally fatal design for a production system.

## Extensive Explanation of the Structural Flaw
Storing the mutable game state in a local memory dict introduces critical failures for modern web application deployment:
1. **Data Volatility**: Any server restart, crash, or deployment update instantly and permanently deletes all ongoing combat encounters.
2. **Horizontal Scaling Impossibility**: If the FastAPI backend scales to more than one worker container (via Kubernetes or Docker Compose replicas), `Worker A` cannot see the encounter state modified by `Worker B`. WebSocket connections routing to different containers will experience violently fragmented realities of the same game table.
3. **Database Desynchronization**: While campaigns and characters are persistently saved in the PostgreSQL database via SQLAlchemy, the actual state of the game (the Encounter) exists completely outside the source of truth, making historical logging or proper REST API querying impossible.

---

## 1-PR Scoped Fix Concept

### Objective
Completely eliminate the `_encounters` memory dict and enforce that all `EncounterState` loads and mutations are strictly brokered through the PostgreSQL database via the `CombatService` using `AsyncSessionLocal`.

### Acceptance Criteria
1. **Schema Addition**: Ensure there is a persistent JSONB or relational structure in the `encounter_sessions` database table capable of storing the serialized `EncounterState` Pydantic model.
2. **Eliminate Memory Dict**: the `_encounters` global dict is deleted entirely from the codebase.
3. **Transactional Mutations**: Every method in the `CombatService` that mutates state (move, damage, turn advance) must:
   - Accept a database `AsyncSession`.
   - Load the current state from DB row.
   - Mutate the Pydantic `EncounterState`.
   - Call `await session.commit()` to persist the row before broadcasting WebSocket updates.
4. **Concurrent Safety**: Implement optimistic concurrency control (like a version integer on the DB row) to ensure two simultaneously arriving WebSocket commands don't overwrite each other's state changes.

### Execution Steps
1. Navigate to the `campaigns/models.py` (or equivalent Encounter DB model) and verify/add a `state_data: JSONB` column.
2. Update `CombatService._load_session()` to query the DB row, and deserialize the JSONB column back into the `EncounterState` Pydantic model.
3. Update `CombatService.save_full_state()` to serialize the `EncounterState.model_dump(mode="json")`, update the DB row, and commit it.
4. Globally find-and-replace all usages of the deprecated `_encounters` manual cache grab in the WebSocket layer.
