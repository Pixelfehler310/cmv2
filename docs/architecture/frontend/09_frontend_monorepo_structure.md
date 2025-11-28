# Frontend Architecture & Monorepo Structure

## 1. Overview

We have migrated to a **pnpm workspace** structure to manage the complexity of multiple Microfrontends (MFEs) and shared packages. This ensures strict dependency management and faster builds.

### Directory Structure

```
frontend/
├── apps/                  # Deployable Applications (MFEs)
│   ├── host/              # The App Shell (Main Entry Point)
│   ├── player-view/       # (Planned) Player MFE
│   └── dm-view/           # (Planned) DM MFE
│
├── packages/              # Shared Libraries
│   ├── bridge/            # Communication Interfaces & Types
│   └── ui/                # Design System (Tailwind + Components)
│
├── package.json           # Root workspace config
└── pnpm-workspace.yaml    # Workspace definition
```

## 2. Components & Responsibilities

### Apps

#### **1. App Shell (`apps/host`)**
*   **Role:** The "Operating System" of the VTT.
*   **Responsibilities:**
    *   **Authentication:** Logs the user in and stores the token.
    *   **Routing:** Decides which MFE to show based on URL and User Role.
    *   **Connectivity:** Manages the persistent WebSocket connection to the backend.
    *   **Global UI:** Renders the Navbar, Settings, and Global Search.
*   **Tech:** React, Vite, React Router, TanStack Query.

### Packages

#### **1. Bridge (`packages/bridge`)**
*   **Role:** The "Contract" between the Host and the MFEs.
*   **Content:**
    *   `IHostBridge`: The interface injected into every MFE.
    *   `IEventBus`: Type definitions for inter-MFE events.
    *   `UserProfile`, `IConnectionState`: Shared data types.
*   **Why?** Allows MFEs to be developed independently of the Host's implementation details.

#### **2. UI Library (`packages/ui`)**
*   **Role:** The Shared Design System.
*   **Content:**
    *   **Tailwind Config:** Shared colors, fonts, and animations.
    *   **CSS Variables:** The 3-layer theming system (Primitives -> Semantics -> Components).
    *   **Components:** Reusable atoms (Button, Input, Card) built with `shadcn/ui`.

## 3. Routing & Integration

### Current Routes (Host)

| Route | Component | Description |
| :--- | :--- | :--- |
| `/` | `LoginRoute` | Entry point. Simple username login. |
| `/campaigns` | `CampaignSelectorRoute` | Grid of available campaigns. |
| `/session/:id` | `SessionRoute` | The Game View. Mounts the `ViewContainer`. |

### MFE Integration Strategy

Currently (Phase 1), MFEs are integrated at **Build Time**.

1.  **Development:** MFEs are developed as local packages or components within the monorepo.
2.  **Runtime:** The `ViewContainer` in `apps/host` imports them (lazy loaded).

```tsx
// apps/host/src/components/shell/ViewContainer.tsx

// Future:
// const PlayerView = React.lazy(() => import('@rpg/player-view'));

const renderView = () => {
  switch (viewType) {
    case 'player': return <PlayerView bridge={bridge} />;
    case 'dm': return <DMView bridge={bridge} />;
  }
}
```

## 4. Data Flow

1.  **Backend** sends data via WebSocket.
2.  **Host** (`WebSocketManager`) receives message.
3.  **Host** updates `React Query` cache or emits Event via `Bridge`.
4.  **MFE** observes data change and re-renders.
