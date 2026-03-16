# WS Combat V2 Frontend Implementation Backlog (Prep)

Status: detailed execution backlog for next step
Depends on:

- frontend/docs/architecture/ws-combat-v2-frontend-alignment-concept.md
- frontend/docs/testing/interchangeable-action-button-concept.md

## 1. Epic Breakdown

Epic 1: Contract and typing alignment
Epic 2: Store and reducer completeness
Epic 3: Request correlation and command lifecycle UX
Epic 4: Shared interchangeable action button lab
Epic 5: DM + player integration and verification

## 2. Story List

### Epic 1 - Contract and typing alignment

1. Add missing outbound event types to `@rpg/types`.
2. Add payload models for resolution telemetry events.
3. Add `command_denied` payload and reason code normalization.
4. Mark command-like inbound events as `request_id` required in TypeScript contracts.

Definition of done:

- Type package exports a complete `ws-combat-v2` outbound union.
- No `any` needed in store reducer for known events.

### Epic 2 - Store and reducer completeness

1. Extend `ingestEnvelope` to handle all known events.
2. Add timeline state for telemetry events.
3. Add unified denied feedback model for action and command denied.
4. Apply `turn_budget` snapshots where available.
5. Add fallback resync trigger conditions.

Definition of done:

- Exhaustive handling for all known outbound event keys.
- Unknown events are logged and ignored safely.

### Epic 3 - Request correlation and command lifecycle UX

1. Add `ensureRequestId` utility in host dispatch path.
2. Inject request ids for command-like envelopes.
3. Persist send-to-terminal outcomes keyed by request id.
4. Expose latest command outcome selectors for UI badges.

Definition of done:

- Every command send has a request id.
- Terminal outcome is traceable in UI and logs.

### Epic 4 - Shared interchangeable action button lab

1. Add shared preset catalog.
2. Build `ActionSelectButton`.
3. Build `ActionPayloadEditor` with typed fields + raw JSON toggle.
4. Build `ActionResultBadge`.
5. Compose `ActionCommandLab`.

Definition of done:

- One reusable lab component can drive most test actions via preset switching.

### Epic 5 - DM + player integration and verification

1. Integrate shared lab into DM action panel.
2. Add player-safe lab variant behind feature flag.
3. Keep role policy enforcement in UI presentation only (backend still authoritative).
4. Execute manual test matrix against backend acceptance critical rows.

Definition of done:

- DM and player test surfaces both use the shared interchangeable command model.

## 3. Suggested PR Slicing

PR 1: Types-only alignment
PR 2: Store event coverage and timeline
PR 3: Request id generation and command outcome tracking
PR 4: Shared action lab components
PR 5: DM integration
PR 6: Player integration + feature flag
PR 7: Cleanup legacy controls and docs sync

## 4. Verification Checklist

- `pnpm -r typecheck` passes.
- `pnpm -r test` passes for touched packages.
- DM can test movement/turn/action denial paths without raw JSON editing.
- Player can test permitted actions with clear denied feedback for forbidden actions.
- Command logs include request correlation from send to terminal event.

## 5. Out-of-Scope for this wave

- Full combat timeline UI redesign.
- Analytics pipeline export of command traces.
- Auto-generated forms from backend schema at runtime.
