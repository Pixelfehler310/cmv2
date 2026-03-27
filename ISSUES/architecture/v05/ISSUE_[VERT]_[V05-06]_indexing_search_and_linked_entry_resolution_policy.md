# ISSUE [VERT][V05-06]: Indexing, Search, and Linked-Entry Resolution Policy

Status: Planned
Owner: Data + Content Systems
Parent: ISSUE [VERT][V05]
Depends on:

- ISSUE [VERT][V05-05]

## Why This Exists

Content management value depends on fast lookup and trustworthy references.
This issue defines deterministic indexing and linked-entry resolution semantics that power compendium navigation and character-sheet viewer lookups.

## Scope

In scope:

- Define index document shape for scoped definition families.
- Define query semantics:
  - global search
  - family filter
  - level/school/type filters
  - pagination and sort stability
- Define linked-entry resolver behavior:
  - forward references
  - reverse references
  - replacement chains
  - cycle detection and denial
- Define cache invalidation policy for content mutations.

Out of scope:

- UI-level ranking experiments and cosmetic search controls.
- Runtime combat-state indexing.

## Deliverables

1. Index schema and rebuild/incremental update policy.
2. Query semantics specification with deterministic ordering requirements.
3. Linked-entry resolution contract including cycle and missing-reference handling.
4. Invalidation and consistency policy across list/detail/viewer caches.

## Acceptance Criteria

1. Query results are deterministic for equivalent input and revision.
2. Linked-entry resolution is deterministic and denial-coded for invalid graphs.
3. Replacement-link traversal behavior is explicit and testable.
4. Index and resolver policies support character-sheet-linked compendium lookups.

## Verification Commands

1. docker compose --profile test run --rm backend-test pytest tests/data -k search -q
2. docker compose --profile test run --rm backend-test pytest tests/data -k reference -q
3. docker compose --profile test run --rm -e PYTHONPATH=/app backend-test python scripts/generate_types.py --check
4. docker compose logs backend --tail=200

## Risks and Notes

- Non-deterministic ordering will break pagination and diff-based UI updates.
- Incomplete cycle handling can create unbounded linked-entry traversal.
