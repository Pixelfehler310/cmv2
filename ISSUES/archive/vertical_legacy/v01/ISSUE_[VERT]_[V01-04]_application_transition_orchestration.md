# ISSUE [VERT][V01-04]: Application Transition Orchestration

Status: Planned
Owner: Systems DnD5e
Parent: ISSUE [VERT][V01]
Depends on:

- ISSUE [VERT][V01-02]
- ISSUE [VERT][V01-03]

## Why This Exists

V01 behavior must be orchestrated in a single application-layer flow with policy validation and deterministic outcomes.
This issue implements and stabilizes transition orchestration for scene selection and scene combat lifecycle commands.

## Scope

In scope:

- Implement/select canonical application service path for:
  - select_scene
  - start_combat
  - end_combat
- Apply authorization and transition policy checks consistently.
- Return deterministic result shape and reason codes.
- Enforce transaction boundaries for lifecycle state changes.

Out of scope:

- WS/REST interface convergence details.
- Frontend-specific projection behavior.

## Deliverables

1. Application service orchestration for V01 lifecycle commands.
2. Deterministic denied/error behavior through stable reason codes.
3. Unit and contract-level tests for core orchestration scenarios.
4. Transition traceability in backend logs for key lifecycle commands.

## Acceptance Criteria

1. Application service behavior matches V01-02 contract freeze.
2. Transition validation remains in policy layer rather than transport.
3. Persistence writes occur only through ownership-approved paths.
4. Core command scenarios pass deterministic tests.

## Verification Commands

1. docker compose --profile test run --rm backend-test pytest tests/campaigns -q
2. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/test_ws_integration.py -q
3. docker compose logs backend --tail=200

## Risks and Notes

- Avoid coupling orchestration to transport payload details.
- MVP policy requires removing obsolete fallback behavior rather than extending it.
