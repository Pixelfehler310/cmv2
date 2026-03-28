# ISSUE [BACKLOG]: Search Index Upgrade — PostgreSQL GIN Full-Text Search

Status: Planned
Owner: Data + Content Systems
Parent: ISSUE [VERT][V05-06]
Depends on:
- ISSUE [VERT][V05-06] (MVP search index must be live first)

## Why This Exists

V05-06 implements the search index as a denormalized SQL table using simple `LIKE`/`ILIKE` queries for the MVP. While this is sufficient for small datasets, it will not scale for large compendiums (thousands of definitions across multiple content packs).

The existing `dnd5e_compendium_definitions` table already carries a GIN index on the `payload` JSONB column (`ix_dnd5e_compendium_definitions_payload_gin`). The `dnd5e_search_index` table introduced in V05-06 should be upgraded to use PostgreSQL's native full-text search (`tsvector`/`tsquery`) with a GIN index for production-grade search performance.

## Implementation Steps

1.  **Add `tsvector` Column to `SearchIndexModel`:**
    - Add a generated `tsvector` column combining `name_normalized` and `search_blob` fields.
    - Create a GIN index on this column.

2.  **Update `SearchIndexRepository.search()` to use `tsquery`:**
    - Replace `LIKE '%term%'` queries with `to_tsquery()` / `plainto_tsquery()`.
    - Support ranking via `ts_rank()` for relevance-ordered results.

3.  **Handle SQLite Fallback for Tests:**
    - SQLite does not support `tsvector`. The repository must fall back to `LIKE`-based search when running against SQLite (test environment).
    - Use a dialect check or strategy pattern in the repository.

4.  **Benchmark:**
    - Seed 5,000+ definitions and verify sub-100ms search response times.

## Acceptance Criteria

1. Search queries on PostgreSQL use GIN-backed full-text search, not sequential `LIKE` scans.
2. SQLite test environments continue to work with fallback search logic.
3. Search results are ranked by relevance when using full-text search.

## Verification Commands
```bash
docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/content/test_search_index.py -q
```
