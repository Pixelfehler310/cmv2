# ISSUE [ARCH][M01-05]: M01 Contract Guardrails and Regression Suite

Status: Planned
Owner: Engineering
Depends on: ISSUE [ARCH][M01-03], ISSUE [ARCH][M01-04]

## Why This Exists

M01 is complete only when regressions are prevented.
This issue codifies tests and checks that enforce backend truth and contract stability.

## Scope

In scope:

- Add boundary-focused integration tests for M01 contracts.
- Add contributor checklist items for M01-impacting changes.
- Ensure contract drift checks are included in M01 workflow.

Out of scope:

- Broad CI redesign.

## Interface Focus

- Test interface: assertions at contract/boundary level.
- Workflow interface: mandatory verification commands and artifact checks.

## Acceptance Criteria

1. M01 critical paths have deterministic automated coverage.
2. Contract drift checks are included in M01 completion criteria.
3. Contributor guardrails for M01 are documented.

## Suggested Verification

1. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/test_ws_integration.py -q
2. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/test_combat_service.py -q
3. docker compose --profile test run --rm -e PYTHONPATH=/app backend-test python scripts/generate_types.py --check
