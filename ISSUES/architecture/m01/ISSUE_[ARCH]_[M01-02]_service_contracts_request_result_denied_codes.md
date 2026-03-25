# ISSUE [ARCH][M01-02]: Service Contracts for Request, Result, and Denied Codes

Status: Planned
Owner: Backend
Depends on: ISSUE [ARCH][M01-01]

## Why This Exists

Without explicit service contracts, transport and frontend depend on accidental behavior.
This issue standardizes request and result DTOs plus denied/error reason contracts.

## Scope

In scope:

- Define service request DTOs for core combat commands.
- Define deterministic result DTOs for success and denied states.
- Define machine-readable denied/error reason code set.

Out of scope:

- WebSocket envelope formatting.

## Interface Focus

- Request interface: required and optional fields per command.
- Result interface: deterministic output shape and semantics.
- Denied/error interface: reason code taxonomy and payload fields.

## Acceptance Criteria

1. DTO contracts are explicit in backend schemas/types.
2. Denied/error reason set is finite and documented.
3. Tests assert contract behavior, not implementation internals.

## Suggested Verification

1. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/test_combat_service.py -q
2. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/test_action_resolver.py -q
