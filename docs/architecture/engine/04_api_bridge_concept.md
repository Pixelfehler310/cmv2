# API Bridge & Synchronization Concept (DM-Only MVP)

## 1. Core Philosophy

The core principle of the MVP is **Backend Authority**. The React frontend (both DM View and Stage View) is completely "dumb". It does not calculate movement costs, it does not determine if an action is valid, and it does not manage initiative.

The Frontend is simply a remote control (sending intents) and a monitor (rendering the current state).

---

## 2. The Communication Protocol (WebSockets)

We will use **FastAPI WebSockets** to maintain a persistent, bidirectional connection between the frontend clients and the backend engine.

### Connection Architecture

- **Route:** `ws://localhost:8000/campaigns/{campaign_id}/ws`
- **Clients:**
  - The DM View connects as the `host` (has write/command privileges).
  - The Stage View connects as an `observer` (read-only, receives sanitized data).

---

## 3. State Broadcasting (Backend -> Frontend)

The Backend Engine holds the `Encounter` state in memory. Every time the state changes (a token moves, damage is taken, a turn ends), the backend serializes the current state and broadcasts it to all connected clients.

### The Payload Structure (JSON)

The backend sends a standardized `GameState` object.

```json
{
  "event_type": "STATE_UPDATE",
  "data": {
    "round_number": 2,
    "active_combatant_id": "goblin_1",
    "combatants": [
      {
        "id": "hero_1",
        "public_name": "Arannis",
        "x": 5,
        "y": 10,
        "size": "Medium",
        "hp_percent": 0.85, // Stage View uses this
        "hp_current": 45, // DM View uses this (Stage View ignores/strips this)
        "action_used": false,
        "bonus_action_used": true,
        "movement_remaining": 15.0
      }
    ]
  }
}
```

### Sanitization Layer

Before the backend sends the JSON payload through the WebSocket, it checks the connection role:

- **If DM:** Sends the unadulterated state.
- **If Stage View:** Runs a `Sanitizer.clean(state)` function which strips out `hp_current`, `hp_max`, and replaces true enemy names with visual archetypes.

---

## 4. Intents (Frontend -> Backend)

When the DM clicks a button in the UI, it sends an "Intent" to the backend. The backend validates the intent, executes it using the `CombatStateMachine` or `CombatController` we built, and then broadcasts the resulting state update.

### Example Intents

**Intent: End Turn**

```json
{
  "action": "END_TURN",
  "payload": {}
}
```

**Intent: Move Token**

```json
{
  "action": "MOVE_TOKEN",
  "payload": {
    "target_id": "hero_1",
    "path": [
      [5, 10],
      [5, 11],
      [6, 11]
    ]
  }
}
```

**Intent: Apply Damage**

```json
{
  "action": "APPLY_DAMAGE",
  "payload": {
    "target_id": "goblin_1",
    "amount": 12,
    "damage_type": "slashing"
  }
}
```

---

## 5. Frontend Architecture (Zustand Store)

To manage this cleanly in React, we will create a global store (`useCombatStore.ts`) using Zustand.

1. **Initialization**: The store connects to the WebSocket `onMount`.
2. **Listening**: When a `STATE_UPDATE` message is received, the store overwrites its internal state with the new JSON payload.
3. **Reactivity**: Both `StageView` and `CommandDeck` hook into this Zustand store. When the store updates, React automatically re-renders the tokens in their new positions and updates the action economy UI.
4. **Dispatching**: The store provides methods like `store.moveToken(target, x, y)` which format the JSON intent and send it through the socket.
