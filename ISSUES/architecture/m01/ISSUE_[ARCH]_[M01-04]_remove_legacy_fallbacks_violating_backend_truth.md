# ISSUE [ARCH][M01-04]: Remove Legacy Fallbacks Violating Backend Truth

Status: Planned
Owner: Backend
Depends on: ISSUE [ARCH][M01-02]

## Why This Exists

MVP policy prefers removing obsolete compatibility paths.
Legacy fallback behavior that bypasses canonical contracts creates hidden authority leaks.

## Scope

In scope:

- Identify fallback paths that conflict with canonical service/event contracts.
- Remove or replace them with explicit denied/error responses.
- Add migration notes for intentional breaking behavior.

Out of scope:

- Generic backward compatibility layer.

## Interface Focus

- Contract enforcement interface: invalid flows must fail explicitly.
- Migration interface: communicated behavior changes and client expectations.

## Acceptance Criteria

1. Contract-violating fallback paths are removed.
2. Rejections use explicit denied/error reason codes.
3. Tests cover previously implicit fallback scenarios.

## Suggested Verification

1. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e -q
2. docker compose --profile test run --rm -e PYTHONPATH=/app backend-test python scripts/generate_types.py --check
