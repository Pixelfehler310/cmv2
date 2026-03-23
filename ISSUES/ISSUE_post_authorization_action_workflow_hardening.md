# ISSUE: Post-Authorization Action Workflow Hardening (Attack, AoE, Save Flow)

Status: Open  
Owner: Engineering  
Priority: High

## Problem Statement

The backend has an implemented post-authorization action pipeline, but it is not yet a fully strict, production-grade workflow for all combat action families and DM-player interaction patterns.

The current flow already performs core checks and resolution, but several behavior gaps remain against the desired contract:

1. Strict action availability enforcement is mixed with fallback candidate generation.
2. Attack/save roll authority and client-provided override semantics are not formally constrained for production.
3. AoE and save-based resolution exists, but advanced targeting semantics and explicit interaction flow (for requested player saves/reactions) are not fully specified as an authoritative contract.

## Current As-Built Coverage (What Exists)

Implemented pipeline exists and runs after approval:

- Authorization and budget checks before resolution in [backend/src/systems/dnd5e/services/combat_service.py](backend/src/systems/dnd5e/services/combat_service.py#L1670).
- Canonical action lookup and action metadata binding in [backend/src/systems/dnd5e/services/combat_service.py](backend/src/systems/dnd5e/services/combat_service.py#L657).
- Target/range/AoE eligibility and template projection in [backend/src/systems/dnd5e/services/combat_service.py](backend/src/systems/dnd5e/services/combat_service.py#L496) and [backend/src/systems/dnd5e/services/combat_service.py](backend/src/systems/dnd5e/services/combat_service.py#L1381).
- Attack roll vs AC resolution in [backend/src/systems/dnd5e/engine/action_resolver.py](backend/src/systems/dnd5e/engine/action_resolver.py#L74).
- Save-based multi-target damage resolution in [backend/src/systems/dnd5e/engine/action_resolver.py](backend/src/systems/dnd5e/engine/action_resolver.py#L199).
- Effect intent application and per-target effect events in [backend/src/systems/dnd5e/services/combat_service.py](backend/src/systems/dnd5e/services/combat_service.py#L2068).

## Gaps and Risks

### 1) Action ownership/availability strictness

Affected files:

- [backend/src/systems/dnd5e/services/combat_service.py](backend/src/systems/dnd5e/services/combat_service.py#L980)

Risk:

- Fallback/heuristic action candidate projection may allow command acceptance paths that are weaker than strict "actor must own this exact action_id" policy.

### 2) Roll authority and override policy

Affected files:

- [backend/src/systems/dnd5e/engine/action_resolver.py](backend/src/systems/dnd5e/engine/action_resolver.py#L74)
- [backend/src/systems/dnd5e/services/combat_service.py](backend/src/systems/dnd5e/services/combat_service.py#L1906)

Risk:

- Client-originating roll override fields are useful for testing, but without explicit production guardrails they can weaken server-authoritative integrity.

### 3) AoE/save interaction contract completeness

Affected files:

- [backend/src/systems/dnd5e/services/combat_service.py](backend/src/systems/dnd5e/services/combat_service.py#L542)
- [backend/src/systems/dnd5e/services/combat_service.py](backend/src/systems/dnd5e/services/combat_service.py#L1777)
- [backend/src/systems/dnd5e/engine/action_resolver.py](backend/src/systems/dnd5e/engine/action_resolver.py#L199)

Risk:

- AoE and save flows are implemented, but player-interactive sub-steps (requested saves/reactions/counters) are not represented as explicit staged contract events.

### 4) Duplicate persistence responsibility in action path

Affected files:

- [backend/src/systems/dnd5e/services/combat_service.py](backend/src/systems/dnd5e/services/combat_service.py#L1868)
- [backend/src/systems/dnd5e/ws_handler.py](backend/src/systems/dnd5e/ws_handler.py#L240)

Risk:

- State persistence occurs in both service and handler layers for action paths, increasing drift and ordering risk.

## In-Scope Fix List

1. Enforce strict "actor has action" policy via canonical bindings only for production path; gate or remove permissive fallback candidates from command execution.
2. Define and enforce roll authority policy:
   - Server rolls by default.
   - Client roll overrides disabled in production or accepted only with signed/verified provenance.
3. Formalize detailed post-authorization action contract:
   - Attack flow contract (authorize -> resolve -> publish with explicit event guarantees).
   - Save flow contract (target save resolution policy and deterministic event ordering).
   - AoE target resolution contract (origin, range, template, affected target determinism).
4. Consolidate persistence ownership for action execution to one layer (service/application), remove duplicate save trigger in handler path.
5. Add integration tests covering:
   - Unknown/unbound action_id denied deterministically.
   - Out-of-range and invalid-template AoE denials.
   - Attack roll vs AC deterministic outcomes.
   - Save-based multi-target AoE with consistent per-target results.
   - Event ordering invariants (`action_authorized` before result/effect events).

## Out of Scope

- New gameplay systems (reaction interrupts, counterspell timing engine, fully interactive save prompts).
- Generic action naming migration outside existing canonical action_id flow.
- Frontend UI redesign for combat logs/timelines.

## Verification Commands

1. `docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/test_action_resolver.py -q`
2. `docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/test_combat_service.py -q`
3. `docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/test_ws_integration.py -q`
4. `docker compose logs backend --tail=200`

## Acceptance Criteria

- Backend rejects unbound action_id with deterministic denied response.
- Attack and save flows are fully server-authoritative with explicit policy for any client-provided roll data.
- AoE targeting and application to affected targets is deterministic and test-covered.
- Single persistence authority per action command path.
- Event contract remains stable and documented in [docs/documentation/event_specification.md](docs/documentation/event_specification.md).
