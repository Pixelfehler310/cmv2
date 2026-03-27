# ISSUE [VERT][V05-05]: REST/WS Contract Convergence for Content Streams

Status: Planned
Owner: Backend + Frontend Contracts
Parent: ISSUE [VERT][V05]
Depends on:

- ISSUE [VERT][V05-04]

## Why This Exists

Content management needs deterministic contracts across transport surfaces.
This issue aligns REST payloads and optional websocket content-stream events so list/detail views and character-sheet-linked lookups remain consistent.

## Scope

In scope:

- Align REST list/detail/create/update/delete payloads to V05 contracts.
- Define and align optional content-stream websocket events for cache invalidation and live update propagation.
- Enforce request correlation and reason-code parity for denied/error outcomes.
- Define stable read-model mapping expectations for frontend adapters.

Out of scope:

- Visual component design.
- Search ranking policy changes.

## Deliverables

1. REST contract matrix for all scoped definition families.
2. WS content-stream event taxonomy and payload contracts.
3. Parity checklist between REST responses and WS event semantics.
4. Adapter mapping notes for content list, content detail, and character-sheet-linked definition views.

## Acceptance Criteria

1. REST payloads are contract-stable and typed.
2. WS content-stream events are contract-stable where enabled.
3. Denied/error reason taxonomy is transport-consistent.
4. Frontend adapter expectations are explicit and test-covered.

## Verification Commands

1. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e -k ws -q
2. docker compose --profile test run --rm backend-test pytest tests/data -k api -q
3. docker compose --profile test run --rm -e PYTHONPATH=/app backend-test python scripts/generate_types.py --check
4. docker compose logs backend --tail=200

## Risks and Notes

- REST/WS drift can cause stale or conflicting management-view state.
- Uncorrelated update events can break linked-entry detail navigation consistency.
