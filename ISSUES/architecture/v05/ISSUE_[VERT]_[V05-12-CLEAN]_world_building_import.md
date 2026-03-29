# ISSUE [VERT][V05-12-CLEAN]: World-Building Integration & Final SRD Data Import

Status: Planned
Owner: DevOps / Data Systems
Parent: ISSUE [VERT][V05]
Depends on: ALL V05-01 to V05-11

## Why This Exists

We have successfully engineered the V05 compendium, identity, and characters, but the backend is "Empty." To fulfill the VHTT promise of a "Ready-to-Play" experience, we must import a baseline set of rules (Systems Reference Document / SRD).

This is not just a data entry task; it is the **Final Test** of our V05 engine's ability to handle complex, deep rule graphs (e.g., Classes referencing Feats, Spells referencing Conditions).

## Implementation Steps (Actionable)

1. **Migration Tooling:**
   * Create a robust script (Alembic or standalone Python) that maps the flattened prototype data from `legacy/data` into the new V05 `DefinitionRecord` format.
2. **SRD Data Mapping:**
   * Specifically ensure that **Monster AC/HP Formulas** and **Spell ActionOperationSpecs** are correctly translated into their new polymorphic payloads.
3. **Graph Integrity:**
   * After import, run the `LinkedEntryResolutionService` over the entire `system-srd` pack to ensure there are zero broken references.
4. **Cleanup:**
   * **(CRITICAL)** Formally delete the `legacy/` directory once 100% of its data has been verified in the new V05 authoritative store.

## Scope

In Scope:
- Transformation logic from prototype flat-tables to V05 JSON-nested tables.
- Decommissioning the final bits of technical debt.

Out of Scope:
- Adding non-SRD (Homebrew) content.

## Acceptance Criteria

1. 100% of SRD rules (monsters, spells, items) are searchable in the new Compendium.
2. The legacy `legacy/data` and `legacy/campaigns` folders are deleted after successful verification.
3. The database schema is pruned of old prototype tables.
4. No regressions occur in the character sheet hydration tests when using the newly imported SRD data.

## Verification Commands

1. `docker compose --profile test run --rm backend-test pytest tests/data/migrations -k srd_integrity`
