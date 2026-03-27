# ISSUE [VERT][V05-07]: Test Matrix and Completion Gate

Status: Planned
Owner: Data + Content Systems
Parent: ISSUE [VERT][V05]
Depends on:

- ISSUE [VERT][V05-06]

## Why This Exists

V05 is complete only when contract-stable content behavior is proven by deterministic tests and drift checks.
This issue defines and enforces the V05 closure gate aligned to V00 Definition of Done.

## Scope

In scope:

- Define and finalize the V05 test matrix:
  - contract tests
  - ownership and invariant tests
  - CRUD integration tests
  - search and linked-entry resolution tests
  - transport parity tests
- Define and execute drift checks for generated contract artifacts.
- Define final closure checklist and pass criteria.
- Produce closure summary and handoff notes for V06.

Out of scope:

- New feature scope beyond approved V05 contracts.
- Broad refactors not required for gate pass.

## Deliverables

1. V05 test matrix mapping requirements to concrete test suites.
2. Completion gate checklist aligned to V00 DoD.
3. Evidence log for test, drift, and backend log checks.
4. V05 closure report with residual risks and follow-up issue list.

## Acceptance Criteria

1. Contract tests are deterministic and green.
2. Ownership and invariant tests are deterministic and green.
3. CRUD, search, and linked-entry integration tests are deterministic and green.
4. REST/WS parity checks pass where WS content streams are enabled.
5. Contract drift checks pass with no unreviewed deltas.
6. V05 closure packet supports clean activation handoff to V06.

## Verification Commands

1. docker compose --profile test run --rm backend-test pytest tests/data -q
2. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e -k compendium -q
3. docker compose --profile test run --rm -e PYTHONPATH=/app backend-test python scripts/generate_types.py --check
4. docker compose logs backend --tail=200

## Risks and Notes

- Flaky linked-entry tests or ordering instability must block V05 closure.
- Unreviewed contract drift must block closure and be resolved or explicitly versioned.
