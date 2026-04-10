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
