# ISSUE [CORE][TECH-DEBT]: WebSocket Dispatcher Modularization

Status: Backlog
Owner: Architecture / Core Systems
Parent: V00

## Why This Exists

Currently, `ws_dispatcher.py` binds a campaign connection to exactly one `ISystemHandler` (e.g., `Dnd5eWsHandler`). This handler is responsible for everything: combat logic, movement, session management, and chat.

As we scale to other game systems (e.g., Pathfinder) or add global VTT features (Sound, Fog of War, generic Chat), this monolithic approach will lead to massive code duplication and "God Object" anti-patterns.

## Proposed Changes

### 1. Refactor `WsDispatcher`
-   Implement a **Multi-Handler Registry**.
-   Allow the dispatcher to route messages to multiple independent handlers based on the message `type` or a prefix.
-   Move from `_get_handler(game_system)` to a list/registry of handlers.

### 2. Extract Generic Chat Handler
-   **Requirement**: Create a `GlobalChatWsHandler` that is independent of any specific RPG game system.
-   **Multiplexing**: This handler should process all `chat_message` types regardless of whether the campaign is D&D 5e or Pathfinder.
-   **Consistency**: Ensure that chat history, mentions, and formatting remain consistent across the platform.

### 3. Modular System Handlers
-   `Dnd5eWsHandler` should only contain logic specific to D&D (Action Economy, Spell resolution, etc.).
-   Cross-cutting concerns like "Ping/Pong" or "Session Sync" should move to a `CoreWsHandler`.

## Acceptance Criteria

1.  `WsDispatcher` correctly routes messages to multiple registered handlers.
2.  Chat functionality works identical in D&D 5e and a theoretical Pathfinder mock without code duplication.
3.  The `Dnd5eWsHandler` file size is reduced by moving non-combat logic to global handlers.
4.  Visibility rules (`DM_ONLY`, `ACTOR_OWNER`) are respected across all modular handlers.

## Verification
1.  Connect to a D&D campaign via WS.
2.  Verify chat message still broadcasts.
3.  Verify combat action still processes.
4.  Mute the D&D handler and verify chat still works (proving modularity).
