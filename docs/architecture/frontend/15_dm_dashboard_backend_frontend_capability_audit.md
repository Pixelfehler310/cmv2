# DM Dashboard Audit: Backend vs Frontend Capability

Date: 2026-03-14  
Scope: DM Dashboard, Stage View, WebSocket connectivity, campaign hydration on session open

---

## Executive Summary

The DM experience is currently a walking-skeleton implementation.

- WebSocket connectivity exists and does exchange state.
- Campaign hydration exists, but it is split across multiple frontend state paths.
- The live DM surface does not reliably bind to the campaign that was opened.
- Backend capability is significantly ahead of frontend visualization and interaction completeness.

---

## Direct Answers

### Is the DM dashboard poorly implemented / placeholder-heavy?

Yes. The DM layer contains multiple walking-skeleton surfaces and partially wired controls.

### Is it connected to WebSockets?

Yes, but through multiple competing paths and payload contracts.

### Is state hydrated when opening a campaign?

Partially. Session route hydration works into one store, but DM gameplay components use another store that currently hardcodes a campaign id.

---

## Highlighted Problem Areas

> [!SUCCESS]
> PROBLEM P1 (Critical): DM session is not campaign-correct. (Fixed 2026-03-14)
>
> - `DmDashboard` now receives `campaignId` and connects with that id.
> - Host `ViewContainer` now passes `campaignId` into DM view.
> - Result: opening `/session/:id` binds DM view to the opened campaign.

Evidence:

- `frontend/packages/dm-view/src/pages/DmDashboard.tsx:14`
- `frontend/apps/host/src/components/shell/ViewContainer.tsx:29`
- `frontend/apps/host/src/routes/SessionRoute.tsx:126`

> [!SUCCESS]
> PROBLEM P1 (Critical): Hydration is split across two independent stores. (Fixed 2026-03-14)
>
> - Session route no longer patches `useGameStateStore` for live DM flow.
> - JSON debugger now reads `useCombatStore`.
> - Result: debug hydration and DM widgets read the same runtime state path.

Evidence:

- `frontend/apps/host/src/routes/SessionRoute.tsx:50`
- `frontend/apps/host/src/components/JSONDebugger.tsx:4`
- `frontend/packages/dm-view/src/pages/DmDashboard.tsx:9`

> [!SUCCESS]
> PROBLEM P1 (Critical): Stage route only reacts to full snapshots, not realtime deltas. (Fixed 2026-03-14)
>
> - Stage route now handles `state_sync` / `state_update` plus realtime deltas.
> - Implemented delta handling for `actor_moved`, `actor_added`, `actor_removed`, `actor_damaged`, `actor_healed`, `actor_died`, `turn_advanced`.
> - Result: Stage state stays current after initial sync.

Evidence:

- `frontend/apps/host/src/routes/StageRoute.tsx:33`
- `backend/src/systems/dnd5e/ws_handler.py:346`
- `backend/src/systems/dnd5e/ws_handler.py:408`
- `backend/src/systems/dnd5e/ws_handler.py:448`
- `backend/src/systems/dnd5e/ws_handler.py:525`
- `backend/src/systems/dnd5e/ws_handler.py:297`

> [!SUCCESS]
> PROBLEM P1 (Critical): Two backend websocket systems are simultaneously mounted. (Fixed 2026-03-14)
>
> - Legacy campaigns websocket router is no longer mounted in backend startup.
> - Frontend combat store no longer keeps legacy `STATE_UPDATE` fallback parsing.
> - Result: runtime path now uses dispatcher endpoint and envelope protocol.

Evidence:

- `backend/src/main.py:86`
- `backend/src/main.py:89`
- `backend/src/campaigns/router.py:81`
- `backend/src/core/ws_dispatcher.py:98`

> [!SUCCESS]
> PROBLEM P2 (High): Role resolution in real mode can keep user in player view. (Fixed 2026-03-14)
>
> - Session route real mode now defaults to DM shell role.
> - Host websocket connect now sends explicit role query (`dm` for session route).
> - Stage route websocket connect now sends explicit `spectator` role.
> - Result: role-correct routing and backend role filtering in real mode.

Evidence:

- `frontend/apps/host/src/routes/SessionRoute.tsx:81`
- `frontend/apps/host/src/routes/SessionRoute.tsx:83`
- `docker-compose.yml:55`

> [!WARNING]
> PROBLEM P2 (High): Visualization coordinate model mismatch.
>
> - DM map renders tokens with grid scaling (`x * 50`, `y * 50`).
> - Stage cartographer treats token `x/y` as direct pixels.
> - Result: DM and Stage may show inconsistent token placement.

Evidence:

- `frontend/packages/dm-view/src/components/MapBoard.tsx:65`
- `frontend/packages/dm-view/src/stage/StageCartographer.tsx:16`

> [!WARNING]
> PROBLEM P2 (High): Sanitization contract mismatch for health descriptors.
>
> - Backend player filter emits `health_status` and removes exact HP.
> - Frontend mapper expects `health_descriptor` in one path.
> - Stage filter defaults to healthy if sanitized HP fields are missing.
> - Result: public health ring quality may be wrong.

Evidence:

- `backend/src/systems/dnd5e/state_filter.py:75`
- `frontend/packages/shared/src/stores/useCombatStore.ts:104`
- `frontend/packages/dm-view/src/stage/useStageFilter.ts:47`

> [!WARNING]
> PROBLEM P3 (Medium): Placeholder controls are present in DM surfaces.
>
> - Fog tools exist visually but are not wired to backend operations.
> - ActionDeck is mounted without bridge, and its dispatch path is effectively inactive.

Evidence:

- `frontend/packages/dm-view/src/components/MapBoard.tsx:48`
- `frontend/packages/dm-view/src/pages/DmDashboard.tsx:30`
- `frontend/packages/dm-view/src/components/ActionDeck.tsx:14`

---

## Backend vs Frontend Capability Comparison

### Backend currently supports

- Real-time event routing and room/session handling
- Role-aware permissions
- State sync + request sync
- Core DM intents:
  - `move_token`
  - `add_actor`
  - `remove_actor`
  - `start_combat`
  - `end_combat`
  - `end_turn`
  - `apply_damage`
  - `apply_healing`
  - `apply_condition`
  - `remove_condition`
  - `chat_message`
  - `roll_dice`

Reference:

- `backend/src/systems/dnd5e/ws_handler.py`
- `backend/src/systems/dnd5e/permissions.py`
- `backend/src/core/ws_dispatcher.py`

### Frontend DM currently surfaces

- WebSocket-based map token movement
- End turn trigger
- Apply damage trigger
- Remove token trigger
- Basic initiative list and selected-token command panel

Reference:

- `frontend/packages/dm-view/src/components/MapBoard.tsx`
- `frontend/packages/dm-view/src/components/CommandDeck.tsx`
- `frontend/packages/dm-view/src/components/InitiativePanel.tsx`

### Missing or incomplete on frontend relative to backend

- Campaign-correct DM connection wiring (Fixed 2026-03-14)
- Single coherent hydration model for session and DM UI (Fixed 2026-03-14)
- Full delta event consumption in Stage route (Fixed 2026-03-14)
- Complete DM command coverage (healing, conditions, chat, actor add in main flow)
- Protocol unification and removal of legacy fallback pathways (Fixed 2026-03-14)
- Coordinate and sanitization contract consistency

---

## Session Open and Hydration Flow (Current)

### What works

- Campaign launcher opens session/stage routes with id:
  - `frontend/packages/management-view/src/components/dashboard/CampaignGrid.tsx:116`
  - `frontend/packages/management-view/src/components/dashboard/CampaignGrid.tsx:123`
- Session route opens websocket to campaign id in real path:
  - `frontend/apps/host/src/routes/SessionRoute.tsx:47`

### What breaks correctness

- DM page campaign binding and prop wiring are fixed (2026-03-14).
- Hydration split between DM runtime/debug paths is fixed (2026-03-14).

---

## Risk Assessment

- Reliability risk: High
- Product confidence risk for live DM usage: High
- Security/privacy correctness risk (public stage sanitization quality): Medium to High
- Maintainability risk (dual websocket stacks): High

---

## Recommended Priority Order

1. Fix campaign id propagation into DM connect path (remove hardcoded `test_123`).
2. Consolidate DM/Stage runtime onto one websocket protocol and one authoritative frontend state flow.
3. Upgrade StageRoute to consume deltas (or guarantee periodic state sync snapshots).
4. Align health/sanitization contract naming across backend and frontend.
5. Remove or complete placeholder controls (fog tools, ActionDeck wiring).

---

## Notes on Runtime Verification

Current sampled backend logs did not show explicit websocket lifecycle markers in the captured tail (mostly SQL fixture/seed activity). This audit is therefore code-path validated and not yet end-to-end browser/session validated in this pass.
