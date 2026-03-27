# V05 Planning Overview: Compendium CRUD and Definition Catalog

Status: Draft for Planning
Related module issue: ISSUE [VERT][V05]
Related playbook: docs/architecture/shared/05_vertical_module_execution_plan.md
Related diagrams:

- V05_compendium_crud_and_definition_catalog_detailed_plan.mmd
- V05_content_management_query_and_projection_detailed_plan.mmd
- test/README.md
- test/V05_test_seq_01_create_publish_spell_with_links.mmd
- test/V05_test_seq_02_update_with_replacement_chain_and_visibility_shift.mmd
- test/V05_test_seq_03_linked_entry_resolution_chain_and_cycle_denial.mmd
- test/V05_test_seq_04_search_filter_pagination_and_detail_projection.mmd
- test/V05_test_seq_05_character_sheet_viewer_linked_lookup_consistency.mmd

Detailed issue set (active module window):

- ISSUE [VERT][V05-01] baseline_and_drift_audit
- ISSUE [VERT][V05-02] definition_contract_and_validation_freeze
- ISSUE [VERT][V05-03] ownership_and_repository_boundary_lock
- ISSUE [VERT][V05-04] crud_application_orchestration
- ISSUE [VERT][V05-05] rest_ws_contract_convergence_for_content_streams
- ISSUE [VERT][V05-06] indexing_search_and_linked_entry_resolution_policy
- ISSUE [VERT][V05-07] test_matrix_and_completion_gate

## What V05 Is Trying to Achieve

V05 stabilizes content management as a deterministic backend truth stream for:

1. CRUD-complete definition catalog behavior.
2. Lifecycle-aware publishing and replacement links.
3. Linked-entry traversal with cycle-safe constraints.
4. Search and detail projection flows that support both content management views and character-sheet-linked reference lookup.

## Why V05 Is Active Now

1. Temporary production priority is content lookup and sheet support for hybrid sessions.
2. Content breadth currently carries high accidental complexity and drift risk.
3. Stabilizing V05 reduces near-term operator overhead even when combat/map automation is minimal.

## Boundaries of V05

In scope:

1. Definition-family CRUD contracts and validation policy.
2. Content lifecycle metadata and replacement-link integrity.
3. Linked-entry resolution semantics for detail and cross-reference navigation.
4. Repository boundaries and deterministic write ownership.
5. REST/WS contract convergence for content mutation and read flows.
6. Deterministic query/search/index behavior for high-volume catalogs.

Out of scope:

1. Encounter lifecycle and turn/action runtime behavior.
2. Deep frontend visual design implementation.
3. World-context runtime deepening beyond content definitions.

## Core Ownership Decisions to Lock

1. Single write authority for definition records.
2. Single write authority for content pack lifecycle metadata.
3. Single write authority for linked-entry graph updates.
4. Single indexing authority for search/read projections.
5. Single contract authority for transport payload schemas.

## Target Runtime and Service Structure

Domain targets:

1. Definition aggregate per family with lifecycle fields.
2. Content pack aggregate with publish/compatibility metadata.
3. Linked-entry graph aggregate with deterministic traversal rules.
4. Query/index aggregate for search, filter, and projection ordering.

Application targets:

1. CompendiumApplicationService orchestrates create/update/delete/publish/archive/supersede.
2. LinkedEntryResolutionService resolves forward/reverse/replacement references.
3. ContentQueryApplicationService handles deterministic list/detail/search flows.

Policy targets:

1. Definition validation policy per family and lifecycle state.
2. Reference integrity policy for missing refs, invalid families, and cycles.
3. Query policy for stable sort/filter/pagination.
4. Visibility policy for draft/published/archive transitions.

Transport targets:

1. REST contracts for list/detail and mutation operations.
2. Optional WS content events for invalidation and live refresh.
3. Stable reason taxonomy across transport surfaces.

## Detailed Content Management Pipeline

### Step A: Intake and Validation

1. Validate request envelope and entity family.
2. Validate contract fields against frozen schema.
3. Validate linked-entry references and lifecycle transition legality.

Expected denied examples:

- invalid_definition_family
- invalid_contract_shape
- invalid_lifecycle_transition
- linked_entry_missing_target
- linked_entry_cycle_detected

### Step B: Ownership and Transaction Preparation

1. Route request to canonical write authority.
2. Establish transaction boundary for definition, link, and index operations.
3. Lock revision/version guards as needed.

Expected denied examples:

- stale_content_version
- ownership_boundary_violation
- concurrent_update_conflict

### Step C: Mutation Execution

1. Persist definition mutation and lifecycle fields.
2. Persist linked-entry graph updates.
3. Apply replacement-link updates and visibility impact.

Expected denied examples:

- replacement_chain_invalid
- publish_dependency_unresolved

### Step D: Index and Query Projection Update

1. Rebuild or incrementally update index documents.
2. Refresh reverse-reference projections.
3. Stamp deterministic state revision for client parity.

### Step E: Transport Mapping

1. Emit stable REST response envelopes.
2. Emit WS content events where enabled.
3. Ensure payload parity and request correlation.

### Step F: Reader Consumption

1. Content manager list/detail views consume catalog projections.
2. Character-sheet viewer resolves linked spell/action/item entries against same catalog truth.
3. Cache invalidation follows revision and event semantics.

## Phase Plan for V05 (Using the Playbook)

### P0 Alignment and Baseline

1. Confirm current definition CRUD and linked-entry paths.
2. Confirm existing contract variants and drift.
3. Capture baseline verification and risk matrix.

Exit signal:

- Team agrees on current-state baseline and key drift risks.

### P1 Contract and Invariant Freeze

1. Freeze canonical definition contracts and lifecycle metadata.
2. Freeze linked-entry invariants and denied taxonomy.
3. Freeze compatibility policy for intentional breaks.

Exit signal:

- Contracts and invariants are stable enough for implementation.

### P2 Ownership and Persistence Boundaries

1. Assign single write authority per mutable aggregate.
2. Lock repository boundaries and transaction policy.
3. Remove ambiguous write paths.

Exit signal:

- No unresolved multi-writer ambiguity remains.

### P3 Application and Domain Implementation

1. Centralize CRUD and lifecycle orchestration.
2. Enforce policy denials consistently.
3. Produce stable mutation result envelopes.

Exit signal:

- Service behavior matches frozen contracts.

### P4 Transport and External Interfaces

1. Align REST payloads and optional WS content events.
2. Enforce reason-code parity and request correlation.
3. Document adapter mapping expectations.

Exit signal:

- Transport behavior is deterministic and converged.

### P5 Frontend Projection and Type Sync

1. Verify content-manager and sheet-viewer read paths consume backend truth.
2. Regenerate and verify shared contract artifacts.
3. Confirm cache invalidation and revision handling behavior.

Exit signal:

- Projection interfaces remain contract-stable.

### P6 Test Matrix and Observability Hardening

1. Add deterministic tests for contracts, CRUD, links, and query behavior.
2. Add parity tests for REST/WS where WS stream is enabled.
3. Validate logs and drift checks for rapid triage.

Exit signal:

- Required V05 suites are deterministic and green.

### P7 Closure and Handoff

1. Summarize completed V05 scope and residual risks.
2. Create focused follow-up issues for deferred scope only.
3. Hand off projection constraints to V06.

Exit signal:

- V05 is marked complete with verified gates.

## Recommended Initial Child-Issue Execution Order

1. V05-01 Baseline and Drift Audit.
2. V05-02 Definition Contract and Validation Freeze.
3. V05-03 Ownership and Repository Boundary Lock.
4. V05-04 CRUD Application Orchestration.
5. V05-05 REST/WS Contract Convergence for Content Streams.
6. V05-06 Indexing, Search, and Linked-Entry Resolution Policy.
7. V05-07 Test Matrix and Completion Gate.

Planning status:

- V05 child issue definitions are authored.
- Detailed architecture and query/projection diagrams are authored.
- Sequence test pack is authored for deterministic scenario coverage.

## Verification Commands (Draft)

1. docker compose --profile test run --rm backend-test pytest tests/data -q
2. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e -k compendium -q
3. docker compose --profile test run --rm -e PYTHONPATH=/app backend-test python scripts/generate_types.py --check
4. docker compose logs backend --tail=200
