# ISSUE: Frontend Compendium Leaf Bundle Plan

Status: In Progress  
Owner: Frontend + API Bridge
Parent Feature: `ISSUES/FLOW/03_IN_PROGRESS/FEATURE_frontend_compendium_ui_master_blueprint.md`
Reference Diagram: `ISSUES/FLOW/03_IN_PROGRESS/DIAGRAM_compendium_entity_dependency_tree.md`

## Goal

Define one implementation-ready plan for all leaf-first compendium entity editors so the team can build the first safe authoring wave before action-centric and runtime-heavy families.

## Legacy Cutover Declaration

1. Target production path: unified definitions CRUD against `/api/compendium/definitions` using the `family` discriminator and typed editor forms.
2. Legacy path bypassed: any family-specific legacy CRUD surface or ad-hoc editor flow outside the unified compendium editor path.
3. Intentional breaking behavior: no compatibility layer for legacy editor state shape, legacy draft keys, or legacy field aliases.

## Why These Are The Leaf Bundle

1. These families either have no content-level inbound dependencies or only bounded-world links.
2. They are the safest foundation for validating shared CRUD atoms, validation mapping, and link UX.
3. They unblock later families that depend on stable references (action, ability, spell, item, monster, character).

## In Scope

1. `lore`
2. `condition`
3. `species`
4. `background`
5. `class`
6. World cluster: `faction`, `region`, `place`

## Out Of Scope

1. `action`, `ability`, `spell`, `item`, `monster`
2. Character and sheet projection editors
3. Runtime instancing tools

## Shared Components Required In This Bundle

1. `DefinitionHeader`: `id`, `slug`, `name`, lifecycle, version, pack, provenance fields. The `id` and `slug` should be visually hidden or very small, and ideally auto-generated (e.g. from `name` or `type_name`) rather than manually typed.
2. `CompendiumAutocomplete`: A universal reference lookup component. While it supports ALL compendium types (`monster`, `character`, `action`, etc.), we will filter it down by family for specific fields. To support visual rendering of the item in the list, we will eventually need mapping functions per type; but initially, we can just display the `slug` and `name`.
3. `StringListEditor`: shared primitive for simple text lists like `skill_proficiencies` and `saving_throw_proficiencies`.
4. `ModifierSpecListEditor`: reusable list editor for configuring `ModifierSpec` payloads (these are the actual mechanic rules a condition bestows, describing fields like `+2 Strength` or `Status: grappled`).
5. `ValidationErrorMap`: maps backend Pydantic error paths to field-level UI messages.
6. `DraftGuard`: local draft persistence + unsaved change navigation guard.

## Frontend Access, Routing, And Migration Plan

The current host app already has a content entry route (`/content`) wired in `frontend/apps/host/src/App.tsx`, and the page is rendered by `frontend/apps/host/src/routes/ContentRoute.tsx` using `@rpg/management-view`'s `ContentManager`. For the new editor wave, we should keep one shell page but introduce family-specific URLs for direct navigation and bookmarking:

1. `GET /content/:family` for list + filter context (examples: `/content/species`, `/content/class`, `/content/condition`).
2. `GET /content/:family/new` for create mode.
3. `GET /content/:family/:definitionId` for detail/edit mode.

Access should come from two places: global nav (`Content Manager` in `AppNavbar`) and an internal family rail/tabs inside `ContentManager`. The internal rail should drive URL state (not just component-local tab state), so reload/deep-link always restores the same family and selected definition. This keeps each family as its own route surface while still feeling like one cohesive workspace.

Migration scope for legacy frontend requests is clear from current code:

1. `frontend/apps/player-view/src/components/CommandDeck.tsx` still calls `apiClient.definitions.species/classes/backgrounds`.
2. `frontend/packages/bridge/src/apiClient.ts` still exposes legacy groups (`definitions.*`, and older top-level `monsters/spells/items` list/get endpoints).

Cutover plan: move all read/write flows to `apiClient.compendium.*` only, with explicit `family` filtering and `pack_id` context. Keep `definitions.*` and old top-level entity clients as temporary wrappers only if needed for a short transition, then remove once all consumers are migrated. This prevents new code from reintroducing unsupported legacy paths.

For design-system quality, we already import Civic tokens globally via `frontend/packages/ui/src/globals.css` (`@civic/design-system` + components). The remaining work is consistency and interaction polish in content views:

1. Standardize on semantic tokens (`bg-surface-*`, `text-foreground`, `border-border`) and avoid ad-hoc colors in editor surfaces.
2. Build a consistent editor shell pattern: family rail (left), definition list (center), editor/detail panel (right drawer on desktop, full-screen sheet on mobile).
3. Use Civic component styles (`btn`, input/select tokens, chips/badges) for lifecycle states (`draft`, `published`, `archived`) and validation feedback.
4. Add focused motion only where meaningful: panel slide-in, optimistic save state transition, and inline field-error reveal.

This gives a clean and intuitive authoring UX while staying fully aligned with the civic design system and the backend-as-truth model.

## D&D Business Logic Specialist Analysis (Missing Entity Data)

Before we start building these editors, a domain review reveals several critical data fields missing from the current backend `pydantic` schemas (and thus missing from our frontend plan). The backend must be the source of truth, so we need to add these fields to the API contract before building the UI:

1. **Global Description / Lore Link**: Currently, `DefinitionRecord` only has `slug` and `name`. None of our mechanical entities (`class`, `species`, `condition`, etc.) have a `description` field or a pointer to `lore_id` for tooltip hover summaries in the VTT.
2. **Species**: Missing a `languages` part. While some species grant proficiencies (like "Dwarven Armor Training"), we will keep the `SpeciesDefinition` lean and handle those specific items via the **`Ability`** link system (where an `Ability` grants a `ModifierSpec`). This prevents schema bloat.
3. **Background**: Missing `tool_proficiencies`, `languages_granted`, and `starting_wealth` or `equipment` ties. Standard SRD backgrounds always provide these alongside skills. Similar to Species, specific one-off mechanical grants should be offloaded to linked `Ability` records to maintain a "Horizontal-First" architecture.
4. **Class**: Currently only has `hit_die` and `saving_throw_proficiencies`. It is missing `armor_proficiencies`, `weapon_proficiencies`, `tool_proficiencies`, and critically, `spellcasting_ability` (e.g. `CHA`, `INT`, `WIS`) to correctly route save DCs and attack bonuses for spells cast by that class. We do NOT need a list of spells here or complex "Spellcaster" flags; since any class can potentially cast spells (via subclasses or feats), we only need to define which attribute that class uses if/when it casts spells. The actual selection/assignment of spells happens at the **Character** layer.

**Note on Cross-Entity Dependency**: Armor/Weapon/Tool proficiencies and Spellcasting can come from Species, Background, OR Class.

- **Proficiencies**: These are additive (a "Set"). We will prioritize `Class` as the primary source for broad categories (e.g., "All Martial Weapons"), but allow `Ability` links on any entity to grant specific ones (e.g., "Longsword" via High Elf).
- **Spellcasting**: The `Spellcasting Ability` field on a `Class` defines the base for that class's spells. If a Species or Feat grants a spell, that specific `Ability` or `Action` record must define its own `spellcasting_ability_override` (e.g., "High Elf Cantrip (INT)") rather than relying on a global character-wide setting.

_Action Item for Backend_: Update `backend/src/systems/dnd5e/content/domain/definition_models.py` with these fields before closing this leaf bundle.

## Entity Editor Plans

### 1) LoreDefinition Editor (`family=lore`)

_(Note on `family` vs `lore_type`: A Compendium `family` strictly dictates the backend mechanical schema of the entity. The `family` is the Polymorphic Discriminator for `/api/compendium/definitions` (so the backend knows whether to parse a `lore`, a `faction`, or a `condition`). Specifically, `family="lore"` represents pure text/description. It has a property called `lore_type` (like `deity`, `history`, `myth`) which just provides a visual categorizer label for the text doc. It does NOT replace the `FactionDefinition` or `RegionDefinition`, which have their OWN distinct, separate mechanical families (`family="faction"`, etc.). It is strictly 1 Family = 1 Entity Editor.)_

Backend contract fields:

1. `lore_type`
2. `rich_text_content`

View sections:

1. Header: shared `DefinitionHeader`.
2. Type: single-select for `lore_type` (e.g., `deity`, `history`, `myth`, `journal`, `description`, etc.). The `lore_type` acts merely as an internal semantic categorization for the pure text.
3. Content: text area for `rich_text_content`. To prevent XSS, either stick to plain text for this wave or use strictly sanitized Markdown/DOMPurify. Do NOT use unsanitized raw HTML outputs.

Validation and UX rules:

1. Preserve drafts for large text entries.
2. Keep editor minimal and fast to save as baseline CRUD smoke target.
3. Rich_text_content is allowed to be empty

### 2) ConditionDefinition Editor (`family=condition`)

Backend contract fields:

1. `condition_type`
2. `has_levels`
3. `modifier_specs[]`

View sections:

1. Header: shared `DefinitionHeader`.
2. Condition metadata: `condition_type` enum and `has_levels` toggle.
3. Effects: `ModifierSpecListEditor` with add/remove/reorder.

Validation and UX rules:

1. Invalid modifier entries surface field-local errors from backend paths.
2. `has_levels` changes do not silently delete modifier rows.
3. Initial list row template should match `ModifierSpec` defaults used by backend validators.

### 3) SpeciesDefinition Editor (`family=species`)

Backend contract fields:

1. `speed`
2. `size`
3. `languages[]` _(New Backend Requirement)_
   _(Note on metadata/descriptions: Species and Classes inherently have many traits and stats. We design this architecture so that the core statblock is small, while complex rules and descriptions are offloaded to `Ability` and `Lore` references. In the future, every compendium entry will likely gain a generic `lore_id` pointer to decouple heavy rich-text descriptions from the mechanical stats context, keeping the JSON payloads small.)_

View sections:

1. Header: shared `DefinitionHeader`.
2. Core stats: numeric `speed`, text/select `size`.
3. Languages: `StringListEditor` for basic language acquisition.
4. **Under Construction**: Ability Management section. Species can grant `Ability` records (which handle Darkvision, resistances, tool proficiencies, etc.), but since the `ability` family is Out of Scope for this leaf bundle, we scaffold this section as visually disabled/hidden or placeholder for now.

Validation and UX rules:

1. `speed` must be numeric and non-negative before submit. In the UI, we should parse different text formats (e.g. `30 ft`, `6 hexes`) but serialize it back to the backend as a standardized integer (e.g. base 5-foot increments).
2. Keep layout compact to serve as a second baseline editor for shared header reuse.

### 4) BackgroundDefinition Editor (`family=background`)

Backend contract fields:

1. `skill_proficiencies[]`
2. `tool_proficiencies[]` _(New Backend Requirement)_
3. `languages[]` _(New Backend Requirement)_

View sections:

1. Header: shared `DefinitionHeader`.
2. Proficiencies & Background Stats: Three `StringListEditor` components for Skills, Tools, and Languages respectively. _(Note on skillset configurations: System-wide or campaign-scoped customized skill sets will be managed much further down the line. Right now, this assumes standard text entries like "Athletics", "Acrobatics".)_

Validation and UX rules:

1. Deduplicate entries client-side before submit.
2. Preserve entry order unless backend normalizes it.

### 5) ClassDefinition Editor (`family=class`)

_(Note regarding modifiers for Species/Class: In standard SRD 5.1/D&D models, a Class or Species does NOT carry direct `ModifierSpecs` like `+2 STRENGTH`. Instead, they grant an `AbilityDefinition` (e.g. "Dwarven Resilience"). The `AbilityDefinition` then holds the `ModifierSpecs`. This prevents the Class or Species root schema from becoming a chaotic mess of unrelated mechanical hooks.)_

Backend contract fields:

1. `hit_die`
2. `spellcasting_ability` (optional, e.g. INT/WIS/CHA) _(New Backend Requirement)_
3. `saving_throw_proficiencies[]`
4. `armor_proficiencies[]` _(New Backend Requirement)_
5. `weapon_proficiencies[]` _(New Backend Requirement)_

View sections:

1. Header: shared `DefinitionHeader`.
2. Core Mechanics: `hit_die` validated text input, and an enum/dropdown for `spellcasting_ability` (None, STR, DEX, CON, INT, WIS, CHA).
3. Proficiencies: `StringListEditor` controls for `saving_throw_proficiencies`, `armor_proficiencies`, and `weapon_proficiencies`.
4. **Under Construction**: Ability Management section. Classes grant `Ability` records at certain levels. Since the `ability` family is Out of Scope for this wave, this part will just be a mocked or disabled placeholder section.

Validation and UX rules:

1. Hit die input shows backend-originated format errors inline.
2. Saving throw list supports keyboard-first entry flow.

### 6) World Cluster Editors (`faction`, `region`, `place`)

Reason handled together:

1. These three are cyclic and need coordinated reference UX from day one.

#### 6a) FactionDefinition (`family=faction`)

Backend contract fields:

1. `alignment`
2. `influence_tier`
3. `base_region_id`

View sections:

1. Header: shared `DefinitionHeader`.
2. Faction metadata: alignment + influence tier select.
3. Region link: `CompendiumAutocomplete` filtered to `region` for `base_region_id`.

#### 6b) RegionDefinition (`family=region`)

Backend contract fields:

1. `climate`
2. `governing_faction_id`
3. `place_ids[]`

View sections:

1. Header: shared `DefinitionHeader`.
2. Region metadata: climate input.
3. Faction link: `CompendiumAutocomplete` filtered to `faction`.
4. Places: repeatable `CompendiumAutocomplete` filtered to `place`.

#### 6c) PlaceDefinition (`family=place`)

Backend contract fields:

1. `region_id`
2. `place_type`
3. `controlling_faction_id`

View sections:

1. Header: shared `DefinitionHeader`.
2. Place type: enum select.
3. Region/faction links: two `CompendiumAutocomplete` controls.

World cluster validation and UX rules:

1. Support unresolved link states gracefully if referenced records are archived/missing.
2. Surface cyclic-link mistakes as validation errors, not hard client-side blocks.
3. Do not auto-write reverse links; backend remains source of truth for integrity policy.

## Integrity and Deletion Strategy (Removal Strategy)

When a dependent entity (like an `Action` used by a `Monster` or `Character`) is deleted, VTTs and standard content systems employ specific strategies to avoid breaking existing data:

1. **Soft Deletes (Archiving)**: Instead of wiping the entity from the database, the backend updates `lifecycle_state` from `active` to `archived`.
   - **Effect:** The item still exists for any Character/Monster referencing it, but it no longer appears in general compendium search for _new_ creations.
2. **Copy-on-Write (Embedding)**: When pulling an item into a character's inventory (e.g. `ItemInstance`), `ActorInstance` will snapshot core stat data or gracefully tolerate missing master-template IDs when rendering historically equipped gear.
3. **Pre-Delete Integrity Check (Blocking/Warning)**: If a user tries to _hard delete_ an entity, the backend checks the `LinkedEntryReference` table. If the entity is a target for inbound links, the API rejects the DELETE with a `409 Conflict` (or standard `CompendiumErrorCode`) error, forcing the user to Archive instead, or update the dependencies.

_For this Leaf Bundle_, the Frontend simply needs to support graceful degradation. If a linked reference ID is not found, the UI should render a missing state (e.g. `[Unknown Faction]`) instead of crashing.

## Build Order Inside This Issue

1. Shared bundle primitives (`DefinitionHeader`, `StringListEditor`, validation map, draft guard).
2. Lore and Species editors as low-complexity smoke path.
3. Background and Class editors for list patterns.
4. Condition editor for `ModifierSpec` complexity.
5. World cluster trio (`faction`, `region`, `place`) at the very end.

## Acceptance Criteria

1. Each in-scope family has create, edit, and delete UI connected to unified compendium endpoint.
2. Backend validation errors are rendered at field-level for all in-scope families.
3. Local draft restore + dirty guard works consistently across all in-scope editors.
4. World cluster link fields use family-scoped autocomplete and round-trip IDs correctly.
5. No compatibility adapter is introduced for legacy editor contracts.

## Verification

1. Run frontend tests covering each editor form submit and backend error mapping.
2. Perform manual CRUD smoke checks for all in-scope families in Docker frontend/backend runtime.
3. Validate that `faction`, `region`, and `place` links can be created and updated without client-side integrity drift.

## Dependencies

1. Stable backend polymorphic `/api/compendium/definitions` behavior.
2. Stable backend validation error payload shape.
3. Availability of family-filtered search endpoint behavior needed by autocomplete.
