# V02 Planning Overview: Combat Actions, Turn Economy, and Effects

Status: Draft for Planning
Related module issue: ISSUE [VERT][V02]
Related playbook: docs/architecture/shared/05_vertical_module_execution_plan.md
Related diagram: V02_combat_actions_detailed_plan.mmd

Detailed issue set (proposed for activation window):

- ISSUE [VERT][V02-01] action_contract_and_denied_taxonomy_freeze
- ISSUE [VERT][V02-02] turn_budget_ownership_and_spend_rules
- ISSUE [VERT][V02-03] effect_lifecycle_and_concentration_policy_lock
- ISSUE [VERT][V02-04] application_orchestration_for_action_execution
- ISSUE [VERT][V02-05] ws_rest_contract_convergence_for_combat_actions
- ISSUE [VERT][V02-06] deterministic_test_matrix_and_completion_gate

## What V02 Is Trying to Achieve

V02 stabilizes the combat execution core after V01 lifecycle authority is in place.
It makes action resolution, turn budget spending, and effect lifecycle semantics deterministic and machine-readable.

## Why V02 Follows V01

1. V02 relies on V01 scene and combat lifecycle invariants to define legal action windows.
2. Action and effect correctness cannot be made reliable while scene and combat ownership are ambiguous.
3. A stable deny taxonomy in V02 reduces projection drift in V06 and frontend state handling.

## Boundaries of V02

In scope:

1. Action execution request and outcome contracts.
2. Turn economy budget ownership and spend semantics.
3. Effect apply, tick, concentration, expire, and removal semantics.
4. Stable deny reason-code taxonomy for combat action and effect transitions.
5. WS and REST parity for combat action execution paths.

Out of scope:

1. Compendium CRUD breadth and content authoring workflows.
2. New frontend gameplay features beyond contract consumption.
3. Non-combat world context runtime deepening (covered by V03).

## Core Ownership Decisions to Lock

1. Single-writer ownership for turn budget mutation.
2. Single authoritative path for action execution and outcome creation.
3. Single authoritative path for effect state transitions.
4. Concentration ownership and interruption semantics.
5. Event mapping ownership for combat action/effect events.

## Target Runtime and Service Structure

Domain runtime targets:

1. Combat encounter runtime with active actor and round state.
2. Actor runtime with concentration and reaction state.
3. Turn budget runtime per actor-turn.
4. Effect instance runtime with explicit lifecycle state and reason codes.

Application targets:

1. ActionExecutionApplicationService orchestrates command handling.
2. Service enforces deterministic read-validate-mutate-map flow.
3. Service returns stable result envelopes for WS and REST mappers.

Policy targets:

1. Authorization policy for action and turn-level commands.
2. Turn economy policy for budget and reaction gating.
3. Effect lifecycle policy for apply/tick/remove/concentration decisions.

## Phase Plan for V02 (Using the Playbook)

### P0 Alignment and Baseline

1. Confirm current action execution paths and where budget/effects mutate today.
2. Confirm existing denied reasons and event payload variants.
3. Capture baseline deterministic and non-deterministic scenarios.

Exit signal:

- Team agrees on exact V02 scope, risk list, and baseline behavior matrix.

### P1 Contract and Denied Taxonomy Freeze

1. Define execute-action contract inputs and outputs.
2. Define deny reason-code taxonomy with stable machine-readable values.
3. Freeze event payload requirements for action, budget, and effect lifecycle events.

Exit signal:

- Action contracts and denied taxonomy are stable enough for implementation.

### P2 Ownership and Persistence Boundaries

1. Map all budget fields to one write authority.
2. Map all effect lifecycle transitions to one write authority.
3. Remove or flag ambiguous mutation paths.

Exit signal:

- No unresolved multi-writer state for budget or effects.

### P3 Policy Consolidation

1. Implement turn economy policy with explicit spend and reaction rules.
2. Implement effect lifecycle policy with concentration and stacking behavior.
3. Verify invariant coverage for budget/effect transitions.

Exit signal:

- Policy layer is complete for target V02 scenarios with stable reason codes.

### P4 Application Orchestration

1. Route action execution through one application orchestration path.
2. Ensure deterministic sequencing: authorize -> validate -> mutate -> map.
3. Ensure result envelope consistency for both success and denied outcomes.

Exit signal:

- Service behavior matches P1 contracts in core combat scenarios.

### P5 Transport and Interface Convergence

1. Align WS and REST handlers to the same action execution contracts.
2. Ensure request_id correlation and deterministic event emission.
3. Validate mappers emit only stable contract fields.

Exit signal:

- WS and REST flows are behaviorally aligned and deterministic.

### P6 Test Matrix and Determinism Hardening

1. Contract tests for action request/result and deny taxonomy.
2. Invariant tests for budget spend, reaction windows, concentration, and lifecycle order.
3. Integration tests for action->effect flows across rounds and transport paths.
4. Replay tests for deterministic outcomes under identical inputs.

Exit signal:

- Required V02 suites are deterministic and green.

### P7 Closure and Handoff

1. Summarize completed V02 scope and residual risks.
2. Create focused follow-up issues for deferred combat work only.
3. Hand off resulting constraints to V03 and V06 planning streams.

Exit signal:

- V02 closure criteria are met and handoff constraints are explicit.

## Recommended Initial Child-Issue Cut (When V02 Is Activated)

1. V02-01 Action Contract and Denied Taxonomy Freeze.
2. V02-02 Turn Budget Ownership and Spend Rules.
3. V02-03 Effect Lifecycle and Concentration Policy Lock.
4. V02-04 Application Orchestration for Action Execution.
5. V02-05 WS and REST Contract Convergence for Combat Actions.
6. V02-06 Deterministic Test Matrix and Completion Gate.

Planning status:

- Target architecture and execution phases are now documented.
- Next step is activation of V02 in the V00 board, then decomposition into child issues.

## Verification Commands (Draft)

1. docker compose --profile test run --rm backend-test pytest tests -k "combat and action" -q
2. docker compose --profile test run --rm backend-test pytest tests -k "effect and concentration" -q
3. docker compose --profile test run --rm -e PYTHONPATH=/app backend-test python scripts/generate_types.py --check
4. docker compose logs backend --tail=200
