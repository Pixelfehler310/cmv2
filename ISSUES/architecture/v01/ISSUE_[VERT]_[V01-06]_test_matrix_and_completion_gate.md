# ISSUE [VERT][V01-06]: Test Matrix and Completion Gate

Status: Planned
Owner: Systems DnD5e
Parent: ISSUE [VERT][V01]
Depends on:

- ISSUE [VERT][V01-05]

## Why This Exists

V01 is complete only when deterministic behavior is proven by repeatable tests and drift checks.
This issue defines and enforces the V01 completion gate aligned to V00 Definition of Done.

## Scope

In scope:

- Define and finalize the V01 test matrix:
  - contract tests
  - invariant tests
  - integration tests
- Define and execute drift checks for contracts and generated artifacts.
- Define final gate checklist and pass criteria.
- Produce closure summary and handoff notes for V02 and V03.

Out of scope:

- New feature development beyond V01 scope.
- Broad refactors not required for V01 gate pass.

## Deliverables

1. V01 test matrix mapping requirements to concrete tests.
2. Completion gate checklist aligned to V00 DoD dimensions.
3. Evidence log of test and drift command results.
4. V01 closure report with residual risk and follow-up issue list.

## Acceptance Criteria

1. Contract tests are deterministic and green.
2. Ownership and invariant tests are deterministic and green.
3. WS and REST integration lifecycle flow tests are deterministic and green.
4. Contract drift checks pass with no unreviewed deltas.
5. V01 closure packet is complete and supports activation of V02.

## Verification Commands

1. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/test_ws_integration.py -q
2. docker compose --profile test run --rm backend-test pytest tests/campaigns -q
3. docker compose --profile test run --rm -e PYTHONPATH=/app backend-test python scripts/generate_types.py --check
4. docker compose logs backend --tail=200

## Risks and Notes

- Non-deterministic tests or undocumented drift must block V01 closure.
- Follow-up issues should be narrow and only for explicitly deferred scope.
