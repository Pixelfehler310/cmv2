# Campaign Creator Detailed Plan

## 1. UX Philosophy: "The Architect's Blueprint"

**Goal:** "Visual Storytelling."
DMs often think in flowcharts ("If players go to the cave -> Encounter A. If they go to town -> Shop B"). This view provides a canvas to map that out visually.

### Core Principles
1.  **Non-Linearity:** Campaigns aren't books; they are graphs. The UI should reflect this.
2.  **Drill-Down:** A node represents a high-level concept (e.g., "Boss Fight"). Double-clicking it opens the detailed editor for that specific encounter.
3.  **Living Document:** This isn't just for planning; the DM can use this view during the game to track where the party is in the story.

---

## 2. Design & Layout

**Layout Strategy:** "Infinite Canvas".
A full-screen zoomable/pannable canvas (using `reactflow` or similar) with floating toolbars.

### Visual Layout (ASCII)

```
┌──────────────────────────────────────────────────────────────────────────┐
│ [Logo]  [ Campaign Name ] [Save Status]           [Status] [User] [Exit] │ <-- AppNavbar (Simplified)
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  [ Toolbar ]                                                             │
│  [ + Scene ]          ( Infinite Canvas )                                │
│  [ + Fight ]                                                             │
│  [ + Note  ]                ┌─────────┐                                  │
│  [ + NPC   ]                │ Start   │──┐                               │
│                             └─────────┘  │                               │
│                                          ▼                               │
│                                     ┌─────────┐      ┌─────────┐         │
│                                     │ Village │─────▶│ Forest  │         │
│                                     └─────────┘      └─────────┘         │
│                                          │                               │
│                                          ▼                               │
│                                     ┌─────────┐                          │
│                                     │ Dungeon │                          │
│                                     └─────────┘                          │
│                                                                          │
│                                                                          │
│                  [ MiniMap ]                                             │
│                  [  [ ]    ]                                             │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Nodes & Components

### A. The Canvas (`reactflow`)
*   **Interaction:** Pan (Right-click drag), Zoom (Scroll), Select (Click), Connect (Drag from handle).
*   **Minimap:** Bottom right for navigation.

### B. Node Types

#### 1. Scene Node
*   **Visual:** Thumbnail of the map/background.
*   **Data:** Links to a specific Scene ID (Map + Walls + Lighting).
*   **Action:** Double-click opens the **Scene Editor** (Map drawing tool).

#### 2. Encounter Node
*   **Visual:** Crossed Swords icon. Difficulty Badge (Easy/Hard/Deadly).
*   **Data:** List of Monsters, XP calculation.
*   **Action:** Double-click opens the **Encounter Builder** (Monster selection).

#### 3. Note / Narrative Node
*   **Visual:** Scroll icon. Title.
*   **Data:** Rich text (GM notes, dialogue snippets).
*   **Action:** Expands to show full text.

#### 4. NPC Node
*   **Visual:** Portrait.
*   **Data:** Name, Role, Quick Stats.
*   **Action:** Double-click opens **NPC Designer**.

### C. The Inspector Panel (Right - Slide-over)
*   **Purpose:** Edit properties of the selected node without leaving the canvas.
*   **Content:**
    *   *Scene Selected:* Name, Music Playlist, Grid Settings.
    *   *Encounter Selected:* Monster List, Total XP, Loot.

---

## 4. Logic & API Calls

### State Management
*   **Graph State:** `useNodesState`, `useEdgesState` (from React Flow).
*   **Dirty Checking:** Track changes to prompt for save (or auto-save).

### API Calls (via Bridge)
*   **Save Graph:** `PUT /campaigns/{id}/graph` (Saves the JSON structure of nodes/edges).
*   **Load Graph:** `GET /campaigns/{id}/graph`.
*   **Create Asset:** `POST /scenes`, `POST /encounters` (When a new node is dropped).

---

## 5. Integration with DM View

This "Creator" view is the *planning* side. The "DM View" is the *playing* side.
*   **Transition:** When the DM clicks "Launch Session" in the Creator, they are taken to the DM View.
*   **Runtime Usage:** The DM View can open a "Story Map" window which renders this graph read-only, allowing the DM to see where they are.

---

## 6. Backend Information Needed

1.  **Campaign Graph Storage:** A JSON blob column in the Campaign table (simplest start).
2.  **Asset Linking:** The graph needs to store IDs of Scenes/Monsters that exist in the DB.
