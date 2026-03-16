# WS Combat V2 Frontend Implementation Backlog (Execution)

Status: phase 7 implemented (cleanup/docs sync complete)
Depends on:

- frontend/docs/architecture/ws-combat-v2-frontend-alignment-concept.md
- frontend/docs/testing/interchangeable-action-button-concept.md
- docs/architecture/backend/16_ws_event_frontend_contract_handover.md

## 1. Delivery Model

This backlog is split into seven PRs grouped by phased risk reduction:

1. Contract and typing first.
2. Reducer/store completeness second.
3. Request correlation infrastructure third.
4. Shared test-harness UI fourth.
5. DM and player integration after shared base is stable.
6. Cleanup last.

## 2. Phases and PRs

### Phase 1 / PR 1: Types-Only Alignment

Objective:

- Freeze frontend type contract to `ws-combat-v2`.

Primary tasks:

1. Extend outbound envelope union with full catalog.
2. Add payload models for `attack_result`, `save_result`, `effect_applied`, utility, lifecycle, and deny/error additions.
3. Add `command_denied` and normalize deny reason-code unions.
4. Enforce `request_id` required typing for command-like inbound envelopes.

Definition of done:

- Types package exports complete ws-combat-v2 envelope unions.
- Shared store compiles with no `any` for known events.

### Phase 2 / PR 2: Store and Reducer Completeness

Objective:

- Make `useCombatStore` exhaustive for known outbound events.

Primary tasks:

1. Extend envelope ingestion switch for all supported outbound keys.
2. Add telemetry timeline entries for result/utility events.
3. Add unified denied model for `action_denied` + `command_denied`.
4. Apply `turn_budget` snapshots on `combat_started`, `turn_advanced`, `actor_moved`, `action_authorized`.
5. Add unknown-event count/log + safe ignore policy.
6. Add fallback resync trigger conditions.

Definition of done:

- Exhaustive switch on known events.
- Unknown events non-fatal and observable.

### Phase 3 / PR 3: Request Correlation and Command Lifecycle UX Foundations

Objective:

- Ensure command sends are traceable from outbound to terminal inbound.

Primary tasks:

1. Add `ensureRequestId` helper at dispatch boundary.
2. Inject request ids for command-like envelopes only.
3. Persist send metadata and terminal outcomes keyed by request id.
4. Expose selectors for latest and per-request outcomes.

Definition of done:

- Every command send has `request_id`.
- Correlation is visible via state/selectors and logs.

### Phase 4 / PR 4: Shared Interchangeable Action Lab Components

Objective:

- Introduce reusable testing components in shared package.

Primary tasks:

1. Add action preset catalog.
2. Build `ActionSelectButton`.
3. Build `ActionPayloadEditor` (typed fields + raw JSON mode).
4. Build `ActionResultBadge`.
5. Compose `ActionCommandLab`.

Definition of done:

- One reusable lab can execute most command presets via runtime switching.

### Phase 5 / PR 5: DM Integration

Objective:

- Move DM testing surface onto shared lab model.

Primary tasks:

1. Integrate `ActionCommandLab` into DM panel.
2. Keep legacy controls in parallel for one validation PR.
3. Verify direct-effect and lifecycle presets in DM role context.

Definition of done:

- DM can run full preset set and observe correlated outcomes.

### Phase 6 / PR 6: Player Integration (Feature-Flagged)

Objective:

- Enable player-side test harness safely.

Primary tasks:

1. Add player-safe variant of shared lab.
2. Gate with `frontendTesting.playerActionLab` feature flag.
3. Enforce role policy in presentation layer (backend remains authoritative).
4. Verify owned-actor defaults and forbidden action feedback.

Definition of done:

- Player can run allowed presets and sees clear denied outcomes for forbidden commands.

### Phase 7 / PR 7: Cleanup and Docs Sync

Objective:

- Remove temporary migration duplication.

Primary tasks:

1. Remove deprecated ad-hoc controls.
2. Restrict raw envelope mode to DM advanced mode.
3. Sync docs to final component and selector names.

Implementation notes:

- DM test surface now uses only `ActionCommandLab` in `frontend/packages/dm-view/src/components/ActionDeck.tsx`.
- Raw envelope is exposed only when DM advanced mode is enabled.
- Player harness remains feature-flagged (`frontendTesting.playerActionLab`) in `frontend/packages/player-view/src/pages/PlayerView.tsx`.
- Request-correlation consumers use shared selectors `selectCommandOutcomeByRequestId` and `selectPendingCommandByRequestId`.

Definition of done:

- Single maintained test harness path for DM and player surfaces.

## 3. Cross-PR Dependency Graph

- PR 2 depends on PR 1.
- PR 3 depends on PR 1 and PR 2.
- PR 4 depends on PR 1 and PR 3.
- PR 5 depends on PR 4.
- PR 6 depends on PR 4 and PR 5.
- PR 7 depends on PR 5 and PR 6.

## 4. Verification Gates by PR

For every PR:

- `pnpm -r typecheck`
- `pnpm -r test` (touched packages)

Additional phase-specific checks:

- PR 2: reducer exhaustive coverage assertions.
- PR 3: request-id injection assertions in dispatch path tests.
- PR 4-6: manual command-lab smoke checks (send, denied, error, correlation).

## 5. Acceptance Matrix Mapping

Critical rows to prove through DM/player test harness and logs:

- Lifecycle: L-03, L-04
- Movement: M-02, M-03, M-04
- Action economy: A-03, A-06
- Resolution: R-01

Expected evidence:

- request-id-correlated outbound/inbound traces
- deterministic terminal event per command
- UI-visible denied reason for negative cases

## 6. Out of Scope

- Full combat timeline UX redesign.
- Analytics export pipeline for command traces.
- Runtime form generation from backend schema.

## 7. Release Readiness Checklist

1. All PR gates complete.
2. Feature flag behavior validated in off/on modes.
3. No optimistic frontend calculations for turn budget/action economy.
4. Docs aligned across architecture/testing/backlog files.
