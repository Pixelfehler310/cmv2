# DM View Detailed Plan

## 1. UX Philosophy: "The Conductor's Podium"

**Goal:** "Omniscience and Control."
The DM view looks similar to the Player View (shared DNA), but the controls are more powerful. The interface must handle switching contexts rapidly (from controlling a Goblin to changing the music to checking a rule).

### Core Principles
1.  **Context-Aware Command Deck:** The bottom bar changes completely based on what is selected.
    *   *No Selection:* Global Scene Controls (Music, Fog of War, Pings).
    *   *Monster Selected:* Monster Stat Block & Attacks.
    *   *Player Selected:* Player Summary & "God Actions" (Heal, Smite).
2.  **Hidden Information:** Clearly distinguish what the DM sees vs. what Players see (Ghost tokens, Hidden rolls).
3.  **Rapid Access:** Drag-and-drop monsters from the side panel directly into combat.

---

## 2. Design & Layout

**Layout Strategy:** "Flexible 3-Column Docking with Background Map" (Same as Player).

### Visual Layout (ASCII)

```
┌──────────────────────────────────────────────────────────────────────────┐
│ [Logo]  [ Global Search / Wiki ]                  [Status] [User] [Menu] │ <-- AppNavbar
├──────────────────────────────────────────────────────────────────────────┤
│ ┌──────────┐                                                ┌──────────┐ │
│ │ Left     │      ( Map Layer - Background 100% )           │ Right    │ │
│ │ Panel    │                                                │ Panel    │ │
│ │ (20%)    │                                                │ (20%)    │ │
│ │          │                                                │          │ │
│ │ Bestiary │                                                │ Chat     │ │
│ │ Campaign │                                                │ Log      │ │
│ │ Players  │                                                │ Combat   │ │
│ │          │                                                │          │ │
│ │          │                                                │          │ │
│ │          │   ┌────────────────────────────────────────┐   │          │ │
│ │          │   │       DM COMMAND DECK (Dynamic)        │   │          │ │
│ │          │   │ [Context Icon] [Controls Grid] [End]   │   │          │ │
│ │          │   │ (Sticky Bottom Center - 60%)           │   │          │ │
│ └──────────┘   └────────────────────────────────────────┘   └──────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Windows & Components Detail

### A. The DM Command Deck (Dynamic)

This is the biggest difference from the Player View. It has modes:

#### Mode 1: "Global / Scene" (Default)
*   **Portrait:** Scene Icon / Campaign Logo.
*   **Grid Controls:**
    *   **Environment:** Toggle Fog of War, Reveal Area, Reset Fog.
    *   **Audio:** Play/Pause Music, Switch Playlist (Combat/Peaceful).
    *   **Time:** Advance Time (Short Rest, Long Rest, Dawn/Dusk).
    *   **Draw:** Drawing tools (Pen, Shape, Erase).

#### Mode 2: "Monster Control" (When Monster Selected)
*   **Portrait:** Monster Image (e.g., Goblin).
*   **Vitals:** HP Bar (Editable), AC Shield.
*   **Grid Controls:**
    *   **Attacks:** Scimitar, Shortbow (Click to roll).
    *   **Actions:** Hide, Dash, Disengage.
    *   **Edit:** "Edit Stats" button (opens full editor).
*   **End Turn:** Advances initiative if it's this monster's turn.

### B. Left Panel (The "Toolbox")
*   **Tabs:**
    *   **Bestiary:** Searchable list of monsters. **Drag & Drop** onto map to spawn. (Advanced Feature)
    *   **Campaign:** Scene list (switch maps), Audio playlists, Handouts list.
    *   **Players:** Live summary of all players (Passive Perception, AC, HP).

### C. Right Panel (The "Comms & Combat")
*   **Tabs:**
    *   **Combat:** Advanced Initiative Tracker.
        *   *Features:* Drag to reorder, "Next Turn", Add custom entry, Toggle Visibility of combatants.
    *   **Chat:** Standard chat but with **"GM Roll" (Hidden)** toggle.
    *   **Log:** Full history (including hidden rolls).

---

## 4. Logic & API Calls

### State Management
*   **Selection State:** Critical. `useSelectionStore()` tracks what is selected (Token, Drawing, or Nothing).
*   **Turn Logic:** The DM View is the "Authority" on whose turn it is.

### API Calls (via Bridge)
*   **Spawn Monster:** `bridge.actions.dispatch('SPAWN_TOKEN', { monsterId, x, y })`.
*   **Update Scene:** `bridge.actions.dispatch('UPDATE_SCENE', { fogOfWar: ... })`.
*   **Force Turn:** `bridge.actions.dispatch('FORCE_NEXT_TURN', {})`.

---

## 5. Communication (Bridge & Events)

### Outgoing Events (DM -> Players)
*   `REVEAL_AREA`: Clears fog for players.
*   `PLAY_MUSIC`: Syncs audio on player clients.
*   `SHOW_HANDOUT`: Forces a handout window to open on player screens.

### Incoming Events
*   `PLAYER_PING`: Shows a ping animation on the DM's map.

---

## 6. Backend Information Needed

1.  **Monster Definitions:** Full stats for the Bestiary.
2.  **Scene Data:** Fog of War mask, Wall definitions, Lighting.
3.  **Player Vitals:** Real-time HP/AC/Passive Perception of all connected players.
