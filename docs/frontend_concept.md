# Frontend Concept: Microfrontends & UI

## 1. Architecture: Microfrontends (MFEs)

Organized as **Microfrontends (MFEs)** in a `pnpm` Workspace.

### A. App Shell ("The Host")

*   **Responsibility:** Layout (`FlexLayout`), Authentication (JWT), Routing.
*   **Communication Hub:**
    *   Holds the **only WebSocket connection** to the backend.
    *   Injects a `dispatchAction(type, payload)` function into the MFEs for downward communication.
    *   Provides a **Client-Side Event Bus** for communication between MFEs (e.g., hover effects).

### B. MFE: The Player Sheet (View)

*   **Responsibility:** Displaying character data. Buttons to trigger actions.
*   **Design:** Tabs for Stats, Inventory, Spells.

### C. MFE: The DM Tools (View)

*   **Responsibility:** God Mode. Spawning monsters (Drag & Drop from Library), editing HP, managing Initiative.

### D. MFE: The Cartographer (Map)

*   **Technology:** React wrapper around **PixiJS/Konva**.
*   **Responsibility:** Displaying Grid, Background, and Tokens. Sending movement commands.
*   **Rationale:** React is too slow for complex maps; WebGL-based 2D engines are required for performance.

## 2. Shared Contract (`@rpg/types`)

*   A local npm package in the monorepo containing **only TypeScript Interfaces**.
*   It is the binding definition of all data structures flowing between Backend and Frontend.
*   **Rule:** Changes to the Pydantic Model must be mirrored here.

## 3. Development Workflow

*   **Framework:** React + Vite
*   **Package Manager:** pnpm workspaces
*   **Testing:** `vitest` + `react-testing-library` for component behavior.
*   **Local Dev:** `pnpm dev` starts all Vite servers in parallel.
