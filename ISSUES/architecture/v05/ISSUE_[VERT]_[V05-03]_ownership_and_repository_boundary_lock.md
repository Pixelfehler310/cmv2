# ISSUE [VERT][V05-03]: Ownership and Repository Boundary Lock

Status: Planned
Owner: Data + Content Systems
Parent: ISSUE [VERT][V05]
Depends on:

- ISSUE [VERT][V05-02]

## Why This Exists

Content correctness depends on deterministic write ownership.
This issue enforces one write authority for definitions, lifecycle transitions, and linked-entry graph updates.

## Scope

In scope:

- Assign single-writer ownership per mutable content aggregate.
- Lock repository boundaries for:
  - definition records
  - content pack metadata
  - linked-entry relationships
  - search index persistence artifacts
- Remove ambiguous write paths between transport, services, and repositories.
- Define transaction boundary for multi-record operations.

Out of scope:

- New entity families outside scoped V05 definitions.
- Frontend projection implementation.

## Deliverables

1. Ownership matrix for V05 aggregates.
2. Repository boundary notes with allowed operations by layer.
3. Transaction policy for create/update/delete/publish operations.
4. Ambiguous-write remediation list and disposition notes.

## Acceptance Criteria

1. Each mutable aggregate has one write authority.
2. No unresolved multi-writer ambiguity remains.
3. Transaction boundaries are explicit and enforceable.
4. Ownership decisions support V05-04 orchestration without fallback paths.

## Verification Commands

1. docker compose --profile test run --rm backend-test pytest tests/data -k repository -q
2. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e -k ownership -q
3. docker compose --profile test run --rm -e PYTHONPATH=/app backend-test python scripts/generate_types.py --check
4. docker compose logs backend --tail=200

## Risks and Notes

- Cross-layer direct writes can reintroduce drift and invalid linked-entry states.
- Transaction gaps in publish flows can leave catalog in partially visible state.
