# ISSUE [ARCH][M01-01]: Aggregate State Ownership Matrix

Status: Planned
Owner: Backend
Depends on: ISSUE [ARCH][M01]

## Why This Exists

Backend truth fails when ownership of mutable state is ambiguous.
A canonical ownership matrix is needed before contract refinement so every state field has one authority.

In practical terms, this matrix answers these questions for every aggregate:

1. Which layer/service is allowed to write it?
2. Which layers may only read it?
3. Which layer is responsible for broadcasting state changes?

Why this is necessary now:

1. Today, ownership is spread across code paths (router, ws handler, service, repository), so authority is implicit instead of explicit.
2. Implicit authority makes regressions likely: two places can mutate related state with different invariants.
3. Contract work (M01-02 and M01-03) is hard to stabilize if the true writer is unclear.
4. Future modularization (M02 to M04) depends on clean boundaries; without ownership clarity, interfaces become vague and leaky.

What problem it prevents:

1. Duplicate writes and race-like behavior between transport/service/persistence paths.
2. Silent drift where emitted events do not match persisted truth.
3. Frontend assumptions accidentally becoming de-facto authority when backend ownership is not explicit.

## Scope

In scope:

- Define ownership per aggregate: campaign, encounter/session, combat snapshot, context, action execution.
- Mark write authority, read authority, and broadcast authority.
- Identify and mark current violations.

Out of scope:

- Refactoring implementations.

## Interface Focus

- Ownership interface: who may mutate each aggregate and through which service boundary.
- Invariant interface: required constraints before and after state transitions.

## Acceptance Criteria

1. Ownership matrix exists and is checked into docs.
2. Every mutable aggregate has exactly one write authority.
3. Known violations are listed with follow-up issue references.

## Suggested Verification

1. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/test_ws_integration.py -q
2. docker compose logs backend --tail=200
