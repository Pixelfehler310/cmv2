# Shared Architecture Document

This document clarifies the shared understanding of the frontend architecture, particularly the relationship between the App Shell and Views.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    App Shell (Host)                      │
│  ┌───────────────────────────────────────────────────┐  │
│  │              AppNavbar (Global)                    │  │
│  │  [Logo] [Search] [Status] [User] [QR] [Settings]  │  │
│  └───────────────────────────────────────────────────┘  │
│                                                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │            ViewContainer                           │  │
│  │                                                    │  │
│  │  ┌──────────────────────────────────────────────┐ │  │
│  │  │     Player View MFE (when active)            │ │  │
│  │  │  ┌────────────────────────────────────────┐  │ │  │
│  │  │  │  FlexLayout (managed by Player View)   │  │ │  │
│  │  │  │  ┌──────────┐ ┌──────────┐ ┌────────┐ │  │ │  │
│  │  │  │  │Character │ │  Chat    │ │ Lore   │ │  │ │  │
│  │  │  │  │  Sheet   │ │          │ │        │ │  │ │  │
│  │  │  │  └──────────┘ └──────────┘ └────────┘ │  │ │  │
│  │  │  │  ┌──────────┐ ┌──────────┐            │  │ │  │
│  │  │  │  │Inventory │ │ Actions  │            │  │ │  │
│  │  │  │  └──────────┘ └──────────┘            │  │ │  │
│  │  │  └────────────────────────────────────────┘  │ │  │
│  │  └──────────────────────────────────────────────┘ │  │
│  │                                                    │  │
│  │  ┌──────────────────────────────────────────────┐ │  │
│  │  │     DM View MFE (when active)                │ │  │
│  │  │  ┌────────────────────────────────────────┐  │ │  │
│  │  │  │  FlexLayout (managed by DM View)       │  │ │  │
│  │  │  │  ┌──────────────────────────────────┐  │ │  │
│  │  │  │  │  Cartographer (Fullscreen)       │  │ │  │
│  │  │  │  │  (Background, focused by default)│  │ │  │
│  │  │  │  └──────────────────────────────────┘  │ │  │
│  │  │  │  ┌──────────┐ ┌──────────┐ ┌────────┐ │  │ │  │
│  │  │  │  │ Monsters │ │Initiative│ │Campaign│ │  │ │  │
│  │  │  │  └──────────┘ └──────────┘ └────────┘ │  │ │  │
│  │  │  └────────────────────────────────────────┘  │ │  │
│  │  └──────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Key Principles

### 1. App Shell Responsibilities
- **Infrastructure Only:** Authentication, routing, WebSocket, event bus, action dispatch
- **Global Navigation:** Navbar with search, user menu, utilities
- **View Switching:** Determines which view (Player/DM) to display
- **No Layout Management:** Does NOT manage FlexLayout for views

### 2. View Responsibilities
- **Complete Interface:** Each view is a full-featured MFE
- **Own Layout Management:** Each view manages its own FlexLayout system
- **Window Management:** Views create, arrange, and persist their own windows
- **View-Specific Logic:** All game logic and UI specific to that role

### 3. Component Hierarchy

#### App Shell Components
- `AppNavbar` - Global navigation bar
- `ViewContainer` - Container that switches between views
- `PlayerViewLoader` - Loads Player View MFE
- `DMViewLoader` - Loads DM View MFE

#### Player View Windows
- Character Sheet
- Chat
- Lore/Notes
- Inventory
- Actions/Combat

#### DM View Windows
- Cartographer (map - fullscreen by default)
- Monsters
- Initiative Tracker
- Campaign Management
- Additional windows as needed

### 4. Special Components

#### Cartographer
- **Type:** Component (not standalone MFE)
- **Location:** Window inside DM View's FlexLayout
- **Default State:** Fullscreen, focused, background layer
- **Technology:** PixiJS/Konva

#### Wiki
- **Type:** Global utility
- **Access:** Via navbar search bar
- **Display:** Modal/dialog overlay
- **Availability:** Both Player and DM views

## Data Flow

```
User Action → View Window → dispatchAction() → App Shell → WebSocket → Backend
                                                                    ↓
Backend → WebSocket → App Shell → Event Bus → View → Window Update
```

## Layout Persistence

- **App Shell:** Does NOT persist layouts
- **Player View:** Persists its own FlexLayout configuration
- **DM View:** Persists its own FlexLayout configuration
- **Storage:** Each view stores its layout in localStorage with view-specific keys

## View Switching

1. User selects campaign or navigates to route
2. App Shell determines view type (Player/DM) based on:
   - User role/permissions
   - Campaign settings
   - Route parameters
3. App Shell unmounts current view (if any)
4. App Shell mounts appropriate view
5. View loads and restores its saved layout
6. View initializes its FlexLayout with windows

## Future Considerations

- **Module Federation:** Views could be loaded from external URLs
- **View Plugins:** Additional windows could be added dynamically
- **Layout Templates:** Views could offer preset layouts (e.g., "Combat Layout")
- **Multi-View:** Future possibility of split-screen Player/DM view (advanced)

