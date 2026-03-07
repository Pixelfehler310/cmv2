# Walking Skeleton Methodology

## 1. What is a Walking Skeleton?

A "Walking Skeleton" is a minimalist, end-to-end implementation of the system. It connects all major architectural components (from the UI layer down through the state manager, across the WebSocket, into the backend rules engine, and back up to the UI) but does so with the absolute minimum amount of styling and visual complexity.

**Key Characteristics:**

- **Ugly but Functional:** Uses raw native HTML elements (`<button>`, `<ul>`, `<div>` with basic borders) instead of the polished `@civic/design-system` components.
- **State-Focused:** Prioritizes validating the data contracts and state synchronization (`Zustand` -> `WebSocket` -> `FastAPI` -> `Zustand`).
- **End-to-End Testable:** Proves that an action taken on the frontend correctly mutates the backend state and broadcasts back to the frontend.

## 2. Why use it for CMV2?

The CMV2 VTT is a highly state-driven real-time application. The complexity does not lie in rendering a pretty button, but in ensuring that the button sends the correct `ActionPayload` and correctly interprets the resulting `WsEnvelope`.

By building the walking skeleton first, we:

1. **De-risk Integration Early:** We prove the WebSocket communication and data formats before investing time in complex UI layouts.
2. **Isolate Logic Bugs:** If the `SelectionStore` or `GameStateStore` has a bug, we find it easily because there is no complex UI code obfuscating the issue.
3. **Avoid Wasted Effort:** We don't spend hours writing Tailwind classes for a component whose underlying data structure might need to change based on backend integration realities.

## 3. The Skeleton Workflow

1. **Scaffold:** Set up the basic routes and empty components.
2. **Wire State & Bridge:** Implement the `GameStateStore` and connect it to the raw WebSocket.
3. **Draft UI (Ugly):** Build raw HTML components hooked to the Zustand state.
4. **Validate:** Test the data flows (e.g., click a raw `<button>`, verify the raw JSON payload in backend logs, verify the raw UI text updates).
5. **Lock Logic:** Write snapshot/unit tests for the finalized data flows.
6. **Polish (Deferred):** Phase 2 will involve replacing the raw HTML with the `@civic/design-system` and adding animations/layouts.
