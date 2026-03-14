# DM/Stage Implementation Status & Next Steps Concept

Last updated: 2026-03-14

## 1. Purpose

This document records where the DM-first implementation currently stands and defines the next implementation concept from this exact baseline.

It is intentionally practical and should be read together with:

- `docs/architecture/frontend/11_implementation_phase_plan.md`
- `docs/architecture/frontend/12_dm_view_seed_phase_plan.md`
- `docs/frontend/reference/04_stage_view.md`
- `docs/frontend/reference/05_dm_podium_layout.md`
- `docs/frontend/reference/06_dm_command_deck.md`
- `docs/backend/reference/07_websocket_api_and_sessions.md`
- `docs/backend/reference/08_websocket_events_reference.md`

---

## 2. Current State (Implemented)

### 2.1 Backend WebSocket: `move_token` is now functional

Implemented in:

- `backend/src/systems/dnd5e/ws_handler.py`
- `backend/tests/systems/dnd5e/test_ws_integration.py`

Behavior now available:

1. Inbound `move_token` payload validation (`actor_id`, non-empty `path`).
2. Path coordinate validation via schema conversion and map-bound checks.
3. Canonical state mutation of both:
   - `ActorInstance.position`
   - matching `MapToken.position` (or creation if missing)
4. Outbound `actor_moved` broadcast with final position and normalized path.

Test coverage added:

1. Happy path: actor and token both move.
2. Invalid target: returns `invalid_target` error.
3. Player permission path: non-DM player can send `move_token` under current permission model.

### 2.2 Frontend DM interaction slice updated

Implemented in:

- `frontend/packages/shared/src/stores/useCombatStore.ts`
- `frontend/packages/dm-view/src/components/MapBoard.tsx`
- `frontend/packages/dm-view/src/components/CommandDeck.tsx`

Behavior now available:

1. Store websocket contract aligned to envelope model (`type` + `payload`).
2. State hydration from `state_sync` plus incremental handling for:
   - `actor_moved`
   - `actor_damaged`
   - `actor_healed`
   - `actor_died`
   - `turn_advanced`
3. DM token drag-drop sends `move_token` in snake_case payload format.
4. Optimistic token position update on drop.
5. Rollback strategy: on backend `error`, request canonical `request_sync`.
6. Command Deck actions narrowed to currently implemented backend actions:
   - apply damage
   - end turn

### 2.3 Validation performed

Backend verification:

- `PYTHONPATH=backend backend/.venv/Scripts/python.exe -m pytest backend/tests/systems/dnd5e/test_ws_integration.py -q`
- Result at this snapshot: movement tests pass and full file passes.

---

## 3. Current Gaps (Known)

### 3.1 Contract gaps still pending in backend

Documented events that are still not fully implemented in runtime handler include:

1. `add_actor`
2. `remove_actor`
3. `action`
4. `chat_message` handler behavior
5. additional effect/combat delta events expected by richer DM/Stage flows

### 3.2 Frontend architecture gaps still pending

1. DM is still in a walking-skeleton UI state (not full podium architecture yet).
2. Stage view sanitization/rendering is not yet fully integrated with the updated DM interaction loop.
3. Bestiary-to-map spawn flow is not wired to backend `add_actor` because handler is pending.
4. Initiative control is only partially surfaced (basic end-turn path present; richer controls pending).

### 3.3 Workspace-level technical noise

There are unrelated workspace build concerns outside this DM/Stage slice (for example package-level TypeScript/env typing issues in other packages). Treat these as separate maintenance tasks unless they block this flow directly.

---

## 4. Next Steps Concept (From This Baseline)

## 4.1 Goal

Complete a DM-first vertical slice that can reliably drive a read-only Stage View over the same campaign room, with backend authority and frontend optimistic UX reconciliation.

## 4.2 Principles for next steps

1. Backend remains source of truth.
2. Transport naming remains snake_case at websocket boundary.
3. DM can be optimistic for map interactions but must reconcile against canonical state.
4. Stage consumes sanitized state from backend role filtering, never client-side trust.

## 4.3 Execution tracks

### Track A: Backend contract completion (high priority)

1. Implement `add_actor` handler.
2. Implement `remove_actor` handler.
3. Implement `chat_message` handler with visibility-safe outbound message.
4. Add strict payload validation and targeted tests for each handler.
5. Keep `state_sync` as reconciliation fallback after any recoverable error.

Definition of done for Track A:

1. DM can spawn/remove tokens via websocket only.
2. DM and Stage both receive consistent deltas for spawn/remove.
3. Tests cover success + validation errors + permission failures.

### Track B: DM View interaction completion

1. Introduce a clearer command-deck mode split (global vs selected token).
2. Wire initiative controls:
   - start combat
   - end combat
   - end turn
3. Add lightweight Bestiary panel wiring to dispatch spawn intents (once Track A ready).
4. Preserve optimistic move + rollback behavior already implemented.

Definition of done for Track B:

1. DM can move, damage, end turn, start/end combat, and spawn from one screen.
2. UI state remains consistent after backend errors through sync reconciliation.

### Track C: Stage handoff completion

1. Validate same-room spectator connection path end-to-end.
2. Ensure Stage receives only sanitized combatant fields.
3. Confirm no exact monster HP leakage.
4. Confirm hidden/DM-only events are absent from public stage log.

Definition of done for Track C:

1. Two-window test passes (DM + Stage).
2. DM actions reflect on Stage in real time with sanitization intact.

---

## 5. Practical Short Sprint Plan

### Sprint Step 1

Implement `add_actor` + tests, then wire Bestiary drop to this event.

### Sprint Step 2

Implement `remove_actor` + tests and basic DM token removal control.

### Sprint Step 3

Implement `chat_message` + DM/Stage log split with visibility filtering.

### Sprint Step 4

Run dual-window verification script:

1. Load seeds.
2. Open DM route.
3. Open Stage route.
4. Move token.
5. Spawn token.
6. Apply damage.
7. End turn.
8. Confirm Stage sanitization and state parity.

---

## 6. Open Decisions to Keep Explicit

1. Keep current player permission on `move_token` or constrain by ownership checks.
2. Decide whether every non-trivial backend error should auto-trigger `request_sync` from frontend (current behavior in store does this).
3. Decide whether to retain temporary compatibility parsing for legacy websocket payload shapes while migration completes.
