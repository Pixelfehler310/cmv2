# ISSUE [VERT][V05-08]: Character Domain Decoupling & Foreign Key Removal

Status: Planned
Owner: Campaign Systems
Parent: ISSUE [VERT][V05]
Depends on: ISSUE [VERT][V05-04]

## Why This Exists

Currently, the `Character` table in `backend/src/campaigns/lib/character.py` uses strict SQL `ForeignKey` constraints directly to individual definition tables (e.g., `species_id` -> `species.id`). 

This creates a high-severity architectural violation for several reasons:
1. **Lifecycle Blocking**: We cannot `ARCHIVE` or `DELETE` a content definition if a character sheet references it, as the database engine will block the operation or cascade-delete the character.
2. **Namespace Pollution**: The Campaign Domain (Characters) is hard-coupled to the Compendium Logic, preventing us from running the Compendium as a separate service or using a different storage engine (e.g., NoSQL) for definitions.
3. **Version Fragility**: Characters are forced to point to a specific row ID. If we want a character to stay on "Version 1" of a class while a "Version 2" is released, the current relational mapping makes this extremely complex to manage.

## Implementation Steps (Actionable)

1. **Refactor SQLAlchemy Models:**
   * Remove `ForeignKey` constraints from `class_id`, `species_id`, and `background_id` in `Character` models.
   * Rename fields to `class_def_id`, `species_def_id`, etc., to signify they are V05 Definition IDs rather than DB Primary Keys.
2. **Update Service Layer:**
   * Modify the character loading logic to use the `LinkedEntryResolutionService` to fetch the definition data at runtime.
   * Implement a "Resolution Policy" that handles cases where a referenced definition is missing or archived (e.g., fallback to a 'Legacy Placeholder' or return a validation error).
3. **Migration Plan:**
   * Create an Alembic migration to drop the FK constraints while preserving the data (IDs).
4. **Validation:**
   * Ensure that deleting a `DefinitionRecord` in the Compendium does not trigger a DB exception in the Campaign domain.

## Scope

In Scope:
- `backend/src/campaigns/lib/character.py` refactoring.
- Removal of strict DB-level coupling between Campaign and Compendium.

Out of Scope:
- Refactoring the entire character sheet UI.
- Implementing the full "Prepared Spells" logic (covered in V05-11).

## Acceptance Criteria

1. Character models no longer contain SQL `ForeignKey` references to `CompendiumDefinitionModel`.
2. All character-to-definition links are managed as "Weak References" (string IDs).
3. Runtime resolution successfully fetches the correct `DefinitionRecord` using the Compendium Read Path.
4. Unit tests confirm that "Dangling References" (orphaned definitions) are handled gracefully without crashing the character sheet.

## Verification Commands

1. `docker compose --profile test run --rm backend-test pytest tests/campaigns -k model_integrity`
