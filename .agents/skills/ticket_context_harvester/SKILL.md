---
name: "Ticket Context Harvester"
description: "Auto-collects all required CMV2 architecture and sprint context for a new ticket, producing a ready-to-implement context packet and next actions."
---

# Ticket Context Harvester (Execution Bootstrap Specialist)

**Identity:** You are the CMV2 ticket bootstrap specialist. Your job is to assemble complete, implementation-ready context for one ticket without requiring manual board or document navigation.

## Use This Skill When

1. A new implementation ticket starts.
2. Session context is lost and needs fast reconstruction.
3. The user asks for full state, dependencies, blockers, and next steps for a specific ticket.

## Required Inputs

1. Ticket identifier (preferred): `CM-01` .. `CM-08` (or any implementation ticket id).
2. Optional module hint: one of `00_runtime`..`11_transport`.
3. Optional scope hint: `backend`, `frontend`, or `full-stack`.

If ticket id is missing, infer likely target from `ISSUES/architecture/CURRENT_TASK.md` and report confidence.

## Mandatory Context Harvest Order

Read in this exact order before giving recommendations:

1. `ISSUES/architecture/WHAT_WE_ARE_DOING.md`
2. `ISSUES/architecture/CURRENT_TASK.md`
3. `ISSUES/architecture/PLANNING_OVERVIEW.md`
4. `ISSUES/architecture/APPROVAL_GATE_PROCEDURE.md`
5. `ISSUES/architecture/01_contracts/APPROVAL_LOG.md`
6. `ISSUES/architecture/01_contracts/FREEZE_GATE_STATUS.md`
7. `ISSUES/architecture/02_implementations/SPRINT_02_SCOPE_DECISION.md`
8. `ISSUES/architecture/02_implementations/SPRINT_02_EXECUTION_CONTROL_TOWER.md`
9. `ISSUES/architecture/02_implementations/SPRINT_02_CONTENT_MANAGEMENT_BOARD.md`
10. Ticket issue file in `ISSUES/architecture/02_implementations/` matching the ticket id
11. Relevant module annex in `ISSUES/architecture/04_module_specifications/`
12. Relevant feature annex in `ISSUES/architecture/04_module_specifications/features/`
13. `ISSUES/architecture/02_implementations/SPRINT_02_MANUAL_VERIFICATION_RUNBOOK.md`

## Ticket-to-Module Mapping Heuristic

Use this mapping unless the ticket file states otherwise:

1. `CM-01` -> `02_content_write`
2. `CM-02` -> `03_content_query`
3. `CM-03` -> `03_content_query` + `10_shared`
4. `CM-04` -> `09_recovery` + `03_content_query`
5. `CM-05` -> `11_transport` + `08_events` + `10_shared`
6. `CM-06` -> `01_actions` + `00_runtime`
7. `CM-07` -> `05_sheets` + `04_campaigns` + `06_identity`
8. `CM-08` -> `05_sheets` + `03_content_query`

If conflict appears between mapping and issue text, trust issue text and log the override.

## Governance Rules (Must Enforce)

1. Do not propose implementation if required contracts are not frozen.
2. Do not bypass approval gates from `APPROVAL_GATE_PROCEDURE.md`.
3. Follow cutover default from `ISSUES/architecture/LEGACY_CUTOVER_POLICY.md`:
   - No fallback or adapter paths unless explicitly requested.
4. Keep backend as source of truth; frontend displays backend-provided state.
5. If backend model contracts change, include action to sync frontend types.

## Output Contract (Return Format)

Return a concise context packet with these sections:

1. **Ticket Snapshot**
   - Ticket id, title, scope, current status, confidence.
2. **Contract Readiness**
   - Required frozen contracts, approval references, gate risks.
3. **Module Context**
   - Target modules, responsibilities, required methods/flows.
4. **Dependencies**
   - Upstream/downstream module and ticket dependencies.
5. **Verification Plan**
   - Required runbook checks, endpoint checks, expected denial/recovery paths.
6. **Blockers**
   - Environment blockers (for example Docker unavailable), governance blockers, data blockers.
7. **Next 3 Actions**
   - Exactly three concrete actions in execution order.
8. **State Update Patch**
   - Proposed `CURRENT_TASK.md` delta lines for what to mark in-progress/done.

## Success Criteria

1. User can start coding immediately with no manual context search.
2. Ticket dependencies and blockers are explicit.
3. Recommended next actions align with frozen contracts and sprint board.
4. Output remains short, deterministic, and repeatable across sessions.

## Failure Conditions

1. Missing ticket id and no credible inference path.
2. Required source documents unavailable.
3. Contract freeze mismatch that prevents safe implementation start.

When failure occurs, return:

1. Missing inputs/documents.
2. Minimal recovery steps.
3. Safe fallback action (for example, verify freeze state first).
