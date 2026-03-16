# WS Combat V2 Frontend Alignment Concept

Status: implemented (phase 7 cleanup applied)
Owner: frontend
Input contract: docs/architecture/backend/16_ws_event_frontend_contract_handover.md
Companion docs:

- frontend/docs/testing/interchangeable-action-button-concept.md
- frontend/docs/testing/ws-combat-v2-player-dm-implementation-backlog.md

## 1. Intent

This document defines the contract-alignment implementation for the frontend layer after backend phases 13-16.

Primary outcomes:

- Frontend consumes the full `ws-combat-v2` outbound catalog.
- Command-like sends always include `request_id`.
- Store remains backend-authoritative for turn, budget, and state mutation.
- Denied/error outcomes are deterministic and visible in UI.

## 2. Non-Negotiable Rules

1. Backend is source of truth. Frontend does not infer combat outcomes.
2. Unknown outbound events are non-fatal and logged.
3. Budget/action economy UI mirrors backend snapshots only.
4. Contract typing must use discriminated unions by `type`.
5. Command-like envelopes must be `request_id`-complete before transport send.

## 3. Package Scope

### 3.1 frontend/packages/types

Required:

- Extend outbound unions for all `ws-combat-v2` events:
  - `state_sync`, `pong`, `dice_rolled`, `chat_message`
  - `action_authorized`, `action_denied`, `command_denied`, `error`
  - `combat_started`, `combat_ended`, `turn_advanced`, `actor_moved`, `actor_added`, `actor_removed`
  - `attack_result`, `save_result`, `effect_applied`, `actor_damaged`, `actor_healed`, `actor_died`, `condition_added`, `condition_removed`
- Add deny reason code union updates from handover.
- Add optional `turn_budget` snapshot fields on applicable payloads.
- Split inbound envelope unions into:
  - command-like (`request_id` required)
  - utility (`request_id` optional)

### 3.2 frontend/packages/shared

Required in store/reducer path:

- Exhaustive handling of known outbound keys.
- Add unified denied view model for `action_denied` + `command_denied`.
- Add timeline/telemetry state for result and utility events.
- Apply `turn_budget` snapshots where emitted.
- Add fallback reconciliation trigger (`request_sync`) for snapshot mismatch conditions.

### 3.3 frontend/apps/host and frontend/packages/bridge

Required at dispatch boundary:

- Inject `request_id` for all command-like sends.
- Preserve request correlation in local bridge events (`ws:send`, `ws:send_result`, `ws:error`, `ws:recv`).
- Keep helper deterministic and side-effect free (`ensureRequestId`).

### 3.4 frontend/packages/dm-view and frontend/packages/player-view

Required consumer updates:

- Render unified denied feedback.
- Render timeline entries for newly supported result/telemetry events.
- Consume new selectors from shared store only (no duplicate local parsing).

## 4. Event Handling Buckets

### 4.1 State mutation

- `state_sync`, `combat_started`, `combat_ended`, `turn_advanced`, `actor_moved`, `actor_added`, `actor_removed`, `actor_damaged`, `actor_healed`, `actor_died`, `condition_added`, `condition_removed`

### 4.2 Telemetry/result

- `attack_result`, `save_result`, `effect_applied`, `dice_rolled`, `chat_message`, `pong`

### 4.3 Feedback/control

- `action_authorized`, `action_denied`, `command_denied`, `error`

## 5. Store Additions (Concept Contract)

```ts
type CombatTimelineEntry = {
  id: string;
  at: string;
  type: string;
  requestId?: string;
  actorId?: string;
  summary: string;
  rawPayload: Record<string, unknown>;
};

type DeniedFeedback = {
  requestId?: string;
  type: "action_denied" | "command_denied";
  reasonCode: string;
  message?: string;
  at: string;
};
```

Proposed additive state:

- `eventTimeline: CombatTimelineEntry[]`
- `latestDenied: DeniedFeedback | null`
- `unknownEventCount: number`
- `lastRequestSyncAt: string | null`

## 6. Phase and PR Plan (This Document)

### Phase 1 / PR 1: Type Contract Freeze in Frontend

Scope:

- Implement complete outbound/inbound unions and payloads.
- Remove reducer-facing `any` for known ws-combat-v2 events.

Files (expected):

- frontend/packages/types/src/\*_/_
- frontend/packages/types/package.json (if exports need adjustment)

Acceptance:

- `pnpm -r typecheck` passes.
- Known event types can be narrowed exhaustively by `type`.

### Phase 2 / PR 2: Shared Store Event Completeness

Scope:

- Exhaustive event reducer coverage.
- Timeline + unified denied model.
- Snapshot application and mismatch fallback hooks.

Files (expected):

- frontend/packages/shared/src/stores/\*_/_
- frontend/packages/shared/src/selectors/\*_/_ (if present)
- frontend/packages/shared/src/types/\*_/_ (if local store types exist)

Acceptance:

- Unknown events are counted/logged, not fatal.
- `command_denied` is UI-consumable through same feedback lane as `action_denied`.

### Phase 3 / PR 3: Request Correlation Infrastructure

Scope:

- `ensureRequestId` injection in host/bridge dispatch path.
- Send-to-terminal correlation traceability foundations.

Files (expected):

- frontend/apps/host/src/\*_/_
- frontend/packages/bridge/src/\*_/_

Acceptance:

- Command-like outbound envelopes always have `request_id`.
- Correlation ids appear consistently in local bridge diagnostics.

### Phase 7 / PR 7: Cleanup and Docs Sync

Scope:

- Remove temporary duplicate DM ad-hoc testing controls.
- Keep raw envelope usage DM-only via advanced mode gate.
- Sync final harness and selector naming in docs.

Acceptance:

- DM and player test harnesses use shared `ActionCommandLab` path.
- Raw envelope is available only in DM advanced mode.
- Correlation consumers use shared selectors (`selectCommandOutcomeByRequestId`, `selectPendingCommandByRequestId`).

## 7. Risks and Mitigations

- Risk: union growth breaks existing narrowing paths.
  - Mitigation: enforce `never` checks in reducer switch defaults.
- Risk: optimistic state races authoritative deltas.
  - Mitigation: remove command-driven optimistic mutations where contract events already cover result.
- Risk: partial request-id injection misses niche call sites.
  - Mitigation: centralize dispatch and prohibit bypass sends.

## 8. Done Criteria

This alignment concept is implemented when:

- All `ws-combat-v2` outbound keys are reduced or explicitly ignored with rationale.
- Command-like sends always include `request_id`.
- Budget/turn UI is fully backend-snapshot driven.
- Denied feedback is deterministic for both action and command families.
- Critical acceptance rows are reproducible from frontend test surfaces: L-03, L-04, M-02, M-03, M-04, A-03, A-06, R-01.
