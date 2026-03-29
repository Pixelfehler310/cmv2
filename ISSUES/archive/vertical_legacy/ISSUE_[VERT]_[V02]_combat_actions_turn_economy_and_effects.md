# ISSUE [VERT][V02]: Combat Actions, Turn Economy, and Effects

Status: Planned
Owner: Systems DnD5e
Depends on: ISSUE [VERT][V01]

## Why This Exists

Combat correctness is the highest-risk business logic area.
This module isolates action execution, budget spending, and effect lifecycle semantics into one vertically testable stream.

## Scope

In scope:

- Action execution request and outcome contracts.
- Turn economy and deny semantics.
- Effect apply, tick, concentration, and removal behavior.

Out of scope:

- Compendium CRUD breadth.

## D2.9 Alignment

- RuntimeHierarchy (TurnBudget, EffectInstanceRuntime)
- CombatEvents
- ApplicationLayer (ActionExecutionApplicationService)
- DomainPolicies

## High-Level Acceptance Criteria

1. Combat outcomes are deterministic under integration tests.
2. Denied reason taxonomy is stable and machine-readable.
3. Effect lifecycle behavior matches declared policy boundaries.

## Decomposition Policy

Create child issues only when V02 becomes active.
