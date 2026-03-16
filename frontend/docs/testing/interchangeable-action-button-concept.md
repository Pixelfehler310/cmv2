# Interchangeable Action Button Concept (DM + Player Test Harness)

Status: concept draft for implementation step
Related: frontend/docs/architecture/ws-combat-v2-frontend-alignment-concept.md

## 1. Problem

You want a single reusable button/control model with interchangeable action values so most combat actions can be tested quickly in both DM and player flows.

Today, test controls exist mostly in DM panels with ad-hoc buttons and raw envelope input.
Player view has no comparable command lab surface.

## 2. Goals

- One shared action-trigger component for both DM and player experiences.
- Action value can be switched at runtime from a catalog (no code edits needed).
- Cover most practical test actions with typed defaults and editable payload fields.
- Show immediate feedback tied to request correlation (`request_id`, outcome event, denied reason).

Non-goals:

- This concept is not a gameplay UX redesign.
- This concept is not replacing backend validation with frontend validation.

## 3. High-Level Solution

Introduce a shared `ActionCommandLab` composed from three reusable primitives:

1. `ActionSelectButton`

- Main interchangeable action trigger.
- Can switch action preset (value) via dropdown/segmented picker.

2. `ActionPayloadEditor`

- Structured field editor generated from preset schema.
- Optional raw JSON mode for edge-case tests.

3. `ActionResultBadge`

- Displays latest terminal outcome for the selected action:
  - success event type
  - denied reason
  - error code/message
  - request id

Use one shared action catalog so DM/player surfaces differ only by policy and visibility, not by wiring.

## 4. Shared Action Catalog

Create a catalog in shared package (conceptual path):

- `frontend/packages/shared/src/testing/actionCatalog.ts`

### 4.1 Catalog entry shape

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
  }>;
};
```

### 4.2 Initial preset coverage

Lifecycle:

- `start_combat`
- `end_turn`
- `end_combat`

Movement:

- `move_token`

Action family:

- `request_action` (action)
- `request_action` (bonus_action)
- `request_action` (reaction)

Direct effect tools:

- `apply_damage`
- `apply_healing`
- `apply_condition`
- `remove_condition`
- `add_actor`
- `remove_actor`

Utility:

- `request_sync`
- `ping`
- `roll_dice`
- `chat_message`

Optional advanced preset:

- `raw_envelope` passthrough for unknown/experimental keys

## 5. Interchangeable Button Behavior

`ActionSelectButton` acts as one command button with configurable value.

Expected interactions:

- Primary click sends currently selected preset.
- Secondary control changes selected preset instantly.
- Optional keyboard cycle (`[` and `]`) through presets for rapid testing.

Label format example:

- `Send: request_action (bonus_action)`

Disabled state rules:

- Missing required payload fields.
- Role policy violation in current view mode.
- Transport disconnected.

## 6. DM vs Player Behavior

Both use same shared component; policy differs by role context.

DM view:

- Full preset catalog visible.
- Actor impersonation (`actingAsUserId`) can be toggled and injected where relevant.
- Supports direct-effect tools (`apply_damage`, `remove_actor`, etc.).

Player view:

- Only player-allowed/all presets visible by default.
- DM-only presets hidden or visible-but-disabled with reason text.
- Uses selected owned actor as default `actor_id`.

## 7. Request Correlation and Feedback

For each send, capture:

- outbound `request_id`
- command type
- payload snapshot

Then resolve against first terminal inbound event with same `request_id`:

- success terminal event (for example: `turn_advanced`, `actor_moved`, `action_authorized`, `combat_started`)
- denied (`action_denied`, `command_denied`)
- `error`

Render this in `ActionResultBadge` and append to command log timeline.

## 8. Proposed Component Placement

Shared package:

- `frontend/packages/shared/src/components/testing/ActionCommandLab.tsx`
- `frontend/packages/shared/src/components/testing/ActionSelectButton.tsx`
- `frontend/packages/shared/src/components/testing/ActionPayloadEditor.tsx`
- `frontend/packages/shared/src/components/testing/ActionResultBadge.tsx`
- `frontend/packages/shared/src/testing/actionCatalog.ts`

DM integration:

- Replace or wrap current `ActionDeck` with `ActionCommandLab`.

Player integration:

- Add a compact `PlayerActionLab` section in stage/sidebar (feature-flagged).

## 9. State and API Contract

Store-level additions (concept):

- `dispatchPreset(presetId: string, payloadOverrides?: Record<string, unknown>): Promise<void>`
- `lastCommandOutcomeByRequestId: Record<string, CommandOutcome>`
- `latestOutcome: CommandOutcome | null`

`CommandOutcome` shape:

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

## 10. UX Flow

1. Pick actor (or use selected token).
2. Pick preset in interchangeable action button.
3. Adjust payload fields (optional).
4. Send command.
5. Observe correlated terminal result badge.
6. Repeat quickly with next preset.

This enables deterministic exploratory testing without editing source code between attempts.

## 11. Rollout Plan

Phase A - Shared foundations

- Add action catalog and shared components.
- Keep existing DM controls available in parallel.

Phase B - DM migration

- Replace ad-hoc DM action controls with shared lab.
- Validate no loss of current capabilities.

Phase C - Player enablement

- Add player-safe action lab subset.
- Gate behind `frontendTesting.playerActionLab` feature flag.

Phase D - Cleanup

- Remove duplicate legacy controls.
- Keep raw envelope mode only in DM advanced mode.

## 12. Acceptance Criteria

- One interchangeable action button exists and is used in DM and player testing surfaces.
- At least 12 presets from Section 4.2 are executable without code edits.
- Every send has visible `request_id` and terminal result status.
- Denied outcomes display normalized reason codes.
- Player surface cannot execute DM-only presets unless explicitly running in impersonated DM context.

## 13. Test Matrix (Manual)

Core checks:

- Send `end_turn` in active turn => terminal response appears.
- Send `move_token` on non-active/non-owned actor => denied reason visible.
- Send `request_action` with exhausted budget => denied reason visible.
- Send `request_sync` => state refresh visible.
- Send `apply_damage` as DM => hp delta reflected.

Correlation checks:

- Rapidly send 5 different presets and verify outcome mapping remains request-id correct.

Resilience checks:

- Unknown preset type via raw mode yields `error` and does not break UI.

## 14. Open Decisions

- Whether player lab should be visible by default or only via debug flag.
- Whether DM keeps both simplified quick buttons and advanced interchangeable mode.
- Whether raw JSON editing is globally available or DM-only.
