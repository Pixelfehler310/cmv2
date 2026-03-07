# Walking Skeleton: Core State & Bridge

## 1. Overview

With the visual styling deferred, the absolute focus of the Walking Skeleton is the **State Architecture**. The VTT relies on syncing the backend `EncounterState` with the frontend `GameStateStore` via the WebSocket Bridge.

## 2. The Core State Stores

We will implement three distinct Zustand stores for the skeleton.

### `useGameStateStore` (The Replica)

Holds the local copy of the combat state.
**Skeleton Goal:** Render raw text dumps of this state to the screen to verify it hydrates correctly on WebSocket connection.

```typescript
interface GameStateStore {
  encounter: EncounterState | null; // The exact Pydantic model payload
  status: "disconnected" | "connecting" | "connected";
  patchState: (delta: Partial<EncounterState>) => void;
}
```

### `useSelectionStore` (The UI Context)

Tracks what the user is interacting with locally.
**Skeleton Goal:** Allow a user to select an item from a raw HTML list and verify the `selectedId` updates.

```typescript
interface SelectionStore {
  selectedTokenId: string | null;
  selectedActionUrl: string | null; // e.g., 'attack', 'move'
  setSelection: (id: string | null) => void;
}
```

### `useWsBridge` (The Communicator)

Manages the raw WebSocket connection and dispatches typed actions.
**Skeleton Goal:** Connect to the locally running FastAPI server and log incoming/outgoing raw JSON strings.

## 3. The End-to-End Skeleton Flow Test

The primary objective of the Walking Skeleton is to successfully execute this exact flow without any styling:

1. **Mount:** The DM View mounts. `useWsBridge` connects using a hardcoded valid JWT test token.
2. **Hydrate:** The server sends the initial `state_sync` event. `useGameStateStore.patchState()` is called.
3. **Render:** A bare `<pre>` tag on the screen renders `JSON.stringify(gameState.encounter)`. The text appears.
4. **Interact:** The user clicks a raw native `<button id="attack-btn">Attack Goblin</button>`.
5. **Dispatch:** The button click calls `bridge.actions.dispatchAction(attackerId, 'Bite', [goblinId])`.
6. **Receive Result:** The backend resolves the math, sends back an `attack_result` event, followed by an `hp_changed` patch event.
7. **Re-render:** The `<pre>` tag automatically updates to show the Goblin's new lower HP.

If this flow works, the architecture is sound.

## 4. Dependencies for Skeleton

- `zustand`
- Native WebSocket API.
- TypeScript interfaces matching the Python Phase 6 Pydantic models.
