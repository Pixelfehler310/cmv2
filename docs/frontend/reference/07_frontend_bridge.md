# Frontend Bridge & WebSocket Synchronization

## 1. Overview

The `packages/bridge` module is the crucial circulatory system of the frontend. It isolates the WebSocket connection logic, state parsing, and API request typing away from the React component tree. The MFEs (DM, Stage, Management) rely on the Bridge to read from the backend and mutate the state.

## 2. Core Concepts / Layout

The Bridge is responsible for bridging the divide between React's predictable view rendering and the chaotic, asynchronous real-time events coming from the FastAPI server.

### The Connection Manager

Establishes the WebSocket connection using the `JWT` fetched by the `apps/host` auth context. It handles reconnection logic, ping/pong heartbeats, and error surfacing.

### State Replication (The "Local Copy")

The backend holds the absolute "True State" of the game (the `EncounterState`). When a connection is made, the Bridge receives a full snapshot of this state.

- The Bridge hydrates a massive `Zustand` or context store with this snapshot.
- Subsequently, the backend only sends "Delta Updates" (e.g., `TOKEN_MOVED`, `HP_CHANGED`).
- The Bridge processes these deltas and patches the local store, triggering minimal React re-renders.

### Specialized TypeScript Wrappers

The Bridge provides strongly typed function calls (like an SDK) for the UI components to use when invoking backend actions.
Instead of:
`ws.send({ type: 'action', payload: ... })`
Components use:
`bridge.actions.attack(attackerId, targetId, weaponId)`

## 3. Key Components / State

- **`WsClient`**: A raw WebSocket wrapper class containing exponential backoff retry logic.
- **`GameStateStore`**: The massive unified Zustand store holding the local replica of the `EncounterState`. It is considered "Read-Only" to the UI components. The UI cannot manually set `state.hp = 10`. It must dispatch an action to the server, and wait for the server to reply with the `HP_CHANGED` event to update the local store.
- **`useGameEvent` Hook**: A React hook allowing components to listen for ephemeral events that _don't_ mutate the store (e.g., a `CHAT_MESSAGE_RECEIVED` or `SOUND_EFFECT_PLAY`).

## 4. Optimistic UI vs Authoritative Server Flow

```mermaid
graph TD
    ReactUI[DM Command Deck] --> |Clicks "Attack"| BridgeSDK[bridge.actions.attack]
    BridgeSDK -- Validates Payload --> WSOut[WebSocket Send]

    WSOut --> |Network| Server[Backend FastAPI Engine]
    Server -- Resolves Math/Damage --> WSIn[WebSocket Return Event: HP_CHANGED]

    WSIn --> StorePatch[Update GameStateStore]
    StorePatch --> ReactUI[Re-render with new HP]
```

_(Note: To prevent rollbacks or de-sync, the VTT relies on the fast Server Authoritative model rather than optimistic UI faking.)_

## 5. Dependencies

- Shared TypeScript types generated directly from the Python Pydantic models to ensure identical JSON mappings.
- `Zustand` for state hydration.
