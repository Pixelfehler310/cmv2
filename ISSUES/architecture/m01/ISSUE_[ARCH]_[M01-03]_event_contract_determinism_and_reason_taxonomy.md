# ISSUE [ARCH][M01-03]: Event Contract Determinism and Reason Taxonomy

Status: Planned
Owner: Backend + Transport Contract
Depends on: ISSUE [ARCH][M01-02]

## Why This Exists

Frontend projection depends on deterministic events.
If event ordering or reason semantics drift, state projection becomes fragile and backend truth is undermined.

## Scope

In scope:

- Define deterministic event sequence per critical command flow.
- Define event payload contract and correlation fields.
- Align denied/error reason taxonomy between service and events.

Out of scope:

- Frontend rendering behavior.

## Interface Focus

- Event interface: payload shape, required fields, and ordering guarantees.
- Correlation interface: request_id and traceability semantics.

## Acceptance Criteria

1. Critical command flows have documented deterministic event order.
2. Event payload contracts are explicit and consistent.
3. Integration tests verify order and reason code mapping.

## Suggested Verification

1. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/test_ws_integration.py -q
2. docker compose logs backend --tail=200
