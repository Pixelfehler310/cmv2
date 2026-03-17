# WS Event Refactor Frontend Contract Handover

This document is the Phase 5 backend-to-frontend handover for the WS event refactor.

Companion documents:

- Baseline: [docs/architecture/backend/13_ws_event_system_baseline_as_built.md](docs/architecture/backend/13_ws_event_system_baseline_as_built.md)
- Refactor plan: [docs/architecture/backend/14_ws_event_refactor_backend_phase_plan.md](docs/architecture/backend/14_ws_event_refactor_backend_phase_plan.md)
- Acceptance matrix: [docs/architecture/backend/15_ws_event_refactor_acceptance_matrix.md](docs/architecture/backend/15_ws_event_refactor_acceptance_matrix.md)

## 1. Contract Version and Scope

- Contract version: `ws-combat-v2`.
- Endpoint remains: `/ws/{campaign_id}?token=...&role=...`.
- Envelope remains: `{ type, request_id?, payload }`.
- Command policy (required): command-like inbound events must include `request_id`.
- Terminal response policy (required): command flows must end in success event(s), denied event, or `error`.

This handover freezes the current backend behavior for frontend migration.

## 2. Changelog (Baseline -> ws-combat-v2)

## 2.0 Added inbound command-like keys

- `request_executable_actions`
- `request_move_preview`
- `request_attack_preview`

## 2.1 Added outbound event keys

- `command_denied`
- `attack_result`
- `save_result`
- `effect_applied`
- `executable_actions_snapshot`
- `movement_preview`
- `attack_preview`

## 2.2 Reintroduced from older architecture and now emitted

These were listed as not emitted in the baseline but are now emitted for action resolution:

- `attack_result`
- `save_result`
- `effect_applied`

Still not emitted:

- `effect_expired`
- `concentration_broken`

## 2.3 Payload additions on existing events

- `action_authorized.payload`
  - added `family`
  - added `turn_budget`
- `actor_moved.payload`
  - added `turn_budget`
- `turn_advanced.payload`
  - added `turn_budget`
- `combat_started.payload`
  - added `turn_budget`

## 2.4 Behavioral contract changes

- `end_turn` is no longer allowed to return silent no-op responses.
- Command denials are split into:
  - `action_denied` for action-family requests
  - `command_denied` for non-action command requests
- Unknown inbound event keys return `error` (`invalid_message`).
- Preview requests are deterministic command flows:
  - `request_executable_actions` -> `executable_actions_snapshot` or terminal deny/error
  - `request_move_preview` -> `movement_preview` or terminal deny/error
  - `request_attack_preview` -> `attack_preview` or terminal deny/error
- Previously declared-but-unrouted keys remain removed from active contract:
  - `update_hp`
  - `roll_initiative`
  - `cast_spell`
  - `toggle_equip`

## 3. Canonical Outbound Catalog (ws-combat-v2)

## 3.1 Sync and utility

- `state_sync`
- `pong`
- `dice_rolled`
- `chat_message`

## 3.2 Command lifecycle

- `action_authorized`
- `action_denied`
- `command_denied`
- `error`

## 3.3 Encounter and movement

- `combat_started`
- `combat_ended`
- `turn_advanced`
- `actor_moved`
- `movement_preview`
- `actor_added`
- `actor_removed`

## 3.5 Command deck and targeting previews

- `executable_actions_snapshot`
- `attack_preview`

## 3.4 Action resolution and direct effects

- `attack_result`
- `save_result`
- `effect_applied`
- `actor_damaged`
- `actor_healed`
- `actor_died`
- `condition_added`
- `condition_removed`

## 4. State Contract for Frontend

Frontend should treat backend state as authoritative and use a two-lane model:

1. Full-state lane: `state_sync`
2. Delta lane: apply incremental events on top of the last `state_sync`

## 4.1 Authoritative full state (`state_sync` payload)

Key fields:

- `round_number`
- `turn_phase` in `{pre_combat, active, post_combat}`
- `active_index`
- `combatants[]`
- `map.tokens[]`
- `turn_budgets` by `actor_id`

## 4.2 Budget snapshot updates

Budget-affecting events include `turn_budget` snapshots and should update UI action economy without local recomputation:

- `combat_started`
- `turn_advanced`
- `actor_moved`
- `action_authorized`

Recommendation: if a snapshot is missing unexpectedly, issue `request_sync` and reconcile.

## 5. Compatibility and Transitional Alias Policy

Backend decision for Phase 5:

- No backend alias layer is introduced for old event names.
- Frontend migration is done with a temporary adapter in shared/host if needed.
- Legacy support window is client-side only and time-boxed.

Transitional adapter guidance:

- Treat unknown events as non-fatal and log them.
- Normalize deny events into one view model (`action_denied` + `command_denied`).
- Keep a fallback hard-resync path (`request_sync`) for any unrecoverable delta mismatch.

## 6. Frontend Migration Checklist

## 6.1 Type package alignment (`frontend/packages/types`)

- Extend outbound union with new keys:
  - `command_denied`
  - `attack_result`
  - `save_result`
  - `effect_applied`
  - `combat_started`
  - `combat_ended`
  - `condition_added`
  - `condition_removed`
  - `pong`
  - `dice_rolled`
  - `chat_message`
  - `executable_actions_snapshot`
  - `movement_preview`
  - `attack_preview`
- Extend inbound command-like union with:
  - `request_executable_actions`
  - `request_move_preview`
  - `request_attack_preview`
- Add `turn_budget` snapshot field where emitted.
- Add command-deck payload contracts:
  - `ExecutableActionPayload` / `ExecutableActionsSnapshotPayload`
  - `MovementPreviewPayload`
  - `AttackPreviewPayload` / `AttackTemplateProjection`
- Expand deny reason codes to include current backend reasons:
  - `invalid_turn_phase`
  - `no_active_actor`
  - `movement_exhausted`
  - `action_exhausted`
  - `bonus_action_exhausted`
  - `reaction_exhausted`
  - `unsupported_action`
- Mark command envelopes as requiring `request_id` for command events.

## 6.2 Shared store alignment (`frontend/packages/shared`)

- Ingest and reduce all contract events listed in Section 3.
- Add reducer path for `command_denied`.
- Apply `turn_budget` snapshots to combatant action/movement fields.
- Handle `combat_started` and `combat_ended` as state transitions.
- Add reducer support for resolution telemetry events (`attack_result`, `save_result`, `effect_applied`) for UI logs/timeline.

## 6.3 Host bridge and transport alignment (`frontend/apps/host` + `frontend/packages/bridge`)

- Ensure every command dispatch includes generated `request_id`.
- Preserve incoming `request_id` in logs and diagnostics.
- Keep local optimistic changes minimal and always reconcile with backend outbound events.

## 6.4 Recommended rollout sequence

1. Update types package and export new unions/payloads.
2. Update store reducers with event completeness and budget snapshots.
3. Add request correlation IDs in dispatch path.
4. Enable adapter logging for unknown events during migration.
5. Remove temporary compatibility adapter once the matrix-critical rows are green.

## 7. Validation Gate for Frontend Handover

Frontend migration is considered complete when:

- All ws-combat-v2 outbound keys are either reduced or intentionally ignored with documented rationale.
- Command dispatch always includes `request_id` for command events.
- Denied states render deterministically for both `action_denied` and `command_denied`.
- Budget/action economy UI is derived from backend snapshots/state, not local calculations.
- Regression pass is green for critical acceptance rows: L-03, L-04, M-02, M-03, M-04, A-03, A-06, R-01.
