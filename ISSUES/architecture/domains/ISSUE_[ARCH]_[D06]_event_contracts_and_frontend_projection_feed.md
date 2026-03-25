# ISSUE [ARCH][D06]: Event Contracts and Frontend Projection Feed

Status: Planned
Owner: Backend + Frontend Contracts
Depends on: ISSUE [ARCH][D00]

## Why This Exists

Frontend should project backend truth from deterministic event contracts.
This stream isolates event payload shape, ordering guarantees, and adapter expectations.

## Scope

In scope:

- Action/move/preview event payload contracts.
- Event ordering and correlation requirements.
- Projection-read-model expectations for frontend stores/adapters.

Out of scope:

- UI rendering design.

## Related D2.9 Namespaces

- CombatEvents
- ApplicationLayer (ActionExecutionApplicationService outbound events)
- M05 frontend projection boundaries

## Acceptance Criteria

1. Event payloads and ordering guarantees are explicit.
2. Frontend projection contracts are stable and typed.
3. Integration tests cover core event flow determinism.
