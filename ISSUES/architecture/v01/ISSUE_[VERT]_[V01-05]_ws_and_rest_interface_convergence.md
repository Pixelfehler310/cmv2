# ISSUE [VERT][V01-05]: WS and REST Interface Convergence

Status: Planned
Owner: Systems DnD5e
Parent: ISSUE [VERT][V01]
Depends on:

- ISSUE [VERT][V01-04]

## Why This Exists

V01 must expose consistent external behavior independent of transport.
This issue aligns WS handlers and REST routes to one application contract and one deterministic event/response model.

## Scope

In scope:

- Align WS and REST command handling semantics for V01 lifecycle commands.
- Ensure request_id correlation is preserved end to end.
- Ensure event mapper output matches frozen contract payloads.
- Ensure denied/error outcomes are transport-consistent.

Out of scope:

- New command surfaces outside V01 command set.
- Frontend state management implementation.

## Deliverables

1. WS and REST command mapping table to shared application service operations.
2. Event mapper alignment for:
   - scene_selected
   - combat_started
   - combat_ended
   - command_denied
3. Correlation and observability notes for request_id behavior.
4. Transport integration tests proving parity.

## Acceptance Criteria

1. WS and REST flows produce semantically equivalent outcomes.
2. request_id correlation is deterministic for success and denied paths.
3. Event payload shape is stable and contract-compliant.
4. No transport-specific lifecycle authority creep remains.

## Verification Commands

1. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/test_ws_integration.py -q
2. docker compose --profile test run --rm backend-test pytest tests/campaigns -q
3. docker compose logs backend --tail=200

## Risks and Notes

- Legacy WS message styles can mask divergence; contract tests must target canonical format.
- If parity cannot be achieved in one pass, capture exact gap and block V01 completion gate.
