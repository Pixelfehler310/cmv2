# ISSUE: Data Historization and History Tables

Status: Backlogged
Owner: Backend Architecture
Vertical: [V04 Content Schema and Pack Lifecycle](../../docs/archive/planning_legacy/docs_architecture/shared/05_vertical_module_execution_plan.md)

## Goal

Ensure that every change to critical application and content data is tracked over time. This allows for historical auditing, change-set tracking, and potential rollback of erroneous updates.

## Scope

- **History Tables**: Implementation of separate shadow tables (e.g., `monster_instance_history`) to record every state change.
- **Versioning**: Each record version receives a unique increment or timestamp.
- **Audit Logging**: Traceability of who (User ID) made which change and when.
- **Retrieval**: API support for querying the state of an entity at a specific point in time.

## Proposed Components

- `backend/src/persistence/history_manager.py` (Generic history logic/triggers).
- `backend/src/models/history_base.py` (Base class for historical shadow models).
- `backend/src/persistence/repository_historized_decorator.py` (Optional decorator path).

## Tasks

1. Define the persistence pattern (e.g., PostgreSQL temporal tables vs. simple shadow tables).
2. Automate history record insertion on every `INSERT` or `UPDATE` for historized entities.
3. Integrate history tracking into the Service layer (Application Services).
4. Expose a "View History" endpoint for Compendium definitions.

## Definition of Done

1. Every update to a `MonsterInstance` or `ContentPack` entry creates a new row in a history table.
2. The UI can display a diff between two versions of the same entity.
3. Rollback to a previous version is possible through a single command/endpoint call.
