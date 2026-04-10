# AI-Driven Kanban Flow (Local-First PM)

This directory implements a Local-First GitOps issue management system. It acts as the source of truth for all planned, active, and completed work.

## Folder States

- `00_BACKLOG/`: Raw ideas, unrefined specs, and future features.
- `01_PLANNING/`: Tickets currently being drafted, researched, or broken down.
- `02_READY/`: Fully sculpited tickets with a clear "Definition of Done". Ready for AI/human pickup.
- `03_IN_PROGRESS/`: The active work-in-progress. Only 1-2 items should be here at a time. (Prefix with `[BLOCKED]_` if stuck).
- `04_REVIEW/`: Code implemented, waiting for manual verification or code review.
- `05_COMPLETED/`: Successfully implemented in the current sprint.
- `99_ARCHIVE/`: Historical records (zipped or older completed items).

## Usage

- Always check `CURRENT_TASK.md` to see what is currently active.
- Use the `issue_governor` skill to move issues between these folders and append logs appropriately.
