# Player View Detailed Plan

## 1. UX Philosophy & Usability

**Goal:** "Immersion through Frictionless Interaction."
The UI should never get in the way of the roleplay. It should feel like an extension of the player's intent.

### Core Principles
1.  **Contextual Actions:** Don't show "Cast Fireball" if I don't have spell slots. Don't show "Attack" if I'm looking at my inventory.
2.  **Information Hierarchy:** HP and AC are always visible. Lore notes are hidden until needed.
3.  **Feedback Loops:** Every action (click, roll, damage) must have immediate visual feedback (animations, toast, log update).

### Simulated User Journeys

#### Journey 1: The Combat Turn
> **Context:** It is Aragorn's turn. He wants to move up to an Orc and attack with his sword.
1.  **Notification:** "It's your turn!" toast appears. Taskbar icon flashes.
2.  **Focus:** The **Map Window** highlights his token. The **Actions Window** automatically opens/focuses.
3.  **Movement:** Player drags token on Map.
    *   *UX:* Visual path shows distance (15ft / 30ft).
4.  **Action:** Player clicks "Attack" in **Actions Window**.
    *   *UX:* Valid targets on Map highlight.
5.  **Targeting:** Player clicks the Orc on the Map.
6.  **Resolution:** Dice roll animation in **Chat Window**. Damage is applied automatically.
7.  **End Turn:** Player clicks "End Turn" button (prominent only during turn).

#### Journey 2: The Downtime Investigation
> **Context:** The party is exploring a dungeon. The Rogue wants to check for traps and read a scroll.
1.  **Layout:** Player switches to "Exploration Layout" (saved preset). Map is smaller, **Inventory** and **Skills** are larger.
2.  **Skill Check:** Player clicks "Investigation" in **Character Sheet**.
    *   *UX:* 3D Dice roll across the screen. Result posted to Chat.
3.  **Inventory:** Player drags "Ancient Scroll" from **Inventory** to "Read" button.
    *   *UX:* A new **Handout Window** opens displaying the scroll content (image/text).

---

## 2. Design & Layout

**Layout Engine:** `flexlayout-react` (Tabs, Splitters, Draggable Windows).

### Default Layout (ASCII)

```
┌─────────────────────────┬───────────────────────────────────────────────┐
│ [Character Summary]     │  [ Map Window (Cartographer) ]                │
│ HP: 45/45  AC: 18       │                                               │
│ [Skills] [Saves]        │                                               │
│                         │                                               │
│ ┌─────────────────────┐ │                                               │
│ │ Inventory / Spells  │ │                                               │
│ │ [Tab] [Tab]         │ │                                               │
│ │                     │ │                                               │
│ └─────────────────────┘ │                                               │
├─────────────────────────┼───────────────────────────────────────────────┤
│ [ Chat & Log ]          │  [ Actions / Combat ]                         │
│ > GM: You see a door.   │  [Attack] [Dash] [Hide]                       │
│ > Aragorn: I open it.   │                                               │
│                         │  (Contextual: Shows available actions)        │
└─────────────────────────┴───────────────────────────────────────────────┘
```

---

## 3. Windows & Components Detail

### A. Character Sheet Window
*   **Purpose:** The "Paper" sheet digitized.
*   **Tabs:**
    *   **Main:** Stats, Skills, Saves.
    *   **Bio:** Traits, Ideals, Bonds, Flaws, Backstory.
*   **Interactions:** Click Skill -> Roll. Click Stat -> Roll Check.

### B. Actions Window (The "Deck")
*   **Purpose:** The command center.
*   **Logic:** Filters based on state (Combat vs. Exploration).
*   **Sections:**
    *   **Standard:** Attack, Dash, Disengage, Dodge.
    *   **Bonus:** Off-hand attack, Bardic Inspiration.
    *   **Spells:** Quick cast buttons for prepared spells.
    *   **Inventory:** Use Potion, Throw Item.

### C. Inventory Window
*   **Purpose:** Gear management.
*   **Components:**
    *   **Equipment Slots:** Head, Body, Hands, etc. (Drag & Drop).
    *   **Backpack:** Grid or List view of items.
    *   **Currency:** Gold/Silver/Copper tracker.

### D. Spellbook Window
*   **Purpose:** Magic management.
*   **Components:**
    *   **Slots:** Visual pips for available slots (Level 1: ●●○).
    *   **Prepared:** Toggle switches for preparing spells (Long Rest logic).

---

## 4. Logic & API Calls

### State Management
*   **Local State:** `useCharacterState()` (Zustand/Context).
    *   Keeps track of "UI-only" things like *Selected Token*, *Active Tab*, *Pending Action*.
*   **Server State:** `useQuery(['character', id])`.
    *   Syncs HP, Inventory, Stats from backend.

### API Calls (via Bridge)
*   **Fetch Character:** `GET /characters/{id}` (Initial load).
*   **Update Layout:** `POST /users/preferences` (Auto-save layout).

---

## 5. Communication (Bridge & Events)

### Incoming Events (From Host/DM)
*   `COMBAT_START`: Switch Actions Window to "Combat Mode". Open Initiative Tracker. // Whats with COMBAT_END?
*   `YOUR_TURN`: Flash taskbar, play sound, enable "End Turn" button.
*   `HANDOUT_RECEIVED`: Open Handout Window with image.
*   `REQUEST_CHECK`: Pop up "GM requests Perception Check" (Click to roll).

### Outgoing Events (To Host/DM)
*   `CAST_SPELL`: `bridge.actions.dispatch('CAST_SPELL', { spellId, slotLevel })`.
*   `MOVE_TOKEN`: `bridge.actions.dispatch('MOVE_TOKEN', { x, y })`.
*   `PING_MAP`: `bridge.events.emit('PING', { x, y })`.

---

## 6. Backend Information Needed

To render this view, we need the **Full Character View Model**:
1.  **Computed Stats:** Final AC (Armor + Dex + Shield), Final Attack Bonus (Str + Prof + Magic).
    *   *Note:* The Frontend should NOT calculate "AC 18". The Backend sends `ac: 18`.
2.  **Capabilities:** List of available actions (`["Action: Attack", "Bonus: Second Wind"]`).
3.  **Inventory:** Full item details + Equipped state.
4.  **Spellbook:** Known spells + Prepared state + Slots available.
