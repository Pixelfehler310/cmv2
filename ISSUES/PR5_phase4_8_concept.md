# PR5 Phase 4-8 Concept Plan

Status: Draft
Owner: Engineering
Parent Scope: [PR5_remove_fallback_bypasses.md](PR5_remove_fallback_bypasses.md)

## Purpose

Define an implementation concept for PR5 Phase 4-8 after delegation groundwork.

Primary goals:
1. Enforce one authoritative command path in combat.
2. Remove remaining fallback branches that bypass canonical checks.
3. Keep explicit terminal outcomes for all command attempts.
4. Add auditable identity context for delegated execution.
5. Lock behavior with regression tests and verification commands.

## Current Baseline

Phases 1-3 established delegation primitives and removed payload-based impersonation as the intended direction.

Phase 4-8 in this concept assumes:
1. Command identity is server-derived.
2. Canonical action requirements remain strict.
3. Legacy fallback execution paths are not preserved for MVP unless explicitly gated.

## Phase 4: Authoritative Path Enforcement (No-Session Denial + Fallback Removal)

### Objectives
1. Deny combat command mutations when no encounter session is available.
2. Remove in-memory command mutation branches that bypass persistence and canonical invariants.
3. Replace silent exception fallbacks in action candidate build paths with explicit error/denial mapping.

### Key Changes
1. Add a single command precondition gate in transport/service flow for session-required commands.
2. Remove command-path use of in-memory turn budget fallback in mutation methods.
3. Ensure unknown/unavailable canonical action metadata remains explicit denied output.
4. Prevent catalog failures from appearing as "empty successful snapshots".

### Relevant Files
1. [backend/src/systems/dnd5e/ws_handler.py](../backend/src/systems/dnd5e/ws_handler.py)
2. [backend/src/systems/dnd5e/services/combat_service.py](../backend/src/systems/dnd5e/services/combat_service.py)
3. [backend/src/systems/dnd5e/application/action_execution_service.py](../backend/src/systems/dnd5e/application/action_execution_service.py)
4. [backend/src/systems/dnd5e/domain/action_economy.py](../backend/src/systems/dnd5e/domain/action_economy.py)
5. [backend/src/systems/dnd5e/domain/authorization.py](../backend/src/systems/dnd5e/domain/authorization.py)
6. [backend/src/systems/dnd5e/repositories/action_catalog_repository.py](../backend/src/systems/dnd5e/repositories/action_catalog_repository.py)
7. [backend/src/systems/dnd5e/reason_codes.py](../backend/src/systems/dnd5e/reason_codes.py)

## Phase 5: Delegated Audit Context in Command Logging

### Objectives
1. Preserve auditability when delegation is active.
2. Record both socket owner and effective acting identity for command attempts.
3. Keep log shape stable while extending payload/check context.

### Key Changes
1. Extend action log creation path to include delegation metadata in checks or payload.
2. Ensure denied and resolved outcomes carry identity context consistently.
3. Add minimal operational logs for delegation lifecycle actions.

### Relevant Files
1. [backend/src/systems/dnd5e/services/combat_service.py](../backend/src/systems/dnd5e/services/combat_service.py)
2. [backend/src/systems/dnd5e/lib/combat_models.py](../backend/src/systems/dnd5e/lib/combat_models.py)
3. [backend/src/systems/dnd5e/repositories/action_execution_repository.py](../backend/src/systems/dnd5e/repositories/action_execution_repository.py)
4. [backend/src/core/sessions/models.py](../backend/src/core/sessions/models.py)
5. [backend/src/core/sessions/manager.py](../backend/src/core/sessions/manager.py)

## Phase 6: Regression Test Coverage

### Objectives
1. Prove bypass paths are closed.
2. Prove delegation behavior is explicit and policy-constrained.
3. Keep denial/error contracts stable for clients.

### Required Test Themes
1. Non-DM cannot start/stop delegation.
2. DM delegation start/stop/status command flow emits explicit outcomes.
3. Delegated command authorization uses effective identity.
4. No encounter session returns explicit denied for mutation commands.
5. Unknown canonical action remains explicit denied.
6. Catalog failures do not silently produce empty success where denial is expected.

### Relevant Files
1. [backend/tests/systems/dnd5e/test_ws_integration.py](../backend/tests/systems/dnd5e/test_ws_integration.py)
2. [backend/tests/systems/dnd5e/test_combat_service.py](../backend/tests/systems/dnd5e/test_combat_service.py)
3. [backend/tests/systems/dnd5e/test_action_execution_service.py](../backend/tests/systems/dnd5e/test_action_execution_service.py)
4. [backend/tests/systems/dnd5e/test_domain_action_economy.py](../backend/tests/systems/dnd5e/test_domain_action_economy.py)
5. [backend/tests/systems/dnd5e/test_domain_authorization.py](../backend/tests/systems/dnd5e/test_domain_authorization.py)
6. [backend/tests/systems/dnd5e/test_campaign_character_loading.py](../backend/tests/systems/dnd5e/test_campaign_character_loading.py)

## Phase 7: Documentation and Scope Alignment

### Objectives
1. Document the replacement of payload impersonation with delegation mode.
2. Document denial reason behavior for session-required command paths.
3. Keep architecture docs aligned with backend truth.

### Relevant Files
1. [ISSUES/PR5_remove_fallback_bypasses.md](PR5_remove_fallback_bypasses.md)
2. [docs/backend_api_documentation.md](../docs/backend_api_documentation.md)
3. [docs/architecture](../docs/architecture)
4. [docs/diagrams/mmd/D2.9_target_corrected_architecture.mmd](../docs/diagrams/mmd/D2.9_target_corrected_architecture.mmd)

## Phase 8: Verification and Runtime Validation

### Verification Commands
1. `docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/test_ws_integration.py -q`
2. `docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/test_combat_service.py -q`
3. `docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/test_campaign_character_loading.py -q`
4. `docker compose logs backend --tail=200`

### Manual Smoke Checklist
1. DM starts delegation to connected player and executes a valid owned action.
2. DM delegated to player B attempts player A actor action and gets denied.
3. Non-DM tries delegation start and gets denied.
4. Delegation stop returns to default DM behavior.
5. Mutation command with missing encounter session returns explicit denied outcome.

## Cross-Phase Reference Matrix

### Transport and Session Boundaries
1. [backend/src/core/ws_dispatcher.py](../backend/src/core/ws_dispatcher.py)
2. [backend/src/core/ws_protocol.py](../backend/src/core/ws_protocol.py)
3. [backend/src/core/sessions/models.py](../backend/src/core/sessions/models.py)
4. [backend/src/core/sessions/manager.py](../backend/src/core/sessions/manager.py)

### DnD5e Command and Policy Layers
1. [backend/src/systems/dnd5e/ws_handler.py](../backend/src/systems/dnd5e/ws_handler.py)
2. [backend/src/systems/dnd5e/event_types.py](../backend/src/systems/dnd5e/event_types.py)
3. [backend/src/systems/dnd5e/services/combat_service.py](../backend/src/systems/dnd5e/services/combat_service.py)
4. [backend/src/systems/dnd5e/application/action_execution_service.py](../backend/src/systems/dnd5e/application/action_execution_service.py)
5. [backend/src/systems/dnd5e/application/context_service.py](../backend/src/systems/dnd5e/application/context_service.py)
6. [backend/src/systems/dnd5e/domain/action_economy.py](../backend/src/systems/dnd5e/domain/action_economy.py)
7. [backend/src/systems/dnd5e/domain/authorization.py](../backend/src/systems/dnd5e/domain/authorization.py)
8. [backend/src/systems/dnd5e/domain/action_resolution_pipeline.py](../backend/src/systems/dnd5e/domain/action_resolution_pipeline.py)
9. [backend/src/systems/dnd5e/reason_codes.py](../backend/src/systems/dnd5e/reason_codes.py)
10. [backend/src/systems/dnd5e/permissions.py](../backend/src/systems/dnd5e/permissions.py)

### Persistence and Repository Surfaces
1. [backend/src/systems/dnd5e/lib/combat_models.py](../backend/src/systems/dnd5e/lib/combat_models.py)
2. [backend/src/systems/dnd5e/repositories/action_execution_repository.py](../backend/src/systems/dnd5e/repositories/action_execution_repository.py)
3. [backend/src/systems/dnd5e/repositories/action_catalog_repository.py](../backend/src/systems/dnd5e/repositories/action_catalog_repository.py)

### Test Surfaces
1. [backend/tests/systems/dnd5e/test_ws_integration.py](../backend/tests/systems/dnd5e/test_ws_integration.py)
2. [backend/tests/systems/dnd5e/test_combat_service.py](../backend/tests/systems/dnd5e/test_combat_service.py)
3. [backend/tests/systems/dnd5e/test_action_execution_service.py](../backend/tests/systems/dnd5e/test_action_execution_service.py)
4. [backend/tests/systems/dnd5e/test_domain_action_economy.py](../backend/tests/systems/dnd5e/test_domain_action_economy.py)
5. [backend/tests/systems/dnd5e/test_domain_authorization.py](../backend/tests/systems/dnd5e/test_domain_authorization.py)
6. [backend/tests/systems/dnd5e/test_campaign_character_loading.py](../backend/tests/systems/dnd5e/test_campaign_character_loading.py)

## Risks

1. Delegation lifecycle events may require frontend event handling before full UX validation.
2. Stricter no-session denial can surface hidden assumptions in local or test harness flows.
3. Changing fallback behavior can convert previously silent paths into explicit denials or errors.

## Out of Scope

1. Non-combat domain delegation semantics.
2. Full co-DM role enablement implementation (only extension seam planned).
3. Broad infrastructure migration unrelated to combat command correctness.
