# ISSUE [VERT][V01-03]: Ownership and Repository Boundary Lock

Status: Planned
Owner: Systems DnD5e
Parent: ISSUE [VERT][V01]
Depends on:

- ISSUE [VERT][V01-01]
- ISSUE [VERT][V01-02]

## Why This Exists

V01 must enforce single-writer lifecycle ownership.
This issue maps runtime hierarchy fields to one write authority each and locks repository boundaries to prevent multi-writer drift.

## Scope

In scope:

- Map field-level write authority for campaign runtime, scene runtime, and scene combat state.
- Define allowed write paths by repository and application service.
- Identify and remove or flag ambiguous lifecycle write paths.
- Define ownership invariants and their persistence implications.

Out of scope:

- Full domain implementation of transition orchestration.
- Frontend projection behavior.

## Deliverables

1. Ownership matrix:
   - state field
   - allowed writer
   - repository boundary
2. Repository boundary contract for campaign and scene lifecycle writes.
3. Invariant checklist for ownership constraints.
4. List of ambiguous paths removed or explicitly deferred.

## Acceptance Criteria

1. No unresolved multi-writer path remains for V01 lifecycle state.
2. Campaign, scene, and combat-state write authority is explicit and testable.
3. Persistence boundaries match the ownership matrix.
4. Ownership invariants are represented in dedicated invariant tests.

## Verification Commands

1. docker compose --profile test run --rm backend-test pytest tests/campaigns -q
2. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/test_ws_integration.py -q
3. docker compose --profile test run --rm -e PYTHONPATH=/app backend-test python scripts/generate_types.py --check

## Risks and Notes

- Existing helper utilities may hide implicit writes; audit all mutation entry points.
- Any unresolved ownership ambiguity blocks V01 completion gate.
