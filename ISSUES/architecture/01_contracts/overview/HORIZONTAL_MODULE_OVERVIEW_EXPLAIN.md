# Horizontal Module Overview — Explanation

## Purpose

This explanation describes the two-diagram architecture set used for backend modularization:

1. [ISSUES/architecture/01_contracts/overview/HORIZONTAL_MODULE_OVERVIEW.mmd](ISSUES/architecture/01_contracts/overview/HORIZONTAL_MODULE_OVERVIEW.mmd)
   - Logical feature ownership, cross-module dependencies, contracts, and infrastructure.
2. [ISSUES/architecture/01_contracts/overview/HORIZONTAL_BACKEND_NAMESPACE_OVERVIEW.mmd](ISSUES/architecture/01_contracts/overview/HORIZONTAL_BACKEND_NAMESPACE_OVERVIEW.mmd)
   - Concrete Python namespace and package target map under backend/src.

## Why the new structure exists

The previous module map was too generic to guide implementation. The updated structure is anchored to:

- V01 runtime hierarchy boundaries.
- V02 action execution and event contract boundaries.
- V05 content write/read split and linked-entry integrity.
- Planned but separate V03, V04, and V06 extension scopes.

This keeps backend as truth, preserves contract-first governance, and avoids mixing planned streams into active module ownership.

## Diagram 1: Feature Module Map

The feature map is for architecture decisions and contract review.

Included module groups:

- Active and implemented core modules:
  - Runtime Hierarchy (V01)
  - Action Execution and Turn Economy (V02)
  - Content Write Path (V05)
  - Content Query and Projection (V05)
  - Campaign Scope and Membership
  - Character Sheet Domain
  - Identity and Entitlements
  - Asset Management
  - Transport Interfaces
  - Audit and Recovery
- Horizontal contracts:
  - Lifecycle and Revision
  - Referential Integrity
  - Action Operation Graph
  - Event Ordering and Correlation
  - Projection Consistency
  - Authorization and Visibility
- Infrastructure:
  - PostgreSQL source of truth
  - Search projection store
  - Event stream
  - Blob storage
  - Monitoring and telemetry
- Planned extensions (separate scope):
  - V03 World Context Runtime
  - V04 Content Schema and Pack Lifecycle
  - V06 Event Contract Freeze and Frontend Projection

Interpretation rule:

- Solid edges: active ownership and runtime dependencies.
- Dotted edges: planned dependencies to isolated extension scopes.

## Diagram 2: Backend Namespace Map

The namespace map is for implementation planning and refactor sequencing.

It includes:

- Current package anchors in backend/src/systems/dnd5e:
  - application
  - domain
  - engine
  - repositories
  - services
  - schemas
  - transport files
  - content package (already layered)
- Target namespace modules for full backend architecture:
  - runtime
  - actions
  - content_write
  - content_query
  - campaigns
  - sheets
  - assets
  - identity/entitlements
  - events
  - recovery
  - shared contracts/persistence/policies
- Planned extension namespaces (separate scope):
  - world (V03)
  - content_schema (V04)
  - projection_contracts (V06)

Interpretation rule:

- Dotted edges from current anchors to target modules are migration paths, not final runtime dependencies.

## Mapping guidance

Use these diagrams together:

1. Start with the feature map to confirm ownership and contract boundaries.
2. Use the namespace map to decide where Python modules and services live.
3. Keep planned extensions outside active module implementation until the corresponding module is activated.

## Guardrails for future edits

- Do not add a feature node without naming its contract dependencies.
- Do not add a namespace node without indicating whether it is current, target, or planned.
- Keep V03/V04/V06 in the separate planned section unless activation status changes in the vertical program board.
