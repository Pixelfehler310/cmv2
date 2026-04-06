# V01 Planning Overview: Runtime Hierarchy and Scene Combat Lifecycle

Status: Draft for Planning
Related module issue: ISSUE [VERT][V01]
Related playbook: docs/archive/planning_legacy/docs_architecture/shared/05_vertical_module_execution_plan.md
Related diagram: V01_runtime_hierarchy_detailed_plan.mmd

Detailed issue set:

- ISSUE [VERT][V01-01] baseline_and_drift_audit
- ISSUE [VERT][V01-02] lifecycle_contract_freeze
- ISSUE [VERT][V01-03] ownership_and_repository_boundary_lock
- ISSUE [VERT][V01-04] application_transition_orchestration
- ISSUE [VERT][V01-05] ws_and_rest_interface_convergence
- ISSUE [VERT][V01-06] test_matrix_and_completion_gate

## What V01 Is Trying to Achieve

V01 stabilizes the scene-first runtime backbone:
Campaign -> Scene with optional combat state.

This module exists to make lifecycle authority explicit before deeper combat, world context, and projection work.

## Why V01 Comes First

1. All later modules depend on stable scene selection and combat-state transition semantics.
2. Ambiguous lifecycle ownership causes cross-module churn and contract drift.
3. Deterministic transitions in V01 reduce downstream refactor risk.

## Boundaries of V01

In scope:

1. Campaign and scene lifecycle transitions.
2. Combat start and combat end transitions inside scene state.
3. Ownership and persistence boundaries for runtime hierarchy state.
4. Transport-to-service interface behavior for scene and scene-combat lifecycle commands.

Out of scope:

1. Deep action resolution rules.
2. Full effect engine semantics.
3. Broad compendium/content CRUD.

## Core Ownership Decisions to Lock

1. Campaign aggregate write authority.
2. Scene aggregate write authority.
3. Scene combat state write authority.
4. Single-writer rule for scene combat-state transitions.

## Phase Plan for V01 (Using the Playbook)

### P0 Alignment and Baseline

1. Confirm current implementation paths for scene selection and combat start/end on scene.
2. Confirm existing docs and tests covering lifecycle flows.
3. Record baseline commands and observed behavior.

Exit signal:

- Team agrees on exact V01 scope and risk list.

### P1 Contract and Invariant Freeze

1. Define command contracts for:
   - select scene
   - start combat
   - end combat
2. Define denied/error reason code expectations.
3. Freeze lifecycle invariants:
   - scene-campaign ownership
   - combat state belongs to selected scene
   - scene has at most one active combat state
   - allowed phase transitions

Exit signal:

- Contract and invariant list is stable enough for implementation.

### P2 Persistence and Ownership Boundaries

1. Map each lifecycle state field to one write authority.
2. Ensure repository boundaries are explicit for campaign/scene writes (including scene combat state).
3. Remove or flag ambiguous write paths.

Exit signal:

- No unresolved multi-writer lifecycle state.

### P3 Application and Domain Implementation

1. Implement transition orchestration in application service.
2. Keep transition validation in policy layer.
3. Ensure denied outcomes return stable reason codes.

Exit signal:

- Service behavior matches P1 contracts in core scenarios.

### P4 Transport and External Interfaces

1. Align WS and REST handlers to the same application contracts.
2. Ensure request_id correlation and deterministic event emission.
3. Ensure event mapper produces stable payload shape.

Exit signal:

- Interface behavior is deterministic across WS and REST flows.

### P5 Frontend Projection and Type Sync

1. Validate projection inputs for scene and scene-combat lifecycle events.
2. Regenerate and verify shared contract artifacts as needed.
3. Confirm no frontend-side lifecycle authority creep.

Exit signal:

- Frontend consumes backend truth with no lifecycle rule duplication.

### P6 Test Matrix and Observability Hardening

1. Contract tests for each lifecycle command.
2. Invariant tests for ownership and phase transition rules.
3. Integration tests for end-to-end scene to combat-state lifecycle flow.
4. Log checks for transition traceability.

Exit signal:

- Required V01 test suites are deterministic and green.

### P7 Closure and Handoff

1. Summarize completed V01 scope and residual risks.
2. Create focused follow-up issues for deferred work only.
3. Hand off constraints to V02 and V03.

Exit signal:

- V01 is marked complete with verified gates.

## Recommended Initial Child-Issue Cut (When You Approve Deepening)

1. V01-01 Baseline and Drift Audit.
2. V01-02 Lifecycle Contract Freeze.
3. V01-03 Ownership and Repository Boundary Lock.
4. V01-04 Application Transition Orchestration.
5. V01-05 WS and REST Interface Convergence.
6. V01-06 V01 Test Matrix and Completion Gate.

Planning status:

- Child issue definitions are now authored.
- Next step is execution kickoff from V01-01.

## Verification Commands (Draft)

1. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e/test_ws_integration.py -q
2. docker compose --profile test run --rm backend-test pytest tests/campaigns -q
3. docker compose --profile test run --rm -e PYTHONPATH=/app backend-test python scripts/generate_types.py --check
4. docker compose logs backend --tail=200
