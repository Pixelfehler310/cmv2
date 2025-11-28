# Frontend Architecture: Dark Fantasy Productivity

## 1. Design Philosophy

- **Metaphor:** IDE meets Baldur's Gate 3.
- **Tech Stack:** React, Vite, Tailwind CSS, shadcn/ui., pnpm Monorepo for the MFEs
- **Layout Engine:** `flexlayout-react`.
  - **Structure:** The App Shell is a wrapper.
  - **Ownership:** Each View MFE (Player View, DM View) manages its **own** `FlexLayout` instance. This allows completely different window configurations (e.g., DM has many monitoring windows, Player has a focused sheet).

## 2. Theming Engine (Modding)

- **Mechanism:** CSS Custom Properties (Variables) in `:root`.
- **Scope:** Colors, Fonts, Spacing.
- **Modding:** Users replace a CSS file to change the entire Look & Feel (e.g., "Sci-Fi Neon"). (with tailwinds @apply should make this easily possible)

## 3. Microfrontends (MFEs) Strategy

### Phase 1: Build-Time Integration (Monorepo) (pnpm)

- **Approach:** MFEs are separate packages in the Monorepo, imported by the Host at build time.
- **Goal:** Reduce complexity while maintaining logical separation.
- **Host Responsibility:**
  - Authentication (Login, Token Management).
  - WebSocket Connection (Single pipe to backend).
  - Global Event Bus.
- **MFE Responsibility:**
  - Internal Layout (FlexLayout).
  - Feature-specific UI (Character Sheet, Monster Spawner).

### Phase 3 Vision: The "Global App Runtime"

- **Goal:** Complete independence. MFEs can be swapped or modded (even using different frameworks like Vue/Svelte).
- **Architecture:** Host exposes a **Framework-Neutral Bridge**.
  1.  **Global WebSocket Service:** Plain JS Event Emitter (not React Context).
  2.  **Global Auth Service:** Simple functions (`getToken()`, `onTokenChange()`).
  3.  **Global Data/Cache:** Framework-neutral Key/Value store with Pub/Sub. MFEs hydrate their own internal stores (e.g., React Query) from this.

## 4. State Management (Phase 1 Implementation)

- **Auth:** Host manages the JWT. It is passed to MFEs (or accessed via a shared interface) for API calls.
- **Data Fetching:** React Query (TanStack Query).
  - **Sync:** Host receives WebSocket `STATE_UPDATE`.
  - **Update:** Host invalidates/updates the query cache, triggering re-renders in MFEs.
