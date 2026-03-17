# WS Combat V2 Command Deck Next Stages (Frontend Companion)

Status: planned
Owner: frontend
Backend companion: docs/architecture/backend/17_ws_event_command_deck_next_stages.md

Related docs:

- frontend/docs/architecture/ws-combat-v2-frontend-alignment-concept.md
- frontend/docs/testing/ws-combat-v2-player-dm-implementation-backlog.md
- frontend/docs/testing/interchangeable-action-button-concept.md
- docs/architecture/backend/16_ws_event_frontend_contract_handover.md

## 1. Intent

This document translates backend stages A-E into frontend package and component work for command deck action rendering and movement/attack highlighting.

Primary outcomes:

- Player command deck consumes backend action snapshots only.
- Movement highlights are request/response driven and turn-budget accurate.
- Attack highlights are backend-authoritative, first for single-target and then for AoE templates.
- No local combat rules engine is introduced in frontend.

## 2. Non-Negotiable Rules

1. Backend is the source of truth for action availability, target legality, and movement budget.
2. Frontend only renders snapshots/previews and sends intent commands.
3. New command-like sends must always include `request_id`.
4. Every new outbound event must be typed and reducer-handled (or explicitly safe-ignored).
5. Unknown events remain non-fatal and observable.

## 3. Stage Mapping (Frontend)

## Stage A-FE: Executable Action Snapshot Rendering

Depends on backend Stage A.

Scope:

- Add new event contract support for executable action snapshots.
- Render command deck actions from backend snapshot data.

Package checklist:

### frontend/packages/types

- [ ] Add outbound payload typings:
  - `executable_actions_snapshot`
  - `ExecutableActionWire`
- [ ] Add any new enum-like unions for:
  - `action_type_cost`
  - `targeting_mode`
  - `unavailable_reason`
- [ ] Extend known outbound type list and envelope unions.

### frontend/packages/shared

- [ ] Add store state:
  - `executableActionsByActorId`
  - selector helpers for active actor action list
- [ ] Ingest `executable_actions_snapshot` in reducer path.
- [ ] Clear/refresh snapshot data on `state_sync`, `turn_advanced`, and actor removal.
- [ ] Keep denied/error feedback lane unified.

### frontend/apps/player-view and/or frontend/packages/player-view

- [ ] Replace local hardcoded action buttons with backend snapshot-driven rendering.
- [ ] Add unavailable-state presentation using backend reason text/code.
- [ ] Keep controls disabled when no valid snapshot exists.

Definition of done:

- Player action deck can render without hardcoded action catalogs for gameplay actions.
- Action availability state is entirely backend-snapshot driven.

## Stage B-FE: Movement Preview UX Integration

Depends on backend Stage B and current baseline (`request_move_preview` + `movement_preview`).

Scope:

- Integrate drag lifecycle with movement preview overlay rendering.

Package checklist:

### frontend/packages/types

- [ ] Confirm `request_move_preview` command typing is exported and stable.
- [ ] Confirm `movement_preview` payload typing includes:
  - `actor_id`
  - `origin`
  - `movement_remaining`
  - `reachable`

### frontend/packages/shared

- [ ] Keep `movementPreview` state authoritative and clear on:
  - `actor_moved`
  - `turn_advanced`
  - `state_sync`
  - explicit denied paths where stale preview should be removed
- [ ] Add selectors:
  - active actor preview
  - fast lookup set for reachable cells

### player map surface component (current placeholder path)

- [ ] Implement drag-start hook to dispatch `request_move_preview`.
- [ ] Render overlay cells from `movement_preview.reachable`.
- [ ] On drop, send `move_token` and defer position truth to backend response.
- [ ] Remove stale overlays on cancel/turn change/sync.

Definition of done:

- Drag start visibly highlights reachable cells.
- Move commit updates through backend event flow with no local movement budget math.

## Stage C-FE: Single-Target Attack Preview UX

Depends on backend Stage C.

Scope:

- Add action-selection to target-highlight flow for single-target attacks.

Package checklist:

### frontend/packages/types

- [ ] Add command typing for `request_attack_preview`.
- [ ] Add outbound payload typing for `attack_preview`:
  - `actor_id`
  - `action_id`
  - `origin`
  - `eligible_target_ids`
  - optional `eligible_cells`

### frontend/packages/shared

- [ ] Add store state:
  - selected action for preview context
  - latest `attack_preview`
- [ ] Ingest `attack_preview` events.
- [ ] Clear preview when action changes, turn changes, sync occurs, or action resolves.

### frontend command deck + map components

- [ ] On action selection, dispatch `request_attack_preview`.
- [ ] Highlight only eligible targets/cells from backend payload.
- [ ] On target confirm, send `request_action`/`action` with request correlation.
- [ ] Render denied reasons if selected target is invalid.

Definition of done:

- Attack selection produces deterministic highlight candidates.
- Invalid target attempts are user-visible and backend-denied.

## Stage D-FE: AoE Template Rendering

Depends on backend Stage D.

Scope:

- Render AoE template projection data and preserve execution parity with backend validation.

Package checklist:

### frontend/packages/types

- [ ] Extend `attack_preview` typing with template projection shape:
  - `shape`
  - `size`
  - `origin`
  - `direction` (optional)
  - `affected_cells`

### frontend/packages/shared

- [ ] Add shape-aware preview model in store.
- [ ] Keep template data immutable between preview and execute.

### map rendering surface

- [ ] Add overlay renderer for line/cone/sphere/cube/cylinder.
- [ ] Distinguish affected vs selectable cells visually.
- [ ] Ensure accessibility contrast in light/dark theme states.

Definition of done:

- AoE templates render accurately from backend projection payloads.
- No client-side geometric authority beyond rendering provided cells.

## Stage E-FE: Contract Hardening and Cleanup

Depends on backend Stage E.

Scope:

- Finalize docs, tests, and migration cleanup.

Package checklist:

### frontend/packages/types and frontend/packages/shared

- [ ] Remove temporary compatibility types once backend contract is finalized.
- [ ] Ensure exhaustive reducer checks include all new event keys.

### frontend/docs

- [ ] Update architecture and testing docs with final event names and payload fields.
- [ ] Sync examples and checklist references across companion docs.

Definition of done:

- Frontend docs, typing, and runtime behavior match final backend contract.

## 4. Component-Level Worklist

Priority components:

1. player command deck renderer
2. player map interaction surface
3. shared combat store selectors
4. shared testing harness (for rapid validation)

Implementation tasks by component:

- Command deck component:
  - [ ] map backend action snapshot rows to buttons/cards
  - [ ] show economy cost and availability
  - [ ] show disabled reason from backend
- Map component:
  - [ ] drag-start preview request
  - [ ] movement overlay layer
  - [ ] attack/target overlay layer
  - [ ] overlay lifecycle cleanup
- Shared store:
  - [ ] `movementPreview` selectors
  - [ ] `attackPreview` selectors
  - [ ] `executableActions` selectors
- Testing harness:
  - [ ] add presets for `request_move_preview`, `request_executable_actions`, `request_attack_preview`
  - [ ] verify request/outcome correlation in UI

## 5. PR Plan (Frontend)

1. PR-F1: Types and store for executable action snapshots.
2. PR-F2: Player command deck rendering from backend snapshots.
3. PR-F3: Movement preview overlay integration in player map surface.
4. PR-F4: Single-target attack preview request/render/execute flow.
5. PR-F5: AoE template rendering support.
6. PR-F6: Docs sync, cleanup, and final acceptance pass.

## 6. Verification Gates

For each PR:

1. `pnpm --filter @rpg/types build`
2. `pnpm --filter @rpg/shared build`
3. targeted package build for touched app/view package

Functional checks:

- Movement:
  - drag-start sends preview request
  - reachable cells render
  - move commit returns backend actor move and budget update
- Single-target attack:
  - action select sends attack preview request
  - eligible targets highlight
  - invalid target selection returns denied feedback
- AoE:
  - template projection renders from backend payload
  - execute path remains backend-authoritative

Observability checks:

- request_id correlation visible between send and terminal outcome
- unknown event count remains non-fatal and auditable

## 7. Risks and Mitigations

- Risk: player map placeholder delays UX rollout.
  - Mitigation: complete type/store and command deck work first; land map integration as isolated PR.
- Risk: visual overlays become expensive on large maps.
  - Mitigation: use memoized cell lookup sets and lightweight canvas/layer rendering strategy.
- Risk: duplicate logic drifts between command deck and test harness.
  - Mitigation: centralize preview/selector logic in shared store and consume from both surfaces.
