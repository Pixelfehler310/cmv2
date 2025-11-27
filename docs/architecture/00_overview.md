# Architecture Manifesto V2: Open RPG Engine

## 1. The Foundation: Philosophy

We are building a **modular Virtual Tabletop (VTT)**. The core goal is an architecture that enables **modding at all levels** (Data, Logic, UI) without touching the Core Code.

### A. UI/UX Design: "Dark Fantasy Productivity"

We do not want a playful "Video Game Interface", but a **professional working environment** for GMs and Players that aesthetically fits into the Fantasy World.

- **Visual Metaphor:** A mix of a modern IDE (VS Code) and the UI of Baldur's Gate 3.
- **Styling:** Tailwind CSS for utility classes + `shadcn/ui` as the component base.
- **Layout:** Docking Layout (via `flexlayout-react`), not a rigid grid. Users can arrange windows (Chat, Character Sheet, Map), split them, and pop them out to other monitors, just like in an IDE.

### B. Backend Architecture: "Modular Monolith"

We start in a Monorepo as logically separated services that physically run in one process (for simple development) but are designed for separation into real Docker containers (Phase 3).

#### The Separation

We have two main domains that communicate only via defined interfaces:

1.  **Data Service ("The Librarian")**

    - **Task:** Management of all static definitions (Items, Spells, Monsters).
    - **Why separated?** This is the **Modding Hub**. The "Layered Mod Loader" runs here, reading, merging, and serving JSON files from the file system. It knows nothing of running campaigns or dice rules.

2.  **Logic Service ("The Game Master")**
    - **Task:** Management of the state of a running campaign. Execution of rules.
    - **Why separated?** This is the **Calculation Core**. It uses definitions from the Data Service and applies them to the current game state (e.g., calculating damage). The "Effect Engine" lives here.
