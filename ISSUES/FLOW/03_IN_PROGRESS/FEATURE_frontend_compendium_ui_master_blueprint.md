# Master Blueprint: Frontend Compendium UI Vertical

Status: In Progress
Owner: Frontend + API Bridge
Parent Legacy Ticket: `ISSUE_frontend_compendium_ui_vertical.md`

## Mission

Deliver a production-ready CRUD UI for compendium definitions (items, spells, monsters, actions) against the unified backend endpoint:

- `/api/compendium/definitions`

The blueprint turns one large issue into a manageable parent feature with tracked slices and subfeatures.

## Design Constraints

1. Backend is source of truth for validation and business logic.
2. Frontend focuses on editing workflows, UX, and error mapping.
3. `ActionOperationSpec` complexity is preserved (no simplified action editor mode).
4. Form resilience is required (local draft + dirty guard).

## Child Slices and Subfeatures

## Slice 1: Infrastructure and Safety

Goal: Stabilize form lifecycle and cross-form utilities.

Checklist:

- [ ] Implement `useCompendiumDraft` local draft persistence and restore.
- [ ] Implement dirty-state navigation guard for unsaved edits.
- [ ] Build `CompendiumAutocomplete` with family filter support.
- [ ] Add API error mapping utility for backend Pydantic response errors.

## Slice 2: Shared Form Atoms

Goal: Build reusable editor primitives used by all family forms.

Checklist:

- [ ] Build `DefinitionHeader` (id, title, slug, pack fields).
- [ ] Build reusable attributes/vitals/speed editor atoms.
- [ ] Build `OperationSpecBranch` tree editor for nested operation payloads.
- [ ] Add unit tests for atom-level data binding and field state updates.

## Slice 3: Family Editors and Action Side Panel

Goal: Ship primary family editors with advanced action editing path.

Checklist:

- [ ] Build `MonsterEditor` using shared atoms.
- [ ] Build `SpellEditor` using shared atoms.
- [ ] Integrate `ActionSidePanel` (wide drawer layout) for operation editing.
- [ ] Validate create/update/delete flows for at least Monster and Spell families.

## Slice 4: Refinement and Authoring Productivity

Goal: Improve authoring quality and throughput without changing core contracts.

Checklist:

- [ ] Add field-level visual error mapping from backend validation details.
- [ ] Implement action template clone flow (clean clone default).
- [ ] Add last-saved state and stay-in-editor loop.
- [ ] Add UX polish for large operation trees (expand/collapse ergonomics).

## Done Criteria for Parent Feature

1. Monster and spell authoring are production-usable end to end.
2. Action operation editing supports full nested structures in side panel.
3. Unsaved change loss is prevented through guard + local draft restore.
4. Validation feedback is explicit and field-targeted.
5. Template cloning can create a new action-based definition without id collisions.

## Suggested Test Coverage for This Feature

1. Component tests for form atom bindings and operation branch edits.
2. Integration tests for create/update cycles against mocked API responses.
3. UI behavior tests for dirty guard and draft restoration.
4. Error mapping tests for backend validation payloads.

## Dependency Notes

Primary dependency diagram artifact:

- `ISSUES/FLOW/03_IN_PROGRESS/DIAGRAM_compendium_entity_dependency_tree.md`

Key dependency conclusions from the updated diagram:

- `ActionDefinition` is treated as the template container; `ActionOperationSpec` remains the value-object execution primitive.
- Character and sheet projection dependencies are in scope for downstream editor/view planning.
- Runtime instancing (monster and actor inventory via item instances) is included as a follow-on dependency layer.

Primary backend dependencies:

- Unified compendium definitions endpoint availability.
- Stable `family` discriminator behavior.
- Stable validation error schema from backend.

Primary architecture references for later batch work:

- `ISSUES/architecture/04_module_specifications/02_content_write.md`
- `ISSUES/architecture/04_module_specifications/03_content_query.md`
- `ISSUES/architecture/04_module_specifications/05_sheets.md`
- `ISSUES/architecture/04_module_specifications/features/02_content_write_features.md`
- `ISSUES/architecture/04_module_specifications/features/03_content_query_features.md`

## Robust Frontend Compendium System Plan (April 2026)

### Cutover Mode Declaration

1. Target production path: one URL-driven compendium workspace backed only by `apiClient.compendium.*` and family-aware editor modules.
2. Legacy path bypassed: local-tab-only selection flow, mixed legacy entity clients, and always-mounted detail/modal surfaces.
3. Intentional break: remove compatibility for legacy route aliases and implicit in-memory panel state once URL-driven workbench is in place.

### Phase 0: Stability Hotfixes

1. Ensure detail drawer/dialog components fully unmount when closed (no hidden fixed overlays left in DOM).
2. Add keyboard close behavior (`Escape`) and explicit close events for all compendium overlays.
3. Add regression test coverage for open -> close -> reopen cycles across detail and editor drawers.

### Phase 1: Shell Decomposition (File Size and Ownership)

1. Split `ContentManager` into focused modules: `CompendiumWorkbenchShell`, `CompendiumWorkbenchHeader`, `CompendiumFamilyRail`, `CompendiumDefinitionPane`, and `CompendiumOverlayHost`.
2. Extract family metadata/config into registry files (`familyConfig`, column config, family labels).
3. Enforce a soft file budget of 220 lines for container components and 160 lines for leaf presentation components.

### Phase 2: URL-State Workbench

1. Canonical routes are `/content/:family`, `/content/:family/new`, and `/content/:family/:definitionId`.
2. Replace local-only selection state with route-derived state so refresh/deep-linking is deterministic.
3. Define modal/drawer policy from route state, not ad-hoc booleans, to prevent impossible states.

### Phase 3: Overlay State Machine

1. Introduce a single union-state controller for overlay modes: `none`, `detail`, `create`, `edit`, `create-pack`.
2. Guarantee mutual exclusion between overlays and formalize transition guards.
3. Encode close semantics centrally (backdrop, escape, success callback, route change).

### Phase 4: Data Loading and Performance

1. Move family data selection into one query hook (`useCompendiumFamilyData`) keyed by `(packId, family, search)`.
2. Keep backend as truth: no client-side business-rule derivation; only view-model shaping.
3. Add table virtualization for larger packs and defer raw JSON rendering until detail drawer opens.

### Phase 5: Quality Gates

1. Add unit tests for family config registry and overlay state transitions.
2. Add integration tests for route-driven open/close flows and pack switching.
3. Add a smoke test matrix that verifies each family list loads, row selection opens detail/editor correctly, close actions always return to non-overlay state, and create-pack flow returns to selected pack context.

### Definition of Done Extension

1. No compendium overlay remains mounted while closed.
2. Compendium workspace is fully deep-linkable and refresh-safe.
3. Oversized compendium host files are decomposed according to budget.
4. All family editors remain backend-contract aligned with no legacy client fallback.
