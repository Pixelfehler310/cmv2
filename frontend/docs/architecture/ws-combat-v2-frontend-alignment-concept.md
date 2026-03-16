# WS Combat V2 Frontend Alignment Concept

Status: concept draft for implementation step
Owner: frontend
Input contract: docs/architecture/backend/16_ws_event_frontend_contract_handover.md

## 1. Purpose

This concept defines how frontend packages are aligned to the backend `ws-combat-v2` contract.

Primary goals:

- Keep backend authoritative and avoid client-side gameplay calculation.
- Ingest full outbound catalog without dropping meaningful events.
- Ensure command dispatch always includes `request_id` for command-like events.
- Use backend `turn_budget` snapshots instead of local budget math.

## 2. Current Baseline (as observed)

Current frontend already has useful scaffolding:

- `@rpg/shared` has a central `useCombatStore` reducer path.
- `@rpg/types` has basic outbound/inbound envelope typing.
- Host bridge already emits `ws:recv` into store ingestion.
- DM has command/action deck surfaces for manual event probing.

Gaps versus handover contract:

- Missing outbound event types in `@rpg/types`: `command_denied`, `attack_result`, `save_result`, `effect_applied`, plus utility/lifecycle events not fully represented.
- Store reducer does not reduce all `ws-combat-v2` events.
- Command dispatch path does not guarantee `request_id` on command-like sends.
- Optimistic state changes still exist in a few command helpers and can conflict with backend-authoritative deltas.

## 3. Scope by Package

### 3.1 `frontend/packages/types`

Required changes:

- Extend `KnownWsOutboundEnvelope` union with all `ws-combat-v2` events.
- Extend deny payload typing for `command_denied` and newer reason codes.
- Add payload types for:
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
- Add optional `turn_budget` snapshot where backend emits it.
- Split inbound command envelope into:
  - command-like events requiring `request_id`
  - utility events where `request_id` remains optional

Design note:

Do this with discriminated unions per `type` to keep reducer narrowing safe and exhaustive.

### 3.2 `frontend/packages/shared`

Required changes in `useCombatStore`:

- Reduce all catalog events from handover Section 3.
- Add reducer branch for `command_denied` with the same UI-facing deny model as `action_denied`.
- Add state fields for lightweight combat telemetry timeline entries for:
  - attack/save/effect result events
  - utility telemetry (`dice_rolled`, `chat_message`) where useful
- Apply `turn_budget` snapshots whenever present on:
  - `combat_started`
  - `turn_advanced`
  - `actor_moved`
  - `action_authorized`
- Add fallback reconciliation strategy:
  - if required snapshot context is missing, trigger `request_sync`

Anti-drift rule:

For budget and turn state, local state only mirrors backend payloads. No local derived consumption logic.

### 3.3 `frontend/apps/host` and `frontend/packages/bridge`

Required changes:

- Add command request correlation at dispatch boundary.
- Ensure generated `request_id` is attached to all command-like envelopes.
- Preserve and log `request_id` through `ws:send`, `ws:send_result`, and `ws:error` local events.

Suggested implementation detail:

- Add a small helper: `ensureRequestId(envelope)`.
- Request id format: `fe_${Date.now()}_${counter}` (simple and deterministic).

### 3.4 `frontend/packages/dm-view` and `frontend/packages/player-view`

Required changes:

- Consume normalized deny event stream from store (action + command denied).
- Surface timeline/log entries for newly supported result events.
- Add command test controls for player and DM workflows (see companion concept).

## 4. Event Handling Policy

All outbound events should be in one of three buckets:

1. State mutation events

- mutate game state directly (`actor_moved`, `turn_advanced`, etc.)

2. Telemetry/result events

- append to timeline/log (`attack_result`, `save_result`, `effect_applied`, `dice_rolled`, `chat_message`, `pong`)

3. Feedback/control events

- update feedback/errors/deny state (`error`, `action_denied`, `command_denied`, `action_authorized`)

Mandatory rule:

Unknown events are non-fatal. Log and ignore by default, with optional debug counters.

## 5. Data Model Additions (Store-Level)

Proposed additive fields in combat store state:

- `eventTimeline: CombatTimelineEntry[]`
- `lastRequestSyncAt: string | null`
- `unknownEventCount: number`

`CombatTimelineEntry` (proposed):

- `id`
- `at`
- `type`
- `requestId`
- `actorId`
- `summary`
- `rawPayload`

This keeps troubleshooting local without overloading the core `gameState` shape.

## 6. Migration Sequence

1. Extend `@rpg/types` unions and payloads.
2. Update store reducer to cover full outbound catalog.
3. Add request id generator/injector in host bridge dispatch path.
4. Wire DM/player views to new deny + timeline model.
5. Remove or minimize optimistic mutations that can race authoritative updates.
6. Run acceptance tests for critical rows from backend matrix (L-03, L-04, M-02, M-03, M-04, A-03, A-06, R-01).

## 7. Risks and Mitigations

Risk: reducer churn causes regressions.
Mitigation: add exhaustive switch checks on known event types plus targeted store unit tests.

Risk: accidental double-application (optimistic + authoritative).
Mitigation: for command-driven state transitions, prefer backend event application only.

Risk: missing request ids in some call paths.
Mitigation: enforce at one central dispatch gateway in host bridge.

## 8. Definition of Done

Frontend alignment is done when:

- All `ws-combat-v2` outbound keys are reduced or intentionally ignored with rationale.
- Command-like sends always include `request_id`.
- UI consistently handles both `action_denied` and `command_denied`.
- Budget/action economy display is based on backend snapshots/state only.
- Critical acceptance scenarios pass in manual and automated frontend checks.
