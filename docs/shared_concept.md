# Shared Concept: The Contract

## 1. The Shared Contract (`@rpg/types`)

*   **Location:** A local npm package in the monorepo (`packages/types` or similar).
*   **Content:** Contains **only TypeScript Interfaces/Types**.
*   **Purpose:** It is the binding definition of all data structures flowing between Backend and Frontend.
*   **Synchronization:**
    *   The "Truth" is defined in the Backend (Pydantic Models).
    *   Changes to the Pydantic Model must be mirrored here in TypeScript.
    *   This ensures type safety across the network boundary.

## 2. Data Flow

*   **Backend -> Frontend:** View Models (fully calculated, ready to render).
*   **Frontend -> Backend:** Commands (Actions, Intentions).
