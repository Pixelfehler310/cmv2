# ISSUE [VERT][V06]: Event Contracts and Frontend Projection

Status: Planned
Owner: Backend + Frontend Contracts
Depends on: ISSUE [VERT][V01], ISSUE [VERT][V02]

## Why This Exists

Frontend must project backend truth from deterministic event contracts.
This module stabilizes payload shape, ordering guarantees, and projection expectations for end-to-end reliability.

## Scope

In scope:

- Event payload contracts for core command flows.
- Ordering and correlation requirements.
- Projection-read-model expectations for frontend adapters and stores.

Out of scope:

- Visual component design.

## D2.9 Alignment

- CombatEvents
- ApplicationLayer outbound event responsibilities
- Frontend projection consumption boundary

## High-Level Acceptance Criteria

1. Event payload and ordering contracts are explicit.
2. Projection interfaces are stable and typed.
3. Integration tests verify critical event determinism.

## Decomposition Policy

Create child issues only when V06 becomes active.
