# V02 Planning Overview: Combat Actions, Turn Economy, and Effects

Status: Draft for Planning
Related module issue: ISSUE [VERT][V02]
Related playbook: docs/architecture/shared/05_vertical_module_execution_plan.md
Related diagrams:

- V02_combat_actions_detailed_plan.mmd
- V02_action_processing_and_event_contracts_detailed_plan.mmd

Detailed issue set (proposed for activation window):

- ISSUE [VERT][V02-01] action_contract_and_denied_taxonomy_freeze
- ISSUE [VERT][V02-02] turn_budget_ownership_and_spend_rules
- ISSUE [VERT][V02-03] operation_targeting_and_snapshot_contract_lock
- ISSUE [VERT][V02-04] operation_graph_orchestration_for_action_execution
- ISSUE [VERT][V02-05] ws_rest_contract_convergence_for_combat_actions
- ISSUE [VERT][V02-06] effect_zone_and_concentration_lifecycle_policy_lock
- ISSUE [VERT][V02-07] action_execution_tests_matrix_and_completion_gate

## What V02 Is Trying to Achieve

V02 stabilizes the combat execution core after V01 lifecycle authority is in place.

The architecture is now explicitly operation-graph based:

1. One action command contains multiple operations.
2. Each operation can have its own targeting mode.
3. Any operation can produce one or more effect outcomes.
4. Execution order is deterministic and dependency-aware.

## Why V02 Follows V01

1. V02 relies on V01 scene and combat lifecycle invariants to define legal action windows.
2. Action and effect correctness cannot be made reliable while scene and combat ownership are ambiguous.
3. Stable operation-level contracts in V02 reduce projection drift in V06 and frontend state handling.

## Boundaries of V02

In scope:

1. Action command contracts with operation_specs list.
2. Operation-level target resolution contracts for explicit, area, self, derived, and none targeting modes.
3. Turn economy budget ownership and spend semantics.
4. Effect, zone, concentration, tick, expire, and removal semantics.
5. Stable deny reason-code taxonomy for command, operation, targeting, and effect transitions.
6. WS and REST parity for operation-graph execution outcomes.

Out of scope:

1. Compendium CRUD breadth and content authoring workflows.
2. New frontend gameplay features beyond contract consumption.
3. Non-combat world context runtime deepening (covered by V03).

## Core Ownership Decisions to Lock

1. Single-writer ownership for turn budget mutation.
2. Single authoritative path for action command orchestration.
3. Single authoritative path for operation graph planning and ordering.
4. Single authoritative path for effect and zone lifecycle transitions.
5. Concentration ownership and interruption semantics.
6. Deterministic operation-target snapshot ownership for each request_id and operation_id.

## Target Runtime and Service Structure

Domain runtime targets:

1. Combat encounter runtime with active actor and round state.
2. Actor runtime with concentration and reaction state.
3. Turn budget runtime per actor-turn.
4. Operation target snapshot runtime state per request and operation.
5. Effect instance and zone runtime state with explicit lifecycle semantics.

Application targets:

1. ActionExecutionApplicationService orchestrates command handling.
2. Service enforces deterministic authorize -> resolve -> plan -> execute -> map flow.
3. Service builds a validated operation graph before execution.
4. Service returns stable event/result envelopes for WS and REST mappers.

Policy targets:

1. Authorization policy for command and turn-level authority.
2. Turn economy policy for budget and reaction gating.
3. Operation target resolution policy for each operation node.
4. Operation execution policy for dependencies and phase validity.
5. Effect lifecycle policy for apply, stack, tick, remove, and concentration decisions.

## Detailed Execute-Action Pipeline (Operation Graph Model)

### Step A: Request Intake and Authorization

1. Validate command envelope fields.
2. Validate operation_specs shape and request_id.
3. Authorize actor command rights.
4. Validate turn window and spend availability.

Expected denied examples:

- not_active_actor
- insufficient_budget
- reaction_window_closed
- invalid_operation_specs

### Step B: Operation Graph Build

1. Build operation dependency graph.
2. Validate references and reject cycles.
3. Produce deterministic linearized operation order.

Expected denied examples:

- operation_dependency_cycle
- operation_dependency_missing
- operation_kind_invalid

### Step C: Per-Operation Target Resolution

1. Resolve targets independently for each operation.
2. Apply range, geometry, line-of-effect, and policy checks per operation.
3. Persist deterministic operation target snapshots.

Expected denied examples:

- invalid_target_spec
- target_out_of_range
- blocked_line_of_effect
- no_valid_targets

### Step D: Result Planning

1. Build ActionResultPlan from operation graph.
2. Separate immediate, deferred, and tick operations.
3. Freeze deterministic execution order in plan output.

### Step E: Immediate Operation Execution

1. Spend budget exactly once for the command.
2. Execute immediate operations in graph order.
3. Emit operation-level outcome events.
4. Persist actor and encounter deltas.

### Step F: Deferred and Tick Materialization

1. Materialize deferred operation effects.
2. Create/refresh zone instances and scheduled ticks.
3. Emit effect and zone lifecycle events.

### Step G: Concentration and Removal Flow

1. Apply concentration ownership rules per operation output.
2. Handle concentration replacement deterministically.
3. Emit concentration lifecycle events and linked effect removals.

### Step H: Finalization and Mapping

1. Return stable action result envelope.
2. Emit deterministic event sequence with request_id and operation_id correlations.
3. Include state_revision metadata for drift detection and replay.

## Multi-Result Action Example (Smoke Plus Damage Plus Delayed Sleep)

Example behavior in operation-graph model:

1. Operation A: zone_create with area targeting.
2. Operation B: immediate_damage targeting occupants in initial area snapshot.
3. Operation C: delayed_sleep targeting occupants who satisfy remain threshold.
4. Operation D: periodic_damage tick operation (alternative to sleep branch).

All operations belong to one action request and are ordered via dependency graph semantics.

## Phase Plan for V02 (Using the Playbook)

### P0 Alignment and Baseline

1. Confirm current action execution paths and mutation ownership.
2. Confirm existing event payload variants and deny reasons.
3. Capture baseline deterministic and non-deterministic scenarios.

Exit signal:

- Team agrees on operation-graph scope and baseline risk matrix.

### P1 Contract and Denied Taxonomy Freeze

1. Define execute-action command envelope with operation_specs contract.
2. Define operation-level target snapshot and lifecycle contract.
3. Define deny reason taxonomy for command, operation, target, and effect families.
4. Freeze event payload requirements across operation lifecycle phases.

Exit signal:

- Operation-graph contracts and denied taxonomy are stable enough for implementation.

### P2 Ownership and Persistence Boundaries

1. Map budget fields to one write authority.
2. Map operation graph planning and ordering fields to one write authority.
3. Map effect and zone lifecycle transitions to one write authority.
4. Remove or flag ambiguous mutation paths.

Exit signal:

- No unresolved multi-writer state for budget, operation graph, or effects.

### P3 Policy Consolidation

1. Implement turn economy policy with explicit spend and reaction rules.
2. Implement operation target resolution policy for each operation mode.
3. Implement operation execution policy with dependency and phase rules.
4. Implement effect lifecycle policy with concentration and zone tick behavior.

Exit signal:

- Policy layer is complete for operation-graph scenarios with stable reason codes.

### P4 Application Orchestration

1. Route command execution through one operation-graph orchestration path.
2. Ensure deterministic sequencing: authorize -> graph -> targets -> execute -> map.
3. Ensure result envelope consistency for resolved and denied outcomes.

Exit signal:

- Service behavior matches P1 contracts in core combat scenarios.

### P5 Transport and Interface Convergence

1. Align WS and REST handlers to same operation-graph contracts.
2. Ensure request_id and operation_id correlation and deterministic event emission.
3. Validate mappers emit only stable contract fields.

Exit signal:

- WS and REST flows are behaviorally aligned and deterministic.

### P6 Test Matrix and Determinism Hardening

1. Contract tests for command, operation lifecycle, and deny taxonomy.
2. ActionExecutionTests suite for multi-operation orchestration behavior.
3. Invariant tests for budget, operation snapshot stability, concentration, and lifecycle order.
4. Integration tests for command -> operation -> effect -> zone flows across rounds and transport paths.
5. Replay tests for deterministic outcomes under identical inputs.

Exit signal:

- Required V02 suites are deterministic and green.

### P7 Closure and Handoff

1. Summarize completed V02 scope and residual risks.
2. Create focused follow-up issues for deferred combat work only.
3. Hand off resulting constraints to V03 and V06 planning streams.

Exit signal:

- V02 closure criteria are met and handoff constraints are explicit.

## Recommended Initial Child-Issue Cut (When V02 Is Activated)

1. V02-01 Action Command and Denied Taxonomy Freeze.
2. V02-02 Turn Budget Ownership and Spend Rules.
3. V02-03 Operation Targeting and Snapshot Contract Lock.
4. V02-04 Operation Graph Orchestration for Action Execution.
5. V02-05 WS and REST Contract Convergence for Combat Actions.
6. V02-06 Effect, Zone, and Concentration Lifecycle Policy Lock.
7. V02-07 ActionExecutionTests Matrix and Completion Gate.

## Detailed Test Planning: ActionExecutionTests

The ActionExecutionTests suite is a first-class completion gate.

### A. Command and Operation Contract Tests

1. action_command_requires_non_empty_operation_specs
2. operation_entry_requires_operation_id_and_kind
3. operation_event_payload_contains_operation_id
4. denied_reason_is_machine_readable

### B. Operation Graph Tests

1. operation_graph_linearization_deterministic
2. operation_dependency_cycle_rejected
3. operation_dependency_missing_rejected
4. operation_phase_validation_enforced

### C. Operation Targeting Tests

1. explicit_target_operation_resolves_deterministically
2. area_target_operation_resolves_with_geometry_rules
3. derived_target_operation_resolves_from_context
4. per_operation_target_snapshot_stable_on_replay
5. invalid_target_spec_denies_before_mutation

### D. Multi-Operation Execution Tests

1. single_action_executes_multiple_operation_kinds
2. immediate_and_deferred_operations_obey_graph_order
3. budget_spent_once_for_multi_operation_action
4. operation_denial_does_not_corrupt_unrelated_operations

### E. Effect, Zone, and Concentration Tests

1. zone_created_event_emitted_from_zone_operation
2. zone_occupancy_recomputed_before_tick_effects
3. concentration_replaced_emits_remove_then_start
4. concentration_broken_removes_linked_effects
5. zone_and_effect_expiry_order_deterministic

### F. Determinism and Replay Tests

1. identical_inputs_identical_operation_event_sequence
2. actor_iteration_order_stable_during_tick_operations
3. denied_reason_stable_for_same_invalid_input
4. cross_transport_parity_ws_vs_rest_same_semantics

### G. Completion Criteria for ActionExecutionTests

1. All critical behavior families above have passing deterministic tests.
2. At least one smoke-style multi-operation scenario is covered in ws and rest integrations.
3. Flakiness rate remains zero across repeated seeded runs.
4. All denied paths prove no unauthorized mutation side effects.

Planning status:

- Target architecture now models action execution as operation graph with per-operation targeting.
- Event and processing docs are aligned to operation-level semantics.
- Next step is activation of V02 in the V00 board, then decomposition into child issues.

## Verification Commands (Draft)

1. docker compose --profile test run --rm backend-test pytest tests -k "request_action and operation" -q
2. docker compose --profile test run --rm backend-test pytest tests -k "target and operation" -q
3. docker compose --profile test run --rm backend-test pytest tests -k "effect and concentration" -q
4. docker compose --profile test run --rm backend-test pytest tests -k "graph and ordering" -q
5. docker compose --profile test run --rm backend-test pytest tests -k "deterministic and replay" -q
6. docker compose --profile test run --rm -e PYTHONPATH=/app backend-test python scripts/generate_types.py --check
