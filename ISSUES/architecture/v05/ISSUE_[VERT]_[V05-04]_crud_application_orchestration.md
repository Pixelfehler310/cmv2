# ISSUE [VERT][V05-04]: CRUD Application Orchestration

Status: Planned
Owner: Data + Content Systems
Parent: ISSUE [VERT][V05]
Depends on:

- ISSUE [VERT][V05-03]

## Why This Exists

After contract and ownership freeze, orchestration must be centralized.
This issue routes all V05 CRUD and lifecycle operations through one deterministic application path.

## Scope

In scope:

- Implement canonical service orchestration for definition CRUD.
- Implement lifecycle-aware operations:
  - publish
  - archive
  - supersede with replacement link
  - restore where allowed
- Enforce validation and denial semantics in service flow.
- Emit deterministic operation results for transport mappers.

Out of scope:

- Transport-level parity and streaming updates.
- Search-index ranking heuristics.

## Deliverables

1. Orchestration flow spec: validate -> authorize -> resolve links -> persist -> emit result.
2. Service behavior matrix by entity family and operation type.
3. Deterministic result envelope contract for resolved/denied/error outcomes.
4. Migration/removal notes for obsolete orchestration paths.

## Acceptance Criteria

1. One canonical application path handles V05 operations.
2. Lifecycle transitions enforce V05-02 invariants.
3. Result envelopes are stable and machine-readable.
4. Existing fallback or duplicate orchestration paths are removed or explicitly blocked.

## Verification Commands

1. docker compose --profile test run --rm backend-test pytest tests/data -k crud -q
2. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e -k compendium -q
3. docker compose --profile test run --rm -e PYTHONPATH=/app backend-test python scripts/generate_types.py --check
4. docker compose logs backend --tail=200

## Risks and Notes

- Partial migration leaves non-deterministic behavior across entity families.
- Service/mapper mismatch can break content-manager detail views and linked-entry navigation.
