# ISSUE [ARCH][D02]: Combat Actions, Turn Economy, and Effects

Status: Planned
Owner: Systems DnD5e
Depends on: ISSUE [ARCH][D00]

## Why This Exists

Combat correctness is the highest-risk core business logic area.
This stream isolates action execution, budget spending, and effect lifecycle behavior.

## Scope

In scope:

- Action request handling and target resolution.
- Turn budget policies and spend/deny logic.
- Effect application, ticking, concentration, and removal triggers.

Out of scope:

- Compendium CRUD details.

## Related D2.9 Namespaces

- RuntimeHierarchy (TurnBudget, EffectInstanceRuntime)
- CombatEvents
- ApplicationLayer (ActionExecutionApplicationService)
- DomainPolicies

## Acceptance Criteria

1. Combat outcomes are deterministic under contract tests.
2. Denied reason taxonomy is stable and machine-readable.
3. Effect lifecycle behavior aligns with declared policy boundaries.
