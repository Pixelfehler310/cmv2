# Interchangeable Action Button Concept (DM + Player Test Harness)

Status: implementation concept (phase-ready)
Related:

- frontend/docs/architecture/ws-combat-v2-frontend-alignment-concept.md
- frontend/docs/testing/ws-combat-v2-player-dm-implementation-backlog.md

## 1. Problem Statement

DM testing currently relies on ad-hoc controls while player testing has no equivalent command lab. This creates slow validation loops for ws-combat-v2 acceptance rows and poor parity between DM and player command flows.

## 2. Product Goal

Deliver one shared test harness component that lets users switch command type at runtime and execute most combat commands without source edits.

Success conditions:

- Same core component drives DM and player labs.
- Preset switching is instant and safe.
- Payload editing is structured first, raw JSON optional.
- Each send shows correlated terminal outcome by `request_id`.

## 3. Explicit Non-Goals

- No gameplay UX redesign outside testing surfaces.
- No frontend-side rule enforcement replacing backend validation.
- No schema auto-generation in this wave.

## 4. Target Architecture

`ActionCommandLab` is composed from:

1. `ActionSelectButton`
2. `ActionPayloadEditor`
3. `ActionResultBadge`

Shared, role-aware action catalog drives all behavior. DM/player differences are policy and visibility, not implementation forks.

## 5. Catalog Contract

### 5.1 Preset shape

```ts
export type ActionPreset = {
  id: string;
  label: string;
  envelopeType: string;
  family: "lifecycle" | "movement" | "action" | "effect" | "utility";
  rolePolicy: "dm-only" | "player-or-dm" | "all";
  payloadTemplate: Record<string, unknown>;
  editableFields: Array<{
    key: string;
    type: "string" | "number" | "boolean" | "actor-id" | "path" | "json";
    required?: boolean;
    helpText?: string;
  }>;
};
```

### 5.2 Preset baseline (minimum)

- Lifecycle: `start_combat`, `end_turn`, `end_combat`
- Movement: `move_token`
- Action family: `request_action` (`action`, `bonus_action`, `reaction`)
- Direct effects: `apply_damage`, `apply_healing`, `apply_condition`, `remove_condition`, `add_actor`, `remove_actor`
- Utility: `request_sync`, `ping`, `roll_dice`, `chat_message`
- Advanced (DM only): `raw_envelope`

## 6. Behavior Specification

### 6.1 ActionSelectButton

- Primary click sends selected preset.
- Secondary selector changes preset immediately.
- Optional keyboard cycle: `[` previous, `]` next.
- Disabled if transport disconnected, role denied, or required fields missing.

### 6.2 ActionPayloadEditor

- Starts from `payloadTemplate`.
- Renders editable fields by `editableFields` metadata.
- Supports raw JSON mode (DM-only by default).
- Performs only structural input checks (required/type shape), not game rules.

### 6.3 ActionResultBadge

- Displays latest terminal result tied to current send/request.
- Terminal categories:
  - success event (`turn_advanced`, `actor_moved`, `action_authorized`, etc.)
  - denied (`action_denied`, `command_denied`)
  - `error`
- Always shows `request_id`.

## 7. DM and Player Policy Model

DM view:

- Full catalog access.
- Supports impersonation metadata injection where needed.
- Raw envelope mode available in advanced section.

Player view:

- Only allowed presets by default.
- DM-only presets hidden or disabled with reason text.
- Default `actor_id` from selected owned actor.

## 8. Request Correlation Contract

For each send, persist:

- `request_id`
- outbound `type`
- payload snapshot
- send timestamp

Then match first terminal inbound event with same `request_id` and compute normalized outcome.

```ts
type CommandOutcome = {
  requestId: string;
  sentType: string;
  terminalType: string;
  ok: boolean;
  reasonCode?: string;
  message?: string;
  at: string;
};
```

## 9. File Placement (Planned)

Shared:

- frontend/packages/shared/src/testing/actionCatalog.ts
- frontend/packages/shared/src/components/testing/ActionSelectButton.tsx
- frontend/packages/shared/src/components/testing/ActionPayloadEditor.tsx
- frontend/packages/shared/src/components/testing/ActionResultBadge.tsx
- frontend/packages/shared/src/components/testing/ActionCommandLab.tsx

DM integration:

- frontend/packages/dm-view/src/\*_/_ (replace/wrap current action deck surface)

Player integration:

- frontend/packages/player-view/src/\*_/_ (feature-flagged player lab)

## 10. Phase and PR Plan (This Document)

### Phase 4 / PR 4: Shared Lab Foundations

Scope:

- Add catalog and all shared lab components.
- Add preset dispatch contract and result-badge input contract.

Acceptance:

- Shared lab renders and can send at least 12 presets without code edits.
- Result badge can display success/denied/error states.

### Phase 5 / PR 5: DM Integration

Scope:

- Integrate `ActionCommandLab` in DM test panel.
- Keep legacy controls temporarily for parity verification.

Acceptance:

- DM can execute all DM-capable presets.
- No regression versus prior DM ad-hoc controls.

### Phase 6 / PR 6: Player Integration (Feature Flag)

Scope:

- Add `PlayerActionLab` variant wired to shared component.
- Gate with `frontendTesting.playerActionLab`.

Acceptance:

- Player can execute permitted presets.
- DM-only presets are blocked in UI presentation layer.

### Phase 7 / PR 7: Cleanup and Consolidation

Scope:

- Remove duplicate legacy testing controls.
- Restrict raw mode to DM advanced mode.
- Finalize docs and matrix links.

Acceptance:

- Single interchangeable command model remains.
- All testing docs reflect final component paths.

## 11. Manual Validation Matrix

Core:

- `end_turn` in active turn -> terminal response visible.
- `move_token` for non-active/non-owned actor -> denied reason visible.
- `request_action` with exhausted budget -> denied reason visible.
- `request_sync` -> state refresh observed.
- `apply_damage` as DM -> hp delta observed.

Correlation:

- Send five different presets rapidly and verify one-to-one request/outcome mapping.

Resilience:

- Unknown command through raw mode returns `error` and does not break UI state.

## 12. Open Decisions (Must Close Before PR 6)

- Player lab default visibility: always-on or debug-only.
- DM dual-mode strategy: quick shortcuts + lab, or lab only.
- Raw JSON exposure: DM-only strict vs broader debug audience.
