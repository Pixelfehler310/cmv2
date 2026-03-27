# V05 Test Sequence Diagram Pack

Status: Draft test-design artifacts for V05 backend and projection planning.

This folder contains five concrete content-management sequence diagrams intended to drive deterministic contract, CRUD, linked-entry, and projection test authoring for V05.
Each diagram includes explicit request identifiers, revision behavior, denial semantics, and projection update expectations.

Eventing policy in this test pack:

1. Public projection lane: content list/detail responses, linked-entry results, revision metadata, content mutation/lifecycle events, invalidation events.
2. Internal trace lane: contract validation stage, ownership/transaction scope checks, index updates, cycle detection checks.

## Diagram Index

1. V05_test_seq_01_create_publish_spell_with_links.mmd
   - Draft creation plus publish transition for one spell with linked entries and deterministic revision increments.
2. V05_test_seq_02_update_with_replacement_chain_and_visibility_shift.mmd
   - Supersede flow from old definition to replacement with visibility shift and replacement traversal consistency.
3. V05_test_seq_03_linked_entry_resolution_chain_and_cycle_denial.mmd
   - Linked-entry read chain success path and cycle-detection denial path.
4. V05_test_seq_04_search_filter_pagination_and_detail_projection.mmd
   - Deterministic list query, stable pagination, detail hydration, and reverse-reference projection behavior.
5. V05_test_seq_05_character_sheet_viewer_linked_lookup_consistency.mmd
   - Character-sheet-linked lookup flow with mutation-driven revision gap invalidation and targeted refetch.

## Intended Test Family Mapping

1. Seq 01 -> Contract and lifecycle transition tests.
2. Seq 02 -> Replacement-chain invariants and visibility-transition tests.
3. Seq 03 -> Linked-entry resolver integrity tests.
4. Seq 04 -> Query determinism and projection-shape tests.
5. Seq 05 -> Cross-view projection consistency and invalidation tests.

## Shared Test Invariants

1. Every mutation command has one terminal outcome (resolved, denied, or error).
2. Every successful mutation increments catalog_revision exactly once.
3. Linked-entry graph mutations are attributable to request_id.
4. Query ordering is deterministic for identical filters, revision, and cursor.
5. Revision gaps trigger explicit invalidation and resync behavior for affected scopes.
6. Character-sheet lookup follows replacement chains consistently under same revision snapshot.
