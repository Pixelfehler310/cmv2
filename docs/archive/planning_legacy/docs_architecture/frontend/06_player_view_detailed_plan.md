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

**Layout Strategy:** "Flexible 3-Column Docking with Background Map".
We use `flexlayout-react` to create a robust 3-column structure, but the **Map acts as the immersive background**.
*   **Left Panel (20%):** Persistent tools (Notes, Party). Collapsible and supports transparency (Glassmorphism).
*   **Center Panel (60%):** The Command Deck.
*   **Right Panel (20%):** Communication (Chat, Logs). Collapsible and supports transparency.
*   **Map Layer:** Technically sits behind the panels or fills the center. If side panels are closed or transparent, the Map is visible across 100% of the width.

**Flexibility:** All containers support Tabs and Splitting. A user can drag their Notes to the Right panel or split the Chat panel to show Combat Log and Messages simultaneously.

### Visual Layout (ASCII)

```
┌──────────────────────────────────────────────────────────────────────────┐
│ [Logo]  [ Global Search / Wiki ]                  [Status] [User] [Menu] │ <-- AppNavbar
├──────────────────────────────────────────────────────────────────────────┤
│ ┌──────────┐                                                ┌──────────┐ │
│ │ Left     │                                                │ Right    │ │
│ │ Panel    │                                                │ Panel    │ │
│ │ (20%)    │                                                │ (20%)    │ │
│ │          │      ( Map Layer - Background 100% )           │          │ │
│ │          │                                                │          │ │
│ │ Notes    │                                                │ Chat     │ │
│ │ Party    │                                                │ Log      │ │
│ │          │                                                │ Combat   │ │
│ │          │                                                │          │ │
│ │          │                                                │          │ │
│ │          │   ┌────────────────────────────────────────┐   │          │ │
│ │          │   │           COMMAND DECK                 │   │          │ │
│ │          │   │ [Face] [Action Grid] [End Turn]        │   │          │ │
│ │          │   │ (Sticky Bottom Center - 60%)           │   │          │ │
│ └──────────┘   └────────────────────────────────────────┘   └──────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Windows & Components Detail

### A. Center Panel
1.  **Map Window (Background/Top):**
    *   Full interactive map.
    *   **Behavior:** Can extend to 100% width if side panels are collapsed. Visible through transparent panels.
2.  **Command Deck (Bottom - Sticky):**
    *   **Dimensions:** Takes full width of the Center Panel (60% of screen).
    *   **Components:** Portrait, HP, Action Grid, End Turn.

### B. Left Panel (The "Journal")
*   **Default Tabs:**
    *   **Notes:** Rich text editor for campaign notes.
    *   **Party:** List of allies with HP/Status.
    *   **Quests:** Active quest log.

### C. Right Panel (The "Comms")
*   **Default Tabs:**
    *   **Chat:** Messages and Whispers.
    *   **Combat Log:** Roll results and damage history.
    *   **Combat View:** (See below).

### D. Combat View
*   **Purpose:** Tactical overview during fights.
*   **Location:** Often placed in Right Panel or split Center.
*   **Features:**
    *   **Initiative List:** Vertical list of all combatants (Monsters, Friends) ordered by initiative.
    *   **Status:** Shows current HP (approximate for monsters), Active Conditions.
    *   **Targeting:** Clicking a name here targets them on the map.




### Other windows to be docked: 
#### Character Sheet Window
*   **Purpose:** Character management.
*   **Components:**
    *   **Portrait:** Click to open Character Sheet.
    *   **HP:** Current hit points.
    *   **AC:** Armor Class.
    *   **Speed:** Movement speed.
    *   **Actions:** List of available actions.
#### Spellbook Window
*   **Purpose:** Magic management.
*   **Components:**
    *   **Slots:** Visual pips for available slots (Level 1: ●●○).
    *   **Prepared:** Toggle switches for preparing spells (Long Rest logic).
#### Inventory Window
*   **Purpose:** Gear management.
*   **Components:**
    *   **Equipment Slots:** Head, Body, Hands, etc. (Drag & Drop).
    *   **Backpack:** Grid or List view of items.
    *   **Currency:** Gold/Silver/Copper tracker.

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
