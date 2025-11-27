# App Shell Detailed Plan

## 1. Design & Layout

The App Shell is the "OS" of our application. It provides the frame, the engine, and the utilities, but delegates the actual gameplay to the Views.

### Visual Layout (ASCII)

```
┌──────────────────────────────────────────────────────────────────────────┐
│  [Logo]  [Global Search (Ctrl+K)]           [Status] [User] [Settings]   │ <-- AppNavbar
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│                                                                          │
│                       < ViewContainer >                                  │
│                                                                          │
│           (Renders: PlayerView | DMView | CampaignEditor)                │
│                                                                          │
│                                                                          │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

[ Overlay: LoginModal (Centered, Glassmorphism) ]
[ Overlay: WikiModal (Draggable, Resizeable) ]
[ Overlay: ToastNotifications (Bottom Right) ]
```

### Components

1.  **AppNavbar (`@rpg/ui/navbar`)**
    *   **Logo:** Click to return to Campaign Selector.
    *   **Global Search:** The "Omnibar". Searches Wiki, Rules, and (future) executes commands.
    *   **Status Indicator:** Green/Yellow/Red dot for WebSocket health.
    *   **User Menu:** Avatar with dropdown (Profile, Logout).
    *   **Settings:** Opens the Global Settings Dialog.

2.  **ViewContainer (`apps/host/src/components/ViewContainer`)**
    *   **Input:** `currentView` (from State).
    *   **Logic:** Lazy loads the appropriate MFE package. Handles loading spinners and error boundaries.

3.  **Global Overlays**
    *   **LoginModal:** Simple username prompt if not authenticated.
    *   **WikiModal:** The "Encyclopedia". Can be opened over any view.
    *   **Toasts:** System notifications ("Saved", "Error", "New Message").

---

## 2. Logic & API Calls

### Authentication Service
*   **Logic:** Check for `token` in HttpOnly Cookie (or localStorage fallback).
*   **API:**
    *   `POST /auth/login` (Body: `{ username }`) -> Returns Token.
    *   `GET /auth/me` -> Returns User Profile.

### WebSocket Manager
*   **Logic:** Establish connection, handle reconnection (exponential backoff), keep-alive (heartbeat).
*   **API:**
    *   `WS /campaigns/{id}/ws`
*   **Bridge:** Exposes `send(type, payload)` to MFEs.

### Routing & View Switching
*   **Logic:** URL-based routing.
    *   `/` -> Login / Campaign Selector.
    *   `/campaign/{id}` -> Auto-detect role (DM vs Player) -> Render View.
    *   `/campaign/{id}/edit` -> Campaign Editor.

---

## 3. Communication (The Bridge Provider)

The App Shell is the **Provider** of the Bridge. It does not "request" info from MFEs; it **supplies** the infrastructure.

### Global Events (Listened to by Shell)
*   `SHOW_TOAST`: MFEs emit this to show a notification.
*   `OPEN_WIKI`: MFEs emit this to open the Wiki Modal (e.g., clicking a spell link in chat).
*   `LOGOUT`: Triggered by User Menu or 401 error.

### Information Provided to MFEs
*   `currentUser`: Who am I?
*   `campaignId`: Where am I?
*   `wsState`: Is the connection alive?
*   `bridge`: The toolset to talk to the world.

---

## 4. Backend Information Needed

To function, the Shell needs:

1.  **User Profile:** `id`, `username`, `avatar_url`, `preferences` (Theme, Keybinds).
2.  **Campaign List:** For the Selector screen. `[{ id, name, role }]`.
3.  **Permissions:** "Is this user the DM of this campaign?" (Determines which View to load).

---

## 5. Implementation Steps

1.  **Scaffold:** Create `apps/host` (Vite + React + TS).
2.  **Infrastructure:** Implement `WebSocketManager` and `AuthProvider`.
3.  **Bridge:** Implement the `IHostBridge` concrete class.
4.  **UI:** Build `AppNavbar` and `ViewContainer` using the Design System.
5.  **Integration:** Connect Auth and WS to the real backend.
