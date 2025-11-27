# Communication Architecture: The Bridge

## 1. The "Bridge" Pattern

To ensure our Microfrontends (MFEs) are truly independent and can eventually run in a generic JavaScript framework (Phase 3), we must decouple them from the specific implementation of the Host (React/Vite).

We achieve this via **The Bridge**: A strict interface that the Host implements and injects into every MFE.

### The Contract (`@rpg/bridge`)

This package defines *only* interfaces and types. No logic.

```typescript
// packages/bridge/src/index.ts

export interface IHostBridge {
  // 1. Communication
  events: IEventBus;
  actions: IActionDispatcher;
  
  // 2. State Access (Read-Only)
  auth: IAuthService;
  connection: IConnectionState;
  
  // 3. UI Utilities
  toast: (message: string, type: 'info'|'error') => void;
  openModal: (id: string, props?: any) => void;
}

export interface IEventBus {
  emit(event: string, payload: any): void;
  on(event: string, handler: (payload: any) => void): () => void; // Returns unsubscribe
}

export interface IActionDispatcher {
  dispatch(actionType: string, payload: any): Promise<ActionResult>;
}
```

---

## 2. Data Flow

### A. Action Flow (MFE -> Backend)
*User clicks "Attack" in Player View.*

1.  **MFE:** Calls `bridge.actions.dispatch('COMBAT_ATTACK', { targetId: 'goblin-1' })`.
2.  **Host (Bridge Impl):**
    *   Validates the action structure.
    *   Serializes it.
    *   Sends via WebSocket: `{ type: 'ACTION', payload: ... }`.
3.  **Backend:** Processes logic, updates DB.
4.  **Backend:** Broadcasts `STATE_UPDATE` via WebSocket.

### B. State Update Flow (Backend -> MFE)
*Backend confirms damage dealt.*

1.  **Host:** Receives `STATE_UPDATE` (e.g., `CampaignState` changed).
2.  **Host:** Updates its internal React Query Cache (`queryClient.setQueryData(...)`).
3.  **MFE:** Since the MFE uses `useQuery(['campaign', id])`, it *automatically* re-renders with the new data.
    *   *Note:* In Phase 1 (Monorepo), sharing the Query Client is easy. In Phase 3, the Bridge will expose a `subscribeToState('campaign')` method.

### C. Inter-MFE Communication (The Event Bus)
*User hovers over a Goblin in the Combat Tracker.*

1.  **Combat Tracker MFE:** `bridge.events.emit('HOVER_ENTITY', { entityId: 'goblin-1' })`.
2.  **Map MFE:** Listens for `HOVER_ENTITY`.
3.  **Map MFE:** Highlights the token for 'goblin-1'.

---

## 3. Implementation Details

### The Host Implementation (`apps/host`)

The Host creates the concrete implementation of the Bridge.

```typescript
// apps/host/src/lib/bridge.ts

class ReactHostBridge implements IHostBridge {
  constructor(
    private ws: WebSocketManager,
    private queryClient: QueryClient,
    private toastFn: any
  ) {}

  actions = {
    dispatch: async (type, payload) => {
      // Optimistic updates could happen here
      return this.ws.sendAction(type, payload);
    }
  };

  events = new EventEmitter(); // Simple pub/sub

  // ...
}
```

### The MFE Consumption (`packages/player-view`)

MFEs receive the bridge as a prop.

```tsx
// packages/player-view/src/App.tsx

interface Props {
  bridge: IHostBridge;
  campaignId: string;
}

export const PlayerView = ({ bridge, campaignId }: Props) => {
  return (
    <BridgeProvider value={bridge}>
       <CharacterSheet />
       <CombatTracker />
    </BridgeProvider>
  );
};
```

---

## 4. Future Proofing (Phase 3)

When we move to a "Generic JS Framework" or allow 3rd party modules:

1.  **The Interface stays the same.**
2.  **The Host changes:** We can rewrite the Host in Vue, Svelte, or Vanilla JS. As long as it passes an object matching `IHostBridge` to the MFEs, the MFEs (React) won't know the difference.
3.  **Sandboxing:** We can wrap the Bridge in a proxy to prevent malicious MFEs from crashing the Host or stealing tokens.

---

## 5. Next Steps

1.  Create `@rpg/bridge` package.
2.  Define the core Event types (Hover, Select, Ping).
3.  Define the core Action types (Attack, Move, Cast).
