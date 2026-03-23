# PR3: Action Execution Application Service and Repositories

Status: Planned
Owner: Engineering
Depends on: PR2

## Goal

Split action execution orchestration into a dedicated application service backed by repositories, while preserving current action contract behavior.

## Scope

In scope:

- Introduce action execution application orchestration.
- Move persistence concerns (budgets, logs, effects, encounter state writes) behind repositories.
- Keep current canonical lookup flow: action_name -> bound action_id.

Out of scope:

- Generic action-id migration.
- New action families.

## Proposed Files

Create:

- backend/src/systems/dnd5e/application/action_execution_service.py
- backend/src/systems/dnd5e/repositories/action_catalog_repository.py
- backend/src/systems/dnd5e/repositories/action_execution_repository.py

Update:

- backend/src/systems/dnd5e/services/combat_service.py
- backend/src/systems/dnd5e/ws_handler.py
- backend/src/systems/dnd5e/services/validation.py (only if needed for DTO boundaries)

## Tasks

1. Define DTO boundary for action execution request/response in application layer.
2. Move DB reads and writes for execution path into repositories.
3. Keep authorization/resolve sequence deterministic: authorize -> resolve -> persist -> emit.
4. Preserve request_id correlation and denied/error response semantics.
5. Add tests for application service orchestration with repository mocks.
6. Keep existing WS integration tests passing.

## Definition of Done

1. Action execution DB operations are repository-owned.
2. WS handler no longer orchestrates detailed execution steps.
3. Existing action denied/result event contract remains stable.
4. Added tests cover success, denied, and invalid action cases.

## Verification

1. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/test_ws_integration.py -q
2. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/test_combat_service.py -q
3. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/test_action_resolver.py -q
4. docker compose logs backend --tail=200

## Risks

- Event ordering drift during refactor of orchestration.
- Incomplete transfer of persistence side effects (effects/logs/budgets).

## Rollback

- Keep compatibility wrapper from old service call into new application API until stabilized.
