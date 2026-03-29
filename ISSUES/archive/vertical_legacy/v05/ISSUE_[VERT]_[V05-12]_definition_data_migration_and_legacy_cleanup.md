# ISSUE [VERT][V05-12]: Final Data Migration & Legacy Cleanup

Status: Planned
Owner: DevOps / Data Systems
Parent: ISSUE [VERT][V05]
Depends on: ALL V05-01 to V05-11

## Why This Exists

We have successfully engineered a new, "World-Class" compendium system, but our existing "Live" data is still trapped in the legacy V01/V02 tables (`spells`, `monsters`, `items`). 

To avoid the overhead of maintaining two parallel storage systems and to fulfill the V05 promise of a "Single Source of Truth," we must execute a one-way migration and decommission the old tables.

## Implementation Steps (Actionable)

1. **Migration Script Development:**
   * Write a robust Python script to:
     * Read from `legacy_monsters`, `legacy_spells`, etc.
     * Transform data into the V05 `DefinitionRecord` format (e.g., converting `hit_points` to `hit_points_formula`).
     * Assign them to a `system-srd` Content Pack.
     * Upsert into the new `compendium_definitions` table.
2. **Dry Run & Validation:**
   * Execute the migration on a staging database and run the V05-07 test suite against the migrated data.
3. **Cut-over:**
   * Update all remaining legacy code paths to point to the new table.
4. **Decommissioning:**
   * Issue a "DROP TABLE" for the legacy relational tables once 100% verification is achieved.

## Scope

In Scope:
- Data transformation logic.
- Migration scripts (Alembic or standalone).
- Removal of legacy SQLAlchemy models in `backend/src/data/lib/`.

Out of Scope:
- Cleaning up frontend code (this is a backend-focused cleanup).

## Acceptance Criteria

1. 100% of legacy rule content is successfully migrated to the new schema.
2. The old `monsters`, `spells`, and `items` tables are removed from the database schema.
3. No "FOREIGN KEY" violations occur during the drop (ensuring V05-08 was successful).
4. System performance tests show no regressions when querying the unified definition table.

## Verification Commands

1. `docker compose --profile test run --rm backend-test pytest tests/data/migrations`
