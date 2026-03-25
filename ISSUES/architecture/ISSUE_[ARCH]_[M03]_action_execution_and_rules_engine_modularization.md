# ISSUE [ARCH][M03]: Action Execution and Rules Engine Modularization

Status: Planned
Owner: Systems DnD5e
Depends on: ISSUE [ARCH][M00]

## Why This Exists

Action execution paths are central to gameplay and will keep evolving.
Without strict module seams, future effect processing and modding become risky.

## Scope

In scope:

- Define clear separation between action orchestration, rule resolution, and side effects.
- Formalize extension points for future effect processor integration.
- Ensure deterministic result contracts for action outcomes.

Out of scope:

- Full generic action-id migration unless explicitly scheduled.

## Interface Focus

- Action execution request/result contracts.
- Rule engine strategy interface for swappable logic.
- Effect pipeline interface placeholder for future processor.

## Acceptance Criteria

1. Execution flow responsibilities are explicit per layer.
2. Extension interface exists for effect processing.
3. Tests assert deterministic outcomes and reason codes.
