# PR5: Remove Fallback Bypasses in Combat Slice

Status: In Progress
Owner: Engineering
Depends on: PR4

## Goal

Remove remaining in-memory bypass paths in combat context load and action resolve where they violate authoritative invariants, while replacing payload-based impersonation with explicit delegation mode.

## Scope

In scope:

- Remove bypass logic that skips authorization, turn ownership, or action economy checks.
- Replace `acting_as_user_id` payload impersonation behavior with server-side delegation lifecycle commands.
- Enforce one authoritative execution path per command in this slice.
- Keep explicit denied/error outcomes for non-authorized or invalid requests.

Out of scope:

- Expanding to non-combat domains.
- Broad infrastructure changes.

## Proposed Files

Update likely:

- backend/src/systems/dnd5e/ws_handler.py
- backend/src/systems/dnd5e/services/combat_service.py
- backend/src/systems/dnd5e/application/context_service.py
- backend/src/systems/dnd5e/application/action_execution_service.py

Tests likely:

- backend/tests/systems/dnd5e/test_ws_integration.py
- backend/tests/systems/dnd5e/test_combat_service.py

## Tasks

1. Identify and remove in-memory fallback branches that bypass canonical checks.
2. Ensure all command paths produce explicit terminal outcomes (success, denied, error).
3. Remove dead compatibility code that conflicts with MVP target architecture.
4. Add regression tests for previous bypass scenarios.
5. Add regression tests for delegation lifecycle and delegated authorization behavior.

## Definition of Done

1. No production command path in this slice bypasses canonical checks.
2. Turn, ownership, and budget enforcement is uniform.
3. Legacy fallback branches removed or explicitly gated for non-production use.
4. Regression tests prove bypass scenarios are closed.
5. Delegated execution is auditable (`authenticated_user_id` + `effective_user_id`) and policy-constrained.

## Verification

1. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/test_ws_integration.py -q
2. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/test_combat_service.py -q
3. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/test_campaign_character_loading.py -q
4. docker compose logs backend --tail=200

## Risks

- Unexpected coupling with local/test harness workflows.
- Short-term friction if hidden callers relied on fallback behavior.

## Rollback

- Reintroduce minimal guarded compatibility only if hard blocker is discovered, with explicit deprecation marker.
