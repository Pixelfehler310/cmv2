# Combat Slice Layer Refactor ADR

Status: Accepted
Date: 2026-03-22
Owners: Engineering

## Context

The DND5E backend combat slice currently mixes transport, orchestration, domain rules, and persistence in shared code paths.

Primary hotspots:

- `backend/src/systems/dnd5e/ws_handler.py`
- `backend/src/systems/dnd5e/services/combat_service.py`
- `backend/src/campaigns/routers/campaigns.py`

This causes high regression risk and slows feature changes for:

- Combat context load (campaign -> scene -> encounter)
- Action resolve (authorize -> resolve -> persist -> emit)

The known-issues document identifies this as critical architecture debt (A2/A3/A5/A6).

## Decision

We will refactor one backend vertical slice end-to-end using explicit layers:

1. Transport layer
2. Application service layer
3. Domain layer
4. Repository layer

The first implementation slice is:

- Combat context load
- Action resolve

We will implement this as a multi-PR migration (6 PR target) and keep the system runnable after every PR.

## Layer Boundaries

## Transport Layer

Files:

- `backend/src/systems/dnd5e/ws_handler.py`
- `backend/src/campaigns/routers/campaigns.py`
- `backend/src/systems/dnd5e/encounter_router.py`

Responsibilities:

- Parse and validate inbound protocol payloads.
- Call application service methods with typed inputs.
- Map service results to outbound response/envelope models.

Non-responsibilities:

- No SQL/persistence operations.
- No direct domain rule implementation.
- No side-effect orchestration beyond dispatch.

## Application Service Layer

Target modules (new):

- `backend/src/systems/dnd5e/application/context_service.py`
- `backend/src/systems/dnd5e/application/action_execution_service.py`

Responsibilities:

- Use-case orchestration.
- Transaction boundaries and sequencing.
- Calling repositories and domain services in deterministic order.

Non-responsibilities:

- No protocol envelope parsing.
- No low-level SQL statements.

## Domain Layer

Files (existing + extracted):

- `backend/src/systems/dnd5e/engine/action_resolver.py`
- `backend/src/systems/dnd5e/domain/*` (new extraction targets)

Responsibilities:

- Combat invariants.
- Authorization and action economy rules.
- Action family resolution and domain event outcomes.

Non-responsibilities:

- No DB session usage.
- No framework/websocket concerns.

## Repository Layer

Target modules (new):

- `backend/src/systems/dnd5e/repositories/context_repository.py`
- `backend/src/systems/dnd5e/repositories/encounter_session_repository.py`
- `backend/src/systems/dnd5e/repositories/action_catalog_repository.py`
- `backend/src/systems/dnd5e/repositories/action_execution_repository.py`

Responsibilities:

- Data access and persistence adapters.
- Mapping DB records to service/domain DTOs.

Non-responsibilities:

- No orchestration logic.
- No protocol/transport behavior.

## Scope Rules

In scope now:

- Layered refactor for context load and action resolve only.
- Remove fallback paths in this slice when they conflict with architecture target (MVP policy).
- Preserve existing contract shapes unless explicitly versioned.

Out of scope now:

- Real-time broadcast of context selection changes (follow-up).
- Full backend-wide architecture rewrite.
- Generic action-id migration (A7) before boundary extraction.

## Why Generic Action Naming Is Not First

Generic action naming is a content/modeling migration. It should run after the action execution boundary is stable.

Therefore, this ADR sequences:

1. Boundary extraction and layering.
2. Generic action-id migration in a follow-up epic.

## Delivery Plan (PR Sequence)

1. PR1: ADR + characterization tests for current behavior.
2. PR2: Context repositories and application service extraction.
3. PR3: Action execution repositories and application service extraction.
4. PR4: Domain extraction and cleanup from current mixed service.
5. PR5: Remove remaining in-memory bypasses for this slice.
6. PR6: Hardening tests and guardrails.

## Guardrails

Every PR in this epic must state:

- Which layer changed.
- Which contract changed (if any).
- Which generated artifacts were updated.

PRs are rejected if they:

- Add hardcoded gameplay state in production paths.
- Re-introduce direct persistence access in routers or websocket handlers.

## Verification

Per PR verification requirements:

1. Run backend tests for touched slice.
2. Add/update service-layer tests without FastAPI/router wiring.
3. Verify no direct repository access from transport handlers.
4. Validate key WS contracts (`state_sync`, action denied/result envelopes) remain stable.
5. Validate persistence survives restart for this slice.

## Consequences

Positive:

- Safer refactors and clearer ownership.
- Lower coupling for future microservice split.
- Easier testability of combat logic.

Trade-offs:

- Temporary duplication during migration.
- Multi-PR coordination overhead.

This is accepted as the lower-risk path compared to a full rewrite.
