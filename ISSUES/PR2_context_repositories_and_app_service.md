# PR2: Context Repositories and Application Extraction

Status: Planned
Owner: Engineering
Depends on: PR1

## Goal

Extract combat context load (campaign -> scene -> encounter) from mixed service internals into repository-backed application orchestration.

## Scope

In scope:

- Introduce context repositories for catalog/session access.
- Move context orchestration into application layer APIs.
- Keep router/handler behavior and response payloads unchanged.

Out of scope:

- Context-change realtime WS push.
- Action resolution logic changes.

## Proposed Files

Create:

- backend/src/systems/dnd5e/repositories/context_repository.py
- backend/src/systems/dnd5e/repositories/encounter_session_repository.py

Update:

- backend/src/systems/dnd5e/application/context_service.py
- backend/src/systems/dnd5e/services/combat_service.py
- backend/src/campaigns/routers/campaigns.py
- backend/src/systems/dnd5e/ws_handler.py (only if needed for context load call site)

## Tasks

1. Define repository interfaces and DB implementations for context reads/writes.
2. Move context catalog and encounter selection data access out of service orchestration methods.
3. Keep transport thin: routers/WS handlers call application methods only.
4. Preserve existing error mapping (404/403 behavior).
5. Add service-level tests with mocked repositories.
6. Keep existing integration tests green.

## Definition of Done

1. No direct SQL operations from transport files in this slice.
2. Context operations pass through application + repositories.
3. Existing context endpoint behavior remains unchanged.
4. Added tests cover application orchestration success and failure paths.

## Verification

1. docker compose --profile test run --rm backend-test pytest tests/campaigns/test_campaigns_router.py -q
2. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/test_ws_integration.py -q
3. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/test_combat_service.py -q
4. docker compose logs backend --tail=200

## Risks

- Hidden side effects in catalog bootstrap methods.
- Behavior drift if campaign context version increments are moved incorrectly.

## Rollback

- Keep old service methods behind temporary wrapper until tests are green.
- Revert only repository wiring if orchestration drift appears.
