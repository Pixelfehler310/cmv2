# Walking Skeleton Phase Plan

This Phase Plan replaces the initial visual-focused phase plan. We build the functional backbone first, heavily focusing on the Bridge and State integration, and save **all** design system implementation and complex layouts for later "Polish" phases.

---

## Phase 1.1 — The Raw Bridge

**Goal:** Establish the workspace and prove the frontend can talk to the backend.

- Initialise Monorepo packages (`bridge`, `dm-view`, `host`).
- Create `WsClient.ts` in the bridge.
- Build a raw "Connection Test" page in `host` that connects to the FastAPI websocket and `console.log`s the initial `state_sync` payload.

## Phase 1.2 — The State Hydration

**Goal:** Prove the data can be stored and displayed.

- Implement the Zustand `useGameStateStore`.
- Wire `WsClient` to automatically call `patchState` on incoming events.
- Build a raw `JSONDebugger` component that renders `<pre>{JSON.stringify(state, null, 2)}</pre>` on the screen.

## Phase 1.3 — The "Ugly" DM Podium (Selection & Interaction)

**Goal:** Prove local selection and outbound action dispatching.

- Implement `useSelectionStore`.
- Build an ugly `ActionDeck`: A cluster of raw HTML `<button>` elements that only appear when a token ID is manually typed into a text input (simulating selection).
- Wire the `<button>` clicks to send `ACTION` events (e.g., Attack, Heal) over the bridge.
- **Acceptance:** Clicking the ugly button successfully lowers the HP displayed in the `JSONDebugger`.

## Phase 1.4 — The "Ugly" Stage View (Sanitization Check)

**Goal:** Prove that opening a second browser window receives only sanitized data via the bridge.

- Scaffold the `/stage` route.
- Connect it via a second WebSocket connection using a "Player" or "Stage" role JWT.
- Render its own `JSONDebugger`.
- **Acceptance:** Side-by-side windows. The DM View's JSON shows `hp: 45`. The Stage View's JSON completely lacks the `hp` key, proving backend sanitization is active.

## Phase 1.5 — The "Ugly" Management Sandbox

**Goal:** Prove REST CRUD without styling.

- Scaffold `packages/management-view`.
- Build a raw unstyled list fetching from `/api/campaigns`.
- Build a raw HTML form that successfully POSTs a new Dummy Campaign to the backend.

---

_Once all Phase 1.x steps are complete, the Walking Skeleton is alive. We then transition to **Phase 2.x**. Phase 2.x involves tearing out the `<pre>` tags and raw `<button>`s, installing `@civic/design-system`, and building the beautiful layout documented in the primary fronted architectural specs._
