# ISSUE: Compendium CRUD UI Vertical

**Status:** DRAFT (Discussion in Progress)

## 1. Goal

Provide a production-ready UI for creating, reading, updating, and deleting (CRUD) all 5.1 SRD-compatible definitions (Items, Spells, Monsters, Actions, etc.) using the existing Unified Compendium API.

## 2. Technical Context (Backend "Gold")

- **Endpoint:** `/api/compendium/definitions`
- **Pattern:** Polymorphic Discriminator via `family` field.
- **Complex Logic:** `ActionOperationSpec` nested inside Speels, Items, and Monsters determines how the future combat engine will execute these nodes.
- **Linking:** Definitions use UUIDs for `id` and slugs for human-readable references.

## 3. UI Discussion Log & Decisions

- **Decision (v1):** Prioritize the **Creator UIs** (CRUD) over the Player Interaction/Combat UI.
- **Decision (v2):** **Static View Architecture**: Dedicated forms for each major family (`MonsterForm`, `SpellForm`, etc.) but sharing low-level atoms (Attributes, Speed, Vitals).
- **Decision (v3):** **Advanced Actions Editor**: Actions use a specialized standalone component/dialog. No "simple mode"—full `ActionOperationSpec` complexity is exposed. Support for **Action Templates** (cloning an existing action definition to a new ID) is required.
- **Decision (v4):** **Smart Autocomplete Linker**: Unified `CompendiumAutocomplete` component used for all reference links. Support for dynamic filters (e.g., `family=condition` when selecting spell effects). Display uses the string ID for now; preview/name mapping is a deferred feature.

- **Decision (v5):** **Action Template Workflow**: "Clean Clone" is the default. UUIDs are regenerated, and metadata is cleared. Action superseding is deferred/out of scope for now.
- **Decision (v6):** **Live Validation**: Frontend validation (Zod/Hook Form) is the target, but the initial MVP will rely on backend error mapping to speed up development. [Backlogged: Comprehensive UI Pre-save Validation].

- **Decision (v7):** **Action Editor Layout**: **Wide Side-Panel (Drawer)**. To accommodate tree-like `OperationSpecs`, the panel will be wide (approx. 40-50% screen width). Advanced feature: Add "Expand to Fullscreen" or "Context Preview Service" in later versions.
- **Decision (v8):** **Persistence & Safety**:
  - **Local Drafts**: Form state is mirrored to `localStorage` to survive accidental tab closes.
  - **Dirty State Guard**: UI displays a "Unsaved Changes" confirmation dialog if the user attempts to navigate away with modified state.
- **Decision (v9):** **Post-Save Workflow**: "Stay and Tweak". Saving does not navigate away; it updates the "Last Saved" timestamp and allows iterative editing. Manual closure is required to return to the browser.

## 6. Phase-Based Roadmap (Production Blueprint)

1.  **Phase 1 (Infrastructure):**
    - `useCompendiumDraft`: Hook for `localStorage` sync and dirty-checking.
    - `CompendiumAutocomplete`: Filtered search component.
2.  **Phase 2 (Form Atoms):**
    - Reusable `DefinitionHeader`: ID, Title, Slug, Pack selection.
    - `OperationSpecBranch`: Tree-renderer for Attack/Save/Heal payloads.
3.  **Phase 3 (Implementation):**
    - `MonsterEditor` & `SpellEditor` static forms.
    - `ActionSidePanel` integration.
4.  **Phase 4 (Refinement):**
    - Validation error highlight (mapping Pydantic errors to fields).
    - Template cloning browser.
