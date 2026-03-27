# ISSUE [VERT][V05-02]: Definition Contract and Validation Freeze

Status: Planned
Owner: Data + Content Systems
Parent: ISSUE [VERT][V05]
Depends on:

- ISSUE [VERT][V05-01]

## Why This Exists

CRUD consistency is impossible without a frozen contract layer.
This issue locks canonical definition payloads, lifecycle fields, linked-entry rules, and validation semantics before orchestration changes.

## Scope

In scope:

- Define canonical contract fields per definition family.
- Freeze shared lifecycle metadata fields:
  - lifecycle_state
  - content_version
  - replaced_by_ref
  - provenance metadata
- Freeze linked-entry reference semantics:
  - reference key format
  - target-family constraints
  - cycle-denial behavior
  - missing-reference denial behavior
- Freeze machine-readable denied/error reason taxonomy for definition CRUD.

Out of scope:

- Repository ownership restructuring.
- UI rendering implementation details.

## Deliverables

1. Contract delta specification for all scoped definition families.
2. Validation rule matrix by operation type:
   - create
   - update
   - delete
   - publish
   - archive
3. Reason-code taxonomy document for contract and validation denials.
4. Compatibility policy for intentional breaking changes.

## Acceptance Criteria

1. All scoped definition families have canonical field contracts.
2. Linked-entry constraints are explicit and testable.
3. Validation denials map to stable, machine-readable reason codes.
4. Contract decisions are sufficient to implement V05-03 and V05-04 without contract churn.

## Verification Commands

1. docker compose --profile test run --rm backend-test pytest tests/data -k validation -q
2. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e -k contract -q
3. docker compose --profile test run --rm -e PYTHONPATH=/app backend-test python scripts/generate_types.py --check
4. docker compose logs backend --tail=200

## Risks and Notes

- Late contract edits after V05-04 start can create endpoint and projection drift.
- Denial taxonomy instability will block V05-05 parity work.
