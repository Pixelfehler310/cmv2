# App Shell Design Document

## Executive Summary

The App Shell ("The Host") is the foundational infrastructure component of the Open RPG Engine frontend. It provides the minimal necessary infrastructure for the application to function, while delegating all content and game-specific functionality to Microfrontends (MFEs). This document outlines the requirements, design principles, and implementation strategy for the App Shell.

## 1. Core Requirements

### 1.1 Functional Requirements

#### FR1: Authentication & Authorization

- **Requirement:** Manage user authentication state and JWT token lifecycle
- **Rationale:** All game data access requires authentication. The App Shell is the single point of authentication management.
- **Acceptance Criteria:**
  - User can log in/log out
  - JWT token is stored securely (httpOnly cookies preferred, localStorage as fallback)
  - Authentication state persists across page refreshes
  - Unauthenticated users are redirected to login
  - Token refresh mechanism (if backend supports it)

#### FR2: WebSocket Connection Management

- **Requirement:** Maintain the single WebSocket connection to the backend
- **Rationale:** Per architecture, only the App Shell holds the WebSocket connection. All MFEs communicate through the App Shell.
- **Acceptance Criteria:**
  - Single WebSocket connection per session
  - Automatic reconnection with exponential backoff
  - Connection state visible to user (connected/disconnected/reconnecting)
  - Message routing to appropriate MFEs via event bus
  - Graceful degradation when WebSocket unavailable

#### FR3: Action Dispatch System

- **Requirement:** Provide `dispatchAction(type, payload)` function to all MFEs
- **Rationale:** MFEs are "dumb" - they send commands, not direct API calls. The App Shell routes commands to backend.
- **Acceptance Criteria:**
  - All MFEs receive dispatchAction via context/props
  - Actions are sent via WebSocket (preferred) or HTTP fallback
  - Action queue for offline scenarios
  - Action acknowledgment/error handling

#### FR4: Client-Side Event Bus

- **Requirement:** Provide event bus for MFE-to-MFE communication
- **Rationale:** MFEs need to communicate (e.g., hover effects, selection changes) without tight coupling.
- **Acceptance Criteria:**
  - Pub/sub pattern implementation
  - Type-safe event definitions
  - Event history/audit trail (for debugging)
  - Memory leak prevention (automatic cleanup)

#### FR5: View Selection & Routing

- **Requirement:** Display either Player View or DM View based on user role and campaign selection
- **Rationale:** Player and DM have fundamentally different interfaces. Each view manages its own FlexLayout system internally.
- **Acceptance Criteria:**
  - Host determines which view to show (Player or DM) based on:
    - User role/permissions
    - Selected campaign
    - Route parameters
  - Only one view is active at a time
  - Smooth transition between views
  - View state is preserved when switching

#### FR6: Routing

- **Requirement:** Handle application-level routing
- **Rationale:** Different routes for different contexts (campaign selection, character creation, game session)
- **Acceptance Criteria:**
  - Route structure: `/`, `/campaigns`, `/campaigns/:id`, `/campaigns/:id/play` (Player view), `/campaigns/:id/dm` (DM view)
  - Route-based view switching (Player vs DM view)
  - Deep linking support
  - Browser history management
  - Campaign selection before entering game view

#### FR7: Error Boundaries & Error Handling

- **Requirement:** Catch and handle errors gracefully
- **Rationale:** Prevent one MFE crash from bringing down the entire application
- **Acceptance Criteria:**
  - Error boundary around the active view (Player or DM)
  - Error reporting/logging
  - User-friendly error messages
  - Recovery mechanisms

#### FR8: Navigation Bar

- **Requirement:** Provide global navigation and utility functions
- **Rationale:** Users need quick access to search, profile, and settings regardless of which view they're in
- **Acceptance Criteria:**
  - Search bar for Wiki (and later command palette)
  - Player/User icon with dropdown menu
  - QR code icon (placeholder for friend management - future feature)
  - Settings icon (placeholder - future feature)
  - Always visible, regardless of active view
  - Responsive design

### 1.2 Non-Functional Requirements

#### NFR1: Performance

- **Target:** App Shell should add <50ms to initial load time
- **Rationale:** App Shell is infrastructure, not content. It should be lightweight.

#### NFR2: Accessibility

- **Target:** WCAG 2.1 AA compliance
- **Rationale:** Gaming should be accessible to all users.

#### NFR3: Browser Support

- **Target:** Modern browsers (Chrome, Firefox, Safari, Edge - last 2 versions)
- **Rationale:** Balance between modern features and user base.

#### NFR4: Responsive Design

- **Target:** Support desktop (primary) and tablet (secondary) viewports
- **Rationale:** VTTs are primarily desktop tools, but tablet support enables mobile DMing.

## 2. Design Principles

### 2.1 Minimalism

**Principle:** The App Shell contains only infrastructure. No game-specific UI.

**Rationale:**

- Clear separation of concerns
- Easier to maintain and test
- MFEs can be developed independently
- App Shell changes don't affect game functionality

**Implications:**

- No character sheets in App Shell
- No monster libraries in App Shell
- No game rules or calculations
- Only infrastructure: auth, routing, communication, layout

### 2.2 Single Responsibility

**Principle:** Each component in App Shell has one clear responsibility.

**Rationale:**

- Easier to understand and maintain
- Easier to test
- Easier to replace/upgrade individual pieces

**Implications:**

- Separate components for: Header, Layout Manager, Connection Status, etc.
- No monolithic components
- Clear component boundaries

### 2.3 Type Safety

**Principle:** Strict TypeScript types for all interfaces.

**Rationale:**

- Catch errors at compile time
- Better IDE support
- Self-documenting code
- Enforces contracts between App Shell and MFEs

**Implications:**

- All MFE interfaces typed
- All event types defined
- All action types defined
- Use `@rpg/types` for shared types

### 2.4 Progressive Enhancement

**Principle:** App Shell works even if some MFEs fail to load.

**Rationale:**

- Better user experience
- Easier debugging
- Graceful degradation

**Implications:**

- Error boundaries around each MFE
- Fallback UI for missing MFEs
- Lazy loading with loading states

## 3. Architecture & Component Structure

### 3.1 MFE Architecture

#### Architecture Overview:

The Host App Shell displays **one of two main views** based on user role and campaign selection. Each view is a complete MFE with its own FlexLayout system managing multiple windows.

#### Main Views:

1. **Player View MFE** (`@rpg/player-view`)

   - **Purpose:** Complete player interface with its own FlexLayout system
   - **Internal Windows (managed by Player View's FlexLayout):**
     - Character Sheet window
     - Chat window
     - Lore/Notes window (Wiki access)
     - Inventory window
     - Actions/Combat window (during combat)
     - Additional windows as needed
   - **Responsibilities:**
     - Manage its own FlexLayout configuration
     - Handle player-specific UI and interactions
     - Display character data and actions
     - Communicate with backend via App Shell

2. **DM View MFE** (`@rpg/dm-view`)
   - **Purpose:** Complete DM interface with its own FlexLayout system
   - **Internal Windows (managed by DM View's FlexLayout):**
     - Monster window (active/planned monsters with properties)
     - Cartographer window (map - fullscreen, focused, background by default)
     - Initiative tracker window (during combat)
     - Campaign management window
     - Additional windows as needed
   - **Responsibilities:**
     - Manage its own FlexLayout configuration
     - Handle DM-specific UI and interactions
     - Display campaign state and controls
     - Communicate with backend via App Shell

#### Special Components:

3. **Cartographer** (`@rpg/cartographer`)

   - **Purpose:** Map rendering and interaction
   - **Integration:** Rendered as a window inside DM View's FlexLayout
   - **Default State:** Fullscreen, focused, background layer
   - **Technology:** PixiJS/Konva for performance

4. **Wiki** (Accessible via Navbar Search)
   - **Purpose:** Campaign notes, lore, world building
   - **Integration:** Accessed via search bar in App Shell navbar
   - **Display:** Modal/dialog overlay (not part of view FlexLayouts)
   - **Access:** Available to both Player and DM views

#### Shared Components (`@rpg/ui`):

- Item Browser (used within Player/DM view windows)
- Spell Browser (used within Player/DM view windows)
- Character Creation Form
- Campaign Creation Form
- Generic data browsers
- All reusable UI components

**Key Architectural Principle:**

- **Host App Shell** = Infrastructure only (auth, routing, WebSocket, navbar)
- **Player/DM Views** = Complete interfaces with their own layout management
- **Cartographer** = Specialized component integrated into DM View
- **Wiki** = Global utility accessible via navbar search

### 3.2 App Shell Component Hierarchy

```
App (Root)
├── AuthProvider (Context)
├── RouterProvider (React Router)
├── WebSocketProvider (Context)
├── EventBusProvider (Context)
├── ActionDispatchProvider (Context)
└── AppShell (Main Component)
    ├── AppNavbar
    │   ├── Logo/Branding (Left)
    │   ├── SearchBar (Center) - Wiki search, future: command palette
    │   ├── ConnectionStatus (Subtle indicator)
    │   └── NavbarActions (Right)
    │       ├── Player/User Icon (with dropdown)
    │       ├── QR Code Icon (placeholder - friend management)
    │       └── Settings Icon (placeholder)
    └── ViewContainer
        ├── Player View MFE (when active)
        │   └── [Player View manages its own FlexLayout with windows]
        └── DM View MFE (when active)
            └── [DM View manages its own FlexLayout with windows]
                └── Cartographer (as window in DM View's FlexLayout)
```

**Note:** Only one view (Player or DM) is rendered at a time. The Host App Shell does not manage FlexLayout - each view does.

### 3.3 Context Providers

The App Shell provides several React contexts:

1. **AuthContext**

   - `user: User | null`
   - `token: string | null`
   - `login(token, user): void`
   - `logout(): void`
   - `isAuthenticated: boolean`

2. **WebSocketContext**

   - `connectionState: 'disconnected' | 'connecting' | 'connected' | 'error'`
   - `send(message): void`
   - `subscribe(event, handler): () => void` (unsubscribe)

3. **EventBusContext**

   - `emit(event, data): void`
   - `on(event, handler): () => void` (unsubscribe)
   - `off(event, handler): void`

4. **ActionDispatchContext**

   - `dispatchAction(type, payload): Promise<ActionResult>`
   - `actionQueue: Action[]` (for offline)
   - `lastActionResult: ActionResult | null`

5. **ViewContext**
   - `currentView: 'player' | 'dm' | null`
   - `selectedCampaign: Campaign | null`
   - `switchView(view): void`
   - `canAccessView(view): boolean` (permission check)

## 4. UI/UX Design

### 4.1 Design System Integration

**shadcn/ui Components to Use:**

- `Button` - All interactive elements
- `Card` - Container for MFEs
- `Badge` - Status indicators
- `Separator` - Visual dividers
- `DropdownMenu` - User menu, context menus
- `Dialog` - Modals (login, settings)
- `Toast` - Notifications
- `Tabs` - If needed for App Shell UI (minimal)
- `Avatar` - User profile picture
- `Tooltip` - Helpful hints

**Tailwind CSS Approach:**

- Use semantic color tokens (from shadcn/ui theme)
- Consistent spacing scale
- Responsive breakpoints
- Dark mode support (via CSS variables)

### 4.2 Visual Design Principles

#### 4.2.1 Navbar Design

**Purpose:** Global navigation and utility access that's always available.

**Layout:**

- **Left:** Logo/Branding (small, unobtrusive, clickable to go home)
- **Center:** Search bar (Wiki search, future: command palette)
  - Placeholder: "Search Wiki..." or "Search or run command..."
  - Keyboard shortcut: `Ctrl+K` / `Cmd+K`
  - Shows search results in dropdown
- **Right:** Action icons
  - Connection status indicator (subtle dot, color-coded)
  - Player/User icon (avatar, dropdown menu: Profile, Logout)
  - QR code icon (placeholder, tooltip: "Friend Management - Coming Soon")
  - Settings icon (placeholder, tooltip: "Settings - Coming Soon")

**Design:**

- Height: 56px (slightly taller for search bar)
- Background: `bg-background` with subtle border-bottom
- Sticky positioning (always visible)
- No shadows or heavy styling
- Icons: 24px, with tooltips
- Search bar: Full-width in center, max-width: 600px

#### 4.2.2 View Container

**Purpose:** Container for the active view (Player or DM).

**Design:**

- Full viewport minus navbar (calc(100vh - 56px))
- No App Shell styling - views handle their own styling
- Smooth transitions when switching views
- Views manage their own FlexLayout systems internally
- Only one view rendered at a time

#### 4.2.3 Status Indicators

**Purpose:** Show system state without being intrusive.

**Components:**

- Connection status (green/yellow/red dot)
- Loading states (skeleton screens, not spinners)
- Error states (inline, not blocking)

**Design:**

- Small, subtle
- Color-coded (green = good, yellow = warning, red = error)
- Icon + tooltip for details
- Non-blocking

### 4.3 User Experience Flow

#### 4.3.1 First-Time User

1. Land on login page (if not authenticated)
2. After login, see default layout with welcome message
3. Guided tour (optional) showing how to use layout
4. Default to Player view (if player) or DM view (if DM)

#### 4.3.2 Returning User

1. Auto-login if token valid
2. Restore last used layout
3. Restore last viewed campaign/character
4. Show connection status

#### 4.3.3 Error Scenarios

1. **WebSocket Disconnected:**

   - Show subtle indicator
   - Queue actions locally
   - Auto-reconnect
   - Show notification when reconnected

2. **MFE Failed to Load:**

   - Show error boundary UI
   - Option to retry
   - Option to report error
   - Continue with other MFEs

3. **Authentication Expired:**
   - Show login dialog
   - Preserve current state
   - Restore after re-authentication

## 5. Implementation Details

### 5.1 File Structure

```
apps/host/
├── src/
│   ├── App.tsx                    # Root component
│   ├── main.tsx                   # Entry point
│   ├── index.css                  # Global styles
│   │
│   ├── components/                # App Shell components only
│   │   ├── AppNavbar/
│   │   │   ├── AppNavbar.tsx
│   │   │   ├── SearchBar.tsx
│   │   │   ├── ConnectionStatus.tsx
│   │   │   ├── UserMenu.tsx
│   │   │   ├── NavbarActions.tsx
│   │   │   └── index.ts
│   │   ├── ViewContainer/
│   │   │   ├── ViewContainer.tsx
│   │   │   ├── PlayerViewLoader.tsx
│   │   │   ├── DMViewLoader.tsx
│   │   │   └── index.ts
│   │   └── ErrorBoundary.tsx
│   │
│   ├── contexts/                  # React contexts
│   │   ├── AuthContext.tsx
│   │   ├── WebSocketContext.tsx
│   │   ├── EventBusContext.tsx
│   │   ├── ActionDispatchContext.tsx
│   │   └── LayoutContext.tsx
│   │
│   ├── lib/                       # Infrastructure libraries
│   │   ├── websocket/
│   │   │   ├── WebSocketManager.ts
│   │   │   └── types.ts
│   │   ├── eventBus/
│   │   │   ├── EventBus.ts
│   │   │   └── types.ts
│   │   ├── actions/
│   │   │   ├── ActionDispatcher.ts
│   │   │   └── types.ts
│   │   ├── view/
│   │   │   ├── ViewManager.ts
│   │   │   └── ViewTypes.ts
│   │   └── api/
│   │       └── client.ts          # HTTP client (fallback)
│   │
│   ├── routes/                    # Route definitions
│   │   ├── routes.tsx
│   │   └── RouteGuards.tsx
│   │
│   └── types/                     # App Shell specific types
│       ├── mfe.ts                 # MFE interface definitions
│       ├── view.ts                # View type definitions
│       └── navbar.ts              # Navbar/search types
│
├── public/
│   └── favicon.ico
│
├── index.html
├── package.json
├── tsconfig.json
└── vite.config.ts
```

### 5.2 View MFE Interface Contract

Player View and DM View MFEs must implement this interface:

```typescript
interface ViewMFEProps {
  // Injected by App Shell
  dispatchAction: (type: string, payload: any) => Promise<ActionResult>;
  eventBus: EventBus;
  wsState: WebSocketState;

  // View-specific props
  campaignId: string;
  userId: string;

  // Optional props
  initialData?: any;
  onError?: (error: Error) => void;
}

interface ViewMFEComponent {
  (props: ViewMFEProps): React.ReactElement;
}
```

**Note:** Each view manages its own FlexLayout internally. The Host App Shell does not control window layouts within views.

### 5.3 View Configuration

```typescript
type ViewType = "player" | "dm";

interface ViewConfig {
  type: ViewType;
  campaignId: string;
  userId: string;
  permissions: string[];
}

// Layout configuration is managed internally by each view
// Views persist their own FlexLayout configurations
```

### 5.4 Action Types

```typescript
type ActionType = "ATTACK" | "CAST_SPELL" | "USE_ITEM" | "MOVE" | "END_TURN" | "SPAWN_MONSTER" | "UPDATE_HP" | "ROLL_DICE";
// ... more action types

interface Action {
  type: ActionType;
  payload: Record<string, any>;
  timestamp: number;
  id: string;
}

interface ActionResult {
  success: boolean;
  data?: any;
  error?: string;
  actionId: string;
}
```

## 6. Testing Strategy

### 6.1 Unit Tests

- Context providers
- WebSocket manager
- Event bus
- Action dispatcher
- Layout persistence

### 6.2 Integration Tests

- MFE loading
- Action dispatch flow
- WebSocket message routing
- Layout save/restore

### 6.3 E2E Tests

- Full user flows (login → select campaign → play)
- Error scenarios
- Layout customization

## 7. Migration Plan

### 7.1 Phase 1: Refactor Current App Shell

1. Extract infrastructure from current implementation
2. Remove game-specific UI and FlexLayout management
3. Implement proper context providers
4. Add AppNavbar with search, user menu, and action icons
5. Implement ViewContainer that switches between Player/DM views
6. Add proper error boundaries around views

### 7.2 Phase 2: View MFE Integration

1. Create Player View MFE with its own FlexLayout system
2. Create DM View MFE with its own FlexLayout system
3. Integrate Cartographer as window in DM View
4. Implement Wiki search functionality in navbar
5. Test view switching and communication

### 7.3 Phase 3: Polish

1. Add proper shadcn/ui components
2. Improve error handling
3. Add loading states
4. Performance optimization

## 8. Success Criteria

The App Shell redesign is successful when:

1. ✅ No game-specific UI in App Shell
2. ✅ Navbar with search, user menu, and action icons
3. ✅ View switching (Player/DM) works correctly
4. ✅ Each view manages its own FlexLayout
5. ✅ WebSocket connection is stable
6. ✅ Error handling is graceful
7. ✅ Code is maintainable and testable
8. ✅ UI is clean and professional
9. ✅ Performance is acceptable (<50ms overhead)

## 9. Open Questions

1. **Authentication Flow:** Should we implement OAuth or stick with JWT?
2. **Offline Support:** How much offline functionality do we need?
3. **Layout Templates:** How many default layouts should we provide?
4. **MFE Versioning:** How do we handle MFE updates without breaking the App Shell?
5. **Module Federation:** When do we implement true Module Federation vs current workspace approach?

## 10. References

- [Frontend Concept](../../docs/frontend_concept.md)
- [Backend Concept](../../docs/backend_concept.md)
- [Project Vision](../../docs/project_vision.md)
- [Shared Concept](../../docs/shared_concept.md)
- [Shared Architecture](./shared-architecture.md) - Detailed architecture overview
- [shadcn/ui Documentation](https://ui.shadcn.com)
- [FlexLayout Documentation](https://github.com/caplin/FlexLayout)
