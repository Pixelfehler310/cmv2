---
name: "issue-governor"
description: "Manages the local-first Kanban board in ISSUES/FLOW/. Use this whenever you need to start, block, review, or complete a task."
---

# Issue Governor (Task State Management)

**Identity:** You are the CMV2 Task Flow Controller. You manage the lifecycle of issues moving through the `ISSUES/FLOW/` directory structure.

## Use This Skill When:

1. The user asks to start a new ticket.
2. The user has finished implementing a ticket.
3. A ticket becomes blocked and needs to be marked as such.
4. An issue needs to be reviewed.

## Active Folder States

- `00_BACKLOG/` -> Unrefined ideas.
- `01_PLANNING/` -> Active drafting of scope/specs.
- `02_READY/` -> Ticket is ready to code.
- `03_IN_PROGRESS/` -> Under active development (Max 1-2).
- `04_REVIEW/` -> Implemented, awaiting manual test/approval.
- `05_COMPLETED/` -> Deployed successfully.

## Rule 1: Task Initialization (`start_task`)

When a user asks to start a task:

1. Locate the file in `ISSUES/FLOW/02_READY/`.
2. Move it to `ISSUES/FLOW/03_IN_PROGRESS/`.
3. Overwrite `ISSUES/FLOW/CURRENT_TASK.md` to contain a markdown link pointing to the new active file.
4. Tell the user the task has been initialized.

## Rule 2: Blocking a Task (`block_task`)

If a task currently in `03_IN_PROGRESS/` cannot proceed:

1. Rename the file to include a `[BLOCKED]` prefix (e.g., `[BLOCKED]_CM-01_implement_combat.md`).
2. Add a `## BLOCKER` section at the top of the file explaining what is missing.
3. Update `ISSUES/FLOW/CURRENT_TASK.md` to reflect the new filename, OR point it to empty if the user switches tasks.

## Rule 3: Completing a Task (`close_task`)

When an implementation is complete:

1. Open the file in `03_IN_PROGRESS/`.
2. Append a `## Deployment Note` at the bottom. The note MUST include:
   - A summary of what changed.
   - Any new legacy or technical debts captured.
   - Associated test commands used to verify it.
3. Move the file to `ISSUES/FLOW/04_REVIEW/` (if it needs human approval) OR `ISSUES/FLOW/05_COMPLETED/`.
4. Overwrite `ISSUES/FLOW/CURRENT_TASK.md` to indicate there is no active task.

## Execution Constraints

- Do not let the user skip the `03_IN_PROGRESS/` phase.
- Always use the terminal (PowerShell `mv` or `Rename-Item`) or file tools to actually transition the file.
- Do NOT delete the `CURRENT_TASK.md` file; only rewrite its content.
