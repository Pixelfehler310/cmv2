# WS Event Command Deck Next Stages

This document defines the next implementation stages after the current baseline where `request_move_preview` and `movement_preview` are available.

Primary references:

- [docs/architecture/backend/14_ws_event_refactor_backend_phase_plan.md](docs/architecture/backend/14_ws_event_refactor_backend_phase_plan.md)
- [docs/architecture/backend/15_ws_event_refactor_acceptance_matrix.md](docs/architecture/backend/15_ws_event_refactor_acceptance_matrix.md)
- [docs/architecture/backend/16_ws_event_frontend_contract_handover.md](docs/architecture/backend/16_ws_event_frontend_contract_handover.md)

## 1. Scope and Outcomes

Target outcomes for this sequence:

- Player command deck renders backend-provided executable actions.
- Movement highlight flow is integrated end-to-end (drag start preview -> move commit -> budget update).
- Attack highlighting ships in two steps:
  - single-target (melee/ranged) first,
  - AoE templates second.
- All new commands remain deterministic (success/denied/error), request-correlated, and compatible with `ws-combat-v2` principles.

## 2. Current Baseline (Already Implemented)

Completed in code:

- Inbound command: `request_move_preview`
- Outbound event: `movement_preview`
- Permission scope: DM or owner
- Budget- and turn-gated movement preview computation in backend service
- Frontend shared contracts/store support for movement preview state

Current limitation:

- Player map surface is still placeholder-level and not yet consuming preview overlays.

## 3. Stage Sequence

## Stage A - Executable Action Snapshot Contract

Goal:

- Introduce backend-provided action list for command deck rendering.

Tasks:

1. Add outbound payload `executable_actions_snapshot` containing:
   - `actor_id`
   - `actions[]` with `action_id`, `label`, `family`, `action_type_cost`, `is_available`, `unavailable_reason`, `targeting_mode`, `range`
   - optional `turn_budget` snapshot
2. Add a command-like request event `request_executable_actions` (or publish on sync/turn changes).
3. Source action candidates from actor/runtime definitions (not frontend hardcoding).
4. Normalize deny/unavailable reason vocabulary to current canonical reason codes.

Definition of done:

- Player command deck can render from backend snapshots only.
- No local frontend rule computation required for availability.

## Stage B - Player Movement Highlight Integration

Goal:

- Wire movement preview contract to real player interactions.

Tasks:

1. Implement/upgrade player map interaction component to support drag lifecycle.
2. On drag start:
   - send `request_move_preview` for active actor,
   - render `movement_preview.reachable` cells.
3. On move commit:
   - send `move_token` with path,
   - clear overlay after terminal response.
4. On turn change / sync / denied response:
   - clear stale overlays.

Definition of done:

- Drag start consistently shows reachable cells.
- Move commit decreases movement budget and updates highlighted potential on next drag.

## Stage C - Single-Target Attack Preview and Validation

Goal:

- Ship first attack highlighting path with strict backend validation parity.

Tasks:

1. Add request command: `request_attack_preview`.
2. Add outbound event: `attack_preview` with:
   - `actor_id`, `action_id`, `origin`
   - `eligible_target_ids`
   - optional `eligible_cells`
3. Enforce execution-time eligibility parity in action handlers:
   - if selected target is not in eligible set, return deterministic denied response.
4. Ensure compatibility with existing `action` / `request_action` flows.

Definition of done:

- Selecting an attack highlights legal targets.
- Invalid target attempts are denied deterministically with request correlation.

## Stage D - AoE Template Expansion

Goal:

- Expand highlighting and validation to template-based actions.

Tasks:

1. Add backend AoE geometry helpers for:
   - `line`, `cone`, `sphere`, `cube`, `cylinder`
2. Extend `attack_preview` payload with template projection data:
   - `shape`, `size`, `origin`, `direction` (when needed), `affected_cells`
3. Enforce template intersection checks at resolve time.
4. Keep event naming stable; no alias layer unless explicitly approved.

Definition of done:

- AoE actions can preview and validate affected areas using backend-authoritative geometry.

## Stage E - Contract and Migration Hardening

Goal:

- Finalize stability and rollout safety.

Tasks:

1. Update backend event docs and frontend type package together.
2. Add version/changelog entries for all new events.
3. Extend acceptance matrix rows for:
   - executable action snapshots,
   - movement preview lifecycle,
   - attack preview lifecycle,
   - AoE template validation.
4. Ensure no silent command paths are introduced.

Definition of done:

- Contract docs, backend handlers, and frontend types are synchronized.
- Acceptance checks are green for implemented scope.

## 4. Event Contract Additions (Planned)

Planned inbound additions:

- `request_executable_actions`
- `request_attack_preview`

Planned outbound additions:

- `executable_actions_snapshot`
- `attack_preview`

Already added in current baseline:

- `request_move_preview` (inbound)
- `movement_preview` (outbound)

## 5. Suggested Delivery PRs

1. PR-1: Executable action snapshot contracts + backend projection + frontend types.
2. PR-2: Player map interaction integration for movement preview.
3. PR-3: Single-target attack preview contracts + eligibility validation.
4. PR-4: AoE template geometry + preview + resolver validation.
5. PR-5: Docs/changelog/acceptance matrix completion.

## 6. Verification Plan

Per stage run:

1. Backend unit/integration tests for command determinism and reason codes.
2. Frontend package build checks for `@rpg/types` and `@rpg/shared`.
3. End-to-end smoke using Docker logs with request_id correlation:
   - inbound request,
   - outbound terminal event,
   - expected state mutation.

Mandatory checks:

- No command exits without terminal outbound response.
- Turn/budget authorization behavior is identical in in-memory and DB-backed modes.
- Frontend only renders backend-provided action availability/highlight state.

## 7. Risks and Mitigations

- Risk: preview payload size grows too large on bigger maps.
  - Mitigation: introduce payload bounds, optional region windowing, or server-side compression strategy later.
- Risk: preview validation and execution validation drift.
  - Mitigation: share eligibility helpers between preview and execute paths.
- Risk: frontend fallback logic reintroduces local gameplay rules.
  - Mitigation: keep frontend as pure renderer with request/reply flow only.
