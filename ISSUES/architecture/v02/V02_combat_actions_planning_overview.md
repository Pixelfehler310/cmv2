# V02 Planning Overview: Combat Actions, Turn Economy, and Effects

Status: Draft for Planning
Related module issue: ISSUE [VERT][V02]
Related dependency: ISSUE [VERT][V01]
Related playbook: docs/architecture/shared/05_vertical_module_execution_plan.md
Related diagram: V02_combat_actions_detailed_plan.mmd

Detailed issue set (proposed for activation):

- ISSUE [VERT][V02-01] baseline_and_drift_audit
- ISSUE [VERT][V02-02] action_and_deny_contract_freeze
- ISSUE [VERT][V02-03] turnbudget_and_effect_ownership_lock
- ISSUE [VERT][V02-04] action_execution_orchestration
- ISSUE [VERT][V02-05] ws_rest_convergence_and_event_determinism
- ISSUE [VERT][V02-06] test_matrix_and_completion_gate

## What V02 Is Trying to Achieve

V02 stabilizes the highest-risk runtime stream in combat:
requesting an action, validating turn economy and policy constraints, applying effects, and producing deterministic outcomes.

This module exists to make action outcomes predictable and machine-testable before deeper world runtime and event projection expansion.

## Why V02 Follows V01

1. V01 establishes scene/combat lifecycle authority; V02 depends on those lifecycle boundaries.
2. Without V01 transition clarity, V02 action semantics can leak across ambiguous state ownership.
3. Deterministic turn/effect semantics in V02 lower risk for V06 event projection and frontend consumption.

## Boundaries of V02

In scope:

1. Action execution command and outcome contracts.
2. Turn economy rules and denied reason taxonomy.
3. Effect runtime lifecycle (apply, tick, concentration, expire/remove).
4. WS and REST convergence for action outcomes and events.
5. Deterministic test matrix for combat action and effect flow.

Out of scope:

1. Broad compendium CRUD and catalog lifecycle.
2. Full world-context relationship modeling (V03).
3. Frontend-side gameplay rule execution.

## Core Ownership Decisions to Lock

1. Turn budget state has one write authority in backend domain/application boundaries.
2. Effect instance runtime lifecycle transitions have one authoritative mutation path.
3. Action execution outcome envelope is produced by backend services, not transport layers.
4. Denied reason taxonomy is canonical in backend contracts and shared unchanged externally.

## Phase Plan for V02 (Using the Playbook)

### P0 Alignment and Baseline

1. Inventory current action execution paths across WS/REST and service entrypoints.
2. Capture baseline behavior for accepted and denied actions.
3. Record drift risks (race conditions, event ordering mismatch, inconsistent deny reasons).

Exit signal:

- Scope and dependency map approved for V02 execution.

### P1 Contract and Invariant Freeze

1. Freeze action command contract fields and validation semantics.
2. Freeze action outcome envelope (accepted/denied, reason code, deltas/events).
3. Freeze denied reason taxonomy as machine-readable and stable.
4. Freeze invariants: single turn owner, non-negative budget, deterministic effect ordering.

Exit signal:

- Contracts and invariants are stable enough to implement.

### P2 Persistence and Ownership Boundaries

1. Map each mutable runtime field to a single write authority.
2. Lock repository boundaries for turn budget and effect state persistence.
3. Remove or explicitly reject multi-writer update paths.

Exit signal:

- No unresolved ownership ambiguity remains for V02 aggregates.

### P3 Application and Domain Implementation

1. Implement orchestration in ActionExecutionApplicationService.
2. Keep rule checks in domain policy layers (turn budget, legality, effect policy).
3. Enforce deterministic denied/accepted outcomes and request correlation.

Exit signal:

- Service behavior matches frozen contracts and invariants.

### P4 Transport and External Interfaces

1. Converge WS and REST handlers on the same application contracts.
2. Align payload shapes and denied taxonomy across interfaces.
3. Enforce deterministic event ordering and correlation visibility.

Exit signal:

- External behavior is deterministic and documented.

### P5 Frontend Projection and Type Sync

1. Regenerate shared contract artifacts.
2. Verify projection consumes backend truth without local gameplay authority.
3. Validate denied-reason rendering without semantic translation drift.

Exit signal:

- Frontend projection remains contract-stable.

### P6 Test Matrix and Observability Hardening

1. Build contract tests for accepted and denied action matrix.
2. Build invariant tests for turn budget and effect lifecycle guarantees.
3. Build integration tests proving WS and REST parity.
4. Validate logs include request correlation and deterministic reason traces.

Exit signal:

- Required V02 suites are green and deterministic.

### P7 Closure and Handoff

1. Publish completion note with scope delivered and residual risks.
2. Create focused follow-up issues only for deferred material risks.
3. Hand off constraints to V03 and V06 modules.

Exit signal:

- V02 is marked complete with verified gates.

## Child-Issue Cut Recommendation (Activation Package)

1. V02-01 Baseline and Drift Audit.
2. V02-02 Action and Deny Contract Freeze.
3. V02-03 TurnBudget and Effect Ownership Lock.
4. V02-04 Action Execution Orchestration.
5. V02-05 WS/REST Convergence and Event Determinism.
6. V02-06 V02 Test Matrix and Completion Gate.

Planning status:

- V02 planning artifacts are authored (overview + detailed diagram).
- Child issue creation can begin when V00 board marks V02 active.

## Verification Commands (Draft)

1. docker compose --profile test run --rm backend-test pytest tests/systems/dnd5e -q
2. docker compose --profile test run --rm backend-test pytest tests/events -q
3. docker compose --profile test run --rm -e PYTHONPATH=/app backend-test python scripts/generate_types.py --check
4. docker compose logs backend --tail=200
