# ISSUE: Legacy Static Analysis Cleanup in Combat Service

Status: Planned
Owner: Engineering
Related: Completed combat-slice refactor (PR1-PR5)

## Goal

Remove pre-existing static-analysis/type-check debt in the combat service slice that was not part of PR3 architectural extraction, while preserving runtime behavior and contract stability.

## Why This Exists

During PR3 implementation and verification, integration/runtime tests passed, but multiple static-analysis warnings remained in older service code paths. These are legacy quality gaps and should be cleaned up in a dedicated hardening issue.

## Affected Areas

Primary file:

- backend/src/systems/dnd5e/services/combat_service.py

Known warning clusters:

1. SQLAlchemy rowcount typing mismatch around reset encounter state.
2. Potentially unbound local variables in movement budget flow.
3. SQLAlchemy expression typing in monster lookup predicate appends.
4. Canonical effect definition strict typing conversion warnings.

Representative references:

- backend/src/systems/dnd5e/services/combat_service.py:252
- backend/src/systems/dnd5e/services/combat_service.py:341
- backend/src/systems/dnd5e/services/combat_service.py:349
- backend/src/systems/dnd5e/services/combat_service.py:361
- backend/src/systems/dnd5e/services/combat_service.py:960
- backend/src/systems/dnd5e/services/combat_service.py:962
- backend/src/systems/dnd5e/services/combat_service.py:2221

## Scope

In scope:

- Eliminate current static-analysis warnings listed above.
- Keep behavior and event contracts unchanged.
- Add focused tests only where control-flow/type fixes could alter behavior.

Out of scope:

- New features or schema changes.
- Broad refactors unrelated to warning resolution.

## Tasks

1. Fix Result rowcount handling in reset flow with a type-safe branch.
2. Refactor movement budget logic to remove possibly-unbound local paths.
3. Normalize SQLAlchemy predicate typing in monster lookup.
4. Add explicit conversion/validation for canonical effect definition typed fields.
5. Run backend targeted suites plus static checks and confirm no regressions.

## Definition of Done

1. Existing static-analysis warnings in this issue are cleared.
2. Existing runtime tests remain green.
3. No behavior drift in WS action/turn flows.

## Verification

1. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/test_ws_integration.py -q
2. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/test_combat_service.py -q
3. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/test_action_resolver.py -q
4. Run workspace static-analysis diagnostics and confirm warning removal for listed references.
5. docker compose logs backend --tail=200

## Risk

- Cleanup in control-flow-heavy areas (movement and effect conversion) could introduce subtle behavioral drift if not covered with focused assertions.

## Rollback

- Revert warning-specific commits independently if any runtime behavior changes.
