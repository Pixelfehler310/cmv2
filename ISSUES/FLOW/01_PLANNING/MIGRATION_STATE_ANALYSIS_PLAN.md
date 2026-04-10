# Migration and State Analysis Plan (Legacy Backlog -> FLOW)

## Scope

This document covers only:

1. Migration of the current legacy backlog files into the new `ISSUES/FLOW/` state model.
2. State analysis decisions for each migrated file.

Out of scope for this phase:

1. Batch execution and implementation.
2. Splitting module specification tickets into execution batches.
3. Detailed rewrites of legacy architecture issue sets.

## Source of Truth for This Migration

Legacy source folder:

- `ISSUES/backlog/`

Target state model:

- `ISSUES/FLOW/00_BACKLOG/`
- `ISSUES/FLOW/01_PLANNING/`
- `ISSUES/FLOW/02_READY/`
- `ISSUES/FLOW/03_IN_PROGRESS/`
- `ISSUES/FLOW/04_REVIEW/`
- `ISSUES/FLOW/05_COMPLETED/`
- `ISSUES/FLOW/99_ARCHIVE/`

## Migration Decisions (Ticket-by-Ticket)

| Legacy Ticket                                       | Assigned FLOW State | Decision Basis                                                                           |
| --------------------------------------------------- | ------------------- | ---------------------------------------------------------------------------------------- |
| `ISSUE_frontend_compendium_ui_vertical.md`          | `03_IN_PROGRESS`    | Marked as current active direction; discussion and phased UI roadmap already present.    |
| `ISSUE_core_websocket_dispatcher_modularization.md` | `02_READY`          | Well-scoped technical debt ticket with concrete acceptance and verification.             |
| `ISSUE_ci_cd_docs_freshness_warning_workflow.md`    | `01_PLANNING`       | Clear goal but still needs pipeline placement and policy details finalized.              |
| `ISSUE_content_import_export_bulk.md`               | `00_BACKLOG`        | Broad feature, currently not execution-ready at endpoint/schema-level precision.         |
| `ISSUE_data_historization.md`                       | `00_BACKLOG`        | High-impact architectural topic requiring dedicated contract + migration planning first. |
| `ISSUE_search_index_gin_fulltext.md`                | `00_BACKLOG`        | Planned optimization dependent on baseline search vertical maturity and benchmark setup. |

## Current Resulting Board Snapshot

### 00_BACKLOG

- `ISSUE_content_import_export_bulk.md`
- `ISSUE_data_historization.md`
- `ISSUE_search_index_gin_fulltext.md`

### 01_PLANNING

- `ISSUE_ci_cd_docs_freshness_warning_workflow.md`

### 02_READY

- `ISSUE_core_websocket_dispatcher_modularization.md`

### 03_IN_PROGRESS

- `ISSUE_frontend_compendium_ui_vertical.md`

## Integrity Rules Applied During Migration

1. Legacy files were copied into FLOW states so original backlog remains intact as historical input.
2. No content edits were applied to migrated issue files during this phase.
3. No tickets were promoted to `04_REVIEW` or `05_COMPLETED` without implementation evidence.

## Immediate Follow-Up (Next Phase, Not Executed Here)

1. Convert the in-progress compendium ticket into a parent blueprint with explicit subfeature checklists.
2. Batch-split broader architecture tickets into implementation-ready parent tickets.
3. Define migration waves for `ISSUES/architecture/` tickets into FLOW entries.

## Batch-Level Detail

Detailed Batch A file placement and readiness mapping:

- `ISSUES/FLOW/01_PLANNING/BATCH_A_MIGRATION_OVERVIEW.md`
- `ISSUES/FLOW/01_PLANNING/BATCH_B_MIGRATION_OVERVIEW.md`
- `ISSUES/FLOW/01_PLANNING/BATCH_C_MIGRATION_OVERVIEW.md`
- `ISSUES/FLOW/01_PLANNING/BATCH_D_MIGRATION_OVERVIEW.md`
