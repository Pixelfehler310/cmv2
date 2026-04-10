# ISSUE: Content Import/Export and Bulk Operations

Status: Backlogged
Owner: Architecture
Vertical: [V04 Content Schema and Pack Lifecycle](../../docs/archive/planning_legacy/docs_architecture/shared/05_vertical_module_execution_plan.md)

## Goal

Provide a robust mechanism for users to migrate, back up, and bulk-load content into the D&D engine. This covers both individual items and entire campaign worlds/repositories.

## Scope

- **JSON Import/Export**: Standardized JSON format for single definitions (Monsters, Items, Spells).
- **Bulk Import (Campaigns)**: Support for loading full homebrew campaigns as a single monolithic JSON file.
- **Repository Import (ZIP)**: Support for importing a ZIP file containing a structured directory of JSON entries (mimicking the internal content pack structure).
- **Validation**: Strict schema validation during bulk import to ensure data integrity.

## Proposed Components

- `backend/src/services/bulk_import_service.py`
- `backend/src/routers/import_export_router.py`
- `frontend/apps/admin-view/src/components/ImportExportDialog.tsx`

## Tasks

1. Define the "Mega-JSON" schema for full campaign exports.
2. Implement ZIP extraction and recursive JSON processing for bulk pack loads.
3. Add backend endpoints for bulk upload with progress reporting (WS or polling).
4. Implement frontend UI for selecting and uploading import packages.

## Definition of Done

1. A full "Homebrew Repository" ZIP can be uploaded and correctly populates the Compendium.
2. A single JSON export of a campaign can be re-imported without data loss.
3. Schema violations in bulk imports are caught and reported with specific line/file context.
